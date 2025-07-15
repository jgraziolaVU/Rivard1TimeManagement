import sqlite3
import json
from datetime import datetime
import os

DATABASE_PATH = 'studyflow.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    
    # Create deadlines table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            deadline_date DATE NOT NULL,
            deadline_time TIME NOT NULL,
            deadline_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create student_schedules table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS student_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            schedule_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table for future authentication
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            user_type TEXT DEFAULT 'student',
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_deadline(course_code, course_name, deadline_date, deadline_time, deadline_type, title, description=''):
    """Add a new deadline to the database"""
    conn = get_db_connection()
    
    cursor = conn.execute('''
        INSERT INTO deadlines (course_code, course_name, deadline_date, deadline_time, deadline_type, title, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (course_code, course_name, deadline_date, deadline_time, deadline_type, title, description))
    
    deadline_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return deadline_id

def get_deadlines(course_code=None):
    """Get all deadlines or deadlines for a specific course"""
    conn = get_db_connection()
    
    if course_code:
        deadlines = conn.execute('''
            SELECT * FROM deadlines 
            WHERE course_code = ? 
            ORDER BY deadline_date, deadline_time
        ''', (course_code,)).fetchall()
    else:
        deadlines = conn.execute('''
            SELECT * FROM deadlines 
            ORDER BY deadline_date, deadline_time
        ''').fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries
    result = []
    for deadline in deadlines:
        result.append({
            'id': deadline['id'],
            'course_code': deadline['course_code'],
            'course_name': deadline['course_name'],
            'date': deadline['deadline_date'],
            'time': deadline['deadline_time'],
            'type': deadline['deadline_type'],
            'title': deadline['title'],
            'description': deadline['description'],
            'created_at': deadline['created_at']
        })
    
    return result

def remove_deadline(deadline_id):
    """Remove a deadline from the database"""
    conn = get_db_connection()
    
    cursor = conn.execute('DELETE FROM deadlines WHERE id = ?', (deadline_id,))
    affected_rows = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected_rows > 0

def add_student_schedule(email, schedule_data):
    """Add or update a student's schedule"""
    conn = get_db_connection()
    
    # Check if schedule already exists for this email
    existing = conn.execute(
        'SELECT id FROM student_schedules WHERE email = ?', (email,)
    ).fetchone()
    
    schedule_json = json.dumps(schedule_data)
    
    if existing:
        # Update existing schedule
        conn.execute('''
            UPDATE student_schedules 
            SET schedule_data = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE email = ?
        ''', (schedule_json, email))
    else:
        # Insert new schedule
        conn.execute('''
            INSERT INTO student_schedules (email, schedule_data)
            VALUES (?, ?)
        ''', (email, schedule_json))
    
    conn.commit()
    conn.close()

def get_student_schedule(email):
    """Get a student's schedule"""
    conn = get_db_connection()
    
    schedule = conn.execute(
        'SELECT schedule_data FROM student_schedules WHERE email = ?', (email,)
    ).fetchone()
    
    conn.close()
    
    if schedule:
        return json.loads(schedule['schedule_data'])
    return None

def get_upcoming_deadlines(days_ahead=7):
    """Get deadlines within the next N days"""
    from datetime import date, timedelta
    
    conn = get_db_connection()
    
    today = date.today()
    future_date = today + timedelta(days=days_ahead)
    
    deadlines = conn.execute('''
        SELECT * FROM deadlines 
        WHERE deadline_date BETWEEN ? AND ?
        ORDER BY deadline_date, deadline_time
    ''', (today.isoformat(), future_date.isoformat())).fetchall()
    
    conn.close()
    
    result = []
    for deadline in deadlines:
        result.append({
            'id': deadline['id'],
            'course_code': deadline['course_code'],
            'course_name': deadline['course_name'],
            'date': deadline['deadline_date'],
            'time': deadline['deadline_time'],
            'type': deadline['deadline_type'],
            'title': deadline['title'],
            'description': deadline['description']
        })
    
    return result

def add_user(email, name=None, user_type='student', preferences=None):
    """Add a new user to the system"""
    conn = get_db_connection()
    
    preferences_json = json.dumps(preferences) if preferences else None
    
    try:
        cursor = conn.execute('''
            INSERT INTO users (email, name, user_type, preferences)
            VALUES (?, ?, ?, ?)
        ''', (email, name, user_type, preferences_json))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None  # User already exists

def get_user(email):
    """Get user information"""
    conn = get_db_connection()
    
    user = conn.execute(
        'SELECT * FROM users WHERE email = ?', (email,)
    ).fetchone()
    
    conn.close()
    
    if user:
        return {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'user_type': user['user_type'],
            'preferences': json.loads(user['preferences']) if user['preferences'] else {},
            'created_at': user['created_at']
        }
    return None

def update_user_preferences(email, preferences):
    """Update user preferences"""
    conn = get_db_connection()
    
    preferences_json = json.dumps(preferences)
    
    conn.execute('''
        UPDATE users 
        SET preferences = ? 
        WHERE email = ?
    ''', (preferences_json, email))
    
    conn.commit()
    conn.close()

def cleanup_old_schedules(days_old=30):
    """Clean up old student schedules"""
    from datetime import datetime, timedelta
    
    conn = get_db_connection()
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    cursor = conn.execute('''
        DELETE FROM student_schedules 
        WHERE updated_at < ?
    ''', (cutoff_date.isoformat(),))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count
