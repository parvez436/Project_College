import mysql.connector

def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Rpparvez$28",  # Ensure the password is correct
            database="college_feedback"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
