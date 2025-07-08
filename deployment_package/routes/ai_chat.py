from flask import Blueprint, request, jsonify, session
from app.models import db, User, AuditLog
import cohere
import traceback
from datetime import datetime
import base64
import os

ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/api/ai-chat')

# Initialize Cohere client with API key
COHERE_API_KEY = 'CupTE2mQkJNoA1DY0URp1fYPOV5d0IUSc0Wcmbak'
co = cohere.Client(COHERE_API_KEY)

@ai_chat_bp.route('/send-message', methods=['POST'])
def send_message():
    """Send a message to the KIBS AI Assistant (public endpoint)"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        image_data = data.get('image')
        
        # Removed login_required authentication, so user may not be set.
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            username = user.username if user else "unknown"
        else:
            username = "anonymous"
        
        # Process image if provided
        image_url = None
        if image_data:
            try:
                # Extract base64 data if it contains a prefix
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                
                # Save image to temporary file
                image_bytes = base64.b64decode(image_data)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"user_upload_{user_id or 'anon'}_{timestamp}.jpg"
                filepath = os.path.join('uploads', filename)
                
                # Ensure directory exists
                os.makedirs('uploads', exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                image_url = filepath
            except Exception as e:
                print(f"Error processing image: {str(e)}")
        
        # Prepare chat parameters
        chat_params = {
            'message': message,
            'model': 'command',
            'temperature': 0.7,
        }
        
        # Include conversation ID if provided
        if conversation_id:
            chat_params['conversation_id'] = conversation_id
        
        # Include image attachment if available
        if image_url:
            chat_params['attachments'] = [{'url': image_url}]
        
        # Call Cohere API to get AI response
        response = co.chat(**chat_params)
        
        # Log the interaction (user_id may be None for anonymous users)
        log_entry = AuditLog(
            product_id=1,  # Placeholder value
            user_id=user_id,
            action_type='ai_chat',
            previous_value='user_message',
            new_value='ai_response',
            notes=f"User {username} chatted with AI assistant"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Clean up image file if created
        if image_url and os.path.exists(image_url):
            try:
                os.remove(image_url)
            except Exception:
                pass
        
        return jsonify({
            'response': response.text,
            'conversation_id': response.conversation_id,
            'success': True
        }), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in AI chat: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500