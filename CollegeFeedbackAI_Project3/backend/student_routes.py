from flask import Blueprint, request, render_template, redirect, session, flash
from db import get_db_connection
import hashlib

student_bp = Blueprint('student_bp', __name__)

@student_bp.route('/signup/student', methods=['GET', 'POST'])
def signup_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        branch = request.form['branch']
        year = request.form['year']

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO students (student_id, name, email, password, branch, year) VALUES (%s, %s, %s, %s, %s, %s)",
                (student_id, name, email, hashed_password, branch, year)
            )
            conn.commit()
            flash('Student registered successfully! Please login.')
            return redirect('/login')
        except Exception as e:
            flash(f'Error: {str(e)}')
            return render_template('signup_student.html')
        finally:
            cursor.close()
            conn.close()
    else:
        return render_template('signup_student.html')

@student_bp.route('/login/student', methods=['POST'])
def login_student():
    student_id = request.form['student_id']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE student_id=%s AND password=%s",
        (student_id, hashed_password)
    )
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    if student:
        session['user_id'] = student['student_id']
        session['user_type'] = 'student'
        return redirect('/feedback_form')
    else:
        flash('Invalid student ID or password')
        return redirect('/login')

@student_bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if session.get('user_type') != 'student':
        return redirect('/login')

    student_id = session['user_id']
    course_id = request.form['course_id']
    comment = request.form['comment']

    # For now, sentiment analysis can be empty or simple placeholder
    sentiment = None
    sentiment_label = None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO feedback (student_id, course_id, comment, sentiment, sentiment_label, date) VALUES (%s, %s, %s, %s, %s, NOW())",
        (student_id, course_id, comment, sentiment, sentiment_label)
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash('Feedback submitted successfully!')
    return redirect('/feedback_form')
