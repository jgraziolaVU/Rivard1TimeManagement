from datetime import datetime, timedelta
import json

def create_schedule(parsed_dates, user_data):
    """
    Create a personalized study schedule based on user preferences and deadlines
    """
    schedule = {}
    
    # Extract user preferences
    wakeup = int(user_data.get("wakeup", 8))
    sleep = int(user_data.get("sleep", 23))
    study_style = user_data.get("study_style", "pomodoro")
    deadlines = user_data.get("deadlines", [])
    email = user_data.get("email", "")
    
    # Create schedule for the next 4 months (semester length)
    start_date = datetime.today()
    for i in range(120):
        current_day = start_date + timedelta(days=i)
        date_str = current_day.strftime('%Y-%m-%d')
        
        # Skip dates in the past
        if current_day < start_date:
            continue
            
        daily_plan = generate_daily_plan(
            current_day, wakeup, sleep, study_style, deadlines, parsed_dates
        )
        
        schedule[date_str] = daily_plan
    
    return schedule

def generate_daily_plan(date, wakeup, sleep, study_style, deadlines, parsed_dates):
    """Generate a daily plan for a specific date"""
    daily_plan = []
    day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
    
    # Morning routine
    daily_plan.append({
        "time": f"{wakeup:02d}:00",
        "activity": "🌅 Morning Routine & Wake Up",
        "type": "routine",
        "duration": 60
    })
    
    # Breakfast
    breakfast_time = wakeup + 1
    daily_plan.append({
        "time": f"{breakfast_time:02d}:00",
        "activity": "🍳 Breakfast",
        "type": "meal",
        "duration": 30
    })
    
    # Add study sessions based on study style
    study_sessions = generate_study_sessions(
        wakeup, sleep, study_style, day_of_week
    )
    daily_plan.extend(study_sessions)
    
    # Add meals
    daily_plan.extend([
        {
            "time": "12:00",
            "activity": "🥗 Lunch Break",
            "type": "meal",
            "duration": 60
        },
        {
            "time": "18:00",
            "activity": "🍽️ Dinner",
            "type": "meal",
            "duration": 60
        }
    ])
    
    # Add deadlines for this specific date
    deadline_activities = get_deadlines_for_date(date, deadlines)
    daily_plan.extend(deadline_activities)
    
    # Add review sessions before major deadlines
    review_sessions = generate_review_sessions(date, deadlines)
    daily_plan.extend(review_sessions)
    
    # Add exercise/wellness time
    if day_of_week < 5:  # Weekdays
        daily_plan.append({
            "time": f"{wakeup + 8:02d}:00",
            "activity": "💪 Exercise/Wellness Time",
            "type": "wellness",
            "duration": 45
        })
    
    # Add free time before sleep
    free_time = sleep - 2
    daily_plan.append({
        "time": f"{free_time:02d}:00",
        "activity": "🎉 Free Time & Relaxation",
        "type": "free",
        "duration": 120
    })
    
    # Sort activities by time
    daily_plan.sort(key=lambda x: x["time"])
    
    return daily_plan

def generate_study_sessions(wakeup, sleep, study_style, day_of_week):
    """Generate study sessions based on user's preferred study style"""
    sessions = []
    
    # Calculate available study hours
    available_hours = sleep - wakeup - 4  # Account for meals, breaks, etc.
    
    if study_style == "pomodoro":
        # 25-minute study blocks with 5-minute breaks
        morning_start = wakeup + 2
        afternoon_start = 14  # 2 PM
        evening_start = 19    # 7 PM
        
        sessions.extend([
            {
                "time": f"{morning_start:02d}:00",
                "activity": "📚 Morning Study Block (4 Pomodoros)",
                "type": "study",
                "duration": 120,
                "description": "25min study + 5min break × 4"
            },
            {
                "time": f"{afternoon_start:02d}:00",
                "activity": "📚 Afternoon Study Block (4 Pomodoros)",
                "type": "study",
                "duration": 120,
                "description": "25min study + 5min break × 4"
            }
        ])
        
        # Add evening session on weekdays
        if day_of_week < 5:
            sessions.append({
                "time": f"{evening_start:02d}:00",
                "activity": "📚 Evening Study Block (2 Pomodoros)",
                "type": "study",
                "duration": 60,
                "description": "25min study + 5min break × 2"
            })
    
    elif study_style == "focused":
        # Longer focused sessions
        sessions.extend([
            {
                "time": f"{wakeup + 2:02d}:00",
                "activity": "📚 Deep Focus Session 1",
                "type": "study",
                "duration": 180,  # 3 hours
                "description": "Extended focused study session"
            },
            {
                "time": "14:00",
                "activity": "📚 Deep Focus Session 2",
                "type": "study",
                "duration": 150,  # 2.5 hours
                "description": "Extended focused study session"
            }
        ])
    
    else:  # flexible
        # Shorter, flexible sessions
        sessions.extend([
            {
                "time": f"{wakeup + 2:02d}:00",
                "activity": "📚 Morning Study Session",
                "type": "study",
                "duration": 90,
                "description": "Flexible study session"
            },
            {
                "time": "13:00",
                "activity": "📚 Afternoon Study Session",
                "type": "study",
                "duration": 60,
                "description": "Flexible study session"
            },
            {
                "time": "16:00",
                "activity": "📚 Late Afternoon Study",
                "type": "study",
                "duration": 90,
                "description": "Flexible study session"
            },
            {
                "time": "19:30",
                "activity": "📚 Evening Review",
                "type": "study",
                "duration": 45,
                "description": "Review and light study"
            }
        ])
    
    return sessions

