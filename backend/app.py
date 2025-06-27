from functools import wraps
import jwt
from models import User
from models import User, JournalEntry
from models import User, JournalEntry, ChatMessage
import random
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, bcrypt
import requests
from dotenv import load_dotenv


load_dotenv()

# --- Initialization ---
app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_secure_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.xvvmrixhqqlwguqgzsan:AYOmhi562032;:@aws-0-eu-west-2.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Allow requests from specific origins for all routes under /api/
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://192.168.10.221:3000"]}})

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)

# --- Load Pre-trained Model and Data ---
intents = json.loads(open('intents.json').read())

# Decorator for token-based authentication
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        # --- Start Debug Prints ---
        print("\n--- Verifying Token ---")
        print(f"Secret Key being used: {app.config.get('SECRET_KEY')}")
        print(f"Token received: {token}")
        # --- End Debug Prints ---

        if not token:
            print("DEBUG: Token is missing.")
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Decode the token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['sub'])
            print(f"DEBUG: Token successfully decoded for user_id: {current_user.id}")

        except Exception as e:
            # This will print the exact decoding error to your terminal
            print(f"!!! TOKEN DECODE FAILED: {e}") 
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# --- Helper Functions ---
def query_hugging_face(payload, api_token):
    # Using a known, working conversational model URL
    API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
    headers = {"Authorization": f"Bearer {api_token}"}

    response = requests.post(API_URL, headers=headers, json=payload)

    print(f"--- Calling Hugging Face ---")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("ERROR: Hugging Face returned 200 OK but response was not valid JSON.")
            return {"error": "Received invalid success response from Hugging Face."}
    else:
        print(f"ERROR: Hugging Face returned an error. Raw Response Text: {response.text}")
        if "is currently loading" in response.text:
            return {"error": response.text} # Pass the loading message to the frontend
        return {"error": f"Hugging Face API failed with status {response.status_code}"}

# --- API Endpoints ---
@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    # --- IMPORTANT: PASTE YOUR HUGGING FACE TOKEN HERE ---
    # It's better to use environment variables for this in a real app,
    # but for now, we'll place it here for simplicity.
    HUGGING_FACE_API_TOKEN = os.environ.get("HUGGING_FACE_API_TOKEN")

    data = request.get_json()
    user_input = data.get('message', '')

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # Save the user's message to history first
    user_message = ChatMessage(content=user_input, sender='user', user_id=current_user.id)
    db.session.add(user_message)
    db.session.commit()

    # Get the last few messages to provide context to the model
    past_messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp.desc()).limit(5).all()
    past_user_inputs = [msg.content for msg in past_messages if msg.sender == 'user']
    generated_responses = [msg.content for msg in past_messages if msg.sender == 'bot']

    # Call the Hugging Face API
    api_payload = {
        "inputs": {
            "past_user_inputs": past_user_inputs,
            "generated_responses": generated_responses,
            "text": user_input,
        },
    }
    print("Calling Hugging Face API with payload...")
    api_response = query_hugging_face(api_payload, HUGGING_FACE_API_TOKEN)
    print(f"Hugging Face API Response: {api_response}")

    # Extract the bot's response
    bot_response_text = api_response.get('generated_text', "Sorry, I'm having trouble thinking right now.")

    # Save the bot's response to history
    bot_message = ChatMessage(content=bot_response_text, sender='bot', user_id=current_user.id)
    db.session.add(bot_message)
    db.session.commit()

    return jsonify({"response": bot_response_text})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    # Check if user already exists
    user = User.query.filter_by(email=data.get('email')).first()
    if user:
        return jsonify({'message': 'User already exists.'}), 400

    try:
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password')
        )
        db.session.add(new_user)
        db.session.commit()
        auth_token = new_user.encode_auth_token()
        return jsonify({'auth_token': auth_token}), 201
    except Exception as e:
        return jsonify({'message': 'Registration failed!', 'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        user = User.query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            auth_token = user.encode_auth_token()
            return jsonify({'auth_token': auth_token})
        else:
            return jsonify({'message': 'Invalid email or password.'}), 401
    except Exception as e:
        return jsonify({'message': 'Login failed!', 'error': str(e)}), 500

@app.route('/api/journal/entries', methods=['GET'])
@token_required
def get_journal_entries(current_user):
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.date_posted.desc()).all()
    output = []
    for entry in entries:
        entry_data = {
            'id': entry.id,
            'content': entry.content,
            'date_posted': entry.date_posted.strftime('%Y-%m-%d %H:%M:%S')
        }
        output.append(entry_data)
    return jsonify({'entries': output})

@app.route('/api/journal/entries', methods=['POST'])
@token_required
def create_journal_entry(current_user):
    data = request.get_json()
    new_entry = JournalEntry(content=data['content'], user_id=current_user.id)
    db.session.add(new_entry)
    db.session.commit()
    return jsonify({'message': 'Journal entry created!'}), 201

@app.route('/api/chat/history', methods=['GET'])
@token_required
def get_chat_history(current_user):
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp.asc()).all()
    history = []
    for msg in messages:
        history.append({
            'sender': msg.sender,
            'text': msg.content
        })
    return jsonify({'history': history})

if __name__ == '__main__':
    app.run(debug=True)