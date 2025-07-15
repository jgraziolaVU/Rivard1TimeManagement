from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from parser import parse_schedule
from scheduler import create_schedule
from emailer import send_weekly_email
from database import init_db, add_deadline, get_deadlines, remove_deadline, add_student_schedule
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
init_db()

@app.route('/')
def index():
    """Serve the main application"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle student schedule upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract form data
        email = request.form.get('email')
        wakeup = int(request.form.get('wakeup', 8))
        sleep = int(request.form.get('sleep', 23))
        study_style = request.form.get('studyStyle', 'pomodoro')
        
        # Parse the uploaded file
        dates = parse_schedule(filepath)
        
        # Get existing deadlines from database
        deadlines = get_deadlines()
        
        # Create personalized schedule
        schedule = create_schedule(dates, {
            'email': email,
            'wakeup': wakeup,
            'sleep': sleep,
            'study_style': study_style,
            'deadlines': deadlines
        })
        
        # Save student schedule to database
        add_student_schedule(email, schedule)
        
        # Send welcome email with schedule and attachments
        send_weekly_email(email, schedule, {
            'email': email,
            'wakeup': wakeup,
            'sleep': sleep,
            'study_style': study_style
        })
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'status': 'success',
            'schedule': schedule,
            'message': 'Schedule created successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deadlines', methods=['GET'])
def get_all_deadlines():
    """Get all course deadlines"""
    try:
        deadlines = get_deadlines()
        return jsonify(deadlines)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deadlines', methods=['POST'])
def add_course_deadline():
    """Add a new course deadline"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['courseCode', 'courseName', 'date', 'time', 'type', 'title']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        deadline_id = add_deadline(
            course_code=data['courseCode'],
            course_name=data['courseName'],
            deadline_date=data['date'],
            deadline_time=data['time'],
            deadline_type=data['type'],
            title=data['title'],
            description=data.get('description', '')
        )
        
        return jsonify({
            'status': 'success',
            'deadline_id': deadline_id,
            'message': 'Deadline added successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deadlines/<int:deadline_id>', methods=['DELETE'])
def delete_deadline(deadline_id):
    """Remove a course deadline"""
    try:
        success = remove_deadline(deadline_id)
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Deadline removed successfully!'
            })
        else:
            return jsonify({'error': 'Deadline not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_email', methods=['POST'])
def email():
    """Send weekly schedule email to student"""
    try:
        data = request.get_json()
        user_email = data.get("email")
        message = data.get("message")
        
        if not user_email or not message:
            return jsonify({'error': 'Email and message are required'}), 400
        
        send_weekly_email(user_email, message)
        return jsonify({
            'status': 'success',
            'message': 'Email sent successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

def secure_filename(filename):
    """Secure filename by removing dangerous characters"""
    import re
    filename = re.sub(r'[^\w\s-.]', '', filename)
    return filename.strip()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