def get_deadlines_for_date(date, deadlines):
    """Get all deadlines that fall on a specific date"""
    deadline_activities = []
    date_str = date.strftime('%Y-%m-%d')
    
    for deadline in deadlines:
        if deadline.get('date') == date_str:
            # Determine emoji based on deadline type
            type_emojis = {
                'exam': '📝',
                'assignment': '📄',
                'project': '🚀',
                'quiz': '❓',
                'presentation': '🎤'
            }
            
            emoji = type_emojis.get(deadline.get('type', ''), '⚠️')
            
            deadline_activities.append({
                "time": deadline.get('time', '23:59'),
                "activity": f"{emoji} {deadline.get('type', '').upper()}: {deadline.get('title', '')}",
                "type": "deadline",
                "course": deadline.get('course_code', ''),
                "description": deadline.get('description', ''),
                "priority": "high"
            })
    
    return deadline_activities

def generate_review_sessions(date, deadlines):
    """Generate review sessions leading up to major deadlines"""
    review_sessions = []
    
    for deadline in deadlines:
        deadline_date = datetime.strptime(deadline.get('date', ''), '%Y-%m-%d')
        days_until = (deadline_date - date).days
        
        # Add review sessions 1, 3, and 7 days before major deadlines
        if days_until in [1, 3, 7] and deadline.get('type') in ['exam', 'project']:
            intensity = {1: 'Intensive', 3: 'Focused', 7: 'Initial'}[days_until]
            
            review_sessions.append({
                "time": "20:00",
                "activity": f"📖 {intensity} Review: {deadline.get('title', '')}",
                "type": "review",
                "course": deadline.get('course_code', ''),
                "duration": 60 if days_until == 1 else 45,
                "priority": "high" if days_until <= 3 else "medium"
            })
    
    return review_sessions

def optimize_schedule_for_difficulty(schedule, course_difficulty_map=None):
    """
    Optimize schedule based on course difficulty (future enhancement)
    """
    if not course_difficulty_map:
        return schedule
    
    # This could be expanded to adjust study time allocation
    # based on course difficulty ratings
    return schedule

def generate_weekly_summary(schedule):
    """Generate a weekly summary of the schedule"""
    today = datetime.today()
    week_start = today - timedelta(days=today.weekday())
    
    weekly_stats = {
        'total_study_hours': 0,
        'deadlines_this_week': 0,
        'study_sessions': 0,
        'upcoming_deadlines': []
    }
    
    for i in range(7):
        date = week_start + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        if date_str in schedule:
            daily_plan = schedule[date_str]
            
            for activity in daily_plan:
                if activity.get('type') == 'study':
                    weekly_stats['total_study_hours'] += activity.get('duration', 60) / 60
                    weekly_stats['study_sessions'] += 1
                elif activity.get('type') == 'deadline':
                    weekly_stats['deadlines_this_week'] += 1
                    weekly_stats['upcoming_deadlines'].append({
                        'date': date_str,
                        'title': activity.get('activity', ''),
                        'course': activity.get('course', '')
                    })
    
    return weekly_stats
