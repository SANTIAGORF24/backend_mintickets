from app import db

class Tercero(db.Model):
    """
    Representa una entidad Tercero en la base de datos.
    Atributos:
        id (int): El identificador único para el Tercero.
        name (str): El nombre del Tercero. No puede ser nulo.
        email (str): La dirección de correo electrónico del Tercero. No puede ser nulo.
        user_id (int, opcional): La clave foránea que enlaza con la entidad Usuario. Puede ser nulo.
    Métodos:
        __repr__(): Devuelve una representación en cadena de la instancia de Tercero.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f"Tercero('{self.name}','{self.email}')"