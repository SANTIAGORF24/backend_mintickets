import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import secrets
import string
from dotenv import load_dotenv
from datetime import timedelta
from flask_migrate import Migrate


# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# JWT Secret Key Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# Si no existe en las variables de entorno, genera una nueva
if not JWT_SECRET_KEY:
    key_length = 64
    characters = string.ascii_letters + string.digits + string.punctuation
    JWT_SECRET_KEY = ''.join(secrets.choice(characters) for _ in range(key_length))

# JWT Configuration
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": [os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize extensions
# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Import and register blueprints
from app.models import user_model, topic_model, statu_model, tercero_model, ticket_model
from app.routes import (
    auth_routes, 
    topic_routes, 
    statu_routes, 
    tercero_routes, 
    ticket_routes, 
    terceros_routes
)

app.register_blueprint(auth_routes.bp)
app.register_blueprint(topic_routes.bp)
app.register_blueprint(statu_routes.bp)
app.register_blueprint(tercero_routes.bp)
app.register_blueprint(ticket_routes.bp)
app.register_blueprint(terceros_routes.bp)

@app.route('/')
def home():
    return "Servidor funcionando correctamente"

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True')