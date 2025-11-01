from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy 
import datetime, os

app = Flask(__name__)

DATABASE_URI = os.environ.get('DATABASE_URL')

if DATABASE_URI:
    # Render (PostgreSQL) の場合
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI.replace("postgres://", "postgresql://", 1)
else:
    # ローカル (SQLite) の場合
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'task.db')
    
#external_url = "postgresql://task_database_nbrp_user:0plzZ2YJcEW8UBrs9n6IX24NRvZG84Kt@dpg-d42e7q95pdvs73d17gag-a.oregon-postgres.render.com/task_database_nbrp" # あなたのURLに置き換える
#app.config['SQLALCHEMY_DATABASE_URI'] = external_url

db = SQLAlchemy(app)

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.Integer, default=3)
    progress = db.Column(db.Integer, default=0)

@app.route("/")
def mypage():
    return render_template('mypage.html')

@app.route("/task", methods=['GET', 'POST'])
def task():
    if request.method =='POST':
        title = request.form.get('title')
        if not title:
            return redirect(url_for('task'))
        
        is_completed = request.form.get('is_completed') == 'true'
       
        due_date_str = request.form.get('due_date')
        due_date = None
        if due_date_str:
            due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
        
        priority_str = request.form.get('priority')
        priority = int(priority_str) if priority_str else 3

        progress_str = request.form.get('progress')
        progress = int(progress_str) if progress_str else 0

        task = Task(title=title, is_completed=is_completed, due_date=due_date, priority=priority, progress=progress)
    
        db.session.add(task)
        db.session.commit()
        return redirect('/task')
    else:
        tasks = Task.query.order_by(Task.priority.asc(), Task.due_date.asc()).all()
        return render_template('task.html', tasks=tasks)
    
@app.route("/task/delete/<int:task_id>", methods=['POST'])
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('task'))

@app.route("/task/edit/<int:task_id>", methods=['GET', 'POST'])
def task_edit(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.is_completed = request.form.get('is_completed') == 'true'

        due_date_str = request.form.get('due_date')
        task.due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

        priority_str = request.form.get('priority')
        task.priority = int(priority_str) if priority_str else 3

        progress_str = request.form.get('progress')
        task.progress = int(progress_str) if progress_str else 0
    
        db.session.commit()
    return redirect(url_for('task'))