from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket_model import Ticket
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_SERVER = 'smtp.office365.com'
SMTP_PORT = 587
SMTP_USERNAME = 'soportetics@mindeporte.gov.co'
SMTP_PASSWORD = '#B0g0t0@2024*'

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

        # Obtener el ID del ticket creado
        ticket_id = new_ticket.id

        # Preparar el cuerpo del correo electrónico
        email_body = f"""
        Ticket creado para {data['tercero_nombre']}

        Cordial saludo {data['tercero_nombre']}

        para consultar el estado de su ticket ingrese a http://localhost:3000/historial y digite el ID del ticket

        Se ha creado un nuevo ticket con la siguiente descripción:

        ID de ticket: {ticket_id}

        Tema: {data['tema']}

        Descripcion:

        {data['descripcion_caso']}

        El especialista {data['especialista_nombre']} lo atenderá lo más pronto posible

        Tenga en cuenta que los casos los especialistas los atienden en orden de llegada

        Atentamente,
        Soporte TICS
        """

        # Enviar correo electrónico
        send_email(
            to_address=[data["especialista_email"], data["tercero_email"]],
            subject=f"Nuevo Ticket Creado para {data['tercero_nombre']}",
            body=email_body
        )

        return jsonify({"message": "Ticket creado correctamente"}), 201
    except KeyError as e:
        return jsonify({"message": f"Falta el campo requerido: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"message": f"Error en el formato de fecha: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def send_email(to_address, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = ', '.join(to_address)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_address, text)
        server.quit()
    except Exception as e:
        print(f"Error enviando correo: {str(e)}")

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
            "tercero_email": ticket.tercero_email,
            "especialista_nombre": ticket.especialista_nombre,
            "especialista_email": ticket.especialista_email,
            "descripcion_caso": ticket.descripcion_caso,
            "solucion_caso": ticket.solucion_caso,
            "tiempo_de_respuesta": ticket.tiempo_de_respuesta,
            "actitud": ticket.actitud,
            "respuesta": ticket.respuesta
        }
        if ticket.fecha_finalizacion:
            ticket_info["fecha_finalizacion"] = ticket.fecha_finalizacion.strftime("%Y-%m-%d")
        else:
            ticket_info["fecha_finalizacion"] = None
        tickets_data.append(ticket_info)
    return jsonify(tickets_data)


@bp.route("/<int:id>", methods=["DELETE"])
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket eliminado correctamente"}), 200


@bp.route("/<int:id>", methods=["PATCH"])
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.json
    try:
        print("Datos recibidos para actualizar:", data)  # Verifica los datos recibidos

        ticket.fecha_finalizacion = datetime.utcnow()  # Actualizar la fecha de finalización
        ticket.tema = data.get("tema", ticket.tema)
        ticket.estado = data.get("estado", ticket.estado)  # Actualizar el estado si se recibe uno nuevo
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
        print(f"Error al actualizar el ticket: {str(e)}")  # Verifica el error
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:id>/finalize", methods=["PUT"])
def finalize_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.json
    try:
        ticket.fecha_finalizacion = datetime.utcnow()  # Actualizar la fecha de finalización
        ticket.tema = data.get("tema", ticket.tema)
        ticket.estado = "Solucionado"  # Cambiar el estado a Solucionado
        ticket.tercero_nombre = data.get("tercero_nombre", ticket.tercero_nombre)
        ticket.tercero_email = data.get("tercero_email", ticket.tercero_email)  # Actualizar el correo del tercero
        ticket.especialista_nombre = data.get("especialista_nombre", ticket.especialista_nombre)
        ticket.especialista_email = data.get("especialista_email", ticket.especialista_email)  # Actualizar el correo del especialista
        ticket.descripcion_caso = data.get("descripcion_caso", ticket.descripcion_caso)
        ticket.solucion_caso = data.get("solucion_caso", ticket.solucion_caso)
        db.session.commit()

        # Generar enlace de encuesta
        encuestaLink = f"http://localhost:3000/encuesta?id={ticket.id}"

        # Preparar el cuerpo del correo electrónico
        email_body = f"""
        Cordial saludo {ticket.tercero_nombre},

        El especialista {ticket.especialista_nombre} ha solucionado su ticket.

        Tema: {ticket.tema}

        Descripción del caso:
        {ticket.descripcion_caso}

        Solución al caso:
        {ticket.solucion_caso}

        Por favor, califique la solución del ticket aquí: {encuestaLink}

        Atentamente,
        Soporte TICS
        """

        # Enviar correo electrónico
        send_email(
            to_address=[ticket.tercero_email],
            subject=f"Solución ticket de {ticket.tercero_nombre}",
            body=email_body
        )

        return jsonify({"message": "Ticket finalizado y correo enviado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:id>", methods=["GET"])
def get_ticket(id):
    try:
        ticket = Ticket.query.get_or_404(id)
        ticket_info = {
            "id": ticket.id,
            "fecha_creacion": ticket.fecha_creacion.strftime("%Y-%m-%d"),
            "tema": ticket.tema,
            "estado": ticket.estado,
            "tercero_nombre": ticket.tercero_nombre,
            "tercero_email": ticket.tercero_email,
            "especialista_nombre": ticket.especialista_nombre,
            "especialista_email": ticket.especialista_email,
            "descripcion_caso": ticket.descripcion_caso,
            "solucion_caso": ticket.solucion_caso
        }
        if ticket.fecha_finalizacion:
            ticket_info["fecha_finalizacion"] = ticket.fecha_finalizacion.strftime("%Y-%m-%d")
        else:
            ticket_info["fecha_finalizacion"] = None
        return jsonify(ticket_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404



@bp.route("/<int:id>/rate", methods=["POST"])
def rate_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.json
    try:
        ticket.tiempo_de_respuesta = data.get("tiempo_de_respuesta")
        ticket.actitud = data.get("actitud")
        ticket.respuesta = data.get("respuesta")
        db.session.commit()
        return jsonify({"message": "Calificaciones actualizadas correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
