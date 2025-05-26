from flask import Blueprint, request, render_template, redirect, session, flash
from db import get_db_connection
import hashlib

faculty_bp = Blueprint('faculty_bp', __name__)

@faculty_bp.route('/signup/faculty', methods=['GET', 'POST'])
def signup_faculty():
    if request.method == 'POST':
        faculty_id = request.form['faculty_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        department = request.form['department']

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO faculty (faculty_id, name, email, password, department) VALUES (%s, %s, %s, %s, %s)",
                (faculty_id, name, email, hashed_password, department)
            )
            conn.commit()
            flash('Faculty registered successfully! Please login.')
            return redirect('/login')
        except Exception as e:
            flash(f'Error: {str(e)}')
            return render_template('signup_faculty.html')
        finally:
            cursor.close()
            conn.close()
    else:
        return render_template('signup_faculty.html')

@faculty_bp.route('/login/faculty', methods=['POST'])
def login_faculty():
    faculty_id = request.form['faculty_id']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM faculty WHERE faculty_id=%s AND password=%s",
        (faculty_id, hashed_password)
    )
    faculty = cursor.fetchone()
    cursor.close()
    conn.close()

    if faculty:
        session['user_id'] = faculty['faculty_id']
        session['user_type'] = 'faculty'
        return redirect('/admin_dashboard')
    else:
        flash('Invalid faculty ID or password')
        return redirect('/login')
