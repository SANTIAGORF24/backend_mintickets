import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE
import logging

# Load environment variables from .env file
load_dotenv()

bp = Blueprint('terceros_da', __name__, url_prefix='/tercerosda')

def get_ad_users():
    # Retrieve LDAP configuration from environment variables
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_USERNAME = os.getenv('LDAP_USERNAME')
    LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')

    # Validate that all required environment variables are set
    if not all([LDAP_SERVER, LDAP_USERNAME, LDAP_PASSWORD, LDAP_SEARCH_BASE]):
        raise ValueError("Missing required LDAP environment variables")

    try:
        # Establece conexión con el servidor
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, auto_bind=True)

        # Realiza búsqueda de usuarios activos
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter='(&(objectClass=user)(objectCategory=person)' +
                          '(|(userAccountControl=512)(userAccountControl=66048)))',  # Filtro para usuarios activos y con permisos especiales
            attributes=['cn', 'displayName', 'mail', 'sAMAccountName', 'department', 'title', 'memberOf']
        )

        # Procesa los resultados
        users = []
        for entry in conn.entries:
            user = {
                'username': entry['sAMAccountName'].value,
                'fullName': entry['displayName'].value,
                'email': entry['mail'].value if 'mail' in entry else '',
                'department': entry['department'].value if 'department' in entry else '',
                'groups': [str(group) for group in entry['memberOf']] if 'memberOf' in entry else []
            }
            users.append(user)

        return users

    except Exception as e:
        print(f"Error al conectar con Active Directory: {e}")
        return []

@bp.route('', methods=['GET'])
def get_terceros_users():
    users = get_ad_users()
    return jsonify(users)

@bp.route('/<username>', methods=['GET'])
def get_tercero_by_username(username):
    users = get_ad_users()
    user = next((user for user in users if user['username'].lower() == username.lower()), None)
    
    if user:
        return jsonify(user)
    else:
        return jsonify({'error': 'Usuario no encontrado'}), 404

@bp.route('/departamento/<departamento>', methods=['GET'])
def get_users_by_department(departamento):
    users = get_ad_users()
    departamento_users = [user for user in users if 'department' in user and departamento.lower() in user['department'].lower()]
    
    return jsonify(departamento_users)

@bp.route('/grupo/<grupo>', methods=['GET'])
def get_users_by_group(grupo):
    users = get_ad_users()
    grupo_users = [user for user in users if any(grupo.lower() in g.lower() for g in user['groups'])]
    
    return jsonify(grupo_users)

def get_ad_specialists():
    # Retrieve LDAP configuration from environment variables
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_USERNAME = os.getenv('LDAP_USERNAME')
    LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')

    # Validate that all required environment variables are set
    if not all([LDAP_SERVER, LDAP_USERNAME, LDAP_PASSWORD, LDAP_SEARCH_BASE]):
        raise ValueError("Missing required LDAP environment variables")

    try:
        # Establece conexión con el servidor
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, auto_bind=True)

        # Búsqueda de especialistas activos con estado/provincia 260 o 307
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter='(&(objectClass=user)(objectCategory=person)' +
                          '(|(userAccountControl=512)(userAccountControl=66048))' +  # Usuarios activos y con permisos especiales
                          '(|(st=260)(st=307)))',  # Filtro para estado/provincia 260 o 307
            attributes=['cn', 'displayName', 'mail', 'sAMAccountName', 'department', 'title', 'st']
        )

        # Procesa los resultados
        specialists = []
        for entry in conn.entries:
            specialist = {
                'username': entry['sAMAccountName'].value if 'sAMAccountName' in entry else '',
                'fullName': entry['displayName'].value if 'displayName' in entry else '',
                'email': entry['mail'].value if 'mail' in entry else '',
                'department': entry['department'].value if 'department' in entry else '',
                'title': entry['title'].value if 'title' in entry else '',
                'state': entry['st'].value if 'st' in entry else ''
            }
            specialists.append(specialist)

        return specialists

    except Exception as e:
        print(f"Error al conectar con Active Directory: {e}")
        return []

@bp.route('/especialistas', methods=['GET'])
def get_specialists():
    specialists = get_ad_specialists()
    return jsonify(specialists)