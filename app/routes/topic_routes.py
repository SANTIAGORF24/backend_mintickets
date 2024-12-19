from flask import Blueprint, jsonify, request
from app.models.topic_model import Topic
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity



bp = Blueprint('topics', __name__, url_prefix='/topics')



@bp.route('/', methods=['GET'])
def get_topics():
    """
    Recupera todos los temas de la base de datos y los devuelve como una respuesta JSON.

    Esta función consulta el modelo Topic para obtener todos los registros de temas,
    los formatea en una lista de diccionarios y devuelve la lista
    como una respuesta JSON.

    Returns:
        Response: Una respuesta JSON de Flask que contiene una lista de temas,
        donde cada tema se representa como un diccionario con las claves 'id' y 'name'.
    """
    topics = Topic.query.all()
    output = []
    for topic in topics:
        output.append({'id': topic.id, 'name': topic.name})
    return jsonify({'topics': output})

@bp.route('/', methods=['POST'])
def add_topic():
    """
    Agrega un nuevo tema a la base de datos.

    Esta función recupera datos JSON de la solicitud, extrae el campo 'name',
    y crea un nuevo objeto Topic con el nombre proporcionado. El nuevo tema se agrega
    a la sesión de la base de datos y se confirma.

    Returns:
        Response: Una respuesta JSON con un mensaje de éxito y un código de estado HTTP 201 si el tema se agrega correctamente.
        Response: Una respuesta JSON con un mensaje de error y un código de estado HTTP 400 si falta el campo 'name'.
    """
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'message': 'El nombre del tema es requerido'}), 400
    new_topic = Topic(name=name)
    db.session.add(new_topic)
    db.session.commit()
    return jsonify({'message': 'Tema agregado correctamente'}), 201

@bp.route('/<int:topic_id>', methods=['OPTIONS', 'DELETE'])
def handle_topic(topic_id):
    """
    Maneja solicitudes HTTP para un tema específico.

    Args:
        topic_id (int): El ID del tema a manejar.

    Returns:
        tuple: Una tupla que contiene una respuesta JSON y un código de estado HTTP.

    Maneja los siguientes métodos HTTP:
    - OPTIONS: Devuelve una respuesta de preflight para CORS.
    - DELETE: Elimina el tema especificado de la base de datos.
        - Si se encuentra y elimina el tema, devuelve un mensaje de éxito con un código de estado 200.
        - Si no se encuentra el tema, devuelve un mensaje de error con un código de estado 404.
    """
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight request handled successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 200
    elif request.method == 'DELETE':
        topic = Topic.query.get(topic_id)
        if topic:
            db.session.delete(topic)
            db.session.commit()
            return jsonify({'message': 'Topic deleted successfully'}), 200
        else:
            return jsonify({'message': 'Topic not found'}), 404

@bp.route('/<int:topic_id>', methods=['PUT'])
def update_topic(topic_id):
    """
    Actualiza el nombre de un tema existente.

    Args:
        topic_id (int): El ID del tema a actualizar.

    Returns:
        Response: Una respuesta JSON con un mensaje que indica el resultado de la operación de actualización.
                  - Si falta el campo 'name' en los datos de la solicitud, devuelve un código de estado 400 con un mensaje de error.
                  - Si se encuentra y actualiza correctamente el tema con el ID dado, devuelve un código de estado 200 con un mensaje de éxito.
                  - Si no se encuentra el tema con el ID dado, devuelve un código de estado 404 con un mensaje de error.
    """
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'message': 'El nombre del tema es requerido'}), 400
    topic = Topic.query.get(topic_id)
    if topic:
        topic.name = name
        db.session.commit()
        return jsonify({'message': 'Tema actualizado correctamente'}), 200
    else:
        return jsonify({'message': 'Tema no encontrado'}), 404