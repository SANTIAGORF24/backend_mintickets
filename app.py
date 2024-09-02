import os
from flask import Flask
from app.routes.auth_routes import bp as auth_bp

app = Flask(__name__)

# Registra el blueprint de autenticación
app.register_blueprint(auth_bp)

@app.route("/")
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))