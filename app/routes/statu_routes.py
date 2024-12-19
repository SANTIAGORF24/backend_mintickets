from flask import Blueprint, jsonify, request
from app.models.statu_model import Statu
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity



bp = Blueprint('status', __name__, url_prefix='/status')



@bp.route('/', methods=['GET'])
def get_status():
    """
    Recupera todos los registros de estado de la base de datos y los devuelve como una respuesta JSON.

    Esta función consulta todos los registros de la tabla Statu, los formatea en una lista de diccionarios,
    y devuelve la lista como una respuesta JSON.

    Retorna:
        Response: Una respuesta JSON que contiene una lista de registros de estado, donde cada registro
                  se representa como un diccionario con las claves 'id' y 'name'.
    """
    status = Statu.query.all()
    output = []
    for statu in status:
        output.append({'id': statu.id, 'name': statu.name})
    return jsonify({'status': output})

@bp.route('/', methods=['POST'])
def add_statu():
    """
    Agrega un nuevo estado a la base de datos.

    Esta función recupera datos JSON de la solicitud, extrae el campo 'name',
    y agrega un nuevo estado a la base de datos. Si falta el campo 'name', devuelve
    una respuesta de error 400.

    Retorna:
        Response: Una respuesta JSON con un mensaje de éxito y un código de estado 201 si el
                  estado se agrega correctamente.
                  Una respuesta JSON con un mensaje de error y un código de estado 400 si falta el
                  campo 'name'.
    """
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
    """
    Maneja solicitudes HTTP para un estado específico.

    Args:
        statu_id (int): El ID del estado a manejar.

    Retorna:
        Response: Un objeto de respuesta de Flask con un mensaje JSON y un código de estado HTTP.

    Maneja los siguientes métodos HTTP:
    - OPTIONS: Devuelve una respuesta de preflight para CORS.
    - DELETE: Elimina el estado con el ID dado de la base de datos.
        - Si se encuentra y elimina el estado, devuelve un mensaje de éxito con un código de estado 200.
        - Si no se encuentra el estado, devuelve un mensaje de error con un código de estado 404.
    """
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
    """
    Actualiza el nombre de un estado en la base de datos.

    Args:
        statu_id (int): El ID del estado a actualizar.

    Retorna:
        Response: Una respuesta JSON con un mensaje que indica el resultado de la operación.
                  - Si falta el campo 'name' en los datos de la solicitud, devuelve un código de estado 400 con un mensaje de error.
                  - Si se encuentra y actualiza correctamente el estado con el ID dado, devuelve un código de estado 200 con un mensaje de éxito.
                  - Si no se encuentra el estado con el ID dado, devuelve un código de estado 404 con un mensaje de error.
    """
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