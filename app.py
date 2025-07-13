from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from models import db, User, Course, Enrollment
import random

# --- Flask App ---
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Mail Config ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ashwini907583@gmail.com'
app.config['MAIL_PASSWORD'] = 'berwpxvwnljnjnxm'  # App Password (No spaces)

mail = Mail(app)
db.init_app(app)

# --- Seed Courses ---
def seed_courses():
    course_data = [
        {
            "name": "Data Science",
            "duration": "8 Weeks",
            "quiz_link": "/quizzes/data_science",
            "certificate_link": "/certificates/data_science"
        },
        {
            "name": "Machine Learning",
            "duration": "10 Weeks",
            "quiz_link": "/quizzes/machine_learning",
            "certificate_link": "/certificates/machine_learning"
        },
        {
            "name": "Full Stack Web Dev",
            "duration": "12 Weeks",
            "quiz_link": "/quizzes/full_stack",
            "certificate_link": "/certificates/full_stack"
        },
        {
            "name": "Cyber Security",
            "duration": "6 Weeks",
            "quiz_link": "/quizzes/cyber_security",
            "certificate_link": "/certificates/cyber_security"
        }
    ]

    for course in course_data:
        if not Course.query.filter_by(name=course["name"]).first():
            db.session.add(Course(**course))
    db.session.commit()


# --- Create Tables + Seed Courses ---
with app.app_context():
    db.create_all()
    seed_courses()


# --- Welcome Page ---
@app.route('/')
def welcome():
    return render_template('welcome.html')

# --- Registration + OTP ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        session['name'] = name
        session['email'] = email
        session['otp'] = str(random.randint(100000, 999999))

        try:
            msg = Message('EduFlex OTP Verification',
                          sender='ashwini907583@gmail.com',
                          recipients=[email])
            msg.body = f"Hello {name},\n\nYour OTP for EduFlex registration is: {session['otp']}\n\nThank you for using EduFlex!"
            mail.send(msg)
            print("OTP sent successfully to:", email)
        except Exception as e:
            print("Error sending OTP:", e)
            return f"<h3>Failed to send OTP. Error: {e}</h3>"

        return redirect(url_for('verify_otp'))

    return render_template('register.html')

# --- OTP Verification ---
@app.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session.get('otp'):
            return redirect(url_for('courses'))
        else:
            flash('Incorrect OTP. Try again.', 'warning')
            return redirect(url_for('verify_otp'))

    return render_template('verify.html')

# --- Courses ---
@app.route('/courses', methods=['GET', 'POST'])
def courses():
    all_courses = Course.query.all()

    if request.method == 'POST':
        selected = request.form.getlist('courses')
        session['selected_courses'] = selected

        user = User.query.filter_by(email=session['email']).first()
        if not user:
            user = User(name=session['name'], email=session['email'])
            db.session.add(user)
            db.session.commit()

        for course_name in selected:
            course = Course.query.filter_by(name=course_name).first()
            if course:
                existing = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
                if not existing:
                    enrollment = Enrollment(user_id=user.id, course_id=course.id, progress=0)
                    db.session.add(enrollment)

        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('courses.html', courses=all_courses)

# --- Dashboard ---
@app.route('/dashboard')
def dashboard():
    user = User.query.filter_by(email=session.get('email')).first()
    if not user:
        return redirect(url_for('register'))

    enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    courses = []
    for e in enrollments:
        course = Course.query.get(e.course_id)
        courses.append({
            'id': course.id,
            'name': course.name,
            'progress': e.progress or 0,
            'certificate': course.certificate_link,
            'quiz': course.quiz_link
        })

    return render_template('dashboard.html', name=user.name, courses=courses)

# --- Edit Courses ---
@app.route('/edit_courses', methods=['GET', 'POST'])
def edit_courses():
    user = User.query.filter_by(email=session.get('email')).first()
    if not user:
        return redirect(url_for('register'))

    enrollments = Enrollment.query.filter_by(user_id=user.id).all()

    if request.method == 'POST':
        for e in enrollments:
            # Get form inputs safely
            progress = int(request.form.get(f'progress_{e.course_id}', 0))
            cert = request.form.get(f'certificate_{e.course_id}', '')
            quiz = request.form.get(f'quiz_{e.course_id}', '')
            remove = request.form.get(f'remove_{e.course_id}')

            if remove:  # Checkbox returns 'on' if checked, else None
                db.session.delete(e)
            else:
                e.progress = progress
                e.certificate_link = cert
                e.quiz_link = quiz

        db.session.commit()
        flash('Courses updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_courses.html', enrollments=enrollments)


# --- Admin Panel ---
@app.route('/admin')
def admin():
    users = User.query.all()
    data = []
    for user in users:
        enrollments = Enrollment.query.filter_by(user_id=user.id).all()
        courses = [Course.query.get(e.course_id).name for e in enrollments]
        data.append({'name': user.name, 'email': user.email, 'courses': courses})
    return render_template('admin.html', data=data)

# --- Serve Quiz Pages ---

@app.route('/quizzes/<course>', methods=['GET', 'POST'])
def show_quiz(course):
    if request.method == 'POST':
        # 👉 Optional: You can evaluate the form here if needed

        # Show a thank-you page after submission
        return render_template('quiz_submitted.html')

    try:
        return render_template(f'quizzes/{course}.html')
    except:
        return "<h3>❌ Quiz not found for this course.</h3>"




# --- Serve Certificate Pages ---
@app.route('/certificates/<course>')
def show_certificate(course):
    user = User.query.filter_by(email=session.get('email')).first()
    if not user:
        return redirect(url_for('register'))
    try:
        return render_template(f'certificates/{course}.html', user=user)
    except:
        return "<h3>❌ Certificate not found for this course.</h3>"

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
