from flask import Blueprint, request, jsonify, current_app
import cohere
from app.models import Product, Room
from app.database import db
from sqlalchemy import func, or_

inventory_assistant_bp = Blueprint('inventory_assistant', __name__, url_prefix='/api/inventory-assistant')

@inventory_assistant_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message')
        chat_history = data.get('history', [])
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Initialize Cohere client
        co = cohere.Client(current_app.config['COHERE_API_KEY'])
        
        # Get relevant inventory data to provide context
        inventory_context = get_inventory_context(user_message)
        
        # Create system prompt with biotech focus
        system_prompt = """
        You are KIBS AI Inventory Assistant, an expert in biotechnology laboratory inventory management.
        
        Your capabilities:
        - Provide accurate information about lab products, reagents, and equipment
        - Answer questions about inventory levels, storage requirements, and safety protocols
        - Suggest alternatives for out-of-stock items
        - Explain the use cases for different lab products
        - Provide guidance on proper storage and handling of sensitive materials
        - Help with inventory organization and optimization
        
        Guidelines:
        - Be concise, accurate, and scientifically precise
        - Use proper scientific terminology for biotechnology applications
        - When discussing products, include relevant details like storage temperature, concentration, and hazard information
        - For equipment, mention calibration requirements and maintenance schedules when relevant
        - Always prioritize safety when discussing hazardous materials
        - If you don't know something specific, acknowledge it and provide general guidance
        - Always respond with practical, actionable information
        - Use web search when needed to provide up-to-date information about biotechnology products
        - When discussing reagents, mention their applications in molecular biology, genomics, or proteomics
        - For PCR reagents, mention their specificity, fidelity, and optimal reaction conditions
        - For sequencing products, discuss their compatibility with different platforms (Illumina, Oxford Nanopore, PacBio)
        
        IMPORTANT FORMATTING INSTRUCTIONS:
        - Format your responses with clear headings and bullet points when appropriate
        - Use markdown formatting for emphasis: *italic* for emphasis, **bold** for important points
        - When mentioning product names, make them **bold**
        - When mentioning hazard levels, use appropriate emphasis: *mild*, **moderate**, ***severe***
        - Use numbered lists for step-by-step instructions
        - Use bullet points for listing features or characteristics
        
        The following is current inventory information that may be relevant to the user's query:
        {inventory_context}
        """
        
        # Format the system prompt with inventory context
        formatted_system_prompt = system_prompt.format(inventory_context=inventory_context)
        
        # Prepare chat history in Cohere format
        formatted_chat_history = []
        for message in chat_history:
            role = "USER" if message.get('role') == 'user' else "CHATBOT"
            formatted_chat_history.append({"role": role, "message": message.get('content')})
        
        try:
            # Try with web search connector first
            response = co.chat(
                message=user_message,
                model="command-r",
                temperature=0.1,
                chat_history=formatted_chat_history,
                preamble=formatted_system_prompt,
                connectors=[{"id": "web-search"}]
            )
        except Exception as e:
            print(f"Error with web search connector: {str(e)}")
            # Fall back to standard chat without connectors
            response = co.chat(
                message=user_message,
                model="command",
                temperature=0.1,
                chat_history=formatted_chat_history,
                preamble=formatted_system_prompt
            )
        
        return jsonify({
            'response': response.text,
            'citations': response.citations if hasattr(response, 'citations') else []
        }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_inventory_context(query):
    """Get relevant inventory data based on the user query"""
    try:
        # Search for products related to the query
        search_terms = query.lower().split()
        products_query = Product.query
        
        # Filter products based on search terms
        if len(search_terms) > 0:
            search_filters = []
            for term in search_terms:
                if len(term) > 2:  # Only search for terms with more than 2 characters
                    search_filters.append(
                        or_(
                            Product.product_name.ilike(f'%{term}%'),
                            Product.product_type.ilike(f'%{term}%'),
                            Product.category.ilike(f'%{term}%'),
                            Product.manufacturer.ilike(f'%{term}%'),
                            Product.special_instructions.ilike(f'%{term}%')
                        )
                    )
            
            if search_filters:
                products_query = products_query.filter(or_(*search_filters))
        
        # Get the top 10 most relevant products
        products = products_query.limit(10).all()
        
        # Format product information
        product_info = []
        for product in products:
            product_info.append({
                "id": product.id,
                "name": product.product_name,
                "type": product.product_type,
                "category": product.category,
                "manufacturer": product.manufacturer,
                "quantity": product.quantity,
                "unit": product.unit_of_measure,
                "concentration": product.concentration,
                "storage": product.storage_temperature,
                "hazard_level": product.hazard_level,
                "expiration_date": product.expiration_date.strftime('%Y-%m-%d') if product.expiration_date else None,
                "special_instructions": product.special_instructions,
                "room": product.room.name if product.room else "Unknown"
            })
        
        # Get overall inventory statistics
        total_products = Product.query.count()
        low_stock_count = Product.query.filter(Product.quantity <= Product.low_stock_alert).count()
        room_count = Room.query.count()
        
        # Get category statistics
        categories = db.session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
        category_stats = {category: count for category, count in categories}
        
        # Format the context as a string
        context = f"Inventory Summary: {total_products} total products, {low_stock_count} low stock items, {room_count} rooms\n\n"
        
        # Add category breakdown
        context += "Category Breakdown:\n"
        for category, count in category_stats.items():
            if category:
                context += f"- {category}: {count} products\n"
        
        context += "\n"
        
        if product_info:
            context += "Relevant Products:\n"
            for i, product in enumerate(product_info, 1):
                context += f"{i}. {product['name']} (ID: {product['id']}, Type: {product['type']}) - {product['quantity']} {product['unit']} - Manufacturer: {product['manufacturer']}\n"
                
                # Add concentration if available
                if product['concentration']:
                    context += f"   Concentration: {product['concentration']}, "
                
                context += f"Storage: {product['storage']}, Hazard: {product['hazard_level']}, Room: {product['room']}\n"
                
                # Add expiration date if available
                if product['expiration_date']:
                    context += f"   Expires: {product['expiration_date']}\n"
                
                # Add special instructions if available
                if product['special_instructions']:
                    context += f"   Special Instructions: {product['special_instructions']}\n"
                
                context += "\n"
        else:
            context += "No specific products found matching the query.\n"
        
        return context
        
    except Exception as e:
        print(f"Error getting inventory context: {str(e)}")
        return "Error retrieving inventory data."