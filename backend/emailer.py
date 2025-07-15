import smtplib
from email.message import EmailMessage
from email.mime.text import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime, timedelta
import json

# Email configuration - use environment variables for security
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'your_email@example.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your_app_password')

def send_weekly_email(to_email, schedule_data, student_preferences=None):
    """Send a weekly schedule summary email with calendar and document attachments"""
    try:
        from email.mime.base import MIMEBase
        from email import encoders
        import tempfile
        import os
        
        # Generate email content
        subject = '📅 Your StudyFlow Schedule & Calendar Files'
        html_content = generate_weekly_email_html(schedule_data, student_preferences)
        text_content = generate_weekly_email_text(schedule_data)
        
        # Create message with attachments
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        
        # Create alternative container for text/html
        msg_alternative = MIMEMultipart('alternative')
        
        # Add both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg_alternative.attach(part1)
        msg_alternative.attach(part2)
        msg.attach(msg_alternative)
        
        # Generate and attach calendar file
        try:
            ics_content = generate_calendar_ics_file(schedule_data, to_email)
            
            calendar_attachment = MIMEBase('text', 'calendar')
            calendar_attachment.set_payload(ics_content.encode('utf-8'))
            encoders.encode_base64(calendar_attachment)
            calendar_attachment.add_header(
                'Content-Disposition',
                'attachment; filename="StudyFlow_Schedule.ics"'
            )
            msg.attach(calendar_attachment)
        except Exception as e:
            print(f"Warning: Could not generate calendar file: {e}")
        
        # Generate and attach summary document
        try:
            doc_content = generate_schedule_summary_doc(schedule_data, student_preferences or {})
            
            doc_attachment = MIMEBase('text', 'plain')
            doc_attachment.set_payload(doc_content.encode('utf-8'))
            encoders.encode_base64(doc_attachment)
            doc_attachment.add_header(
                'Content-Disposition',
                'attachment; filename="StudyFlow_Summary.txt"'
            )
            msg.attach(doc_attachment)
        except Exception as e:
            print(f"Warning: Could not generate summary document: {e}")
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_deadline_reminder(to_email, deadline_info):
    """Send a deadline reminder email"""
    try:
        subject = f'⚠️ Upcoming Deadline: {deadline_info.get("title", "Assignment")}'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .deadline-box {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .urgent {{ background: #f8d7da; border-color: #f5c6cb; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 StudyFlow Reminder</h1>
                    <p>Don't forget about your upcoming deadline!</p>
                </div>
                
                <div class="content">
                    <div class="deadline-box {'urgent' if deadline_info.get('days_until', 0) <= 1 else ''}">
                        <h2>🎯 {deadline_info.get('title', 'Assignment')}</h2>
                        <p><strong>Course:</strong> {deadline_info.get('course_code', 'N/A')} - {deadline_info.get('course_name', '')}</p>
                        <p><strong>Due Date:</strong> {deadline_info.get('date', '')} at {deadline_info.get('time', '')}</p>
                        <p><strong>Type:</strong> {deadline_info.get('type', '').title()}</p>
                        <p><strong>Days Remaining:</strong> {deadline_info.get('days_until', 0)} days</p>
                        {f"<p><strong>Description:</strong> {deadline_info.get('description', '')}</p>" if deadline_info.get('description') else ''}
                    </div>
                    
                    <h3>💡 Study Tips:</h3>
                    <ul>
                        <li>Break down the work into smaller, manageable tasks</li>
                        <li>Use the Pomodoro technique for focused study sessions</li>
                        <li>Don't wait until the last minute - start today!</li>
                        <li>Ask for help if you need clarification</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>This reminder was sent by StudyFlow - Your Smart College Planner</p>
                    <p>Stay organized, stay successful! 🎓</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        StudyFlow Deadline Reminder
        
        Upcoming Deadline: {deadline_info.get('title', 'Assignment')}
        Course: {deadline_info.get('course_code', 'N/A')} - {deadline_info.get('course_name', '')}
        Due Date: {deadline_info.get('date', '')} at {deadline_info.get('time', '')}
        Type: {deadline_info.get('type', '').title()}
        Days Remaining: {deadline_info.get('days_until', 0)} days
        
        {f"Description: {deadline_info.get('description', '')}" if deadline_info.get('description') else ''}
        
        Study Tips:
        - Break down the work into smaller, manageable tasks
        - Use the Pomodoro technique for focused study sessions
        - Don't wait until the last minute - start today!
        - Ask for help if you need clarification
        
        Stay organized, stay successful!
        StudyFlow - Your Smart College Planner
        """
        
        # Create and send message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending deadline reminder: {e}")
        return False

def generate_calendar_ics_file(schedule_data, student_email):
    """Generate an ICS calendar file that students can import to Google/Outlook"""
    from datetime import datetime
    import uuid
    
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//StudyFlow//StudyFlow App//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""
    
    for date_str, activities in schedule_data.items():
        for activity in activities:
            if activity.get('type') in ['study', 'deadline', 'exam']:
                # Create unique event ID
                event_id = str(uuid.uuid4())
                
                # Parse date and time
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
                activity_time = activity.get('time', '09:00')
                
                try:
                    hour, minute = map(int, activity_time.split(':'))
                    start_datetime = event_date.replace(hour=hour, minute=minute)
                    
                    # Default duration based on activity type
                    duration_minutes = activity.get('duration', 60)
                    end_datetime = start_datetime.replace(minute=start_datetime.minute + duration_minutes)
                    
                    # Format for ICS
                    start_str = start_datetime.strftime('%Y%m%dT%H%M%S')
                    end_str = end_datetime.strftime('%Y%m%dT%H%M%S')
                    
                    ics_content += f"""BEGIN:VEVENT
UID:{event_id}@studyflow.app
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{activity.get('activity', 'Study Session')}
DESCRIPTION:{activity.get('description', 'Generated by StudyFlow')}
CATEGORIES:EDUCATION
END:VEVENT
"""
                except:
                    continue  # Skip malformed times
    
    ics_content += "END:VCALENDAR"
    return ics_content

def generate_schedule_summary_doc(schedule_data, student_preferences):
    """Generate a Word document summary of the student's input and schedule"""
    summary = f"""
STUDYFLOW - YOUR PERSONALIZED STUDY PLAN SUMMARY
===============================================

STUDENT PREFERENCES:
- Email: {student_preferences.get('email', 'Not provided')}
- Wake Up Time: {student_preferences.get('wakeup', 8)}:00 AM
- Sleep Time: {student_preferences.get('sleep', 23)}:00 PM
- Study Style: {student_preferences.get('study_style', 'Not specified')}

SCHEDULE OVERVIEW:
=================

"""
    
    # Add daily breakdown
    for date_str, activities in sorted(schedule_data.items())[:14]:  # First 2 weeks
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = date_obj.strftime('%A, %B %d, %Y')
        
        summary += f"\n{day_name}:\n"
        summary += "-" * 40 + "\n"
        
        for activity in activities:
            summary += f"{activity.get('time', '')} - {activity.get('activity', '')}\n"
            if activity.get('description'):
                summary += f"    Notes: {activity.get('description')}\n"
        summary += "\n"
    
    summary += """
STUDY TIPS FOR SUCCESS:
======================
- Take regular 10-15 minute breaks between study sessions
- Stay hydrated and maintain good nutrition
- Get adequate sleep (7-9 hours per night)
- Use active learning techniques (flashcards, practice problems)
- Create a dedicated study space free from distractions
- Don't hesitate to ask professors or classmates for help

USING THIS DOCUMENT:
===================
- Save this document for your records
- If you need to recreate your schedule, you have all your preferences here
- Share relevant parts with study partners or tutors
- Use the calendar file (if attached) to import into Google Calendar or Outlook

Generated by StudyFlow - Your Smart College Planner
Visit us again anytime to create updated schedules!
"""
    
    return summary

def generate_weekly_email_html(schedule_data, student_preferences=None):
    """Generate HTML content for weekly schedule email"""
    today = datetime.today()
    week_start = today - timedelta(days=today.weekday())
    
    # Calculate this week's schedule
    weekly_schedule = {}
    for i in range(7):
        date = week_start + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        if date_str in schedule_data:
            weekly_schedule[date_str] = schedule_data[date_str]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; }}
            .week-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .day-card {{ background: #ffffff; border: 1px solid #e1e5e9; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .day-header {{ font-weight: bold; color: #667eea; margin-bottom: 15px; font-size: 1.1em; border-bottom: 2px solid #667eea; padding-bottom: 5px; }}
            .activity {{ background: #f8f9fa; padding: 10px; margin: 8px 0; border-radius: 6px; border-left: 4px solid #667eea; }}
            .study {{ border-left-color: #28a745; background: #d4edda; }}
            .deadline {{ border-left-color: #dc3545; background: #f8d7da; }}
            .meal {{ border-left-color: #ffc107; background: #fff3cd; }}
            .summary {{ background: #e8f4fd; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #6c757d; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📚 Your Weekly Study Schedule</h1>
                <p>Week of {week_start.strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Week Summary</h2>
                <p>Here's your personalized study plan for this week. Stay consistent and you'll achieve great results!</p>
            </div>
            
            <div class="week-grid">
    """
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for i, day_name in enumerate(day_names):
        date = week_start + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        formatted_date = date.strftime('%m/%d')
        
        html += f"""
                <div class="day-card">
                    <div class="day-header">{day_name} ({formatted_date})</div>
        """
        
        if date_str in weekly_schedule:
            for activity in weekly_schedule[date_str]:
                activity_type = activity.get('type', 'other')
                css_class = f"activity {activity_type}"
                
                html += f"""
                    <div class="{css_class}">
                        <strong>{activity.get('time', '')}</strong> - {activity.get('activity', '')}
                        {f"<br><small>{activity.get('description', '')}</small>" if activity.get('description') else ''}
                    </div>
                """
        else:
            html += '<div class="activity">No scheduled activities</div>'
        
        html += "</div>"
    
    html += f"""
            </div>
            
            <div class="footer">
                <p>🎓 Keep up the great work! Consistency is key to academic success.</p>
                <p>This email was generated by StudyFlow - Your Smart College Planner</p>
                <p>Need to update your schedule? Log into your StudyFlow account anytime.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_weekly_email_text(schedule_data):
    """Generate plain text content for weekly schedule email"""
    today = datetime.today()
    week_start = today - timedelta(days=today.weekday())
    
    text = f"""
StudyFlow - Your Weekly Study Schedule
Week of {week_start.strftime('%B %d, %Y')}

📊 WEEK SUMMARY
Here's your personalized study plan for this week. Stay consistent and you'll achieve great results!

📅 DAILY SCHEDULE
"""
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for i, day_name in enumerate(day_names):
        date = week_start + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        formatted_date = date.strftime('%m/%d')
        
        text += f"\n{day_name} ({formatted_date}):\n"
        text += "-" * 30 + "\n"
        
        if date_str in schedule_data:
            for activity in schedule_data[date_str]:
                text += f"{activity.get('time', '')} - {activity.get('activity', '')}\n"
                if activity.get('description'):
                    text += f"    {activity.get('description')}\n"
        else:
            text += "No scheduled activities\n"
        
        text += "\n"
    
    text += """
💡 STUDY TIPS FOR SUCCESS:
- Take regular breaks between study sessions
- Stay hydrated and maintain good nutrition
- Get adequate sleep (7-9 hours per night)
- Use active learning techniques
- Don't hesitate to ask for help when needed

🎓 Keep up the great work! Consistency is key to academic success.

This email was generated by StudyFlow - Your Smart College Planner
Need to update your schedule? Log into your StudyFlow account anytime.
"""
    
    return text

def send_motivation_email(to_email, student_name="Student"):
    """Send a motivational email to keep students engaged"""
    motivational_quotes = [
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "Education is the most powerful weapon which you can use to change the world. - Nelson Mandela",
        "The expert in anything was once a beginner. - Helen Hayes",
        "Don't watch the clock; do what it does. Keep going. - Sam Levenson"
    ]
    
    import random
    quote = random.choice(motivational_quotes)
    
    subject = "🌟 You're Doing Great! Keep Going!"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 10px; margin: 20px 0; text-align: center; }}
            .quote {{ font-style: italic; font-size: 1.2em; color: #667eea; margin: 20px 0; }}
            .footer {{ text-align: center; color: #6c757d; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌟 StudyFlow Motivation</h1>
                <p>A little encouragement for your academic journey</p>
            </div>
            
            <div class="content">
                <h2>Hey {student_name}! 👋</h2>
                <p>We wanted to take a moment to remind you how awesome you're doing!</p>
                
                <div class="quote">
                    "{quote}"
                </div>
                
                <p>Remember:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Every small step counts toward your goals</li>
                    <li>Consistency beats perfection every time</li>
                    <li>You're building skills that will last a lifetime</li>
                    <li>It's okay to have difficult days - keep pushing forward</li>
                </ul>
                
                <p><strong>You've got this! 💪</strong></p>
            </div>
            
            <div class="footer">
                <p>StudyFlow is here to support your success every step of the way</p>
                <p>Keep studying, keep growing, keep achieving! 🎓</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending motivation email: {e}")
        return False
