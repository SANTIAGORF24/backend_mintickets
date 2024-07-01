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
            return jsonify({'access_token': access_token, 'user_id': user.id, 'user_email': user.email}), 200
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
        full_name = f"{user.first_name} {user.last_name}"
        return jsonify({'email': user.email, 'id': user.id, 'full_name': full_name}), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@bp.route('/users/username/<username>', methods=['GET'])
def get_user_by_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@bp.route('/users/email/<email>', methods=['GET'])
def get_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@bp.route('/users/firstName/<first_name>', methods=['GET'])
def get_user_by_first_name(first_name):
    user = User.query.filter_by(first_name=first_name).first()
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@bp.route('/users/lastName/<last_name>', methods=['GET'])
def get_user_by_last_name(last_name):
    user = User.query.filter_by(last_name=last_name).first()
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@bp.route('/users/username/<username>', methods=['PUT'])
def update_user_by_username(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    data = request.get_json()

    new_username = data.get('username', user.username)
    new_password = data.get('password', user.password)
    new_email = data.get('email', user.email)
    new_first_name = data.get('first_name', user.first_name)
    new_last_name = data.get('last_name', user.last_name)

    user.username = new_username
    user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user.email = new_email
    user.first_name = new_first_name
    user.last_name = new_last_name

    try:
        db.session.commit()
        return jsonify({'message': 'Usuario actualizado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar el usuario: {str(e)}'}), 500


@bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
def update_user_by_id(id):
    user = User.query.get(id)

    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    data = request.get_json()

    new_username = data.get('username', user.username)
    new_password = data.get('password', user.password)
    new_email = data.get('email', user.email)
    new_first_name = data.get('first_name', user.first_name)
    new_last_name = data.get('last_name', user.last_name)

    user.username = new_username
    user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user.email = new_email
    user.first_name = new_first_name
    user.last_name = new_last_name

    try:
        db.session.commit()
        return jsonify({'message': 'Usuario actualizado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar el usuario: {str(e)}'}), 500

@bp.route('/users/<username>', methods=['DELETE'])
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Usuario eliminado con éxito'}), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@bp.route('/users/names', methods=['GET'])
def get_user_names():
    users = User.query.all()
    if users:
        user_names = [{'id': user.id, 'name': f"{user.first_name} {user.last_name}", 'email': user.email} for user in users]
        return jsonify({'user_names': user_names}), 200
    else:
        return jsonify({'message': 'No se encontraron usuarios'}), 404

@bp.route('/tickets/register', methods=['POST'])
def register_ticket():
    data = request.get_json()
    fecha_creacion = data.get('fecha_creacion')
    tema = data.get('tema')
    estado = data.get('estado')
    tercero_nombre = data.get('tercero_nombre')
    especialista_nombre = data.get('especialista_nombre')
    especialista_id = data.get('especialista_id')
    descripcion_caso = data.get('descripcion_caso')
    solucion_caso = data.get('solucion_caso')

    # Aquí puedes utilizar los datos recibidos para crear el ticket en tu base de datos
    # Asegúrate de utilizar especialista_id para almacenar el ID del especialista

    return jsonify({'message': 'Ticket creado exitosamente'}), 201
