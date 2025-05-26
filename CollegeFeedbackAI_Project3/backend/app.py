from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from db import get_db_connection, add_student, add_instructors
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob   # -1 to +1

analyzer = SentimentIntensityAnalyzer()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a strong secret key in production!

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if role == 'student':
            query = "SELECT * FROM students WHERE student_id = %s AND password = %s"
        else:
            query = "SELECT * FROM instructors WHERE name = %s AND password = %s"

        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['student_id'] if role == 'student' else user['instructor_id']
            session['role'] = role
            session['user_name'] = user['name']
            if role == 'student':
                return redirect(url_for('feedback_form'))
            else:
                return redirect(url_for('instructor_dashboard'))
        else:
            flash("Username or password is incorrect", "error")
            return redirect(url_for('login'))

    return render_template("login.html")

@app.route('/signup/student', methods=['GET', 'POST'])
def signup_student():
    if request.method == 'POST':
        student_id = request.form['student_id'].strip()
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        branch = request.form['branch'].strip()
        year = request.form['year'].strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        exists = cursor.fetchone()

        if exists:
            flash('Student ID already exists.', 'warning')
        else:
            add_student(student_id, name, email, password, branch, year)
            flash('Student registered successfully. Please login.', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        cursor.close()
        conn.close()

    return render_template('signup_student.html')

@app.route('/signup/instructors', methods=['GET', 'POST'])
def signup_instructors():
    if request.method == 'POST':
        instructor_id = request.form['instructor_id'].strip()
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        department = request.form['department'].strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM instructors WHERE instructor_id = %s", (instructor_id,))
        exists = cursor.fetchone()

        if exists:
            flash('Instructor ID already exists.', 'warning')
        else:
            add_instructors(instructor_id, name, email, password, department)
            flash('Instructor registered successfully. Please login.', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        cursor.close()
        conn.close()

    return render_template('signup_instructors.html')


def analyze_sentiment(comment):
    """Consistent sentiment analysis using either VADER or TextBlob"""
    # Using VADER (already imported)
    vs = analyzer.polarity_scores(comment) # type: ignore
    compound = vs['compound']
    
    if compound >= 0.05:  # Positive
        return "Positive", compound
    elif compound <= -0.05:  # Negative
        return "Negative", compound
    else:  # Neutral
        return "Neutral", compound

@app.route('/feedback', methods=['GET', 'POST'])
def feedback_form():
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please login as student to give feedback.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        student_id = session['user_id']
        course_id = request.form.get('course_id')
        comment = request.form.get('comment', '').strip()  # Added safety

        if not comment:  # Validate comment exists
            flash('Please enter feedback text', 'error')
            return redirect(url_for('feedback_form'))

        # Analyze sentiment
        sentiment_label, sentiment_score = analyze_sentiment(comment)

        # Save to database
        try:
            cursor.execute("""
                INSERT INTO feedback 
                (student_id, course_id, comment, date, sentiment, sentiment_label) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (student_id, course_id, comment, datetime.now(), sentiment_score, sentiment_label))
            conn.commit()
            flash('Feedback submitted successfully!', 'success')
            return redirect(url_for('thanks'))
        except Exception as e:
            conn.rollback()
            flash('Error submitting feedback', 'error')
            app.logger.error(f"Database error: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    try:
        cursor.execute("SELECT course_id, title FROM courses")
        courses = cursor.fetchall()
        return render_template('feedback_form.html', courses=courses)
    except Exception as e:
        flash('Error loading courses', 'error')
        app.logger.error(f"Course load error: {str(e)}")
        return redirect(url_for('home'))
    finally:
        cursor.close()
        conn.close()

# Rest of your routes (login, signup, dashboard, etc.) remain the same...

@app.route('/thanks')
def thanks():
    return render_template('thank_you.html')

@app.route('/instructor/dashboard')
def instructor_dashboard():
    if 'user_id' not in session or session.get('role') != 'instructor':
        flash("Please log in as instructor.", "warning")
        return redirect(url_for('login'))

    instructor_id = session['user_id']
    instructor_name = session.get('user_name', 'Instructor')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get feedback data for table display
    cursor.execute("""
        SELECT f.student_id, s.name AS student_name, f.course_id, c.title AS course_title,
               f.comment, f.date, COALESCE(f.sentiment, 0) AS sentiment,
               COALESCE(f.sentiment_label, 'Neutral') AS sentiment_label
        FROM feedback f
        JOIN students s ON f.student_id = s.student_id
        JOIN courses c ON f.course_id = c.course_id
        WHERE c.instructor_id = %s
        ORDER BY f.date DESC
    """, (instructor_id,))
    feedback_data = cursor.fetchall()

    # Get sentiment counts for pie chart
    cursor.execute("""
        SELECT 
            COALESCE(sentiment_label, 'Neutral') AS sentiment_label,
            COUNT(*) AS count
        FROM feedback
        WHERE course_id IN (
            SELECT course_id FROM courses WHERE instructor_id = %s
        )
        GROUP BY sentiment_label
    """, (instructor_id,))
    chart_data = cursor.fetchall()

    # Ensure all sentiment types are represented
    sentiment_counts = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
    for item in chart_data:
        sentiment_counts[item['sentiment_label']] = item['count']

    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html',
                         feedback_data=feedback_data,
                         chart_data=sentiment_counts,
                         instructor_name=instructor_name)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)