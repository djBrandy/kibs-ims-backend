from flask import Blueprint, request, jsonify, current_app
import requests
import json
import base64
from urllib.parse import quote

ai_agent_bp = Blueprint('ai_agent', __name__, url_prefix='/api/ai-agent')

@ai_agent_bp.route('/product-info', methods=['POST'])
def get_product_info():
    try:
        data = request.get_json()
        product_code = data.get('product_code')
        code_type = data.get('code_type', 'product_code')  # Default to product_code if not specified
        
        if not product_code:
            return jsonify({'error': 'Product code or barcode is required'}), 400
        
        # Define the exact product types and categories as they appear in the form
        product_types = [
            "reagent", "equipment", "consumable", "kit", "software", 
            "biological samples", "reference material", "protective equipment", 
            "data storage devices", "lab furniture", "specialized media", 
            "diagnostic kits", "waste disposal supplies", "other"
        ]
        
        categories = [
            "pcr", "sequencing", "cell_culture", "microscopy", "centrifugation", 
            "electrophoresis", "reagents and chemicals", "laboratory equipment", 
            "consumables and supplies", "Test Kits & Assay Kits", "other"
        ]
        
        # UPC Database API call
        api_key = current_app.config['UPC_DATABASE_API_KEY']
        encoded_code = quote(product_code)
        url = f"https://api.upcdatabase.org/product/{encoded_code}?apikey={api_key}"
        
        response = requests.get(url)
        
        # Initialize default product info
        product_info = {
            "product_name": "",
            "product_type": "other",
            "category": "other",
            "manufacturer": "",
            "price_in_kshs": "",
            "unit_of_measure": "unit",
            "concentration": "",
            "storage_temperature": "Room Temperature (~15°C to 25°C)",
            "hazard_level": "none",
            "protocol_link": "",
            "msds_link": "",
            "special_instructions": "",
            "image_url": "",
            "product_images": None,
            "product_code": product_code  # Include the original product code
        }
        
        if response.status_code == 200:
            upc_data = response.json()
            
            # Map UPC Database fields to our product fields
            if upc_data.get('success'):
                product_info["product_name"] = upc_data.get('title', '')
                product_info["manufacturer"] = upc_data.get('brand', '')
                
                # Try to determine product type based on description or category
                description = upc_data.get('description', '').lower()
                
                # Determine product type based on description
                if any(word in description for word in ['reagent', 'chemical', 'solution']):
                    product_info["product_type"] = "reagent"
                    product_info["category"] = "reagents and chemicals"
                elif any(word in description for word in ['equipment', 'instrument', 'machine']):
                    product_info["product_type"] = "equipment"
                    product_info["category"] = "laboratory equipment"
                elif any(word in description for word in ['consumable', 'disposable']):
                    product_info["product_type"] = "consumable"
                    product_info["category"] = "consumables and supplies"
                elif any(word in description for word in ['kit', 'test kit']):
                    product_info["product_type"] = "kit"
                    product_info["category"] = "Test Kits & Assay Kits"
                
                # Get image if available
                if upc_data.get('images') and len(upc_data['images']) > 0:
                    product_info["image_url"] = upc_data['images'][0]
                    
                    # Try to fetch the image
                    try:
                        image_response = requests.get(product_info["image_url"], timeout=5)
                        if image_response.status_code == 200:
                            product_info["product_images"] = base64.b64encode(image_response.content).decode('utf-8')
                    except Exception as e:
                        print(f"Error fetching image: {str(e)}")
                
                # Convert price to KSh if available (assuming USD to KSh conversion rate of ~130)
                if upc_data.get('msrp'):
                    try:
                        price_usd = float(upc_data['msrp'])
                        product_info["price_in_kshs"] = str(round(price_usd * 130))
                    except (ValueError, TypeError):
                        pass
                
                # Extract any special instructions
                if upc_data.get('description'):
                    product_info["special_instructions"] = upc_data['description']
                
                return jsonify(product_info), 200
            else:
                return jsonify({
                    'error': 'Product not found in UPC Database',
                    'product_info': product_info
                }), 404
        else:
            return jsonify({
                'error': f'UPC Database API error: {response.status_code}',
                'product_info': product_info
            }), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500