import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE, SUBTREE
import logging
import subprocess
import shlex


# Load environment variables from .env file
load_dotenv()

bp = Blueprint('ad_users', __name__, url_prefix='/ad')

def get_ad_users():
    """
    Recupera una lista de usuarios de Active Directory desde un servidor LDAP.
    Esta función se conecta a un servidor LDAP usando credenciales y configuración
    especificadas en variables de entorno. Busca usuarios activos e inactivos y devuelve
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

        users = []

        # Realiza búsqueda de usuarios activos
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter='(&(objectClass=user)(objectCategory=person)(|(userAccountControl=512)(userAccountControl=66048)))',
            attributes=['cn', 'displayName', 'mail', 'sAMAccountName', 'department', 'title', 'memberOf', 'description', 'physicalDeliveryOfficeName', 'postOfficeBox', 'st', 'accountExpires', 'userAccountControl']
        )
        for entry in conn.entries:
            user = {
                'username': entry['sAMAccountName'].value,
                'fullName': entry['displayName'].value,
                'email': entry['mail'].value if 'mail' in entry else '',
                'department': entry['department'].value if 'department' in entry else '',
                'groups': [str(group) for group in entry['memberOf']] if 'memberOf' in entry else [],
                'description': entry['description'].value if 'description' in entry else '',
                'office': entry['physicalDeliveryOfficeName'].value if 'physicalDeliveryOfficeName' in entry else '',
                'postOfficeBox': entry['postOfficeBox'].value if 'postOfficeBox' in entry else '',
                'state': entry['st'].value if 'st' in entry else '',
                'accountExpires': entry['accountExpires'].value if 'accountExpires' in entry else '',
                'isActive': not bool(int(entry['userAccountControl'].value) & 2)  # Check if the account is disabled
            }
            users.append(user)

        # Realiza búsqueda de usuarios inactivos
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter='(&(objectClass=user)(objectCategory=person)(|(userAccountControl=514)(userAccountControl=66050)))',
            attributes=['cn', 'displayName', 'mail', 'sAMAccountName', 'department', 'title', 'memberOf', 'description', 'physicalDeliveryOfficeName', 'postOfficeBox', 'st', 'accountExpires', 'userAccountControl']
        )
        for entry in conn.entries:
            user = {
                'username': entry['sAMAccountName'].value,
                'fullName': entry['displayName'].value,
                'email': entry['mail'].value if 'mail' in entry else '',
                'department': entry['department'].value if 'department' in entry else '',
                'groups': [str(group) for group in entry['memberOf']] if 'memberOf' in entry else [],
                'description': entry['description'].value if 'description' in entry else '',
                'office': entry['physicalDeliveryOfficeName'].value if 'physicalDeliveryOfficeName' in entry else '',
                'postOfficeBox': entry['postOfficeBox'].value if 'postOfficeBox' in entry else '',
                'state': entry['st'].value if 'st' in entry else '',
                'accountExpires': entry['accountExpires'].value if 'accountExpires' in entry else '',
                'isActive': not bool(int(entry['userAccountControl'].value) & 2)  # Check if the account is disabled
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

# AD attribute mapping
AD_ATTRIBUTE_MAP = {
    'fullName': 'displayName',
    'email': 'mail',
    'description': 'description',
    'office': 'physicalDeliveryOfficeName',
    'postOfficeBox': 'postOfficeBox',
    'state': 'st',
    'accountExpires': 'accountExpires'
}

def convert_to_ad_date(date_str):
    """
    Convierte una fecha en formato 'YYYY-MM-DD' a formato de fecha de Active Directory.
    """
    from datetime import datetime
    epoch_start = datetime(1601, 1, 1)
    date = datetime.strptime(date_str, '%Y-%m-%d')
    ad_date = int((date - epoch_start).total_seconds() * 10**7)
    return ad_date

@bp.route('/<username>/', methods=['PUT'])
def update_tercero_by_username(username):
    """
    Actualiza los datos de un usuario en Active Directory.
    Args:
        username (str): El nombre de usuario del usuario a actualizar.
    Retorna:
        Response: Una respuesta JSON que indica el éxito o fracaso de la operación.
    """
    data = request.json

    # Retrieve LDAP configuration from environment variables
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_USERNAME = os.getenv('LDAP_USERNAME')
    LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')

    try:
        # Establece conexión con el servidor
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, auto_bind=True)

        # Busca el usuario por su nombre de usuario
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter=f'(sAMAccountName={username})',
            attributes=['cn']
        )

        if not conn.entries:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        dn = conn.entries[0].entry_dn

        # Convert frontend field names to AD attribute names
        changes = {}
        for frontend_field, value in data.items():
            if frontend_field in AD_ATTRIBUTE_MAP:
                ad_attribute = AD_ATTRIBUTE_MAP[frontend_field]
                # Handle date fields specially
                if frontend_field == 'accountExpires':
                    if value:
                        ad_date = convert_to_ad_date(value)
                        changes[ad_attribute] = [(MODIFY_REPLACE, [str(ad_date)])]
                    else:
                        changes[ad_attribute] = [(MODIFY_REPLACE, ['0'])]
                else:
                    changes[ad_attribute] = [(MODIFY_REPLACE, [value])]

        if changes:
            conn.modify(dn, changes)

            if not conn.result['description'] == 'success':
                if conn.result['description'] == 'insufficientAccessRights':
                    raise Exception("No tiene suficientes derechos de acceso para actualizar este usuario.")
                else:
                    raise Exception(conn.result['message'])

            return jsonify({'message': 'Usuario actualizado correctamente'})
        else:
            return jsonify({'message': 'No hay cambios para actualizar'})

    except Exception as e:
        logging.error(f"Error al actualizar usuario en Active Directory: {str(e)}")
        return jsonify({'error': f'Error al actualizar usuario: {str(e)}'}), 500

@bp.route('/<username>/status', methods=['PUT'])
def update_user_status(username):
    """
    Actualiza el estado de activación de un usuario en Active Directory.
    Args:
        username (str): El nombre de usuario del usuario a actualizar.
    Retorna:
        Response: Una respuesta JSON que indica el éxito o fracaso de la operación.
    """
    data = request.json
    is_active = data.get('isActive')

    # Retrieve LDAP configuration from environment variables
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_USERNAME = os.getenv('LDAP_USERNAME')
    LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')

    try:
        # Establece conexión con el servidor
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, auto_bind=True)

        # Busca el usuario por su nombre de usuario
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter=f'(sAMAccountName={username})',
            attributes=['cn', 'userAccountControl']
        )

        if not conn.entries:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        dn = conn.entries[0].entry_dn
        user_account_control = int(conn.entries[0]['userAccountControl'].value)

        if is_active:
            user_account_control &= ~2  # Clear the disable bit
        else:
            user_account_control |= 2  # Set the disable bit

        conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [user_account_control])]})

        if not conn.result['description'] == 'success':
            raise Exception(conn.result['message'])

        return jsonify({'message': 'Estado del usuario actualizado correctamente'})

    except Exception as e:
        logging.error(f"Error al actualizar estado del usuario en Active Directory: {str(e)}")
        return jsonify({'error': f'Error al actualizar estado del usuario: {str(e)}'}), 500

@bp.route('/<username>/password', methods=['PUT'])
def update_user_password(username):
    """
    Actualiza la contraseña de un usuario en Active Directory utilizando PowerShell en Linux.
    Args:
        username (str): El nombre de usuario del usuario a actualizar.
    Retorna:
        Response: Una respuesta JSON que indica el éxito o fracaso de la operación.
    """
    data = request.json
    new_password = data.get('newPassword')

    if not new_password:
        return jsonify({'error': 'Nueva contraseña no proporcionada'}), 400

    try:
        # Construye el comando de PowerShell de manera segura
        ps_command = f"Set-ADAccountPassword -Identity {shlex.quote(username)} -NewPassword (ConvertTo-SecureString -AsPlainText {shlex.quote(new_password)} -Force) -Reset"
        
        # Ejecuta PowerShell usando pwsh (versión Linux)
        result = subprocess.run(
            ["/usr/bin/pwsh", "-Command", ps_command],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

        return jsonify({'message': 'Contraseña actualizada correctamente'})

    except Exception as e:
        logging.error(f"Error al actualizar contraseña en Active Directory: {str(e)}")
        return jsonify({'error': f'Error al actualizar contraseña: {str(e)}'}), 500

