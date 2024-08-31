from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket_model import Ticket
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64
from datetime import datetime, timedelta
import pytz


SMTP_SERVER = 'smtp.office365.com'
SMTP_PORT = 587
SMTP_USERNAME = 'soportetics@mindeporte.gov.co'
SMTP_PASSWORD = '#B0g0t0@2024*'

bp = Blueprint("tickets", __name__, url_prefix="/tickets")


@bp.route("/register", methods=["POST"])
def create_ticket():
    data = request.json
    try:
        # Usar la fecha y hora actual del servidor
        now = datetime.now(pytz.timezone('America/Bogota'))  # Ajustar la zona horaria si es necesario
        new_ticket = Ticket(
            fecha_creacion=now,
            tema=data["tema"],
            estado=data["estado"],
            tercero_nombre=data["tercero_nombre"],
            tercero_email=data["tercero_email"],
            especialista_nombre=data["especialista_nombre"],
            especialista_email=data["especialista_email"],
            descripcion_caso=data["descripcion_caso"],
            fecha_finalizacion=None  # Asegurar que la fecha de finalización esté en None al crear un nuevo ticket
        )
        db.session.add(new_ticket)
        db.session.commit()

        ticket_id = new_ticket.id

        email_body = f"""
        <h2>Ticket creado para {data['tercero_nombre']}</h2>
        <p>Cordial saludo {data['tercero_nombre']},</p>
        <p>Para consultar el estado de su ticket ingrese a <a href="http://localhost:3000/historial">http://localhost:3000/historial</a> y digite el ID del ticket</p>
        <p>Se ha creado un nuevo ticket con la siguiente descripción:</p>
        <ul>
            <li>ID de ticket: {ticket_id}</li>
            <li>Tema: {data['tema']}</li>
        </ul>
        <h3>Descripción:</h3>
        <p>{data['descripcion_caso']}</p>
        <p>El especialista {data['especialista_nombre']} lo atenderá lo más pronto posible</p>
        <p>Tenga en cuenta que los casos los especialistas los atienden en orden de llegada</p>
        <p>Atentamente,<br>Soporte TICS</p>
        """

        descripcion_images = data.get("descripcion_images", [])

        send_email(
            to_address=[data["especialista_email"], data["tercero_email"]],
            subject=f"Nuevo Ticket Creado para {data['tercero_nombre']}",
            body=email_body,
            images=descripcion_images
        )

        return jsonify({"message": "Ticket creado correctamente"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear el ticket: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def send_email(to_address, subject, body, images=[]):
    msg = MIMEMultipart('related')
    msg['From'] = SMTP_USERNAME
    msg['To'] = ', '.join(to_address)
    msg['Subject'] = subject

    # Crear la parte HTML del correo
    html = f"""
    <html>
        <body>
            {body}
            <br><br>
            {''.join([f'<img src="cid:image{i}" style="max-width:100%;">' for i in range(len(images))])}
        </body>
    </html>
    """

    # Adjuntar la parte HTML
    msg.attach(MIMEText(html, 'html'))

    # Adjuntar las imágenes
    for i, image_data in enumerate(images):
        try:
            # Asegúrate de que image_data es una cadena base64 válida
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            image_binary = base64.b64decode(image_data)
            image = MIMEImage(image_binary)
            image.add_header('Content-ID', f'<image{i}>')
            msg.attach(image)
        except Exception as img_error:
            print(f"Error procesando imagen {i}: {str(img_error)}")

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_address, text)
        server.quit()
        print("Correo enviado exitosamente")
    except Exception as e:
        print(f"Error enviando correo: {str(e)}")
        import traceback
        traceback.print_exc()

from flask import jsonify
from datetime import datetime

@bp.route("/", methods=["GET"])
def get_tickets():
    tickets = Ticket.query.all()
    tickets_data = []
    for ticket in tickets:
        ticket_info = {
            "id": ticket.id,
            "fecha_creacion": ticket.fecha_creacion.isoformat() if ticket.fecha_creacion else None,
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
            "respuesta": ticket.respuesta,
            "fecha_finalizacion": ticket.fecha_finalizacion.isoformat() if ticket.fecha_finalizacion else None
        }
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

        # Preparar el cuerpo del correo electrónico en HTML
        email_body = f"""
        <html>
        <body>
            <h2>Ticket solucionado para {ticket.tercero_nombre}</h2>
            <p>Cordial saludo {ticket.tercero_nombre},</p>
            <p>El especialista {ticket.especialista_nombre} ha solucionado su ticket.</p>
            <ul>
                <li>ID de ticket: {ticket.id}</li>
                <li>Tema: {ticket.tema}</li>
            </ul>
            <h3>Descripción del caso:</h3>
            <p>{ticket.descripcion_caso}</p>
            <h3>Solución al caso:</h3>
            <p>{ticket.solucion_caso}</p>
            <p>Por favor, califique la solución del ticket aquí: <a href="{encuestaLink}">{encuestaLink}</a></p>
            <p>Atentamente,<br>Soporte TICS</p>
        </body>
        </html>
        """

        solucion_images = data.get("solucion_images", [])

        # Enviar correo electrónico con imágenes adjuntas
        send_email(
            to_address=[ticket.tercero_email],
            subject=f"Solución ticket de {ticket.tercero_nombre}",
            body=email_body,
            images=solucion_images
        )

        return jsonify({"message": "Ticket finalizado y correo enviado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error al finalizar el ticket: {str(e)}")
        import traceback
        traceback.print_exc()
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

        if data.get("solutionApproval") == "No":
            ticket.estado = "Devuelto"

        db.session.commit()
        return jsonify({"message": "Calificaciones actualizadas correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
