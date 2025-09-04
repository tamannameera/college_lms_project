

from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory
import mysql.connector
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os, re

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallbacksecret")  # default if .env missing

# ✅ Utility: Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "lms_db")
    )

# -----------------------
# CONFIGS
# -----------------------
UPLOAD_FOLDER = 'uploads'
VIDEO_FOLDER = 'video_uploads'
ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_VIDEO_EXT = {'mp4', 'mov', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VIDEO_FOLDER'] = VIDEO_FOLDER


# -----------------------
# HELPERS
# -----------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(fname):
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXT

def is_email(input_str):
    return re.match(r"[^@]+@[^@]+\.[^@]+", input_str)


# -----------------------
# ROUTES
# -----------------------
@app.route('/')
def home():
    return render_template('home.html')


# ✅ Get user by email/phone
def get_user_by_identifier(identifier):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if is_email(identifier):
        query = "SELECT * FROM users WHERE email = %s"
    else:
        query = "SELECT * FROM users WHERE phone = %s"

    cursor.execute(query, (identifier,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()
    return user


# -----------------------
# LOGIN
# -----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        user = get_user_by_identifier(identifier)

        if user and check_password_hash(user['password_hash'], password):
            session['user'] = {
                'id': user['id'],
                'role': user['role'],
                'email': user['email']
            }
            return redirect(url_for('dashboard'))
        else:
            return "❌ Invalid email/phone or password. Try again."

    return render_template('login.html')


# -----------------------
# DASHBOARD
# -----------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', user=session['user'])


# -----------------------
# NOTES
# -----------------------
@app.route('/upload_note', methods=['GET', 'POST'])
def upload_note():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('home'))

    if request.method == 'POST':
        course_title = request.form['course_title']
        file = request.files['note_file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (course_title, filename, uploaded_by) VALUES (%s, %s, %s)",
                (course_title, filename, session['user']['email'])
            )
            conn.commit()
            cursor.close()
            conn.close()

            return "✅ Note uploaded successfully!"
        else:
            return "❌ Invalid file type. Only PDFs allowed."

    return render_template('upload_notes.html')


@app.route('/view_notes')
def view_notes():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, course_title, filename FROM notes")
    notes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('view_notes.html', notes=notes)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# -----------------------
# LOGOUT
# -----------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# ✅ Inject user into templates
@app.context_processor
def inject_user():
    return dict(user=session.get('user'))



# -----------------------
# MAIN
# -----------------------
if __name__ == '__main__':
    app.run(debug=True)
