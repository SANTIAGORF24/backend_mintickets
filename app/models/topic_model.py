from app import db

class Topic(db.Model):
    """
    Representa un tema en la aplicación.
    Atributos:
        id (int): El identificador único para el tema.
        name (str): El nombre del tema.
        user_id (int, opcional): El ID del usuario asociado con el tema.
    Métodos:
        __repr__(): Devuelve una representación en cadena de la instancia de Topic.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f"Topic('{self.name}')"