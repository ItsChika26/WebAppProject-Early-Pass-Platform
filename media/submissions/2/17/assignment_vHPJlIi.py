# Database Query Example
import sqlite3

def get_students_by_year(year):
    """Fetch all students in a given year"""
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM students WHERE year = ?"
    cursor.execute(query, (year,))
    
    results = cursor.fetchall()
    conn.close()
    return results

# Example usage
students = get_students_by_year(2)
for student in students:
    print(student)
