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
    Convert Windows LDAP timestamp to datetime with comprehensive error handling,
    and subtract one day from the result.
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

@bp.route('/login', methods=['POST'])
def login():
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