import os
import glob
import sqlite3
import shutil
import tempfile


def find_profile():
    appdata = os.environ.get('APPDATA', '')
    patterns = [
        os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles', '*.default-release', 'cookies.sqlite'),
        os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles', '*.default', 'cookies.sqlite'),
        os.path.expanduser('~/.mozilla/firefox/*.default-release/cookies.sqlite'),
        os.path.expanduser('~/.mozilla/firefox/*.default/cookies.sqlite'),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def read_cookies():
    db_path = find_profile()
    if not db_path:
        return {}
    tmp = os.path.join(tempfile.gettempdir(), 'ff_cookies_claude_tmp.sqlite')
    try:
        shutil.copy2(db_path, tmp)
        conn = sqlite3.connect(tmp)
        rows = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE host LIKE '%claude.ai' ORDER BY lastAccessed DESC"
        ).fetchall()
        conn.close()
        return {name: value for name, value in rows}
    except Exception:
        return {}
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass