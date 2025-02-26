from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from models import db, Admin, User, Subject, Chapter, Quiz, Questions, Scores, UserAnswers
from flask_migrate import Migrate
from flask import session, flash
from datetime import datetime
from sqlalchemy import func
import secrets
import os


# Initialize the Flask app and database
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Use Vercel's temp directory or fallback to '/tmp' for other environments
tmp_dir = os.getenv('VERCEL_TEMP', '/tmp')

# Configuration for the database
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_dir}/quiz_master_database.db"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///C:/Users/hp/Desktop/quiz_master_database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)
m = Migrate(app, db)

# Seed function to add default quizzes and questions
# def seed_database():
#     admin_email = 'quizadmin@gmail.com'
#     admin_password = '2222'

#     # Create admin if it doesn't exist
#     if not Admin.query.filter_by(email=admin_email).first():
#         hashed_password = generate_password_hash(admin_password)
#         new_admin = Admin(
#             email=admin_email,
#             password=hashed_password
#         )
#         db.session.add(new_admin)
#         db.session.commit()
#         print("Admin user created.")
#     else:
#         print("Admin user already exists.")
#     # Check if there are already quizzes to avoid duplicate insertion
#     if Quiz.query.count() == 0:
#         # Get or create subjects first (assuming these already exist)
#         subject1 = Subject.query.filter_by(subj_name='Mathematics').first()
#         if not subject1:
#             subject1 = Subject(subj_name='Mathematics', subj_desc='All math-related topics')
#             db.session.add(subject1)

#         subject2 = Subject.query.filter_by(subj_name='Science').first()
#         if not subject2:
#             subject2 = Subject(subj_name='Science', subj_desc='Various science topics')
#             db.session.add(subject2)

#         db.session.commit()

#         # Get or create chapters
#         chapter1 = Chapter.query.filter_by(ch_name='Algebra').first()
#         if not chapter1:
#             chapter1 = Chapter(ch_name='Algebra', ch_desc='Basic algebraic equations and formulas', subj_id=subject1.subj_id)
#             db.session.add(chapter1)

#         chapter2 = Chapter.query.filter_by(ch_name='Physics').first()
#         if not chapter2:
#             chapter2 = Chapter(ch_name='Physics', ch_desc='Basic concepts in physics', subj_id=subject2.subj_id)
#             db.session.add(chapter2)

#         db.session.commit()

#         # Add default quizzes with 2-minute duration
#         current_date = datetime.now().date()

#         quizzes = [
#             Quiz(
#                 ch_id=chapter1.ch_id, subj_id=subject1.subj_id,
#                 date_of_quiz=current_date, time_duration="00:02", remarks="Basic Algebra Quiz"
#             ),
#             Quiz(
#                 ch_id=chapter1.ch_id, subj_id=subject1.subj_id,
#                 date_of_quiz=current_date, time_duration="00:02", remarks="Advanced Algebra Quiz"
#             ),
#             Quiz(
#                 ch_id=chapter2.ch_id, subj_id=subject2.subj_id,
#                 date_of_quiz=current_date, time_duration="00:02", remarks="Physics Fundamentals Quiz"
#             ),
#             Quiz(
#                 ch_id=chapter2.ch_id, subj_id=subject2.subj_id,
#                 date_of_quiz=current_date, time_duration="00:02", remarks="Energy and Motion Quiz"
#             ),
#             Quiz(
#                 ch_id=chapter2.ch_id, subj_id=subject2.subj_id,
#                 date_of_quiz=current_date, time_duration="00:02", remarks="Electricity and Magnetism Quiz"
#             )
#         ]

#         # Add quizzes to the session
#         db.session.bulk_save_objects(quizzes)
#         db.session.commit()
#         print("Default quizzes added to the database.")

#         # Now add 10 realistic questions for each quiz
#         questions = []

