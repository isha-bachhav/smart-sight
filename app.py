import os
import base64
import time
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, session, make_response, current_app
from flask_cors import CORS
from openai_service import analyze_image, describe_surroundings, recognize_text
from voice_service import text_to_speech, recognize_speech
from chatbot_service import get_chatbot_response
from models import db, ChatbotResponse, UserQuery, KnowledgeBase

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# Initialize the database
db.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Enable CORS for all routes
CORS(app)
# Define a function to handle CORS and cache control in a single after_request handler
@app.after_request
def add_cors_and_cache_headers(response):
    """Add CORS and cache control headers to responses."""
    # CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # Cache control headers
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')

@app.route('/api/welcome', methods=['GET'])
def welcome_message():
    """Get the initial welcome message from the chatbot."""
    try:
        # Get the welcome message using the special key
        from chatbot_service import get_chatbot_response
        response = get_chatbot_response("__welcome_message__")
        
        # Return the welcome message
        return jsonify({
            "success": True,
            "message": response,
            "timestamp": str(time.time())
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-image', methods=['POST'])
def process_image():
    """Analyze an image and return the description."""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    try:
        # Get the image from the request
        image_file = request.files['image']
        
        # Make sure we have actual image data
        if image_file.filename == '':
            return jsonify({"error": "Empty image file"}), 400
            
        # Add a timestamp to ensure uniqueness
        timestamp = str(time.time())
        
        # Convert image to base64
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Analyze the image with timestamp to prevent caching
        analysis = analyze_image(image_data, timestamp)
        
        # Return the analysis
        return jsonify({"success": True, "description": analysis, "timestamp": timestamp})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech_api():
    """Convert text to speech and return the audio file."""
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        text = data['text']
        audio_content = text_to_speech(text)
        
        # Return base64 encoded audio
        return jsonify({
            "success": True,
            "audio": base64.b64encode(audio_content).decode('utf-8')
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/describe-surroundings', methods=['POST'])
def describe_surroundings_api():
    """Describe the surroundings based on image and context."""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    try:
        # Get the image and context from the request
        image_file = request.files['image']
        context = request.form.get('context', '')
        
        # Make sure we have actual image data
        if image_file.filename == '':
            return jsonify({"error": "Empty image file"}), 400
            
        # Add a timestamp to ensure uniqueness
        timestamp = str(time.time())
        
        # Convert image to base64
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Get the description with timestamp to prevent caching
        description = describe_surroundings(image_data, context, timestamp)
        
        # Return the description
        return jsonify({"success": True, "description": description, "timestamp": timestamp})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/read-text', methods=['POST'])
def read_text_api():
    """Extract and read text from an image."""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    try:
        # Get the image from the request
        image_file = request.files['image']
        
        # Make sure we have actual image data
        if image_file.filename == '':
            return jsonify({"error": "Empty image file"}), 400
            
        # Add a timestamp to ensure uniqueness
        timestamp = str(time.time())
        
        # Convert image to base64
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Extract text from the image
        # We don't need to modify recognize_text since it doesn't cache results
        text = recognize_text(image_data)
        
        # Return the extracted text
        return jsonify({"success": True, "text": text, "timestamp": timestamp})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """Process a user voice query and return an AI-generated response."""
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Get query from the request
        user_query = data['query']
        use_memory = data.get('use_memory', True)
        
        # Create a session ID if not in session yet
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            
        # Get the chatbot response
        response = get_chatbot_response(user_query, session['session_id'], use_memory)
        
        # Log this query and response to the database
        try:
            # Create a new UserQuery record
            new_query = UserQuery(
                session_id=session['session_id'],
                query=user_query,
                response=response
            )
            db.session.add(new_query)
            db.session.commit()
        except Exception as db_error:
            print(f"Error logging query to database: {str(db_error)}")
            # Continue execution even if logging fails
            db.session.rollback()
        
        # Return the response
        return jsonify({
            "success": True, 
            "response": response, 
            "timestamp": str(time.time())
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text_api():
    """Convert speech audio to text."""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio provided"}), 400
    
    try:
        # Get the audio from the request
        audio_file = request.files['audio']
        
        # Make sure we have actual audio data
        if audio_file.filename == '':
            return jsonify({"error": "Empty audio file"}), 400
            
        # Process the audio data
        audio_data = audio_file.read()
        
        # Convert speech to text
        text = recognize_speech(audio_data)
        
        # Return the recognized text
        return jsonify({
            "success": True, 
            "text": text, 
            "timestamp": str(time.time())
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# The cache control headers are now handled in the add_cors_and_cache_headers function

@app.route('/api/chatbot-responses', methods=['GET', 'POST'])
def manage_chatbot_responses():
    """Get or add chatbot responses."""
    if request.method == 'GET':
        # Get all active chatbot responses
        try:
            responses = ChatbotResponse.query.filter_by(active=True).all()
            response_list = []
            
            for resp in responses:
                response_list.append({
                    'id': resp.id,
                    'pattern': resp.pattern,
                    'response': resp.response,
                    'category': resp.category
                })
            
            return jsonify({
                "success": True,
                "responses": response_list,
                "count": len(response_list),
                "timestamp": str(time.time())
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        # Add a new chatbot response
        data = request.json
        
        if not data or 'pattern' not in data or 'response' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        try:
            # Create a new chatbot response
            new_response = ChatbotResponse(
                pattern=data['pattern'].lower().strip(),
                response=data['response'],
                category=data.get('category', 'general')
            )
            
            db.session.add(new_response)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "id": new_response.id,
                "message": "Chatbot response added successfully",
                "timestamp": str(time.time())
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

# Function to add knowledge base items programmatically
def add_knowledge_base_item(question, answer, category="general"):
    """
    Add a new item to the knowledge base.
    
    Args:
        question (str): The question to be added
        answer (str): The answer to the question
        category (str): Category of the knowledge (default: "general")
        
    Returns:
        KnowledgeBase: The newly created knowledge base item or None if there was an error
    """
    try:
        # Check if this question already exists to avoid duplicates
        existing_item = KnowledgeBase.query.filter(
            KnowledgeBase.question.ilike(f"%{question}%"),
            KnowledgeBase.active == True
        ).first()
        
        if existing_item:
            print(f"Knowledge base item already exists for question: {question}")
            # Update the existing answer if it's different
            if existing_item.answer != answer:
                existing_item.answer = answer
                existing_item.updated_at = datetime.datetime.utcnow()
                db.session.commit()
                print(f"Updated existing knowledge base item: {existing_item.id}")
            return existing_item
            
        # Create a new knowledge base item
        new_item = KnowledgeBase(
            question=question.lower().strip(),
            answer=answer,
            category=category
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        print(f"Added new knowledge base item: {new_item.id}")
        return new_item
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding knowledge base item: {str(e)}")
        return None

@app.route('/api/knowledge-base', methods=['GET', 'POST'])
def manage_knowledge_base():
    """Get or add knowledge base items."""
    if request.method == 'GET':
        # Get all active knowledge base items
        try:
            items = KnowledgeBase.query.filter_by(active=True).all()
            item_list = []
            
            for item in items:
                item_list.append({
                    'id': item.id,
                    'question': item.question,
                    'answer': item.answer,
                    'category': item.category
                })
            
            return jsonify({
                "success": True,
                "items": item_list,
                "count": len(item_list),
                "timestamp": str(time.time())
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        # Add a new knowledge base item
        data = request.json
        
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        new_item = add_knowledge_base_item(
            question=data['question'],
            answer=data['answer'],
            category=data.get('category', 'general')
        )
        
        if new_item:
            return jsonify({
                "success": True,
                "id": new_item.id,
                "message": "Knowledge base item added successfully",
                "timestamp": str(time.time())
            })
        else:
            return jsonify({"error": "Failed to add knowledge base item"}), 500

@app.route('/api/add-knowledge', methods=['POST'])
def add_knowledge_api():
    """
    Add knowledge to the database via a simple API.
    This endpoint is designed to be easy to use for adding knowledge items.
    """
    data = request.json
    
    if not data or 'question' not in data or 'answer' not in data:
        return jsonify({"error": "Missing required fields. Please provide 'question' and 'answer'."}), 400
        
    try:
        question = data['question']
        answer = data['answer']
        category = data.get('category', 'user-provided')
        
        new_item = add_knowledge_base_item(question, answer, category)
        
        if new_item:
            return jsonify({
                "success": True,
                "message": "Knowledge added successfully!",
                "id": new_item.id,
                "question": new_item.question,
                "answer": new_item.answer,
                "timestamp": str(time.time())
            })
        else:
            return jsonify({"error": "Failed to add knowledge item to database"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Replit."""
    return jsonify({"status": "healthy", "timestamp": str(time.time())})

if __name__ == '__main__':
    # Configure the port based on Replit's environment
    # For Replit, we MUST use port 5000 - this is critical for the app to be accessible
    port = 5000
    
    # Print detailed environment info for debugging
    print(f"\n===== ENVIRONMENT INFO =====")
    print(f"Current directory: {os.getcwd()}")
    print(f"Port: {port}")
    replit_domain = os.environ.get("REPL_SLUG", "unknown")
    print(f"Repl slug: {replit_domain}")
    print(f"REPL_ID: {os.environ.get('REPL_ID', 'unknown')}")
    print(f"REPL_OWNER: {os.environ.get('REPL_OWNER', 'unknown')}")
    print(f"===========================\n")
    
    print(f"Starting server on port {port}")
    print(f"Server accessible at http://0.0.0.0:{port}")
    print(f"For local access use: http://localhost:{port}")
    
    # Run the application with Replit-friendly settings - removed use_reloader for stability
    # Print additional URL information for clarity
    print(f"\nFull Replit URL: https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.replit.app")
    print(f"Access this app in your Replit webview\n")
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
