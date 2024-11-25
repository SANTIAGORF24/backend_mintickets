import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import secrets
import string
from dotenv import load_dotenv
from datetime import timedelta

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Generate secret key for JWT
key_length = 64
characters = string.ascii_letters + string.digits + string.punctuation
secret_key = ''.join(secrets.choice(characters) for _ in range(key_length))

# JWT Configuration
app.config['JWT_SECRET_KEY'] = secret_key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],  # Add your frontend URL
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# JWT error handlers
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {"message": "Token inválido"}, 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return {"message": "El token ha expirado"}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {"message": "Token no proporcionado"}, 401

# Import and register blueprints
from app.models import user_model, topic_model, statu_model, tercero_model, ticket_model
from app.routes import auth_routes, topic_routes, statu_routes, tercero_routes, ticket_routes

app.register_blueprint(auth_routes.bp)
app.register_blueprint(topic_routes.bp)
app.register_blueprint(statu_routes.bp)
app.register_blueprint(tercero_routes.bp)
app.register_blueprint(ticket_routes.bp)

@app.route('/')
def home():
    return "Servidor funcionando correctamente"

# Create database tables
with app.app_context():
    db.create_all()