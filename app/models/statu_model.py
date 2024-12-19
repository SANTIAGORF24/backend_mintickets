from app import db

class Statu(db.Model):
    """
    Representa un estado en el sistema.
    Atributos:
        id (int): El identificador único para el estado.
        name (str): El nombre del estado.
        user_id (int, opcional): El ID del usuario asociado con el estado.
    Métodos:
        __repr__(): Devuelve una representación en cadena del estado.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f"Statu('{self.name}')"