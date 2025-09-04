

# app.py
from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory
import mysql.connector
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os, re

# -----------------------
# LOAD ENV VARIABLES
# -----------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallbacksecret")

# -----------------------
# CONFIG
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
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "lms_db")
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(fname):
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXT

def is_email(input_str):
    return re.match(r"[^@]+@[^@]+\.[^@]+", input_str)

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
# ROUTES
# -----------------------
@app.route('/')
def home():
    return render_template('home.html')


# LOGIN
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


# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', user=session['user'])


# NOTES
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
            cursor.execute("INSERT INTO notes (course_title, filename, uploaded_by) VALUES (%s, %s, %s)",
                           (course_title, filename, session['user']['email']))
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


# VIDEOS
@app.route('/upload_video', methods=['GET', 'POST'])
def upload_video():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['video_file']
        if file and allowed_video_file(file.filename):
            fname = secure_filename(file.filename)
            path = os.path.join(app.config['VIDEO_FOLDER'], fname)
            file.save(path)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO videos (title, filename, uploaded_by) VALUES (%s, %s, %s)",
                           (title, fname, session['user']['email']))
            conn.commit()
            cursor.close()
            conn.close()
            return "✅ Video uploaded!"
        else:
            return "❌ Invalid file type."
    return render_template('upload_video.html')

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/view_videos')
def view_videos():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT title, filename FROM videos")
    vids = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_videos.html', videos=vids)


# QUIZZES
@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('home'))
    if request.method == 'POST':
        q = request.form['question']
        a = request.form['option_a']
        b = request.form['option_b']
        c = request.form['option_c']
        d = request.form['option_d']
        correct = request.form['correct_option']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, correct_option, created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (q, a, b, c, d, correct, session['user']['email'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return "✅ Question added successfully!"
    return render_template('create_quiz.html')

@app.route('/take_quiz', methods=['GET', 'POST'])
def take_quiz():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    cursor.close()
    conn.close()

    if request.method == 'POST':
        score = 0
        for q in questions:
            choice = request.form.get(str(q['id']))
            is_corr = (choice == q['correct_option'])
            if is_corr:
                score += 1
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO attempts (student_email, question_id, chosen_option, is_correct) VALUES (%s,%s,%s,%s)",
                      (session['user']['email'], q['id'], choice, is_corr))
            conn.commit()
            c.close()
            conn.close()
        return f"Your score: {score} out of {len(questions)}"
    return render_template('take_quiz.html', questions=questions)


# GRADES
@app.route('/view_grades')
def view_grades():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('home'))
    student_email = session['user']['email']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT timestamp, COUNT(*) AS total,
               SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) AS correct
        FROM attempts WHERE student_email = %s
        GROUP BY timestamp ORDER BY timestamp DESC
    """, (student_email,))
    attempts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_grades.html', attempts=attempts)


# COURSES & ENROLLMENTS
@app.route('/view_courses')
def view_courses():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('home'))
    email = session['user']['email']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    cursor.execute("SELECT course_id FROM enrollments WHERE student_email=%s", (email,))
    enrolled = [row['course_id'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return render_template('view_courses.html', courses=courses, enrolled_courses=enrolled)

@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('home'))
    student_email = session['user']['email']
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO enrollments (student_email, course_id) VALUES (%s,%s)",
                       (student_email, course_id))
        conn.commit()
    except mysql.connector.IntegrityError:
        pass
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('view_courses'))

@app.route('/my_courses')
def my_courses():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.* FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        WHERE e.student_email=%s
    """, (session['user']['email'],))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('my_courses.html', courses=courses)


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Inject user into all templates
@app.context_processor
def inject_user():
    return dict(user=session.get('user'))

# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)

