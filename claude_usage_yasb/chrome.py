import os
import json
import glob
import base64
import sqlite3
import shutil
import tempfile


CHROME_PROFILES = {
    'Chrome':        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data'),
    'Chrome Beta':   os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome Beta', 'User Data'),
    'Edge':          os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data'),
    'Brave':         os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BraveSoftware', 'Brave-Browser', 'User Data'),
}


def _get_key(user_data_dir):
    local_state_path = os.path.join(user_data_dir, 'Local State')
    if not os.path.exists(local_state_path):
        return None
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    encrypted_key = encrypted_key[5:]  # strip 'DPAPI' prefix
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except ImportError:
        return None


def _decrypt(key, encrypted_value):
    if not encrypted_value:
        return ''
    if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
        try:
            from Crypto.Cipher import AES
            nonce = encrypted_value[3:15]
            ciphertext = encrypted_value[15:-16]
            tag = encrypted_value[-16:]
            return AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ciphertext, tag).decode('utf-8')
        except Exception:
            return ''
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
    except Exception:
        return ''


def _read_profile(cookies_path, key):
    tmp = os.path.join(tempfile.gettempdir(), 'chrome_cookies_claude_tmp.sqlite')
    try:
        shutil.copy2(cookies_path, tmp)
        conn = sqlite3.connect(tmp)
        rows = conn.execute(
            "SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%claude.ai' ORDER BY last_access_utc DESC"
        ).fetchall()
        conn.close()
        return {name: _decrypt(key, val) for name, val in rows if val}
    except Exception:
        return {}
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass


def read_cookies():
    for browser, user_data_dir in CHROME_PROFILES.items():
        if not os.path.exists(user_data_dir):
            continue
        key = _get_key(user_data_dir)
        if not key:
            continue
        for profile in ['Default'] + [f'Profile {i}' for i in range(1, 10)]:
            cookies_path = os.path.join(user_data_dir, profile, 'Network', 'Cookies')
            if not os.path.exists(cookies_path):
                cookies_path = os.path.join(user_data_dir, profile, 'Cookies')
            if os.path.exists(cookies_path):
                cookies = _read_profile(cookies_path, key)
                if cookies.get('sessionKey'):
                    return cookies
    return {}