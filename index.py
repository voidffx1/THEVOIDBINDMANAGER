from flask import Flask, render_template, request, jsonify
import requests
import json
import base64
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', 'void-super-secret-key-2026')

# ============================================================
# 🔥 ALL API ENDPOINTS (SAME AS BEFORE)
# ============================================================

GARENA = {
    "app_id": "100067",
    "base_url": "https://100067.connect.garena.com",
    "login_base": "https://loginbp.ggpolarbear.com",
    "support_base": "https://api-otrss.garena.com",
    "msdk_base": "https://100067.msdk.garena.com",
    "ff_service": "https://api.freefireservice.dnc.su",
    "user_agent": "GarenaMSDK/4.0.30(Redmi Note 5;Android 9;en;US;)",
    
    "endpoints": {
        "major_login": "/MajorLogin",
        "major_register": "/MajorRegister",
        "get_login_data": "/GetLoginData",
        "choose_region": "/ChooseRegion",
        "change_nickname": "/MajorModifyNickname",
        "eat_token": "/support/callback/",
        "token_inspect": "/oauth/token/inspect",
        "revoke_token": "/oauth/logout",
        "grant_guest": "/api/v2/oauth/guest/token:grant",
        "register_guest": "/api/v2/oauth/guest/token:register",
        "get_bind_info": "/game/account_security/bind:get_bind_info",
        "send_otp": "/game/account_security/bind:send_otp",
        "verify_otp": "/game/account_security/bind:verify_otp",
        "create_bind": "/game/account_security/bind:create_bind_request",
        "create_rebind": "/game/account_security/bind:create_rebind_request",
        "create_unbind": "/game/account_security/bind:create_unbind_request",
        "verify_identity": "/game/account_security/bind:verify_identity",
        "cancel_request": "/game/account_security/bind:cancel_request",
        "platform_info": "/bind/app/platform/info/get",
        "login_data_from_token": "/oauth/account:login",
        "topup_info": "/api/msdk/v2/info/pricing",
    }
}

