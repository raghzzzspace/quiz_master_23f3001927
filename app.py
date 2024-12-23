from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from models import db, Admin, User, Subject, Chapter, Quiz, Questions, Scores, UserAnswers
from flask_migrate import Migrate
from flask import session, flash
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///C:/Users/hp/Desktop/quiz_master_database.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Initialize the database
db.init_app(app)
m = Migrate(app,db)

# Create the tables (Only needed on the first run)
# with app.app_context():
#     db.create_all()

# Admin Routes
@app.route('/admin/admin_base')
def admin_base():
    return render_template('admin/admin_base.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')

@app.route('/admin/admin_search')
def admin_search():
    return render_template('admin/admin_search.html')

@app.route('/admin/admin_quiz')
def admin_quiz():
    return render_template('admin/admin_quiz.html')

@app.route('/admin/summary')
def admin_summary():
    return render_template('admin/admin_summary.html')

@app.route('/admin/subjects')
def manage_subjects():
    return render_template('admin/manage_subjects.html')

@app.route('/admin/chapters')
def manage_chapters():
    return render_template('admin/manage_chapters.html')

@app.route('/admin/quizzes')
def manage_quizzes():
    return render_template('admin/manage_quizzes.html')

@app.route('/admin/questions')
def manage_questions():
    return render_template('admin/manage_questions.html')

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
    # Fetch the quiz
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for('quiz_list'))  # Redirect if quiz not found

    # Get the list of all questions for the quiz, this will ensure the order of questions is maintained
    questions = db.session.query(Questions).filter_by(quiz_id=quiz_id).all()

    # Get the total number of questions in the quiz
    total_questions = len(questions)

    # Ensure that question_id exists in the list of questions (compare as integers)
    current_question = next((q for q in questions if q.q_id == question_id), None)
    if current_question is None:
        return redirect(url_for('quiz', quiz_id=quiz_id, question_id=questions[0].q_id))  # Redirect to first question if invalid

    # Initialize or decrement the quiz timer
    if 'quiz_time' not in session:
        session['quiz_time'] = 300  # Set total time (e.g., 5 minutes = 300 seconds)
    else:
        session['quiz_time'] = int(session['quiz_time'])  # Ensure it's an integer

    # Decrement the timer
    session['quiz_time'] -= 1

    # If time is up, submit the quiz
    if session['quiz_time'] <= 0:
        session['quiz_time'] = 0  # Ensure time doesn't go negative
        return redirect(url_for('submit_answer', quiz_id=quiz_id))  # Redirect to submit

    # Initialize the user's answers array in the session if not already set
    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}  # Hash map to store answers, question_id as the key

    # Get the user's chosen answer for this question
    user_answer = session['quiz_answers'].get(str(question_id))  # Ensure the question_id is treated as a string in the session

    # Handle form submission (POST method)
    if request.method == 'POST':
        answer = request.form.get('answer')  # Get the option text

        if answer:
            # Store the user's selected answer text (not option number) in the session dictionary
            session['quiz_answers'][str(question_id)] = answer  # Ensure the question_id is stored as a string

        # Determine action based on the form button clicked
        action = request.form.get('action')
        if action == 'next':
            # Move to next question (compare as integers)
            next_question = next((q for q in questions if q.q_id == question_id + 1), None)
            if next_question:
                return redirect(url_for('quiz', quiz_id=quiz_id, question_id=next_question.q_id))
            else:
                return redirect(url_for('submit_answer', quiz_id=quiz_id))  # Redirect to submit if it's the last question

        elif action == 'previous':
            # Move to previous question (compare as integers)
            prev_question = next((q for q in questions if q.q_id == question_id - 1), None)
            if prev_question:
                return redirect(url_for('quiz', quiz_id=quiz_id, question_id=prev_question.q_id))
            else:
                return redirect(url_for('quiz', quiz_id=quiz_id, question_id=question_id))  # Stay on the first question if there's no previous

        elif action == 'submit':
            # Redirect to submit page
            return redirect(url_for('submit_answer', quiz_id=quiz_id))

    # Ensure current question_id and next/previous are integers
    current_index = next((index for index, q in enumerate(questions) if q.q_id == question_id), None)
    next_question = questions[current_index + 1] if current_index + 1 < total_questions else None
    prev_question = questions[current_index - 1] if current_index - 1 >= 0 else None

    # Pass the user's current answer and the remaining time to the template
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

    # Fetch all related questions for the quiz
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()

    # Calculate the number of questions
    num_questions = len(questions)

    # Pass all the relevant details to the template
    return render_template('user/quiz_view.html', quiz=quiz, subject=subject, chapter=chapter, num_questions=num_questions, questions=questions)



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