#         # Define some sample questions for the quizzes
#         algebra_questions = [
#             ("What is 5 + 7?", "12", "13", "14", "15", "12"),
#             ("What is the value of x in 2x + 4 = 12?", "2", "3", "4", "5", "4"),
#             ("What is the square root of 49?", "6", "7", "8", "9", "7"),
#             ("What is 3^3?", "27", "28", "30", "32", "27"),
#             ("Solve for y: 3y - 5 = 16", "5", "6", "7", "8", "7"),
#             ("What is the result of 15 divided by 3?", "4", "5", "6", "7", "5"),
#             ("What is the perimeter of a rectangle with sides 5 and 3?", "16", "18", "20", "22", "16"),
#             ("What is 12 x 9?", "108", "112", "116", "120", "108"),
#             ("Simplify: (3 + 2) x 4", "20", "18", "16", "14", "20"),
#             ("What is the next prime number after 7?", "8", "9", "11", "13", "11")
#         ]

#         physics_questions = [
#             ("What is the force required to accelerate a 5 kg object at 2 m/s²?", "5 N", "10 N", "15 N", "20 N", "10 N"),
#             ("What is the unit of electrical resistance?", "Ohm", "Watt", "Ampere", "Volt", "Ohm"),
#             ("What is the formula for gravitational potential energy?", "mgh", "mv²", "F=ma", "E=mc²", "mgh"),
#             ("How many joules are in 1 kilowatt-hour?", "1000", "2000", "3000", "3600", "3600"),
#             ("What is the speed of light?", "3 x 10^8 m/s", "3 x 10^6 m/s", "3 x 10^9 m/s", "3 x 10^7 m/s", "3 x 10^8 m/s"),
#             ("What is the law of conservation of energy?", "Energy can be created or destroyed.", "Energy is conserved.", "Energy cannot be converted.", "Energy increases.", "Energy is conserved."),
#             ("What is the unit of electric charge?", "Coulomb", "Ampere", "Volt", "Ohm", "Coulomb"),
#             ("What is the acceleration due to gravity on Earth?", "9.8 m/s²", "10 m/s²", "9.5 m/s²", "8.9 m/s²", "9.8 m/s²"),
#             ("What is the formula for kinetic energy?", "mv²", "1/2 mv²", "1/2 mgh", "mgh", "1/2 mv²"),
#             ("What is the unit of force?", "Newton", "Joule", "Watt", "Pascal", "Newton")
#         ]

#         # Add 10 questions for each quiz
#         for quiz_id in range(1, 6):  # Loop through each quiz (1-5 quizzes)
#             for i in range(1, 11):  # Add 10 questions for each quiz
#                 if quiz_id <= 2:  # Algebra quizzes
#                     question_data = algebra_questions[i - 1]
#                 else:  # Physics quizzes
#                     question_data = physics_questions[i - 1]

#                 questions.append(
#                     Questions(
#                         quiz_id=quiz_id,
#                         subj_id=subject1.subj_id if quiz_id <= 2 else subject2.subj_id,
#                         ch_id=chapter1.ch_id if quiz_id <= 2 else chapter2.ch_id,
#                         q_title=question_data[0],
#                         option1=question_data[1],
#                         option2=question_data[2],
#                         option3=question_data[3],
#                         option4=question_data[4],
#                         correctoption=question_data[5]  # Correct answer
#                     )
#                 )

#         # Add questions to the session
#         db.session.bulk_save_objects(questions)
#         db.session.commit()
#         print("10 realistic questions per quiz added to the database.")

# Initialize the database and add default quizzes and questions
with app.app_context():
    db.create_all()  # Create all tables
    #seed_database()  # Add default quizzes and questions if no quizzes exist


