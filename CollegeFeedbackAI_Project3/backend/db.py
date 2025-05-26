import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
            user="root",
            password="Rpparvez$28",  # Ensure the password is correct
            database="college_feedback"
    )

def add_student(student_id, name, email, password, branch, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO students (student_id, name, email, password, branch, year)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (student_id, name, email, password, branch, year))
    conn.commit()
    cursor.close()
    conn.close()
    
def add_instructors(instructor_id, name, email, password, department):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO instructors (instructor_id, name, email, password, department) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (instructor_id, name, email, password, department))
    conn.commit()
    cursor.close()
    conn.close()


def check_student_login(student_id, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM students WHERE student_id=%s AND password=%s"
    cursor.execute(query, (student_id, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def check_faculty_login(name, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM faculty WHERE name=%s AND password=%s"
    cursor.execute(query, (name, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

