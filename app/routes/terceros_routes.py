import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE
import logging

# Load environment variables from .env file
load_dotenv()

bp = Blueprint('terceros_da', __name__, url_prefix='/tercerosda')

def get_ad_users():
    """
    Recupera una lista de usuarios de Active Directory desde un servidor LDAP.
    Esta función se conecta a un servidor LDAP usando credenciales y configuración
    especificadas en variables de entorno. Busca usuarios activos y devuelve
    sus detalles, incluyendo nombre de usuario, nombre completo, correo electrónico,
    departamento y membresías de grupo.
    Retorna:
        list: Una lista de diccionarios, cada uno conteniendo detalles de un usuario de Active Directory.
              Cada diccionario tiene las siguientes claves:
              - 'username': El sAMAccountName del usuario.
              - 'fullName': El nombre completo del usuario.
              - 'email': La dirección de correo electrónico del usuario (si está disponible).
              - 'department': El departamento del usuario (si está disponible).
              - 'groups': Una lista de grupos a los que pertenece el usuario (si está disponible).
    Lanza:
        ValueError: Si alguna de las variables de entorno LDAP requeridas no está configurada.
        Exception: Si hay un error al conectar con el servidor LDAP o al realizar la búsqueda.
    """
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

@bp.route('/', methods=['GET'])
def get_terceros_users():
    """
    Obtiene una lista de usuarios de Active Directory y la devuelve como una respuesta JSON.

    Retorna:
        Response: Una respuesta JSON de Flask que contiene la lista de usuarios.
    """
    users = get_ad_users()
    return jsonify(users)

@bp.route('/<username>/', methods=['GET'])
def get_tercero_by_username(username):
    """
    Recupera un usuario por su nombre de usuario de la lista de usuarios de Active Directory.
    Args:
        username (str): El nombre de usuario del usuario a recuperar.
    Retorna:
        Response: Una respuesta JSON que contiene los datos del usuario si se encuentra,
                  o un mensaje de error con un código de estado 404 si el usuario no se encuentra.
    """
    users = get_ad_users()
    user = next((user for user in users if user['username'].lower() == username.lower()), None)
    
    if user:
        return jsonify(user)
    else:
        return jsonify({'error': 'Usuario no encontrado'}), 404

@bp.route('/departamento/<departamento>/', methods=['GET'])
def get_users_by_department(departamento):
    """
    Recupera usuarios por departamento.
    Esta función obtiene una lista de usuarios y los filtra en función del departamento especificado.
    Devuelve una respuesta JSON que contiene usuarios cuyo departamento coincide con el nombre del departamento dado.
    Args:
        departamento (str): El nombre del departamento para filtrar usuarios.
    Retorna:
        Response: Una respuesta JSON de Flask que contiene una lista de usuarios en el departamento especificado.
    """
    users = get_ad_users()
    departamento_users = [user for user in users if 'department' in user and departamento.lower() in user['department'].lower()]
    
    return jsonify(departamento_users)

@bp.route('/grupo/<grupo>/', methods=['GET'])
def get_users_by_group(grupo):
    """
    Recupera usuarios que pertenecen a un grupo especificado.
    Args:
        grupo (str): El nombre del grupo para filtrar usuarios.
    Retorna:
        Response: Una respuesta JSON que contiene una lista de usuarios que pertenecen al grupo especificado.
    """
    users = get_ad_users()
    grupo_users = [user for user in users if any(grupo.lower() in g.lower() for g in user['groups'])]
    
    return jsonify(grupo_users)

def get_ad_specialists():
    """
    Recupera una lista de especialistas de Active Directory desde un servidor LDAP.
    Esta función se conecta a un servidor LDAP usando credenciales y configuración
    proporcionadas a través de variables de entorno. Busca especialistas activos
    con códigos de estado/provincia específicos (260 o 307) y devuelve sus detalles.
    Retorna:
        list: Una lista de diccionarios, cada uno conteniendo detalles de un especialista.
              Cada diccionario contiene las siguientes claves:
              - 'username': El sAMAccountName del especialista.
              - 'fullName': El nombre completo del especialista.
              - 'email': La dirección de correo electrónico del especialista.
              - 'department': El departamento del especialista.
              - 'title': El título del especialista.
              - 'state': El código de estado/provincia del especialista.
    Lanza:
        ValueError: Si alguna de las variables de entorno LDAP requeridas no está configurada.
        Exception: Si hay un error al conectar con el servidor LDAP o al realizar la búsqueda.
    """
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

@bp.route('/especialistas/', methods=['GET'])
def get_specialists():
    """
    Recupera una lista de especialistas en publicidad.

    Esta función llama a la función `get_ad_specialists` para obtener una lista de
    especialistas y devuelve el resultado como una respuesta JSON.

    Retorna:
        Response: Una respuesta JSON de Flask que contiene la lista de especialistas.
    """
    specialists = get_ad_specialists()
    return jsonify(specialists)