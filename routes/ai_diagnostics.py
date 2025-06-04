from flask import Blueprint, request, jsonify, session
from app import db
from app.models import Product, AuditLog
import cohere
import json
import traceback
import os
from datetime import datetime

ai_diagnostics_bp = Blueprint('ai_diagnostics', __name__, url_prefix='/api/ai-diagnostics')

# Initialize Cohere client with API key
# Note: In production, this should be stored in environment variables
COHERE_API_KEY = 'CupTE2mQkJNoA1DY0URp1fYPOV5d0IUSc0Wcmbak'
co = cohere.Client(COHERE_API_KEY)

@ai_diagnostics_bp.route('/diagnose/<int:product_id>', methods=['POST'])
def diagnose_equipment(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Get initial problem description
        data = request.get_json()
        initial_description = data.get('description', 'not working')
        
        # Log the diagnostic request
        print(f"Generating diagnostic questions for {product.product_name} (ID: {product_id})")
        
        # Generate diagnostic questions using Cohere
        diagnostic_response = co.chat(
            message=f"I need to diagnose a problem with {product.product_name} (type: {product.product_type}). " +
                   f"Initial issue: '{initial_description}'. " +
                   f"Generate exactly 10 diagnostic questions to identify the problem with this equipment. " +
                   f"The questions should be specific to troubleshooting {product.product_type} equipment. " +
                   f"Format the response as a JSON array of questions.",
            model="command",
            temperature=0.3
        )
        
        # Extract questions from response
        questions = []
        try:
            # Try to parse JSON from the response
            response_text = diagnostic_response.text
            print(f"Cohere response: {response_text[:100]}...")  # Log first 100 chars for debugging
            
            if '[' in response_text and ']' in response_text:
                json_str = response_text[response_text.find('['):response_text.rfind(']')+1]
                questions = json.loads(json_str)
            else:
                # Fallback: extract questions by line
                questions = [line.strip().strip('"').strip("'") for line in response_text.split('\n') 
                           if line.strip() and not line.strip().startswith('{') and not line.strip().startswith('}')]
                questions = questions[:10]  # Limit to 10 questions
        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")
            # Fallback questions if parsing fails
            questions = ["What is the specific issue you're experiencing?",
                        "When did the problem start?",
                        "Are there any error messages or unusual sounds?",
                        "Have you tried restarting the equipment?",
                        "Is the equipment receiving power?",
                        "Are all cables properly connected?",
                        "Has the equipment been recently moved or modified?",
                        "Are there any visible damages?",
                        "When was the last time the equipment worked properly?",
                        "Has this issue happened before?"]
        
        # Ensure we have at least 10 questions
        if len(questions) < 10:
            default_questions = [
                "Are there any unusual noises when operating the equipment?",
                "Have you noticed any performance degradation before it stopped working?",
                "Are there any warning lights or indicators showing?",
                "Has the equipment been serviced recently?",
                "Is the issue intermittent or constant?",
                "Has anything changed in the environment where the equipment is used?",
                "Are other similar equipment experiencing the same issue?",
                "What was the last successful operation performed with this equipment?",
                "Have you checked all fuses and circuit breakers?",
                "Is there any physical damage visible on the equipment?"
            ]
            questions.extend(default_questions[:(10-len(questions))])
        
        # Create an initial diagnostic log entry
        diagnostic_log = AuditLog(
            product_id=product.id,
            user_id=session.get('user_id'),
            action_type='ai_diagnostic_started',
            previous_value='equipment_not_working',
            new_value='diagnostic_in_progress',
            notes=f"AI diagnostic session started for {product.product_name}"
        )
        db.session.add(diagnostic_log)
        db.session.commit()
        
        return jsonify({
            'product_id': product_id,
            'product_name': product.product_name,
            'questions': questions[:10],  # Ensure we have max 10 questions
            'diagnostic_session_id': diagnostic_log.id
        }), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in AI diagnostics: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@ai_diagnostics_bp.route('/submit-diagnosis/<int:product_id>', methods=['POST'])
def submit_diagnosis(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # Get answers to diagnostic questions
        answers = data.get('answers', {})
        
        # Log the submission
        print(f"Processing diagnosis submission for {product.product_name} (ID: {product_id})")
        print(f"Received {len(answers)} answers")
        
        # Generate problem summary using Cohere
        answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()])
        
        summary_response = co.chat(
            message=f"Based on these answers about {product.product_name} (type: {product.product_type}), " +
                   f"provide a detailed technical diagnosis summary. Include:\n" +
                   f"1. Most likely cause of the problem\n" +
                   f"2. Recommended troubleshooting steps\n" +
                   f"3. Potential repair options\n\n" +
                   f"Diagnostic information:\n{answers_text}",
            model="command",
            temperature=0.2
        )
        
        problem_summary = summary_response.text
        
        # Format timestamp for the log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create audit log with the AI diagnosis
        audit_log = AuditLog(
            product_id=product.id,
            user_id=session.get('user_id'),
            action_type='ai_diagnosis',
            previous_value='equipment_not_working',
            new_value='diagnosis_complete',
            notes=f"[AI Diagnosis {timestamp}]\n\n{problem_summary}"
        )
        
        # Also update the product's special instructions with a reference to the diagnosis
        product.special_instructions = f"Not working - AI diagnosis completed on {timestamp}. See audit logs for details."
        
        db.session.add(audit_log)
        db.session.commit()
        
        print(f"Diagnosis saved successfully with log ID: {audit_log.id}")
        
        return jsonify({
            'product_id': product_id,
            'diagnosis_summary': problem_summary,
            'log_id': audit_log.id,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        db.session.rollback()
        error_details = traceback.format_exc()
        print(f"Error in AI diagnosis submission: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500