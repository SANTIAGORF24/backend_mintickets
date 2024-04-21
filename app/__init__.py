from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import secrets
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

key_length = 64
characters = string.ascii_letters + string.digits + string.punctuation
secret_key = ''.join(secrets.choice(characters) for _ in range(key_length))
app.config['JWT_SECRET_KEY'] = secret_key

db = SQLAlchemy(app)
CORS(app)  # Habilita CORS para toda la aplicación
jwt = JWTManager(app)

from app.models import user_model, topic_model, statu_model, tercero_model, ticket_model
from app.routes import auth_routes, topic_routes, statu_routes, tercero_routes, ticket_routes

app.register_blueprint(auth_routes.bp)
app.register_blueprint(topic_routes.bp)
app.register_blueprint(statu_routes.bp)
app.register_blueprint(tercero_routes.bp)
app.register_blueprint(ticket_routes.bp)


with app.app_context():
    db.create_all()
