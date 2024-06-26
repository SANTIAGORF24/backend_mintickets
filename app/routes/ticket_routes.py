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
            fecha_creacion=datetime.strptime(data["fecha_creacion"], "%Y-%m-%dT%H:%M:%S.%fZ").date(),
            tema=data["tema"],
            estado=data["estado"],
            tercero_nombre=data["tercero_nombre"],
            tercero_email=data["tercero_email"],  # Incluir el correo del tercero
            especialista_nombre=data["especialista_nombre"],
            especialista_email=data["especialista_email"],  # Incluir el correo del especialista
            descripcion_caso=data["descripcion_caso"],
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
    tickets_data = []
    for ticket in tickets:
        ticket_info = {
            "id": ticket.id,
            "fecha_creacion": ticket.fecha_creacion.strftime("%Y-%m-%d"),
            "tema": ticket.tema,
            "estado": ticket.estado,
            "tercero_nombre": ticket.tercero_nombre,
            "tercero_email": ticket.tercero_email,  # Incluir el correo del tercero
            "especialista_nombre": ticket.especialista_nombre,
            "especialista_email": ticket.especialista_email,  # Incluir el correo del especialista
            "descripcion_caso": ticket.descripcion_caso,
            "solucion_caso": ticket.solucion_caso
        }
        if ticket.fecha_finalizacion:  # Verificar si la fecha de finalización no es None
            ticket_info["fecha_finalizacion"] = ticket.fecha_finalizacion.strftime("%Y-%m-%d")
        else:
            ticket_info["fecha_finalizacion"] = None  # Opcional: Puedes establecerlo como None o cualquier otro valor que desees
        tickets_data.append(ticket_info)
    return jsonify(tickets_data)


@bp.route("/<int:id>", methods=["DELETE"])
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket eliminado correctamente"}), 200


@bp.route("/<int:id>", methods=["PUT", "PATCH"])
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.json
    try:
        ticket.fecha_finalizacion = datetime.utcnow()  # Actualizar la fecha de finalización
        ticket.tema = data.get("tema", ticket.tema)
        ticket.estado = data.get("estado", ticket.estado)
        ticket.tercero_nombre = data.get("tercero_nombre", ticket.tercero_nombre)
        ticket.tercero_email = data.get("tercero_email", ticket.tercero_email)  # Actualizar el correo del tercero
        ticket.especialista_nombre = data.get("especialista_nombre", ticket.especialista_nombre)
        ticket.especialista_email = data.get("especialista_email", ticket.especialista_email)  # Actualizar el correo del especialista
        ticket.descripcion_caso = data.get("descripcion_caso", ticket.descripcion_caso)
        ticket.solucion_caso = data.get("solucion_caso", ticket.solucion_caso)
        db.session.commit()
        return jsonify({"message": "Ticket actualizado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
