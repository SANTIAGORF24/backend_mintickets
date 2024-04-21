from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket_model import Ticket
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint("tickets", __name__, url_prefix="/tickets")

@bp.route("/register", methods=["POST"])
def create_ticket():
    data = request.json
    try:
        new_ticket = Ticket(
            fecha_creacion=datetime.strptime(data["fecha_creacion"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            tema=data["tema"],
            estado=data["estado"],
            tercero_nombre=data["tercero_nombre"],
            especialista_nombre=data["especialista_nombre"],
            descripcion_caso=data["descripcion_caso"],
            solucion_caso=data["solucion_caso"]
        )
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify({"message": "Ticket creado correctamente"}), 201
    except KeyError as e:
        return jsonify({"message": f"Falta el campo requerido: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"message": f"Error en el formato de fecha: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@bp.route("/", methods=["GET"])
def get_tickets():
    tickets = Ticket.query.all()
    tickets_data = [{
        "id": ticket.id,
        "fecha_creacion": ticket.fecha_creacion.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "tema": ticket.tema,
        "estado": ticket.estado,
        "tercero_nombre": ticket.tercero_nombre,
        "especialista_nombre": ticket.especialista_nombre,
        "descripcion_caso": ticket.descripcion_caso,
        "solucion_caso": ticket.solucion_caso
    } for ticket in tickets]
    return jsonify(tickets_data)

@bp.route("/<int:id>", methods=["DELETE"])
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket eliminado correctamente"}), 200