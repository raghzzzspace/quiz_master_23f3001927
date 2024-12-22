from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')

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
        # Handle user registration logic here
        return redirect(url_for('login'))
    return render_template('user/register.html')
@app.route('/user/user_base')
def user_base():
    return render_template('user/user_base.html')
@app.route('/user/dashboard')
def user_dashboard():
    return render_template('user/user_dashboard.html')

@app.route('/user/quiz-list')
def quiz_list():
    return render_template('user/quiz_list.html')

@app.route('/user/quiz/<int:quiz_id>')
def quiz(quiz_id):
    # Pass the quiz_id to the template for quiz logic
    return render_template('user/quiz.html', quiz_id=quiz_id)

@app.route('/user/quiz-result/<int:quiz_id>')
def quiz_result(quiz_id):
    # Pass the quiz_id to display results
    return render_template('user/quiz_result.html', quiz_id=quiz_id)

@app.route('/user/user_search.html')
def user_search():
    return render_template('user/user_search.html')

@app.route('/user/scores')
def scores():
    return render_template('user/scores.html')

@app.route('/user/summary')
def user_summary():
    return render_template('user/user_summary.html')

# Common Routes
@app.route('/')
def first_page():
    return render_template('common/first_page.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login logic here
        return redirect(url_for('user_dashboard'))  # Redirect based on role
    return render_template('common/login.html')


if __name__ == '__main__':
    app.run(debug=True)
