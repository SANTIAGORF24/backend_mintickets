import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE
from flask_jwt_extended import create_access_token
import logging

# Cargar variables de entorno
load_dotenv()

bp = Blueprint('auth', __name__, url_prefix='/auth')

def authenticate_ad_specialist(username, password):
    # Configuración de Active Directory desde variables de entorno
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_BIND_DN = f'{username}@mindeporte.loc'
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')

    try:
        # Primero, intentar enlazar con las credenciales proporcionadas
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, 
                         user=LDAP_BIND_DN, 
                         password=password, 
                         auto_bind=True)

        # Si el enlace es exitoso, verificar si es un especialista con st 260 o 307
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter=f'(&(objectClass=user)(objectCategory=person)(sAMAccountName={username})' +
                          '(userAccountControl=512)(|(st=260)(st=307)))',
            attributes=['cn', 'displayName', 'mail', 'sAMAccountName', 'department', 'title', 'st']
        )

        # Si se encuentra un usuario que coincida
        if len(conn.entries) > 0:
            entry = conn.entries[0]
            specialist = {
                'username': entry['sAMAccountName'].value,
                'fullName': entry['displayName'].value if 'displayName' in entry else '',
                'email': entry['mail'].value if 'mail' in entry else '',
                'department': entry['department'].value if 'department' in entry else '',
                'title': entry['title'].value if 'title' in entry else '',
                'state': entry['st'].value if 'st' in entry else ''
            }
            return specialist
        
        return None

    except Exception as e:
        logging.error(f"Error durante la autenticación de AD: {e}")
        return None

@bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"message": "Faltan credenciales"}), 400

    # Autenticar contra Active Directory
    specialist = authenticate_ad_specialist(username, password)

    if specialist:
        # Crear token de acceso
        access_token = create_access_token(identity=username)
        return jsonify({
            "message": "Inicio de sesión exitoso", 
            "access_token": access_token,
            "user": specialist
        }), 200
    else:
        return jsonify({"message": "Credenciales inválidas o usuario no autorizado"}), 401

