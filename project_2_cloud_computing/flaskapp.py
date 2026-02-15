from flask import Flask, render_template, request, redirect, url_for, send_from_directory, g
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['DATABASE'] = '/var/www/html/flaskapp/data/mydatabase.db'

def connect_to_database():
    return sqlite3.connect(app.config['DATABASE'])

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def execute_query(query, args=()):
    cur = get_db().cursor()
    cur.execute(query, args)
    get_db().commit()
    rows = cur.fetchall()
    cur.close()
    return rows

def init_db():
    with app.app_context():
        execute_query('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            firstname TEXT,
            lastname TEXT,
            email TEXT,
            address TEXT,
            filename TEXT,
            wordcount INTEGER
        )''')

init_db()

@app.route('/')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():

    username = request.form['username']
    password = request.form['password']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    address = request.form['address']

    if not username or not password:
        return "Username and password are required.", 400
    
    execute_query(
        "INSERT INTO users (username,password,firstname,lastname,email,address) VALUES (?,?,?,?,?,?)",
        (username, password, firstname, lastname, email, address)
    )
    return redirect(url_for('profile', username=username))

@app.route('/profile/<username>')
def profile(username):
    rows = execute_query("SELECT * FROM users WHERE username=?", (username,))
    user = rows[0] if rows else None
    return render_template('profile.html', user=user)

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return "Username and password are required.", 400
    
    rows = execute_query("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = rows[0] if rows else None

    if user:
        return redirect(url_for('profile', username=username))
    else:
        return "Invalid credentials"

@app.route('/upload/<username>', methods=['POST'])
def upload_file(username):
    file = request.files['file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    with open(filepath, 'r') as f:
        content = f.read()
        wordcount = len(content.split())

    execute_query("UPDATE users SET filename=?, wordcount=? WHERE username=?",
                  (file.filename, wordcount, username))

    return redirect(url_for('profile', username=username))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

