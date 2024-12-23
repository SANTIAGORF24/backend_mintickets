from app import db
from datetime import datetime

class TicketAttachmentDescripcion(db.Model):
    """
    Modelo que representa una descripción de adjunto de ticket.

    Atributos:
        id (int): Clave primaria para la descripción del adjunto.
        ticket_id (int): Clave foránea que referencia el ticket asociado.
        file_name (str): Nombre del archivo adjunto.
        file_type (str): Tipo del archivo adjunto.
        file_content (bytes): Contenido binario del archivo adjunto.
        is_description_file (bool): Indicador de si el archivo es una descripción. Por defecto es True.
    """
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_content = db.Column(db.LargeBinary, nullable=False)
    is_description_file = db.Column(db.Boolean, default=True)

class TicketAttachmentRespuesta(db.Model):
    """
    Representa una respuesta de adjunto para un ticket.

    Atributos:
        id (int): La clave primaria del adjunto.
        ticket_id (int): La clave foránea que referencia el ticket asociado.
        file_name (str): El nombre del archivo adjunto.
        file_type (str): El tipo del archivo adjunto.
        file_content (bytes): El contenido binario del archivo adjunto.
        is_description_file (bool): Indica si el archivo es una descripción. Por defecto es True.
    """
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_content = db.Column(db.LargeBinary, nullable=False)
    is_description_file = db.Column(db.Boolean, default=True)    


class Ticket(db.Model):
    """
    Representa un ticket de soporte en el sistema.
    Atributos:
        id (int): El identificador único para el ticket.
        fecha_creacion (datetime): La fecha y hora en que se creó el ticket.
        fecha_finalizacion (datetime, opcional): La fecha y hora en que se cerró el ticket.
        tema (str): El asunto o tema del ticket.
        estado (str): El estado actual del ticket.
        tercero_nombre (str, opcional): El nombre del tercero involucrado en el ticket.
        tercero_email (str, opcional): El correo electrónico del tercero involucrado en el ticket.
        especialista_nombre (str, opcional): El nombre del especialista asignado al ticket.
        especialista_email (str, opcional): El correo electrónico del especialista asignado al ticket.
        descripcion_caso (str): La descripción del caso o problema reportado en el ticket.
        solucion_caso (str, opcional): La solución proporcionada para el caso o problema.
        tiempo_de_respuesta (int, opcional): El tiempo de respuesta para el ticket en minutos.
        actitud (int, opcional): La calificación de actitud para el ticket.
        respuesta (int, opcional): La calificación de respuesta para el ticket.
        codigo_seguridad (int, opcional): El código de seguridad del ticket.
        attachments_descripcion (list): Una lista de adjuntos relacionados con la descripción del ticket.
        attachments_respuesta (list): Una lista de adjuntos relacionados con la respuesta del ticket.
    Métodos:
        __repr__(): Devuelve una representación en cadena de la instancia de Ticket.
    """
    id = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    fecha_finalizacion = db.Column(db.DateTime, nullable=True)
    tema = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    tercero_nombre = db.Column(db.String(120), nullable=True)
    tercero_email = db.Column(db.String(120), nullable=True)
    especialista_nombre = db.Column(db.String(120), nullable=True)
    especialista_email = db.Column(db.String(120), nullable=True)
    descripcion_caso = db.Column(db.Text, nullable=False)
    solucion_caso = db.Column(db.Text, nullable=True)
    tiempo_de_respuesta = db.Column(db.Integer, nullable=True)
    actitud = db.Column(db.Integer, nullable=True)
    respuesta = db.Column(db.Integer, nullable=True)
    codigo_seguridad = db.Column(db.Integer, nullable=True)
    attachments_descripcion = db.relationship('TicketAttachmentDescripcion', backref='ticket', lazy=True)
    attachments_respuesta = db.relationship('TicketAttachmentRespuesta', backref='ticket', lazy=True)

    def __repr__(self):
        return (f"Ticket('{self.tema}', '{self.fecha_creacion}', '{self.fecha_finalizacion}', "
                f"'{self.estado}', '{self.tercero_nombre}', '{self.tercero_email}', "
                f"'{self.especialista_nombre}', '{self.especialista_email}', '{self.descripcion_caso}', '{self.solucion_caso}', "
                f"'{self.tiempo_de_respuesta}', '{self.actitud}', '{self.respuesta}', '{self.attachments_descripcion}', '{self.attachments_respuesta}', "
                f"'{self.codigo_seguridad}')")

