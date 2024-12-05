from flask import Blueprint, request, jsonify, send_file, make_response
from app import db
from app.models.ticket_model import Ticket
from app.models.ticket_model import TicketAttachmentDescripcion
from app.models.ticket_model import TicketAttachmentRespuesta
from io import BytesIO
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.mime.application import MIMEApplication


load_dotenv()  # Cargar variables de entorno

# Ejemplos de uso
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL')

UPLOAD_PATH=os.getenv('UPLOAD_PATH')

bp = Blueprint("tickets", __name__, url_prefix="/tickets")


@bp.route("/register", methods=["POST"])
def create_ticket():
    data = request.json
    try:
        # Validar campos requeridos
        required_fields = [
            "tema", "estado", "tercero_nombre", "tercero_email", 
            "especialista_nombre", "especialista_email", "descripcion_caso"
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo requerido faltante: {field}"}), 400

        # Usar la fecha y hora actual del servidor
        now = datetime.now(pytz.timezone('America/Bogota'))
        
        # Crear nuevo ticket
        new_ticket = Ticket(
            fecha_creacion=now,
            tema=data["tema"],
            estado=data["estado"],
            tercero_nombre=data["tercero_nombre"],
            tercero_email=data["tercero_email"],
            especialista_nombre=data["especialista_nombre"],
            especialista_email=data["especialista_email"],
            descripcion_caso=data["descripcion_caso"],
            solucion_caso=data.get("solucion_caso", ""),
            fecha_finalizacion=None
        )
        
        db.session.add(new_ticket)
        db.session.flush()  # Esto poblará el ID sin hacer commit aún

        # Crear las carpetas para los anexos
        ticket_folder = os.path.join(UPLOAD_PATH, str(new_ticket.id))
        descripcion_folder = os.path.join(ticket_folder, "Anexos_Descripcion")
        solucion_folder = os.path.join(ticket_folder, "Anexos_Solucion")
        
        # Crear las carpetas si no existen
        os.makedirs(descripcion_folder, exist_ok=True)
        os.makedirs(solucion_folder, exist_ok=True)

        # Procesar archivos adjuntos
        attachments = data.get("attachments", [])
        for attachment in attachments:
            try:
                if not attachment.get('base64Content'):
                    continue  # Saltar archivos sin contenido

                # Extraer base64 real (remover prefijo data:image/png;base64, si existe)
                base64_content = attachment['base64Content'].split(',')[-1]
                
                # Decodificar contenido
                file_content = base64.b64decode(base64_content)
                
                # Validar tamaño del archivo (por ejemplo, máximo 10MB)
                max_file_size = 10 * 1024 * 1024  # 10 MB
                if len(file_content) > max_file_size:
                    return jsonify({
                        "error": f"Archivo {attachment.get('fileName', 'Sin nombre')} excede el tamaño máximo de 10MB"
                    }), 400

                # Guardar el archivo físicamente en la carpeta de descripcion
                file_name = attachment.get('fileName', f'archivo_{uuid.uuid4()}')
                file_path = os.path.join(descripcion_folder, file_name)

                # Guardar el archivo en el servidor
                with open(file_path, 'wb') as f:
                    f.write(file_content)

                # Crear registro de archivo adjunto
                ticket_attachment = TicketAttachmentDescripcion(
                    ticket_id=new_ticket.id,
                    file_name=file_name,
                    file_type=attachment.get('fileType', 'application/octet-stream'),
                    file_content=file_content,  # Si es necesario almacenar el archivo, puedes hacerlo
                    is_description_file=True
                )
                
                db.session.add(ticket_attachment)

            except Exception as attachment_error:
                print(f"Error procesando archivo: {attachment_error}")
        
        # Enviar correo electrónico de notificación
        frontend_url = os.getenv('FRONTEND_BASE_URL')
        email_body = f"""
        <h2>Ticket creado para {data['tercero_nombre']}</h2>
        <p>Cordial saludo {data['tercero_nombre']},</p>
        <p>Para consultar el estado de su ticket ingrese a <a href="{frontend_url}/historial">{frontend_url}/historial</a> y digite el ID del ticket</p>
        <p>Se ha creado un nuevo ticket con la siguiente descripción:</p>
        <ul>
            <li>ID de ticket: {new_ticket.id}</li>
            <li>Tema: {data['tema']}</li>
        </ul>
        <h3>Descripción:</h3>
        <p>{data['descripcion_caso']}</p>
        <p>El especialista {data['especialista_nombre']} lo atenderá lo más pronto posible</p>
        <p>Tenga en cuenta que los casos los especialistas los atienden en orden de llegada</p>
        <p>Atentamente,<br>Soporte TICS</p>
        """

        try:
            send_email(
                to_address=[data["especialista_email"], data["tercero_email"]],
                subject=f"Nuevo Ticket Creado para {data['tercero_nombre']}",
                body=email_body,
                images=[attachment['base64Content'] for attachment in attachments if attachment.get('fileType', '').startswith('image/')], 
                attachments=[attachment for attachment in attachments if not attachment.get('fileType', '').startswith('image/')]
            )
        except Exception as email_error:
            print(f"Error enviando correo electrónico: {email_error}")

        db.session.commit()

        return jsonify({
            "message": "Ticket creado correctamente", 
            "ticket_id": new_ticket.id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error al crear el ticket: {str(e)}")
        return jsonify({
            "error": "Error interno al procesar el ticket", 
            "details": str(e)
        }), 500
    finally:
        db.session.close()

def send_email(to_address, subject, body, images=[], attachments=[]):
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

    # Mapeo de tipos MIME
    mime_types = {
        'application/pdf': 'application/pdf',
        'application/vnd.ms-powerpoint': 'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-excel': 'application/vnd.ms-excel',  # Archivos .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # Archivos .xlsx
        'video/mp4': 'video/mp4',
        'image/jpeg': 'image/jpeg',
        'image/png': 'image/png',
        'image/gif': 'image/gif'
}


    # Adjuntar archivos
    for attachment in attachments:
        try:
            # Asegúrate de que el contenido base64 es válido
            if ',' in attachment['base64Content']:
                file_content = attachment['base64Content'].split(',', 1)[1]
            else:
                file_content = attachment['base64Content']
            
            # Decodificar contenido
            file_binary = base64.b64decode(file_content)
            
            # Obtener el tipo MIME correcto
            file_type = attachment.get('fileType', 'application/octet-stream')
            mime_type = mime_types.get(file_type, file_type)

            # Crear parte MIME para el archivo
            if mime_type.startswith('image/'):
                part = MIMEImage(file_binary, _subtype=mime_type.split('/')[-1])
            elif mime_type == 'application/pdf':
                part = MIMEApplication(file_binary, _subtype='pdf')
            elif mime_type.startswith('video/'):
                part = MIMEBase('video', mime_type.split('/')[-1])
                part.set_payload(file_binary)
                encoders.encode_base64(part)
            elif mime_type.startswith('application/vnd.'):
                part = MIMEApplication(file_binary, _subtype=mime_type.split('.')[-1])
            else:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file_binary)
                encoders.encode_base64(part)
            
            # Agregar encabezados
            part.add_header(
                'Content-Disposition', 
                f'attachment; filename="{attachment.get("fileName", "archivo")}"'
            )
            
            msg.attach(part)
        except Exception as file_error:
            print(f"Error procesando archivo adjunto: {str(file_error)}")

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        server.sendmail(SMTP_USERNAME, to_address, msg.as_string())
        
        server.quit()
        print("Correo enviado exitosamente")
    except Exception as e:
        print(f"Error completo enviando correo: {str(e)}")
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
    
    try:
        # Obtener el path de la carpeta del ticket
        ticket_folder = os.path.join(UPLOAD_PATH, str(ticket.id))
        
        # Eliminar los anexos de descripción
        attachments_descripcion = TicketAttachmentDescripcion.query.filter_by(ticket_id=id).all()
        for attachment in attachments_descripcion:
            # Eliminar archivos adjuntos físicamente si existen
            file_path = os.path.join(os.getenv('UPLOAD_PATH', '\\Users\\saramirez\\Documents\\MINDEPORTE\\MINTICKETS\\Anexos'), attachment.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Eliminar los anexos de respuesta
        attachments_respuesta = TicketAttachmentRespuesta.query.filter_by(ticket_id=id).all()
        for attachment in attachments_respuesta:
            # Eliminar archivos adjuntos físicamente si existen
            file_path = os.path.join(os.getenv('UPLOAD_PATH', '/default/path/'), attachment.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Eliminar los anexos de descripción
        TicketAttachmentDescripcion.query.filter_by(ticket_id=id).delete()
        # Eliminar los anexos de respuesta
        TicketAttachmentRespuesta.query.filter_by(ticket_id=id).delete()
        
        # Eliminar la carpeta del ticket y sus archivos (si existen)
        if os.path.exists(ticket_folder):
            for root, dirs, files in os.walk(ticket_folder, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))  # Eliminar los archivos
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))  # Eliminar los directorios vacíos
            os.rmdir(ticket_folder)  # Eliminar la carpeta del ticket

        # Eliminar el ticket
        db.session.delete(ticket)
        
        # Confirmar los cambios
        db.session.commit()
        
        return jsonify({"message": "Ticket y sus anexos eliminados correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar el ticket: {str(e)}")
        return jsonify({"error": "Error al eliminar el ticket"}), 500
    finally:
        db.session.close()



@bp.route("/<int:id>", methods=["PATCH"])
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.json
    try:
        ticket.fecha_finalizacion = datetime.utcnow()
        ticket.tema = data.get("tema", ticket.tema)
        ticket.estado = data.get("estado", ticket.estado)
        ticket.tercero_nombre = data.get("tercero_nombre", ticket.tercero_nombre)
        ticket.tercero_email = data.get("tercero_email", ticket.tercero_email)
        ticket.especialista_nombre = data.get("especialista_nombre", ticket.especialista_nombre)
        ticket.especialista_email = data.get("especialista_email", ticket.especialista_email)
        ticket.descripcion_caso = data.get("descripcion_caso", ticket.descripcion_caso)
        ticket.solucion_caso = data.get("solucion_caso", ticket.solucion_caso)

        # Crear las carpetas si no existen
        ticket_folder = os.path.join(UPLOAD_PATH, str(ticket.id))
        solucion_folder = os.path.join(ticket_folder, "Anexos_Solucion")

        # Crear la carpeta de anexos solución si no existe
        os.makedirs(solucion_folder, exist_ok=True)

        # Procesar archivos adjuntos de respuesta
        attachments = data.get("attachments", [])
        for attachment in attachments:
            if not attachment.get('base64Content'):
                continue  # Saltar archivos sin contenido

            base64_content = attachment['base64Content'].split(',')[-1]
            file_content = base64.b64decode(base64_content)
            
            # Guardar el archivo en la carpeta Anexos_Solucion
            file_name = attachment.get('fileName', f'archivo_{uuid.uuid4()}')
            file_path = os.path.join(solucion_folder, file_name)

            # Guardar el archivo en el servidor
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Crear registro de archivo adjunto de solución
            ticket_attachment = TicketAttachmentRespuesta(
                ticket_id=ticket.id,
                file_name=file_name,
                file_type=attachment.get('fileType', 'application/octet-stream'),
                file_content=file_content,
                is_description_file=False  # Es un archivo de solución
            )
            db.session.add(ticket_attachment)

        db.session.commit()

        return jsonify({
            "message": "Ticket actualizado correctamente", 
            "ticket_id": ticket.id
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error actualizando el ticket: {str(e)}")
        return jsonify({
            "error": "Error interno al actualizar el ticket", 
            "details": str(e)
        }), 500
    finally:
        db.session.close()



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

        # Crear las carpetas si no existen
        ticket_folder = os.path.join(UPLOAD_PATH, str(ticket.id))
        solucion_folder = os.path.join(ticket_folder, "Anexos_Solucion")
        os.makedirs(solucion_folder, exist_ok=True)

        # Procesar archivos adjuntos de respuesta
        attachments = data.get("attachments", [])
        respuesta_email_attachments = []  # Para los archivos que se enviarán por correo

        for attachment in attachments:
            try:
                if not attachment.get('base64Content'):
                    continue  # Saltar archivos sin contenido

                base64_content = attachment['base64Content'].split(',')[-1]
                file_content = base64.b64decode(base64_content)

                # Usar la carpeta Anexos_Solucion para guardar el archivo
                file_name = attachment.get('fileName', f'archivo_{uuid.uuid4()}')
                file_path = os.path.join(solucion_folder, file_name)

                # Guardar el archivo físicamente en el servidor
                with open(file_path, 'wb') as f:
                    f.write(file_content)

                # Crear registro de archivo adjunto en la base de datos
                ticket_attachment = TicketAttachmentRespuesta(
                    ticket_id=ticket.id,
                    file_name=file_name,
                    file_type=attachment.get('fileType', 'application/octet-stream'),
                    file_content=file_content,  # Si es necesario almacenar el archivo, puedes hacerlo
                    is_description_file=False  # Es un archivo de respuesta
                )
                db.session.add(ticket_attachment)

                # Añadir archivo a la lista de adjuntos para el correo
                respuesta_email_attachments.append({
                    'fileName': file_name,
                    'fileType': attachment.get('fileType', 'application/octet-stream'),
                    'base64Content': base64.b64encode(file_content).decode('utf-8')
                })

            except Exception as attachment_error:
                print(f"Error procesando archivo de solución: {attachment_error}")
                continue  # Continuar con los siguientes archivos en lugar de fallar completamente

        # Recuperar todos los archivos adjuntos del ticket (Descripción + Respuesta)
        all_attachments = TicketAttachmentRespuesta.query.filter_by(ticket_id=ticket.id).all()
        for attachment in all_attachments:
            respuesta_email_attachments.append({
                'fileName': attachment.file_name,
                'fileType': attachment.file_type,
                'base64Content': base64.b64encode(attachment.file_content).decode('utf-8')
            })

        # Enviar correo electrónico con los archivos adjuntos
        encuestaLink = f"{os.getenv('FRONTEND_BASE_URL')}/encuesta?id={ticket.id}"

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

        send_email(
            to_address=[ticket.tercero_email],
            subject=f"Solución ticket de {ticket.tercero_nombre}",
            body=email_body,
            images=[attachment['base64Content'] for attachment in respuesta_email_attachments if attachment['fileType'].startswith('image/')], 
            attachments=[attachment for attachment in respuesta_email_attachments if not attachment['fileType'].startswith('image/')]
        )

        db.session.commit()
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
    
@bp.route("/<int:ticket_id>/attachments", methods=["GET"])
def get_ticket_attachments(ticket_id):
    """
    Retrieve all attachments associated with a specific ticket.
    
    Returns a list of attachment metadata without the actual file content.
    """
    try:
        # Check if ticket exists
        ticket = Ticket.query.get_or_404(ticket_id)
        
        # Retrieve description attachments
        description_attachments = TicketAttachmentDescripcion.query.filter_by(ticket_id=ticket_id).all()
        
        # Retrieve response attachments
        response_attachments = TicketAttachmentRespuesta.query.filter_by(ticket_id=ticket_id).all()
        
        # Prepare attachment metadata
        attachments_data = []
        
        # Process description attachments
        for attachment in description_attachments:
            attachments_data.append({
                "id": attachment.id,
                "file_name": attachment.file_name,
                "file_type": attachment.file_type,
                "is_description_file": True  # Explicitly set to True for description files
            })
        
        # Process response attachments
        for attachment in response_attachments:
            attachments_data.append({
                "id": attachment.id,
                "file_name": attachment.file_name,
                "file_type": attachment.file_type,
                "is_description_file": False  # Explicitly set to False for response files
            })
        
        return jsonify(attachments_data), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@bp.route("/attachment/<int:attachment_id>", methods=["GET"])
def download_attachment(attachment_id):
    """
    Download a specific attachment by its ID.
    
    Supports both description and response attachments.
    """
    try:
        # Primero intentar encontrarlo en los archivos de descripción
        attachment = TicketAttachmentDescripcion.query.get(attachment_id)
        attachment_type = "description"
        
        # Si no se encuentra, intentar en los archivos de respuesta
        if not attachment:
            attachment = TicketAttachmentRespuesta.query.get(attachment_id)
            attachment_type = "response"
        
        # Si aún no se encuentra, retornar 404
        if not attachment:
            return jsonify({"error": "Attachment not found"}), 404
        
        # Crear la respuesta con el archivo
        response = make_response(attachment.file_content)
        response.headers.set('Content-Type', attachment.file_type)
        response.headers.set('Content-Disposition', 
                             f'attachment; filename="{attachment.file_name}"')
        
        return response
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
