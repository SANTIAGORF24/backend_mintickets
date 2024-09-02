from flask import Blueprint, jsonify, request
from app.models.statu_model import Statu
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('status', __name__, url_prefix='/status')

@bp.route('', methods=['GET'])
def get_status():
    status = Statu.query.all()
    output = []
    for statu in status:
        output.append({'id': statu.id, 'name': statu.name})
    return jsonify({'status': output})

@bp.route('', methods=['POST'])
def add_statu():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'message': 'El nombre del tema es requerido'}), 400
    new_statu = Statu(name=name)
    db.session.add(new_statu)
    db.session.commit()
    return jsonify({'message': 'Tema agregado correctamente'}), 201

@bp.route('/<int:statu_id>', methods=['OPTIONS', 'DELETE'])
def handle_statu(statu_id):
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight request handled successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 200
    elif request.method == 'DELETE':
        statu = Statu.query.get(statu_id)
        if statu:
            db.session.delete(statu)
            db.session.commit()
            return jsonify({'message': 'statu deleted successfully'}), 200
        else:
            return jsonify({'message': 'statu not found'}), 404

@bp.route('/<int:statu_id>', methods=['PUT'])
def update_statu(statu_id):
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'message': 'El nombre del tema es requerido'}), 400
    statu = Statu.query.get(statu_id)
    if statu:
        statu.name = name
        db.session.commit()
        return jsonify({'message': 'Tema actualizado correctamente'}), 200
    else:
        return jsonify({'message': 'Tema no encontrado'}), 404