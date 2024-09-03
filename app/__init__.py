# En app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import secrets
import string
from dotenv import load_dotenv
from datetime import timedelta

# Configuración para que el token expire en 7 días
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuración de la URI de PostgreSQL usando la variable de entorno DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:PSRPtpWqYkZotNbYKRNtUiFoBiiaGsBu@junction.proxy.rlwy.net:38234/railway')
# Generar una clave secreta para JWT
key_length = 64
characters = string.ascii_letters + string.digits + string.punctuation
secret_key = ''.join(secrets.choice(characters) for _ in range(key_length))
app.config['JWT_SECRET_KEY'] = secret_key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # Ajusta la duración aquí


db = SQLAlchemy(app)

# Configura CORS para permitir solicitudes desde tu dominio de producción y localhost
CORS(app, resources={r"/*": {"origins": ["https://mintickets.vercel.app", "http://localhost:3000", "http://127.0.0.1:3000"]}})

jwt = JWTManager(app)

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

with app.app_context():
    db.create_all()
