import bcrypt
from flask import Blueprint, jsonify, request
from app.models.user_model import User
from app import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'El usuario ya existe'}), 409
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    new_user = User(username=username, password=hashed_password.decode('utf-8'), email=email, first_name=first_name, last_name=last_name)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Usuario registrado exitosamente'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user:
        password_bytes = password.encode('utf-8')
        if bcrypt.checkpw(password_bytes, user.password.encode('utf-8')):
            access_token = create_access_token(identity=user.id)
            return jsonify({'access_token': access_token, 'user_email': user.email}), 200
        else:
            return jsonify({'message': 'Contraseña inválida'}), 401
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user:
        return jsonify({'email': user.email}), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404