from app import db
from datetime import datetime

class TicketAttachmentDescripcion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_content = db.Column(db.LargeBinary, nullable=False)
    is_description_file = db.Column(db.Boolean, default=True)

class TicketAttachmentRespuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_content = db.Column(db.LargeBinary, nullable=False)
    is_description_file = db.Column(db.Boolean, default=True)    


class Ticket(db.Model):
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
    attachments_descripcion = db.relationship('TicketAttachmentDescripcion', backref='ticket', lazy=True)
    attachments_respuesta = db.relationship('TicketAttachmentRespuesta', backref='ticket', lazy=True)

    def __repr__(self):
        return (f"Ticket('{self.tema}', '{self.fecha_creacion}', '{self.fecha_finalizacion}', "
                f"'{self.estado}', '{self.tercero_nombre}', '{self.tercero_email}', "
                f"'{self.especialista_nombre}', '{self.especialista_email}', '{self.descripcion_caso}', '{self.solucion_caso}', "
                f"'{self.tiempo_de_respuesta}', '{self.actitud}', '{self.respuesta}', '{self.attachments_descripcion}', '{self.attachments_respuesta}')")