SOCIAL_AUTH = {
    "google": "https://auth.garena.com/universal/oauth?platform=8&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/",
    "facebook": "https://auth.garena.com/universal/oauth?platform=3&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/",
    "twitter": "https://auth.garena.com/universal/oauth?platform=11&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/",
    "apple": "https://auth.garena.com/universal/oauth?platform=10&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/",
    "huawei": "https://auth.garena.com/universal/oauth?platform=7&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/",
    "vk": "https://auth.garena.com/universal/oauth?platform=5&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/"
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def garena_request(endpoint, method='GET', params=None, data=None, headers=None, base=None):
    if base is None:
        base = GARENA['base_url']
    url = base + endpoint
    default_headers = {
        'User-Agent': GARENA['user_agent'],
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, params=params, headers=default_headers, timeout=15)
        else:
            resp = requests.post(url, data=data, headers=default_headers, timeout=15)
        
        if resp.text:
            return {'success': True, 'status': resp.status_code, 'data': resp.json()}
        return {'success': True, 'status': resp.status_code, 'data': {}}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def decode_jwt_full(token):
    try:
        parts = token.split('.')
        if len(parts) < 3:
            return None
        
        header_b64 = parts[0] + '=' * (-len(parts[0]) % 4)
        header = json.loads(base64.b64decode(header_b64))
        
        payload_b64 = parts[1] + '=' * (-len(parts[1]) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        
        result = {
            'header': header,
            'payload': payload,
            'nickname': payload.get('nickname', payload.get('player_name', 'Unknown')),
            'user_id': payload.get('user_id', payload.get('uid', payload.get('sub', 'Unknown'))),
            'country': payload.get('country', payload.get('region', 'Unknown')),
            'email': payload.get('email', 'None'),
            'avatar': payload.get('avatar', ''),
            'expiry': payload.get('exp', 0),
            'issued_at': payload.get('iat', 0),
            'is_human': payload.get('is_human', True),
            'client_type': payload.get('client_type', ''),
            'server_url': payload.get('serverUrl', ''),
            'ano_url': payload.get('anoUrl', ''),
            'ttl': payload.get('ttl', 0),
            'refresh_token': payload.get('refresh_token', '')
        }
        
        if result['expiry']:
            result['expiry_readable'] = datetime.fromtimestamp(result['expiry']).strftime('%Y-%m-%d %H:%M:%S')
        if result['issued_at']:
            result['issued_readable'] = datetime.fromtimestamp(result['issued_at']).strftime('%Y-%m-%d %H:%M:%S')
        
        return result
    except Exception as e:
        return {'error': str(e)}

# ============================================================
# API ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/major-login', methods=['POST'])
def major_login():
    username = request.json.get('username', '').strip()
    password = request.json.get('password', '').strip()
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['major_login'],
        method='POST',
        data={'username': username, 'password': password},
        base=GARENA['login_base']
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Login failed')}), 500

@app.route('/api/major-register', methods=['POST'])
def major_register():
    username = request.json.get('username', '').strip()
    password = request.json.get('password', '').strip()
    email = request.json.get('email', '').strip()
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    data = {'username': username, 'password': password}
    if email:
        data['email'] = email
    
    result = garena_request(
        GARENA['endpoints']['major_register'],
        method='POST',
        data=data,
        base=GARENA['login_base']
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Registration failed')}), 500

@app.route('/api/get-login-data', methods=['POST'])
def get_login_data():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['get_login_data'],
        method='POST',
        data={'access_token': token},
        base=GARENA['login_base']
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Failed to get login data')}), 500

@app.route('/api/choose-region', methods=['POST'])
def choose_region():
    token = request.json.get('token', '').strip()
    region = request.json.get('region', 'PK').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['choose_region'],
        method='POST',
        data={'access_token': token, 'region': region},
        base=GARENA['login_base']
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Failed to choose region')}), 500

@app.route('/api/change-nickname', methods=['POST'])
def change_nickname():
    token = request.json.get('token', '').strip()
    nickname = request.json.get('nickname', '').strip()
    if not token or not nickname:
        return jsonify({'success': False, 'error': 'Token and nickname required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['change_nickname'],
        method='POST',
        data={'access_token': token, 'nickname': nickname},
        base=GARENA['login_base']
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Failed to change nickname')}), 500

@app.route('/api/eat-token', methods=['POST'])
def eat_token():
    token = request.json.get('token', '').strip()
    platform = request.json.get('platform', 'google').strip().lower()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    if platform in SOCIAL_AUTH:
        url = SOCIAL_AUTH[platform]
        if '?' in url:
            url += '&access_token=' + token
        else:
            url += '?access_token=' + token
        return jsonify({'success': True, 'auth_url': url, 'platform': platform})
    
    try:
        resp = requests.get(
            f"{GARENA['support_base']}{GARENA['endpoints']['eat_token']}?access_token={token}",
            headers={'User-Agent': GARENA['user_agent']},
            timeout=15
        )
        if resp.status_code == 200:
            return jsonify({'success': True, 'data': resp.json() if resp.text else {}})
        return jsonify({'success': False, 'error': f'HTTP {resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/social-auth-urls', methods=['GET'])
def social_auth_urls():
    return jsonify({'success': True, 'urls': SOCIAL_AUTH})

@app.route('/api/get-bind-info', methods=['POST'])
def get_bind_info():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['get_bind_info'],
        method='GET',
        params={'app_id': GARENA['app_id'], 'access_token': token}
    )
    
    if result['success'] and result.get('status') == 200:
        data = result.get('data', {})
        return jsonify({
            'success': True,
            'email': data.get('email', 'None'),
            'email_to_be': data.get('email_to_be', 'None'),
            'has_bind': bool(data.get('email'))
        })
    return jsonify({'success': False, 'error': result.get('error', 'API call failed')}), 500

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    token = request.json.get('token', '').strip()
    email = request.json.get('email', '').strip()
    if not token or not email:
        return jsonify({'success': False, 'error': 'Token and email required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['send_otp'],
        method='POST',
        data={
            'email': email,
            'locale': 'en_PK',
            'region': 'PK',
            'app_id': GARENA['app_id'],
            'access_token': token
        }
    )
    
    if result['success'] and result.get('status') == 200:
        data = result.get('data', {})
        if data.get('result') == 0:
            return jsonify({'success': True, 'message': f'OTP sent to {email}'})
    return jsonify({'success': False, 'error': result.get('error', 'Failed to send OTP')}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    token = request.json.get('token', '').strip()
    email = request.json.get('email', '').strip()
    otp = request.json.get('otp', '').strip()
    if not token or not email or not otp:
        return jsonify({'success': False, 'error': 'All fields required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['verify_otp'],
        method='POST',
        data={
            'app_id': GARENA['app_id'],
            'access_token': token,
            'email': email,
            'code': otp,
            'otp': otp,
            'type': '1'
        }
    )
    
    if result['success'] and result.get('status') == 200:
        verifier_token = result.get('data', {}).get('verifier_token')
        if verifier_token:
            return jsonify({'success': True, 'verifier_token': verifier_token})
    return jsonify({'success': False, 'error': 'OTP verification failed'}), 500

@app.route('/api/create-bind', methods=['POST'])
def create_bind():
    token = request.json.get('token', '').strip()
    email = request.json.get('email', '').strip()
    verifier_token = request.json.get('verifier_token', '').strip()
    secondary_password = request.json.get('secondary_password', '').strip()
    
    if not all([token, email, verifier_token, secondary_password]):
        return jsonify({'success': False, 'error': 'All fields required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['create_bind'],
        method='POST',
        data={
            'email': email,
            'app_id': GARENA['app_id'],
            'access_token': token,
            'verifier_token': verifier_token,
            'secondary_password': secondary_password
        }
    )
    
    if result['success'] and result.get('status') == 200:
        if result.get('data', {}).get('result') == 0:
            return jsonify({'success': True, 'message': f'Bind request created for {email}'})
    return jsonify({'success': False, 'error': 'Bind request failed'}), 500

@app.route('/api/create-rebind', methods=['POST'])
def create_rebind():
    token = request.json.get('token', '').strip()
    email = request.json.get('email', '').strip()
    verifier_token = request.json.get('verifier_token', '').strip()
    secondary_password = request.json.get('secondary_password', '').strip()
    
    if not all([token, email, verifier_token, secondary_password]):
        return jsonify({'success': False, 'error': 'All fields required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['create_rebind'],
        method='POST',
        data={
            'email': email,
            'app_id': GARENA['app_id'],
            'access_token': token,
            'verifier_token': verifier_token,
            'secondary_password': secondary_password
        }
    )
    
    if result['success'] and result.get('status') == 200:
        if result.get('data', {}).get('result') == 0:
            return jsonify({'success': True, 'message': f'Rebind request created for {email}'})
    return jsonify({'success': False, 'error': 'Rebind request failed'}), 500

@app.route('/api/create-unbind', methods=['POST'])
def create_unbind():
    token = request.json.get('token', '').strip()
    email = request.json.get('email', '').strip()
    if not token or not email:
        return jsonify({'success': False, 'error': 'Token and email required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['create_unbind'],
        method='POST',
        data={
            'email': email,
            'app_id': GARENA['app_id'],
            'access_token': token
        }
    )
    
    if result['success'] and result.get('status') == 200:
        if result.get('data', {}).get('result') == 0:
            return jsonify({'success': True, 'message': f'Unbind request created for {email}'})
    return jsonify({'success': False, 'error': 'Unbind request failed'}), 500

@app.route('/api/verify-identity', methods=['POST'])
def verify_identity():
    token = request.json.get('token', '').strip()
    identity = request.json.get('identity', '').strip()
    if not token or not identity:
        return jsonify({'success': False, 'error': 'Token and identity required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['verify_identity'],
        method='POST',
        data={
            'app_id': GARENA['app_id'],
            'access_token': token,
            'identity': identity
        }
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Identity verification failed')}), 500

@app.route('/api/cancel-request', methods=['POST'])
def cancel_request():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['cancel_request'],
        method='POST',
        data={'app_id': GARENA['app_id'], 'access_token': token}
    )
    
    if result['success'] and result.get('status') == 200:
        if result.get('data', {}).get('result') == 0:
            return jsonify({'success': True, 'message': 'Request cancelled'})
    return jsonify({'success': False, 'error': 'Cancellation failed'}), 500

@app.route('/api/decode-token', methods=['POST'])
def decode_token():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    decoded = decode_jwt_full(token)
    if decoded and 'error' not in decoded:
        return jsonify({'success': True, 'data': decoded})
    return jsonify({'success': False, 'error': decoded.get('error', 'Invalid JWT')}), 400

@app.route('/api/token-inspect', methods=['POST'])
def token_inspect():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['token_inspect'],
        method='GET',
        params={'token': token}
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Inspection failed')}), 500

@app.route('/api/revoke-token', methods=['POST'])
def revoke_token():
    token = request.json.get('token', '').strip()
    refresh_token = request.json.get('refresh_token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    url = f"{GARENA['base_url']}{GARENA['endpoints']['revoke_token']}?access_token={token}"
    if refresh_token:
        url += f"&refresh_token={refresh_token}"
    
    try:
        resp = requests.get(url, headers={'User-Agent': GARENA['user_agent']}, timeout=10)
        return jsonify({'success': True, 'message': 'Token revoked successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/grant-guest', methods=['POST'])
def grant_guest():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['grant_guest'],
        method='POST',
        data={'access_token': token, 'app_id': GARENA['app_id']}
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Guest grant failed')}), 500

@app.route('/api/register-guest', methods=['POST'])
def register_guest():
    result = garena_request(
        GARENA['endpoints']['register_guest'],
        method='POST',
        data={'app_id': GARENA['app_id']}
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Guest registration failed')}), 500

@app.route('/api/platform-info', methods=['POST'])
def platform_info():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['platform_info'],
        method='POST',
        data={'app_id': GARENA['app_id'], 'access_token': token}
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Failed to get platform info')}), 500

@app.route('/api/login-data-from-token', methods=['POST'])
def login_data_from_token():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    try:
        resp = requests.get(
            f"{GARENA['ff_service']}{GARENA['endpoints']['login_data_from_token']}?data={token}",
            headers={'User-Agent': GARENA['user_agent']},
            timeout=15
        )
        if resp.status_code == 200:
            return jsonify({'success': True, 'data': resp.json() if resp.text else {}})
        return jsonify({'success': False, 'error': f'HTTP {resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/topup-info', methods=['POST'])
def topup_info():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    result = garena_request(
        GARENA['endpoints']['topup_info'],
        method='POST',
        params={'access_token': token},
        base=GARENA['msdk_base']
    )
    
    if result['success'] and result.get('status') == 200:
        return jsonify({'success': True, 'data': result.get('data', {})})
    return jsonify({'success': False, 'error': result.get('error', 'Failed to get topup info')}), 500

# For Vercel - expose the app
app.debug = False
