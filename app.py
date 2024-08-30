import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Usa el puerto asignado por el entorno, con un valor por defecto de 8080