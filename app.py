from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from models import db, Admin, User, Subject, Chapter, Quiz, Questions, Scores, UserAnswers
from flask_migrate import Migrate
from flask import session, flash
from datetime import datetime
from sqlalchemy import func
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///C:/Users/hp/Desktop/quiz_master_database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)
m = Migrate(app, db)

# Admin Routes ////////////////////////////////////////////////

@app.route('/admin/admin_base')
def admin_base():
    return render_template('admin/admin_base.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    
    subject_data = db.session.query(Subject, Chapter, db.func.count(Questions.q_id).label('num_questions')) \
                             .outerjoin(Chapter, Subject.subj_id == Chapter.subj_id) \
                             .outerjoin(Questions, Chapter.ch_id == Questions.ch_id) \
                             .group_by(Subject.subj_id, Chapter.ch_id) \
                             .all()

    subjects = []
    for subject, chapter, num_questions in subject_data:
        subject_entry = next((entry for entry in subjects if entry['subj_name'] == subject.subj_name), None)
        
        if not subject_entry:
            subject_entry = {
                'subj_name': subject.subj_name,
                'subj_id': subject.subj_id, 
                'chapters': []
            }
            subjects.append(subject_entry)

        if chapter:
            subject_entry['chapters'].append({
                'ch_name': chapter.ch_name,
                'ch_id': chapter.ch_id,
                'num_questions': num_questions
            })

        elif not chapter and not subject_entry['chapters']:
            subject_entry['chapters'] = []

    return render_template('admin/admin_dashboard.html', subject_data=subjects)


@app.route('/admin/admin_search', methods=['GET'])
def admin_search():
    search_by = request.args.get('searchBy', '') 
    search_value = request.args.get('searchValue', '').strip()

    search_results = []
    query_options = []

    if search_by == 'user':
        query_options = ['fullname', 'user_email', 'qualification'] 
        if search_value:
            search_results = User.query.filter(
                (User.fullname.ilike(f'{search_value}%')) |  
                (User.user_email.ilike(f'{search_value}%')) |
                (User.qualification.ilike(f'{search_value}%'))
            ).all()
    elif search_by == 'subject':
        query_options = ['subj_name', 'subj_desc'] 
        if search_value:
            search_results = Subject.query.filter(
                (Subject.subj_name.ilike(f'{search_value}%')) | 
                (Subject.subj_desc.ilike(f'{search_value}%'))
            ).all()
    elif search_by == 'quiz':
        query_options = ['quiz_id', 'date_of_quiz'] 
        if search_value:
            search_results = Quiz.query.filter(
                (Quiz.quiz_id.ilike(f'{search_value}%')) | 
                (Quiz.date_of_quiz.ilike(f'{search_value}%'))
            ).all()

    formatted_results = []
    for result in search_results:
        if search_by == 'user':
            formatted_results.append({
                'id': result.user_email,
                'name': result.fullname,
                'type': 'User',
                'date': result.dob.strftime('%Y-%m-%d') if result.dob else 'N/A'
            })
        elif search_by == 'subject':
            formatted_results.append({
                'id': result.subj_id,
                'name': result.subj_name,
                'type': 'Subject',
                'date': 'N/A' 
            })
        elif search_by == 'quiz':
            formatted_results.append({
                'id': result.quiz_id,
                'name': result.remarks,
                'type': 'Quiz',
                'date': result.date_of_quiz.strftime('%Y-%m-%d') if result.date_of_quiz else 'N/A'
            })

    return render_template('admin/admin_search.html', search_by=search_by, search_value=search_value, 
                           search_results=formatted_results, query_options=query_options)


@app.route('/admin/admin_quiz')
def admin_quiz():
    quizzes = db.session.query(Quiz, Subject.subj_name).outerjoin(Subject, Quiz.subj_id == Subject.subj_id).all()
    quizzes_data = []
    
    for quiz, subj_name in quizzes:
        questions = Questions.query.filter_by(quiz_id=quiz.quiz_id).all()
        quiz_data = {
            'quiz_id': quiz.quiz_id,
            'subject_name': subj_name,
            'questions': []
        }
        
        for question in questions:
            quiz_data['questions'].append({
                'q_id': question.q_id,
                'q_title': question.q_title
            })
        
        quizzes_data.append(quiz_data)
    
    return render_template('admin/admin_quiz.html', quizzes=quizzes_data)


@app.route('/admin/summary')
def admin_summary():
    top_scores = db.session.query(
        Subject.subj_name,
        func.max(Scores.scored).label('top_score')
    ).join(
        Quiz, Quiz.subj_id == Subject.subj_id
    ).join(
        Scores, Scores.quiz_id == Quiz.quiz_id
    ).group_by(Subject.subj_id).all()

    
    user_attempts = db.session.query(
        Subject.subj_name,
        func.count(Scores.s_id).label('attempt_count')
    ).join(
        Quiz, Quiz.subj_id == Subject.subj_id
    ).join(
        Scores, Scores.quiz_id == Quiz.quiz_id
    ).group_by(Subject.subj_id).all()

    return render_template('admin/admin_summary.html', top_scores=top_scores, user_attempts=user_attempts)



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


@app.route('/admin/delete_chapter/<int:subject_id>/<int:chapter_id>', methods=['GET', 'POST'])
def delete_chapter(subject_id, chapter_id):
    
    chapter = Chapter.query.filter_by(subj_id=subject_id, ch_id=chapter_id).first()
    
    
    if request.method == 'POST':
        if chapter:
            db.session.delete(chapter)
            db.session.commit()
            flash('Chapter deleted successfully!', 'danger')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Chapter not found.', 'warning')
            return redirect(url_for('admin_dashboard'))


    return render_template('admin/delete_chapter.html', chapter=chapter)



@app.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subj_name']
        subject_desc = request.form['subj_desc']
        
    
        if not subject_name:
            flash('Subject name is required!', 'danger')
            return redirect(url_for('add_subject'))
        
    
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
        
        correct_option_value = request.form['correctoption']
        
        
        correct_option_text = ""
        if correct_option_value == '1':
            correct_option_text = request.form['option1']
        elif correct_option_value == '2':
            correct_option_text = request.form['option2']
        elif correct_option_value == '3':
            correct_option_text = request.form['option3']
        elif correct_option_value == '4':
            correct_option_text = request.form['option4']
        
        
        new_question = Questions(
            quiz_id=quiz.quiz_id,
            subj_id=quiz.subj_id,
            ch_id=quiz.ch_id,
            q_title=request.form['q_title'],
            option1=request.form['option1'],
            option2=request.form['option2'],
            option3=request.form['option3'],
            option4=request.form['option4'],
            correctoption=correct_option_text  
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin_quiz', quiz_id=quiz_id))
    
    return render_template('admin/add_question.html', quiz=quiz)


@app.route('/admin/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'POST':
        
        ch_id = request.form.get('ch_id') 
        subj_id = request.form.get('subj_id')  
        date_of_quiz = request.form.get('date_of_quiz')
        time_duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')

        
        if not ch_id or not subj_id:
            flash('Please select a subject and chapter!', 'danger')
            return redirect(url_for('add_quiz'))
        
        if not date_of_quiz or not time_duration:
            flash('Please fill all required fields!', 'danger')
            return redirect(url_for('add_quiz'))

        
        new_quiz = Quiz(
            ch_id=ch_id,
            subj_id=subj_id,
            date_of_quiz=datetime.strptime(date_of_quiz, '%Y-%m-%d'),
            time_duration=time_duration,
            remarks=remarks
        )

        
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
    
    
    subjects = Subject.query.all()
    return render_template('admin/add_quiz.html', subjects=subjects)

@app.route('/admin/get_chapters/<int:subj_id>', methods=['GET'])
def get_chapters(subj_id):
    
    chapters = Chapter.query.filter_by(subj_id=subj_id).all()
    chapter_list = [{'ch_id': chapter.ch_id, 'ch_name': chapter.ch_name} for chapter in chapters]
    return jsonify({'chapters': chapter_list})


# User Routes //////////////////////////
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

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for('quiz_list'))  
    
    questions = db.session.query(Questions).filter_by(quiz_id=quiz_id).all()

    
    total_questions = len(questions)

    current_question = next((q for q in questions if q.q_id == question_id), None)
    if current_question is None:
        return redirect(url_for('quiz', quiz_id=quiz_id, question_id=questions[0].q_id)) 

    
    if 'quiz_time' not in session:
        if quiz.time_duration:
        
            if quiz.time_duration == "00:00":
                session['quiz_time'] = 10
            else:
                hours, minutes = map(int, quiz.time_duration.split(":"))
                session['quiz_time'] = hours * 60 * 60 + minutes * 60
        else:
            session['quiz_time'] = 300  

    
    if session['quiz_time'] > 0:
        session['quiz_time'] -= 1
    if session['quiz_time'] <= 0:
        session['quiz_time'] = 0  
        
        return redirect(url_for('submit_answer', quiz_id=quiz_id))


    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}

    
    user_answer = session['quiz_answers'].get(str(question_id))

    
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
        return redirect(url_for('quiz_list')) 

    user_email = session.get('user_email')
    user_answers = session.get('quiz_answers')

    if not user_answers:
        return redirect(url_for('quiz', quiz_id=quiz_id, question_id=1))

    
    for q_id, answer in user_answers.items():
        q_id = int(q_id)  
        answer = str(answer)  

        if answer:
            user_answer = UserAnswers(
                quiz_id=quiz_id,
                user_email=user_email,
                q_id=q_id,
                chosen_option=answer
            )
            db.session.add(user_answer)

    db.session.commit()

    
    score = 0
    for q_id, answer in user_answers.items():
        q_id = int(q_id)  
        answer = str(answer) 

        if answer:
            question = Questions.query.get(q_id)
            if question and question.correctoption == answer: 
                score += 1

    total_score = len(user_answers)  
    new_score = Scores(
        quiz_id=quiz_id,
        user_email=user_email,
        time_stamp_of_attempt=datetime.utcnow(),
        scored=score,
        total_score=total_score
    )
    db.session.add(new_score)
    db.session.commit()

    session.pop('quiz_answers', None)

    return redirect(url_for('quiz_result', quiz_id=quiz_id, score=score, total_questions=len(user_answers)))


@app.route('/user/quiz-result/<int:quiz_id>')
def quiz_result(quiz_id):

    quiz = Quiz.query.filter_by(quiz_id=quiz_id).first()
    if not quiz:
        return redirect(url_for('quiz_list'))  

    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    total_questions = len(questions)
    correct_answers = 0
    incorrect_answers = 0

    
    user_answers = UserAnswers.query.filter_by(quiz_id=quiz_id, user_email=session.get('user_email')).all()

    if user_answers:
        for question in questions:
        
            user_answer = next((ans for ans in user_answers if ans.q_id == question.q_id), None)
            if user_answer:
                
                if user_answer.chosen_option == question.correctoption:
                    correct_answers += 1
                else:
                    incorrect_answers += 1

    
    score = f"{correct_answers}/{total_questions}"
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0


    return render_template('user/quiz_result.html', 
                           quiz_id=quiz.quiz_id,
                           total_questions=total_questions,
                           correct_answers=correct_answers,
                           incorrect_answers=incorrect_answers,
                           score=score,
                           percentage=round(percentage, 2))

@app.route('/user/search', methods=['GET'])
def user_search():
    search_by = request.args.get('searchBy')  
    search_query = request.args.get('searchQuery')  

    search_results = []

    
    if search_by == 'quiz_id' and search_query:
        search_results = db.session.query(Quiz, Subject).join(Subject, Quiz.subj_id == Subject.subj_id).filter(Quiz.quiz_id == search_query).all()
        
    
    elif search_by == 'quiz_date' and search_query:
        try:
            search_date = datetime.strptime(search_query, '%Y-%m-%d')  
            search_results = db.session.query(Quiz, Subject).join(Subject, Quiz.subj_id == Subject.subj_id).filter(Quiz.date_of_quiz == search_date).all()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
    
    elif search_by == 'subject' and search_query:
        search_results = db.session.query(Quiz, Subject).join(Subject, Quiz.subj_id == Subject.subj_id).filter(Subject.subj_name.ilike(f'%{search_query}%')).all()
    elif search_by == 'chapter' and search_query:
        search_results = db.session.query(Quiz, Chapter).join(Chapter, Quiz.ch_id == Chapter.ch_id).filter(Chapter.ch_name.ilike(f'%{search_query}%')).all()

    return render_template('user/user_search.html', 
                           search_by=search_by, 
                           search_results=search_results)

@app.route('/user/quiz_view/<int:quiz_id>', methods=['GET'])
def quiz_view(quiz_id):
    
    quiz = Quiz.query.filter_by(quiz_id=quiz_id).first()

    if quiz is None:
        
        return render_template('error.html', message="Quiz not found")


    subject = Subject.query.filter_by(subj_id=quiz.subj_id).first()
    chapter = Chapter.query.filter_by(ch_id=quiz.ch_id).first()

    num_questions = Questions.query.filter_by(quiz_id=quiz_id).count()


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
    user_email = session.get('user_email')  

    
    subject_counts = db.session.query(
        Subject.subj_name,  
        db.func.count(db.distinct(Quiz.quiz_id)).label('quiz_count')  
    ).join(Quiz, Quiz.subj_id == Subject.subj_id) \
     .join(UserAnswers, UserAnswers.quiz_id == Quiz.quiz_id) \
     .filter(UserAnswers.user_email == user_email) \
     .group_by(Subject.subj_name).all()

    
    month_counts = db.session.query(
        db.func.strftime('%m', UserAnswers.time_stamp).label('month'),  
        db.func.count(db.distinct(UserAnswers.quiz_id)).label('quiz_count') 
    ).filter(UserAnswers.user_email == user_email) \
     .group_by(db.func.strftime('%m', UserAnswers.time_stamp)).all()


    subjects = [subject[0] for subject in subject_counts]
    subject_data = [subject[1] for subject in subject_counts]  

    
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    month_data = [0] * 12
    for month, count in month_counts:
        month_data[int(month) - 1] = count  


    return render_template('user/user_summary.html',
                           subjects=subjects,
                           subject_data=subject_data,
                           months=months,
                           month_data=month_data)

# Common Routes ///////////////////////////////
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
