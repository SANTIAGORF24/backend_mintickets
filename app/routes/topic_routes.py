from flask import Blueprint, jsonify, request
from app.models.topic_model import Topic
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('topics', __name__, url_prefix='/topics')

@bp.route('', methods=['GET'])
def get_topics():
    topics = Topic.query.all()
    output = []
    for topic in topics:
        output.append({'id': topic.id, 'name': topic.name})
    return jsonify({'topics': output})

@bp.route('', methods=['POST'])
def add_topic():
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