from flask import Flask
from app.routes.auth_routes import bp as auth_bp
from app.routes.statu_routes import bp as user_bp
from app.routes.tercero_routes import bp as tercero_bp
from app.routes.ticket_routes import bp as ticket_bp
from app.routes.topic_routes import bp as topic_bp

app = Flask(__name__)

# Registra todos los blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(tercero_bp)
app.register_blueprint(ticket_bp)
app.register_blueprint(topic_bp)


@app.route("/")
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)