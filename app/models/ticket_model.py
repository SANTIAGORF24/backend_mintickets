from app import db
from datetime import datetime

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    fecha_finalizacion = db.Column(db.DateTime, nullable=True)
    tema = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    tercero_nombre = db.Column(db.String(120), nullable=True)
    tercero_email = db.Column(db.String(120), nullable=True)  # Nueva columna
    especialista_nombre = db.Column(db.String(120), nullable=True)
    especialista_email = db.Column(db.String(120), nullable=True)  # Nueva columna
    descripcion_caso = db.Column(db.Text, nullable=False)
    solucion_caso = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return (f"Ticket('{self.tema}', '{self.fecha_creacion}', '{self.fecha_finalizacion}', "
                f"'{self.estado}', '{self.tercero_nombre}', '{self.tercero_email}', "
                f"'{self.especialista_nombre}', '{self.especialista_email}', '{self.descripcion_caso}', '{self.solucion_caso}')")