# Admin Routes
@app.route('/admin/admin_base')
def admin_base():
    return render_template('admin/admin_base.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # Perform the left join between Subject, Chapter, and Questions tables
    subject_data = db.session.query(Subject, Chapter, db.func.count(Questions.q_id).label('num_questions')) \
                             .outerjoin(Chapter, Subject.subj_id == Chapter.subj_id) \
                             .outerjoin(Questions, Chapter.ch_id == Questions.ch_id) \
                             .group_by(Subject.subj_id, Chapter.ch_id) \
                             .all()

    # Organize data into a structure that can be passed to the template
    subjects = []
    for subject, chapter, num_questions in subject_data:
        # Check if the subject already exists in the list, if not, add it
        subject_entry = next((entry for entry in subjects if entry['subj_name'] == subject.subj_name), None)
        
        if not subject_entry:
            subject_entry = {
                'subj_name': subject.subj_name,
                'subj_id': subject.subj_id,  # Add subj_id to the dictionary
                'chapters': []
            }
            subjects.append(subject_entry)

        # If the subject has chapters, add them
        if chapter:
            subject_entry['chapters'].append({
                'ch_name': chapter.ch_name,
                'ch_id': chapter.ch_id,  # Include chapter ID
                'num_questions': num_questions
            })

        # If no chapters are found, still include an empty list for the chapters
        elif not chapter and not subject_entry['chapters']:
            subject_entry['chapters'] = []

    return render_template('admin/admin_dashboard.html', subject_data=subjects)

from sqlalchemy.orm import aliased
from sqlalchemy import or_

@app.route('/admin/admin_search', methods=['GET'])
def admin_search():
    search_by = request.args.get('searchBy', '')  # Get the search category (user, subject, quiz)
    search_value = request.args.get('searchValue', '').strip()  # Get the search term

    search_results = []
    query_options = []  # This will store the attributes for the "Search Query" dropdown

    # Determine search attributes based on "searchBy"
    if search_by == 'user':
        query_options = ['fullname', 'user_email', 'qualification']  # User search attributes
        if search_value:
            search_results = User.query.filter(
                (User.fullname.ilike(f'{search_value}%')) |  # Starts with
                (User.user_email.ilike(f'{search_value}%')) |
                (User.qualification.ilike(f'{search_value}%'))
            ).all()
    elif search_by == 'subject':
        query_options = ['subj_name', 'subj_desc']  # Subject search attributes
        if search_value:
            search_results = Subject.query.filter(
                (Subject.subj_name.ilike(f'{search_value}%')) |  # Starts with
                (Subject.subj_desc.ilike(f'{search_value}%'))
            ).all()
    elif search_by == 'quiz':
        query_options = ['quiz_id', 'date_of_quiz']  # Quiz search attributes
        if search_value:
            search_results = Quiz.query.filter(
                (Quiz.quiz_id.ilike(f'{search_value}%')) |  # Starts with
                (Quiz.date_of_quiz.ilike(f'{search_value}%'))
            ).all()

    # Format the results based on the selected category
    formatted_results = []
    for result in search_results:
        if search_by == 'user':
            formatted_results.append({
                'id': result.user_email,  # User email as the ID
                'name': result.fullname,
                'type': 'User',
                'date': result.dob.strftime('%Y-%m-%d') if result.dob else 'N/A'
            })
        elif search_by == 'subject':
            formatted_results.append({
                'id': result.subj_id,
                'name': result.subj_name,
                'type': 'Subject',
                'date': 'N/A'  # No date for subjects
            })
        elif search_by == 'quiz':
            formatted_results.append({
                'id': result.quiz_id,
                'name': result.remarks,
                'type': 'Quiz',
                'date': result.date_of_quiz.strftime('%Y-%m-%d') if result.date_of_quiz else 'N/A'
            })

    # Pass data to the template
    return render_template('admin/admin_search.html', search_by=search_by, search_value=search_value, 
                           search_results=formatted_results, query_options=query_options)


@app.route('/admin/admin_quiz')
def admin_quiz():
    # Left join to get quizzes and their associated questions
    quizzes = db.session.query(Quiz, Subject.subj_name).outerjoin(Subject, Quiz.subj_id == Subject.subj_id).all()
    quizzes_data = []
    
    for quiz, subj_name in quizzes:
        questions = Questions.query.filter_by(quiz_id=quiz.quiz_id).all()  # Fetch all questions related to each quiz
        quiz_data = {
            'quiz_id': quiz.quiz_id,
            'subject_name': subj_name,  # Use subject name from the join
            'questions': []
        }
        
        for question in questions:
            quiz_data['questions'].append({
                'q_id': question.q_id,
                'q_title': question.q_title
            })
        
        quizzes_data.append(quiz_data)
    
    return render_template('admin/admin_quiz.html', quizzes=quizzes_data)


# Route to handle admin summary
@app.route('/admin/summary')
def admin_summary():
    # Fetch top scores by subject using JOINs
    top_scores = db.session.query(
        Subject.subj_name,
        func.max(Scores.scored).label('top_score')
    ).join(
        Quiz, Quiz.subj_id == Subject.subj_id
    ).join(
        Scores, Scores.quiz_id == Quiz.quiz_id
    ).group_by(Subject.subj_id).all()

    # Fetch user attempts by subject using JOINs
    user_attempts = db.session.query(
        Subject.subj_name,
        func.count(Scores.s_id).label('attempt_count')
    ).join(
        Quiz, Quiz.subj_id == Subject.subj_id
    ).join(
        Scores, Scores.quiz_id == Quiz.quiz_id
    ).group_by(Subject.subj_id).all()

    # Render the admin summary template with data
    return render_template('admin/admin_summary.html', top_scores=top_scores, user_attempts=user_attempts)



# Route for Adding a Chapter
@app.route('/admin/add_chapter/<int:subject_id>', methods=['GET', 'POST'])
def add_chapter(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == 'POST':
        chapter_name = request.form['ch_name']
        chapter_desc = request.form['ch_desc']
        new_chapter = Chapter(ch_name=chapter_name, ch_desc=chapter_desc, subj_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_chapter.html', subject=subject)

@app.route('/admin/edit_chapter/<int:subject_id>/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(subject_id, chapter_id):
    # Fetch the chapter based on both subject_id and chapter_id
    chapter = Chapter.query.filter_by(subj_id=subject_id, ch_id=chapter_id).first()
    
    if not chapter:
        flash('Chapter not found.', 'warning')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        chapter.ch_name = request.form['ch_name']
        chapter.ch_desc = request.form['ch_desc']
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_chapter.html', chapter=chapter)

# Route for Deleting a Chapter
@app.route('/admin/delete_chapter/<int:subject_id>/<int:chapter_id>', methods=['GET', 'POST'])
def delete_chapter(subject_id, chapter_id):
    # Fetch the chapter based on both subject_id and chapter_id
    chapter = Chapter.query.filter_by(subj_id=subject_id, ch_id=chapter_id).first()
    
    # Handle POST request for deletion
    if request.method == 'POST':
        if chapter:
            db.session.delete(chapter)
            db.session.commit()
            flash('Chapter deleted successfully!', 'danger')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Chapter not found.', 'warning')
            return redirect(url_for('admin_dashboard'))

    # Handle GET request, render the confirmation page
    return render_template('admin/delete_chapter.html', chapter=chapter)



# Route for Adding a Subject
@app.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subj_name']
        subject_desc = request.form['subj_desc']
        
        # Ensure that subject_name is provided
        if not subject_name:
            flash('Subject name is required!', 'danger')
            return redirect(url_for('add_subject'))
        
        # Create a new Subject instance and add it to the database
        new_subject = Subject(subj_name=subject_name, subj_desc=subject_desc)
        db.session.add(new_subject)
        db.session.commit()
        
        flash('Subject added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_subject.html')

@app.route('/admin/edit_question/<int:quiz_id>/<int:question_id>', methods=['GET', 'POST'])
def edit_question(quiz_id, question_id):
    question= Questions.query.filter_by(quiz_id=quiz_id, q_id=question_id).first()
    if not question:
        flash('Question not found.', 'warning')
        return redirect(url_for('admin_quiz'))
    if request.method == 'POST':
        question.q_title = request.form['q_title']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correctoption = request.form['correctoption']
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin_quiz'))
    return render_template('admin/edit_question.html', question=question)

@app.route('/admin/delete_question/<int:quiz_id>/<int:question_id>', methods=['GET', 'POST'])
def delete_question(quiz_id, question_id):
    question = Questions.query.filter_by(quiz_id=quiz_id, q_id=question_id).first()
    
    if request.method == 'POST':
        if question:
            db.session.delete(question)
            db.session.commit()
            flash('Question deleted successfully!', 'danger')
            return redirect(url_for('admin_quiz', quiz_id=quiz_id))
        else:
            flash('Question not found.', 'warning')
            return redirect(url_for('admin_quiz', quiz_id=quiz_id))

    return render_template('admin/delete_question.html', question=question, quiz_id=quiz_id)


@app.route('/admin/add_question/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        # Get the option text corresponding to the correct option number
        correct_option_value = request.form['correctoption']
        
        # Assign the correct option based on the selected value
        correct_option_text = ""
        if correct_option_value == '1':
            correct_option_text = request.form['option1']
        elif correct_option_value == '2':
            correct_option_text = request.form['option2']
        elif correct_option_value == '3':
            correct_option_text = request.form['option3']
        elif correct_option_value == '4':
            correct_option_text = request.form['option4']
        
        # Create a new question object with the correct options
        new_question = Questions(
            quiz_id=quiz.quiz_id,
            subj_id=quiz.subj_id,
            ch_id=quiz.ch_id,
            q_title=request.form['q_title'],
            option1=request.form['option1'],
            option2=request.form['option2'],
            option3=request.form['option3'],
            option4=request.form['option4'],
            correctoption=correct_option_text  # Save the actual option text
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin_quiz', quiz_id=quiz_id))
    
    return render_template('admin/add_question.html', quiz=quiz)


@app.route('/admin/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'POST':
        # Fetch data from the form
        ch_id = request.form.get('ch_id')  # Chapter ID
        subj_id = request.form.get('subj_id')  # Subject ID
        date_of_quiz = request.form.get('date_of_quiz')
        time_duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')

        # Validate input fields
        if not ch_id or not subj_id:
            flash('Please select a subject and chapter!', 'danger')
            return redirect(url_for('add_quiz'))
        
        if not date_of_quiz or not time_duration:
            flash('Please fill all required fields!', 'danger')
            return redirect(url_for('add_quiz'))

        # Create a new quiz instance
        new_quiz = Quiz(
            ch_id=ch_id,
            subj_id=subj_id,
            date_of_quiz=datetime.strptime(date_of_quiz, '%Y-%m-%d'),
            time_duration=time_duration,
            remarks=remarks
        )

        # Add and commit the new quiz to the database
        try:
            db.session.add(new_quiz)
            db.session.commit()
            flash('Quiz added successfully!', 'success')
            return redirect(url_for('admin_quiz'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the quiz. Please try again.', 'danger')
            print(f"Error: {e}")
            return redirect(url_for('add_quiz'))
    
    # Fetch all subjects for the dropdown
    subjects = Subject.query.all()
    return render_template('admin/add_quiz.html', subjects=subjects)

@app.route('/admin/get_chapters/<int:subj_id>', methods=['GET'])
def get_chapters(subj_id):
    # Fetch chapters for the selected subject
    chapters = Chapter.query.filter_by(subj_id=subj_id).all()
    chapter_list = [{'ch_id': chapter.ch_id, 'ch_name': chapter.ch_name} for chapter in chapters]
    return jsonify({'chapters': chapter_list})


# User Routes
@app.route('/user/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        existing_user = User.query.filter_by(user_email=request.form['email']).first()
        
        if existing_user:
            flash('User already exists!', 'danger')
            return redirect(url_for('register'))
        
        email = request.form['email']
        password = request.form['password']
        fullname = request.form['fullname']
        qualification = request.form['qualification']
        
        try:
            dob = datetime.strptime(request.form['dob'], '%Y-%m-%d')
        except ValueError:
            flash('Invalid date of birth format. Use dd-mm-yyyy.', 'danger')
            return redirect(url_for('register'))

        user = User(
            user_email=email, 
            user_password=generate_password_hash(password), 
            fullname=fullname, 
            qualification=qualification, 
            dob=dob
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('User registered successfully!', 'success')

        return redirect(url_for('register'))
    
    return render_template('user/register.html')


@app.route('/user/quiz-list')
def quiz_list():
    current_date = datetime.today().date()
    quizzes = db.session.query(Quiz, Subject, Chapter).join(Subject, Quiz.subj_id == Subject.subj_id).join(Chapter, Quiz.ch_id == Chapter.ch_id).filter(Quiz.date_of_quiz >= current_date).all()
    user=User.query.filter_by(user_email=session['user_email']).first()
    return render_template('user/quiz_list.html',fullname=user.fullname,quizzes=quizzes)

@app.route('/user/quiz/<int:quiz_id>/question/<int:question_id>', methods=['GET', 'POST'])
def quiz(quiz_id, question_id):
    # Fetch the quiz from the database
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for('quiz_list'))  # Redirect if quiz not found

    # Get the list of all questions for the quiz
    questions = db.session.query(Questions).filter_by(quiz_id=quiz_id).all()

    # Get the total number of questions in the quiz
    total_questions = len(questions)

    # Ensure that question_id exists in the list of questions
    current_question = next((q for q in questions if q.q_id == question_id), None)
    if current_question is None:
        return redirect(url_for('quiz', quiz_id=quiz_id, question_id=questions[0].q_id))  # Redirect to first question if invalid

    # Initialize or decrement the quiz timer
    if 'quiz_time' not in session:
        if quiz.time_duration:
            # Convert hh:mm time duration to seconds
            if quiz.time_duration == "00:00":
                session['quiz_time'] = 10
            else:
                hours, minutes = map(int, quiz.time_duration.split(":"))
                session['quiz_time'] = hours * 60 * 60 + minutes * 60
        else:
            session['quiz_time'] = 300  # Default 5 minutes (300 seconds)

    # Decrement the timer and check if time is up
    if session['quiz_time'] > 0:
        session['quiz_time'] -= 1
    if session['quiz_time'] <= 0:
        session['quiz_time'] = 0  # Ensure time doesn't go negative
        # Redirect only once when time is up
        return redirect(url_for('submit_answer', quiz_id=quiz_id))

    # Initialize the user's answers array in the session if not already set
    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}

    # Get the user's chosen answer for this question
    user_answer = session['quiz_answers'].get(str(question_id))

    # Handle form submission (POST method)
    if request.method == 'POST':
        answer = request.form.get('answer')
        if answer:
            session['quiz_answers'][str(question_id)] = answer

        action = request.form.get('action')
        if action == 'next':
            next_question = next((q for q in questions if q.q_id == question_id + 1), None)
            if next_question:
                return redirect(url_for('quiz', quiz_id=quiz_id, question_id=next_question.q_id))
            else:
                return redirect(url_for('submit_answer', quiz_id=quiz_id))
        elif action == 'previous':
            prev_question = next((q for q in questions if q.q_id == question_id - 1), None)
            if prev_question:
                return redirect(url_for('quiz', quiz_id=quiz_id, question_id=prev_question.q_id))
        elif action == 'submit':
            return redirect(url_for('submit_answer', quiz_id=quiz_id))

    current_index = next((index for index, q in enumerate(questions) if q.q_id == question_id), None)
    next_question = questions[current_index + 1] if current_index + 1 < total_questions else None
    prev_question = questions[current_index - 1] if current_index - 1 >= 0 else None

    remaining_time = session['quiz_time']

    return render_template('user/quiz.html', quiz=quiz, question=current_question,
                           next_question_id=next_question.q_id if next_question else None,
                           prev_question_id=prev_question.q_id if prev_question else None,
                           total_questions=total_questions, user_answer=user_answer,
                           question_id=question_id, remaining_time=remaining_time, questions=questions)



@app.route('/user/quiz/<int:quiz_id>/submit', methods=['GET', 'POST'])
def submit_answer(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for('quiz_list'))  # Redirect if quiz not found

    user_email = session.get('user_email')
    user_answers = session.get('quiz_answers')

    if not user_answers:
        return redirect(url_for('quiz', quiz_id=quiz_id, question_id=1))

    # Store the answers in the database
    for q_id, answer in user_answers.items():
        q_id = int(q_id)  # Ensure q_id is treated as an integer
        answer = str(answer)  # Ensure the answer is treated as a string

        if answer:
            user_answer = UserAnswers(
                quiz_id=quiz_id,
                user_email=user_email,
                q_id=q_id,
                chosen_option=answer  # Store the answer text (not option number)
            )
            db.session.add(user_answer)

    db.session.commit()

    # Calculate score
    score = 0
    for q_id, answer in user_answers.items():
        q_id = int(q_id)  # Ensure q_id is treated as an integer
        answer = str(answer)  # Ensure the answer is treated as a string

        if answer:
            question = Questions.query.get(q_id)
            if question and question.correctoption == answer:  # Compare with the correct answer text
                score += 1

    # Insert the score into the Scores table
    total_score = len(user_answers)  # Assuming total score is the number of questions in the quiz
    new_score = Scores(
        quiz_id=quiz_id,
        user_email=user_email,
        time_stamp_of_attempt=datetime.utcnow(),
        scored=score,
        total_score=total_score
    )
    db.session.add(new_score)
    db.session.commit()

    # Clear user answers from session
    session.pop('quiz_answers', None)

    # Redirect to the result page with quiz_id
    return redirect(url_for('quiz_result', quiz_id=quiz_id, score=score, total_questions=len(user_answers)))


@app.route('/user/quiz-result/<int:quiz_id>')
def quiz_result(quiz_id):
    # Fetch quiz details
    quiz = Quiz.query.filter_by(quiz_id=quiz_id).first()
    if not quiz:
        return redirect(url_for('quiz_list'))  # Redirect if quiz not found

    # Fetch all questions for this quiz
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    total_questions = len(questions)
    correct_answers = 0
    incorrect_answers = 0

    # Fetch user's answers for this quiz
    user_answers = UserAnswers.query.filter_by(quiz_id=quiz_id, user_email=session.get('user_email')).all()

    if user_answers:
        for question in questions:
            # Find the user's answer for this question
            user_answer = next((ans for ans in user_answers if ans.q_id == question.q_id), None)
            if user_answer:
                # Compare the user's answer with the correct option
                if user_answer.chosen_option == question.correctoption:
                    correct_answers += 1
                else:
                    incorrect_answers += 1

    # Calculate the score and percentage
    score = f"{correct_answers}/{total_questions}"
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    # Return the results page
    return render_template('user/quiz_result.html', 
                           quiz_id=quiz.quiz_id,
                           total_questions=total_questions,
                           correct_answers=correct_answers,
                           incorrect_answers=incorrect_answers,
                           score=score,
                           percentage=round(percentage, 2))

@app.route('/user/search', methods=['GET'])
def user_search():
    search_by = request.args.get('searchBy')  # Get search criteria (Quiz ID, Date, Subject, Chapter)
    search_query = request.args.get('searchQuery')  # Get search query from the form

    search_results = []
    
    # Search by Quiz ID
    if search_by == 'quiz_id' and search_query:
        search_results = db.session.query(Quiz, Subject).join(Subject, Quiz.subj_id == Subject.subj_id).filter(Quiz.quiz_id == search_query).all()
        
    # Search by Quiz Date
    elif search_by == 'quiz_date' and search_query:
        try:
            search_date = datetime.strptime(search_query, '%Y-%m-%d')  # Convert to date format
            search_results = db.session.query(Quiz, Subject).join(Subject, Quiz.subj_id == Subject.subj_id).filter(Quiz.date_of_quiz == search_date).all()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
    
    # Search by Subject
    elif search_by == 'subject' and search_query:
        search_results = db.session.query(Quiz, Subject).join(Subject, Quiz.subj_id == Subject.subj_id).filter(Subject.subj_name.ilike(f'%{search_query}%')).all()

    # Search by Chapter
    elif search_by == 'chapter' and search_query:
        search_results = db.session.query(Quiz, Chapter).join(Chapter, Quiz.ch_id == Chapter.ch_id).filter(Chapter.ch_name.ilike(f'%{search_query}%')).all()

    return render_template('user/user_search.html', 
                           search_by=search_by, 
                           search_results=search_results)

@app.route('/user/quiz_view/<int:quiz_id>', methods=['GET'])
def quiz_view(quiz_id):
    # Fetching the quiz by ID
    quiz = Quiz.query.filter_by(quiz_id=quiz_id).first()

    if quiz is None:
        # If the quiz doesn't exist, return a 404 error or a custom message
        return render_template('error.html', message="Quiz not found")

    # Fetch the related subject and chapter details
    subject = Subject.query.filter_by(subj_id=quiz.subj_id).first()
    chapter = Chapter.query.filter_by(ch_id=quiz.ch_id).first()

    # Calculate the number of questions
    num_questions = Questions.query.filter_by(quiz_id=quiz_id).count()

    # Pass only the relevant details to the template
    return render_template('user/quiz_view.html', quiz=quiz, subject=subject, chapter=chapter, num_questions=num_questions)


@app.route('/user/scores')
def scores():
    user_email = session.get('user_email')
    user_scores = Scores.query.filter_by(user_email=user_email).all()
    quizzes = []
    for score in user_scores:
        quiz = Quiz.query.filter_by(quiz_id=score.quiz_id).first()
        chapter = Chapter.query.filter_by(ch_id=quiz.ch_id).first()
        subject = Subject.query.filter_by(subj_id=quiz.subj_id).first()
        quizzes.append({
            'quiz_id': quiz.quiz_id,
            'num_questions': len(Questions.query.filter_by(quiz_id=quiz.quiz_id).all()),
            'quiz_date': quiz.date_of_quiz,
            'duration': quiz.time_duration,
            'score': score.scored,
            'total_score': score.total_score,
            'action_url': url_for('quiz_result', quiz_id=quiz.quiz_id)
        })
    return render_template('user/scores.html', quizzes=quizzes)

@app.route('/user/summary')
def user_summary():
    user_email = session.get('user_email')  # Get the user email from session

    # Query to get the number of unique quizzes attempted by the user in each subject
    subject_counts = db.session.query(
        Subject.subj_name,  # Subject name
        db.func.count(db.distinct(Quiz.quiz_id)).label('quiz_count')  # Count distinct quiz IDs in each subject
    ).join(Quiz, Quiz.subj_id == Subject.subj_id) \
     .join(UserAnswers, UserAnswers.quiz_id == Quiz.quiz_id) \
     .filter(UserAnswers.user_email == user_email) \
     .group_by(Subject.subj_name).all()

    # Query to get the number of unique quizzes attempted per month
    month_counts = db.session.query(
        db.func.strftime('%m', UserAnswers.time_stamp).label('month'),  # Extract month
        db.func.count(db.distinct(UserAnswers.quiz_id)).label('quiz_count')  # Count distinct quiz IDs for each month
    ).filter(UserAnswers.user_email == user_email) \
     .group_by(db.func.strftime('%m', UserAnswers.time_stamp)).all()

    # Prepare the data for the chart
    subjects = [subject[0] for subject in subject_counts]  # Subject names
    subject_data = [subject[1] for subject in subject_counts]  # Quiz count for each subject

    # Prepare month data, initializing with 0 values for each month (1-12)
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    month_data = [0] * 12
    for month, count in month_counts:
        month_data[int(month) - 1] = count  # Assign quiz counts to the correct month

    # Render the template with the data
    return render_template('user/user_summary.html',
                           subjects=subjects,
                           subject_data=subject_data,
                           months=months,
                           month_data=month_data)

# Common Routes
@app.route('/')
def first_page():
    return render_template('common/first_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(user_email=email).first()
        if user and check_password_hash(user.user_password, password):
            session['user_email'] = user.user_email
            flash(f'Welcome back, {user.fullname}!', 'success')
            return redirect(url_for('quiz_list'))

        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_email'] = admin.email
            flash(f'Welcome back, {admin.email}!', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')
        return redirect(url_for('login'))

    return render_template('common/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

# # Function to add an admin to the database

# def add_admin(email, password):
#     # Hash the password
#     hashed_password = generate_password_hash(password)
    
#     # Create the Admin object
#     new_admin = Admin(email=email, password=hashed_password)
    
#     # Add the admin to the database
#     try:
#         db.session.add(new_admin)
#         db.session.commit()
#         print("Admin added successfully!")
#     except Exception as e:
#         db.session.rollback()
#         print(f"Error adding admin: {e}")

    
# if __name__ == '__main__':
#     with app.app_context():  # Create the application context
#         add_admin("quizadmin@gmail.com", "8888")  # Call the function to add admin

#     app.run(debug=True)
