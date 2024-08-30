import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Usa el puerto asignado por el entorno, con un valor por defecto de 5000
    app.run(host='0.0.0.0', port=port, debug=False)
