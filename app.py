from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json
import hashlib
import os
import base64
from urllib.parse import parse_qs, urlparse

# Simple encryption simulation (not secure for production!)
def simple_encrypt(text, key):
    """Simple XOR encryption - NOT for production use!"""
    encrypted = []
    for i, char in enumerate(text):
        key_char = key[i % len(key)]
        encrypted.append(chr(ord(char) ^ ord(key_char)))
    return base64.b64encode(''.join(encrypted).encode()).decode()

def simple_decrypt(encrypted_text, key):
    """Simple XOR decryption - NOT for production use!"""
    try:
        encrypted = base64.b64decode(encrypted_text).decode()
        decrypted = []
        for i, char in enumerate(encrypted):
            key_char = key[i % len(key)]
            decrypted.append(chr(ord(char) ^ ord(key_char)))
        return ''.join(decrypted)
    except:
        return "[Decryption Error]"

class PasswordStoreHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_file('templates/login.html', 'text/html')
        elif path == '/login':
            self.serve_file('templates/login.html', 'text/html')
        elif path == '/signup':
            self.serve_file('templates/signup.html', 'text/html')
        elif path == '/index':
            self.serve_file('templates/index.html', 'text/html')
        elif path == '/static/style.css':
            self.serve_file('static/style.css', 'text/css')
        elif path == '/static/script.js':
            self.serve_file('static/script.js', 'text/javascript')
        elif path == '/api/passwords':
            self.get_passwords()
        else:
            self.send_error(404)
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        if self.path == '/api/login':
            self.login_user(data)
        elif self.path == '/api/signup':
            self.signup_user(data)
        elif self.path == '/api/add-password':
            self.add_password(data)
        elif self.path == '/api/delete-password':
            self.delete_password(data)
        else:
            self.send_error(404)
    
    def serve_file(self, filename, content_type):
        try:
            with open(filename, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404)
    
    def send_response_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def get_db(self):
        return sqlite3.connect('password_store.db')
    
    def hash_password(self, password, salt):
        """Hash password with salt using PBKDF2"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def get_encryption_key(self, user_id, master_password):
        """Generate a simple key from master password"""
        conn = self.get_db()
        c = conn.cursor()
        c.execute('SELECT salt FROM users WHERE id = ?', (user_id,))
        salt = c.fetchone()[0]
        conn.close()
        
        # Create a key from master password and salt
        key_input = master_password + salt
        return hashlib.sha256(key_input.encode()).hexdigest()[:32]
    
    def signup_user(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            self.send_response_json({'error': 'Missing fields'}, 400)
            return
        
        salt = os.urandom(16).hex()
        hashed = self.hash_password(password, salt)
        
        try:
            conn = self.get_db()
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password, salt) VALUES (?, ?, ?)',
                     (username, hashed, salt))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            
            self.send_response_json({'success': True, 'user_id': user_id})
        except sqlite3.IntegrityError:
            self.send_response_json({'error': 'Username already exists'}, 400)
    
    def login_user(self, data):
        username = data.get('username')
        password = data.get('password')
        
        conn = self.get_db()
        c = conn.cursor()
        c.execute('SELECT id, password, salt FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user:
            user_id, hashed, salt = user
            if self.hash_password(password, salt) == hashed:
                self.send_response_json({'success': True, 'user_id': user_id})
                return
        
        self.send_response_json({'error': 'Invalid credentials'}, 401)
    
    def add_password(self, data):
        user_id = data.get('user_id')
        master_password = data.get('password')
        site_name = data.get('site_name')
        site_url = data.get('site_url', '')
        site_username = data.get('username')
        site_password = data.get('site_password')
        
        if not all([user_id, master_password, site_name, site_username, site_password]):
            self.send_response_json({'error': 'Missing fields'}, 400)
            return
        
        try:
            # Get encryption key from master password
            key = self.get_encryption_key(int(user_id), master_password)
            
            # Encrypt the site password
            encrypted = simple_encrypt(site_password, key)
            
            conn = self.get_db()
            c = conn.cursor()
            c.execute('''INSERT INTO passwords (user_id, site_name, site_url, username, encrypted_password)
                        VALUES (?, ?, ?, ?, ?)''',
                     (user_id, site_name, site_url, site_username, encrypted))
            conn.commit()
            conn.close()
            
            self.send_response_json({'success': True})
        except Exception as e:
            self.send_response_json({'error': str(e)}, 500)
    
    def get_passwords(self):
        params = parse_qs(urlparse(self.path).query)
        user_id = params.get('user_id', [None])[0]
        master_password = params.get('password', [None])[0]
        
        if not user_id or not master_password:
            self.send_response_json({'error': 'Missing credentials'}, 400)
            return
        
        try:
            # Get encryption key from master password
            key = self.get_encryption_key(int(user_id), master_password)
            
            conn = self.get_db()
            c = conn.cursor()
            c.execute('''SELECT id, site_name, site_url, username, encrypted_password 
                        FROM passwords WHERE user_id = ?''', (user_id,))
            passwords = []
            for row in c.fetchall():
                # Decrypt the password
                decrypted = simple_decrypt(row[4], key)
                passwords.append({
                    'id': row[0],
                    'site_name': row[1],
                    'site_url': row[2],
                    'username': row[3],
                    'password': decrypted
                })
            conn.close()
            
            self.send_response_json({'success': True, 'passwords': passwords})
        except Exception as e:
            self.send_response_json({'error': str(e)}, 500)
    
    def delete_password(self, data):
        password_id = data.get('id')
        
        conn = self.get_db()
        c = conn.cursor()
        c.execute('DELETE FROM passwords WHERE id = ?', (password_id,))
        conn.commit()
        conn.close()
        
        self.send_response_json({'success': True})

def init_db():
    conn = sqlite3.connect('password_store.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''DROP TABLE IF EXISTS users''')
    c.execute('''DROP TABLE IF EXISTS passwords''')
    
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        salt TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE passwords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        site_name TEXT NOT NULL,
        site_url TEXT,
        username TEXT NOT NULL,
        encrypted_password TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    if not os.path.exists('password_store.db'):
        init_db()
        print("Database initialized!")
    
    server = HTTPServer(('localhost', 8000), PasswordStoreHandler)
    print('Server running on http://localhost:8000')
    print('Press Ctrl+C to stop')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')