from app import app
"""
Este script ejecuta la aplicación Flask definida en el módulo `app`.
La aplicación está configurada para ejecutarse en todas las direcciones IP disponibles (host='0.0.0.0')
y escucha en el puerto 5000. El modo de depuración está habilitado para fines de desarrollo.
Uso:
    Ejecute este script directamente para iniciar la aplicación Flask.
Ejemplo:
    python main.py
Módulos:
    app: La instancia de la aplicación Flask.
Atributos:
    app (Flask): La instancia de la aplicación Flask importada del módulo `app`.
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
