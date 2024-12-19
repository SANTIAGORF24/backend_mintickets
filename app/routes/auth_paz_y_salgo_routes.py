import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE
from flask_jwt_extended import create_access_token
import logging
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

bp = Blueprint('authpazzysalvo', __name__, url_prefix='/authpazysalvo')

from datetime import datetime, timedelta
import logging

def convert_windows_timestamp(windows_timestamp):
    """
    Convierte una marca de tiempo de Windows LDAP a un objeto datetime, resta un día del resultado y lo devuelve como una cadena en formato 'YYYY-MM-DD'.
    Parámetros:
        windows_timestamp (int o datetime o None): La marca de tiempo de Windows LDAP a convertir.
            - Si es None o un valor especial (0 o 9223372036854775807), devuelve None.
            - Si es un objeto datetime, resta un día y devuelve la fecha como una cadena.
            - Si es un entero, lo trata como una marca de tiempo de Windows LDAP y lo convierte en consecuencia.
    Retorna:
        str o None: La fecha convertida como una cadena en formato 'YYYY-MM-DD', o None si la entrada es None o un valor especial.
    Lanza:
        TypeError: Si la entrada no es un entero, datetime o None.
        ValueError: Si la entrada no se puede convertir a un entero.
    """
    # Check if timestamp is None or a special value indicating no expiration
    if windows_timestamp is None or windows_timestamp in [0, 9223372036854775807]:
        return None
    
    try:
        # If it's already a datetime object, extract the date
        if isinstance(windows_timestamp, datetime):
            return (windows_timestamp - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # If it's a timestamp (integer), proceed with original conversion
        timestamp = int(windows_timestamp)
        
        # Windows time is in 100-nanosecond intervals since January 1, 1601
        expiration_date = datetime(1601, 1, 1) + timedelta(microseconds=timestamp/10)
        
        # Subtract one day from the expiration date
        expiration_date_minus_one = expiration_date - timedelta(days=1)
        
        return expiration_date_minus_one.strftime('%Y-%m-%d')
    
    except (TypeError, ValueError) as e:
        logging.error(f"Error converting timestamp {windows_timestamp}: {e}")
        return None


def authenticate_ad_specialist(username, password):
    """
    Autentica a un especialista de Active Directory usando las credenciales proporcionadas.
    Esta función se conecta a un servidor de Active Directory usando credenciales de administrador,
    busca al usuario e intenta autenticar al usuario con el nombre de usuario y la contraseña proporcionados.
    Si la autenticación es exitosa, devuelve un diccionario que contiene los detalles del usuario.
    Args:
        username (str): El nombre de usuario del especialista a autenticar.
        password (str): La contraseña del especialista a autenticar.
    Retorna:
        dict: Un diccionario que contiene los detalles del usuario si la autenticación es exitosa.
              El diccionario incluye las siguientes claves:
              - 'username': El sAMAccountName del usuario.
              - 'fullName': El nombre completo del usuario.
              - 'email': La dirección de correo electrónico del usuario.
              - 'department': El departamento del usuario.
              - 'title': El título del usuario.
              - 'state': El estado del usuario.
              - 'accountExpires': La fecha de expiración de la cuenta del usuario.
        None: Si la autenticación falla o ocurre un error.
    Lanza:
        Exception: Si ocurre un error durante el proceso de autenticación.
    """
    # Active Directory configuration from environment variables
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_USERNAME = os.getenv('LDAP_USERNAME')
    LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')
    LDAP_BIND_DN = f'{username}@mindeporte.loc'

    try:
        # Create server connection with admin credentials
        server = Server(LDAP_SERVER, get_info=ALL)
        admin_conn = Connection(server, 
                                user=f'{LDAP_USERNAME}@mindeporte.loc', 
                                password=LDAP_PASSWORD, 
                                auto_bind=True)

        # Search for the user
        admin_conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter=f'(&(objectClass=user)(objectCategory=person)(sAMAccountName={username})' +
                        '(userAccountControl=512))',
            attributes=['cn', 'displayName', 'mail', 'sAMAccountName', 
                        'department', 'title', 'st', 'accountExpires']
        )


        # If user found
        if len(admin_conn.entries) > 0:
            entry = admin_conn.entries[0]
            
            # Convert account expiration date
            account_expires = entry['accountExpires'].value
            formatted_expiration = convert_windows_timestamp(account_expires)

            # Authenticate the user
            user_conn = Connection(server, 
                                   user=LDAP_BIND_DN, 
                                   password=password, 
                                   auto_bind=True)

            if user_conn.bind:
                specialist = {
                    'username': entry['sAMAccountName'].value,
                    'fullName': entry['displayName'].value if 'displayName' in entry else '',
                    'email': entry['mail'].value if 'mail' in entry else '',
                    'department': entry['department'].value if 'department' in entry else '',
                    'title': entry['title'].value if 'title' in entry else '',
                    'state': entry['st'].value if 'st' in entry else '',
                    'accountExpires': formatted_expiration
                }
                return specialist

        return None

    except Exception as e:
        logging.error(f"Error during AD authentication: {e}")
        return None

@bp.route('/login/', methods=['POST'])
def login():
    """
    Maneja el inicio de sesión del usuario autenticando contra Active Directory y devolviendo un token de acceso.
    Esta función recupera el nombre de usuario y la contraseña del cuerpo de la solicitud JSON,
    valida las credenciales contra Active Directory y devuelve un token de acceso
    si la autenticación es exitosa.
    Retorna:
        Response: Una respuesta JSON que contiene un mensaje de éxito, un token de acceso y los detalles del usuario
                  si la autenticación es exitosa, o un mensaje de error si faltan credenciales
                  o son inválidas.
    Códigos de estado:
        200: Inicio de sesión exitoso.
        400: Faltan credenciales.
        401: Credenciales inválidas o usuario no autorizado.
    """
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"message": "Missing credentials"}), 400

    # Authenticate against Active Directory
    specialist = authenticate_ad_specialist(username, password)

    if specialist:
        # Create access token
        access_token = create_access_token(identity=username)
        return jsonify({
            "message": "Successful login", 
            "access_token": access_token,
            "user": specialist
        }), 200
    else:
        return jsonify({"message": "Invalid credentials or unauthorized user"}), 401