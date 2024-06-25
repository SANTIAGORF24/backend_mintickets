from flask import Blueprint, jsonify, request
from app.models.tercero_model import Tercero
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('terceros', __name__, url_prefix='/terceros')

@bp.route('', methods=['GET'])
def get_terceros():
    terceros = Tercero.query.all()
    if terceros:
        terceros_data = [{'id': tercero.id, 'name': tercero.name, 'email': tercero.email} for tercero in terceros]
        return jsonify({'terceros': terceros_data}), 200
    else:
        return jsonify({'message': 'No se encontraron terceros'}), 404


@bp.route('', methods=['POST'])
def add_tercero():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    if not name or not email:
        return jsonify({'message': 'El nombre y el correo electrónico del tercero son requeridos'}), 400
    new_tercero = Tercero(name=name, email=email)
    db.session.add(new_tercero)
    db.session.commit()
    return jsonify({'message': 'Tercero agregado correctamente'}), 201

@bp.route('/<int:tercero_id>', methods=['OPTIONS', 'DELETE'])
def handle_tercero(tercero_id):
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight request handled successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 200
    elif request.method == 'DELETE':
        tercero = Tercero.query.get(tercero_id)
        if tercero:
            db.session.delete(tercero)
            db.session.commit()
            return jsonify({'message': 'Tercero eliminado correctamente'}), 200
        else:
            return jsonify({'message': 'Tercero no encontrado'}), 404

@bp.route('/<int:tercero_id>', methods=['PUT'])
def update_tercero(tercero_id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    if not name or not email:
        return jsonify({'message': 'El nombre y el correo electrónico del tercero son requeridos'}), 400
    tercero = Tercero.query.get(tercero_id)
    if tercero:
        tercero.name = name
        tercero.email = email
        db.session.commit()
        return jsonify({'message': 'Tercero actualizado correctamente'}), 200
    else:
        return jsonify({'message': 'Tercero no encontrado'}), 404
