import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import secrets
import string
from datetime import timedelta

app = Flask(__name__)

# Configuración directa de la URI de PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://default:SMfsCEoQNW24@ep-falling-butterfly-a4tb3gq8-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"

# Generar una clave secreta para JWT
key_length = 64
characters = string.ascii_letters + string.digits + string.punctuation
secret_key = ''.join(secrets.choice(characters) for _ in range(key_length))
app.config['JWT_SECRET_KEY'] = secret_key

db = SQLAlchemy(app)

# Configurar CORS para permitir múltiples orígenes
CORS(app, resources={r"/*": {"origins": "*"}})

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
