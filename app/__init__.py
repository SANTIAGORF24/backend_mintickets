import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Inicializar extensiones
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    # Cargar variables de entorno desde .env
    load_dotenv()

    app = Flask(__name__)

    # Configuración de la URI de PostgreSQL usando la variable de entorno DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:PSRPtpWqYkZotNbYKRNtUiFoBiiaGsBu@junction.proxy.rlwy.net:38234/railway')
    
    # Clave secreta para JWT desde variable de entorno
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'supersecretkey')  # Usa una clave fija en .env

    # Inicializar las extensiones con la aplicación
    db.init_app(app)
    jwt.init_app(app)
    
    CORS(app, resources={r"/*": {
        "origins": ["http://localhost:3000", "https://mintickets.vercel.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }})

    # Registrar Blueprints
    from app.routes import auth_routes, topic_routes, statu_routes, tercero_routes, ticket_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(topic_routes.bp)
    app.register_blueprint(statu_routes.bp)
    app.register_blueprint(tercero_routes.bp)
    app.register_blueprint(ticket_routes.bp)

    # Ruta simple
    @app.route('/')
    def home():
        return "Servidor funcionando correctamente"

    # Crear las tablas en la base de datos si no existen
    with app.app_context():
        db.create_all()

    return app
