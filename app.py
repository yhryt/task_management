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
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.Integer, default=3)
    progress = db.Column(db.Integer, default=0)

class DailyLog(db.Model):
    __tablename__ = 'daily_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=True) 
    rank = db.Column(db.String(5), nullable=True)      # A〜Dランク
    memo = db.Column(db.Text, nullable=True)           # メモ

with app.app_context():
    db.create_all()

def get_current_score_and_rank():
    # 'is_completed' が無くなったので、全タスクが対象
    active_tasks = Task.query.all()
    
    score = 0
    rank = "N/A"
    
    if active_tasks:
        score = 0
        for task in active_tasks:
            # (警告: この計算は 'priority=3'(低) の方がスコアが高くなります)
            score += task.progress * task.priority

        # ランク付け
        if score >= 270:
            rank = "A"
        elif score >= 210:
            rank = "B"
        elif score >= 120:
            rank = "C"
        else:
            rank = "D"
    else:
        # 未完了タスクが0件の場合 (あなたのロジック)
        score = 100.0
        rank = "A"
        
    return score, rank



@app.route("/")
def mypage():
    return render_template('mypage.html')

@app.route("/task", methods=['GET', 'POST'])
def task():
    if request.method =='POST':
        title = request.form.get('title')
        if not title:
            return redirect(url_for('task'))
       
        due_date_str = request.form.get('due_date')
        due_date = None
        if due_date_str:
            due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
        
        priority_str = request.form.get('priority')
        priority = int(priority_str) if priority_str else 3

        task = Task(title=title, due_date=due_date, priority=priority, progress=0)
    
        db.session.add(task)
        db.session.commit()
        return redirect('/task')
    else:
        tasks = Task.query.order_by(
            db.nullslast(Task.due_date.asc()), 
            Task.priority.asc()
        ).all()

        current_score, current_rank = get_current_score_and_rank()

        return render_template(
            'task.html', 
            tasks=tasks,
            current_score=current_score,
            current_rank=current_rank
        )
    
    
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

        due_date_str = request.form.get('due_date')
        task.due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

        priority_str = request.form.get('priority')
        task.priority = int(priority_str) if priority_str else 3

        progress_str = request.form.get('progress')
        task.progress = int(progress_str) if progress_str else 0
    
        db.session.commit()
    return redirect(url_for('task'))

@app.route("/report", methods=['GET', 'POST'])
def report():
    today = datetime.date.today()

    score, rank = get_current_score_and_rank()

    log = DailyLog.query.filter_by(date=today).first()
    
    if request.method == 'POST':
        # ... (POST処理は変更なし) ...
        # (省略)
        db.session.commit()
        return redirect(url_for('report'))
    else: 
        # ... (GET処理は変更なし) ...
        # (省略)
        db.session.commit()
        
        past_logs = DailyLog.query.filter(DailyLog.date != today).order_by(DailyLog.date.desc()).limit(30).all()
        
        return render_template(
            'report.html', 
            todays_log=log, 
            past_logs=past_logs,
            today_str=today.strftime('%Y年%m月%d日')
        )