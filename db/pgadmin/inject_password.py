#!/usr/bin/env python3
"""
Injects the Postgres password into pgAdmin's SQLite database so the UI
auto-connects without prompting the user.

Waits for gunicorn to be fully up (meaning pgAdmin's own server-import /
REPLACE_SERVERS_ON_STARTUP step is 100% complete) before writing, so there
is no race with the replace step wiping the password.
"""
import importlib.util, os, sqlite3, time, sys

DB_PATH = '/var/lib/pgadmin/pgadmin4.db'
PG_PASSWORD = 'hirepilot_pass'
DESKTOP_USER = 'pgadmin4@pgadmin.org'

# Load pgAdmin's AES crypto helpers without triggering Flask app context
spec = importlib.util.spec_from_file_location('crypto', '/pgadmin4/pgadmin/utils/crypto.py')
crypto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crypto)


def gunicorn_running():
    """Return True once gunicorn has started (pgAdmin fully initialised)."""
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                if b'gunicorn' in f.read():
                    return True
        except OSError:
            pass
    return False


# Wait up to 90 s for gunicorn — it starts only after setup.py load-servers
print('[inject_password] Waiting for gunicorn to start...')
for _ in range(90):
    if gunicorn_running():
        break
    time.sleep(1)
else:
    print('[inject_password] Timed out waiting for gunicorn', file=sys.stderr)
    sys.exit(1)

# Small buffer to let gunicorn finish its own DB writes
time.sleep(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute('SELECT password FROM user WHERE email = ?', (DESKTOP_USER,))
row = cur.fetchone()
if not row:
    print(f'[inject_password] Desktop user {DESKTOP_USER} not found', file=sys.stderr)
    conn.close()
    sys.exit(1)

user_pass_hash = row[0]
encrypted = crypto.encrypt(PG_PASSWORD, user_pass_hash).decode()

cur.execute('UPDATE server SET password = ?, save_password = 1', (encrypted,))
conn.commit()

cur.execute('SELECT COUNT(*) FROM server WHERE save_password = 1')
count = cur.fetchone()[0]
conn.close()
print(f'[inject_password] Password saved for {count} server(s).')
