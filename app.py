from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup, escape
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///letters.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.template_filter('nl2br')
def nl2br_filter(value):
    return Markup(escape(value).replace('\n', '<br>\n'))

# ──────────────────────────────────────────
# Models
# ──────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sent_letters = db.relationship('Letter', foreign_keys='Letter.sender_id', backref='sender', lazy=True)
    received_letters = db.relationship('Letter', foreign_keys='Letter.recipient_id', backref='recipient', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Letter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    is_deleted_by_sender = db.Column(db.Boolean, default=False)
    is_deleted_by_recipient = db.Column(db.Boolean, default=False)

# ──────────────────────────────────────────
# Auth decorators
# ──────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('관리자 권한이 필요합니다.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ──────────────────────────────────────────
# Routes — Auth
# ──────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('모든 항목을 입력해주세요.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('이미 사용 중인 아이디입니다.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('이미 사용 중인 이메일입니다.', 'danger')
            return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('회원가입이 완료되었습니다. 로그인해주세요.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'{user.username}님, 환영합니다! 💌', 'success')
            return redirect(url_for('home'))

        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('login'))

# ──────────────────────────────────────────
# Routes — Main
# ──────────────────────────────────────────

@app.route('/')
@login_required
def home():
    user = current_user()
    recent_letters = (
        Letter.query
        .filter_by(recipient_id=user.id, is_deleted_by_recipient=False)
        .order_by(Letter.sent_at.desc())
        .limit(5)
        .all()
    )
    total_received = Letter.query.filter_by(recipient_id=user.id, is_deleted_by_recipient=False).count()
    total_sent = Letter.query.filter_by(sender_id=user.id, is_deleted_by_sender=False).count()
    unread_count = Letter.query.filter_by(recipient_id=user.id, is_read=False, is_deleted_by_recipient=False).count()

    return render_template('home.html',
        user=user,
        recent_letters=recent_letters,
        total_received=total_received,
        total_sent=total_sent,
        unread_count=unread_count
    )


@app.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    user = current_user()
    users = User.query.filter(User.id != user.id).order_by(User.username).all()

    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()

        if not recipient_id or not subject or not body:
            flash('모든 항목을 입력해주세요.', 'danger')
            return render_template('write.html', user=user, users=users)

        recipient = User.query.get(recipient_id)
        if not recipient:
            flash('받는 사람을 찾을 수 없습니다.', 'danger')
            return render_template('write.html', user=user, users=users)

        letter = Letter(
            sender_id=user.id,
            recipient_id=int(recipient_id),
            subject=subject,
            body=body
        )
        db.session.add(letter)
        db.session.commit()
        flash(f'{recipient.username}님께 편지를 보냈습니다. 💌', 'success')
        return redirect(url_for('sent'))

    # Pre-fill recipient if passed via query param
    to_user = request.args.get('to')
    return render_template('write.html', user=user, users=users, to_user=to_user)


@app.route('/inbox')
@login_required
def inbox():
    user = current_user()
    letters = (
        Letter.query
        .filter_by(recipient_id=user.id, is_deleted_by_recipient=False)
        .order_by(Letter.sent_at.desc())
        .all()
    )
    return render_template('inbox.html', user=user, letters=letters)


@app.route('/sent')
@login_required
def sent():
    user = current_user()
    letters = (
        Letter.query
        .filter_by(sender_id=user.id, is_deleted_by_sender=False)
        .order_by(Letter.sent_at.desc())
        .all()
    )
    return render_template('sent.html', user=user, letters=letters)


@app.route('/letter/<int:letter_id>')
@login_required
def view_letter(letter_id):
    user = current_user()
    letter = Letter.query.get_or_404(letter_id)

    # Access control
    if letter.recipient_id != user.id and letter.sender_id != user.id and not user.is_admin:
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('home'))

    if letter.recipient_id == user.id and not letter.is_read:
        letter.is_read = True
        db.session.commit()

    return render_template('view_letter.html', user=user, letter=letter)


@app.route('/letter/<int:letter_id>/delete', methods=['POST'])
@login_required
def delete_letter(letter_id):
    user = current_user()
    letter = Letter.query.get_or_404(letter_id)

    if letter.recipient_id == user.id:
        letter.is_deleted_by_recipient = True
        db.session.commit()
        flash('편지를 삭제했습니다.', 'info')
        return redirect(url_for('inbox'))
    elif letter.sender_id == user.id:
        letter.is_deleted_by_sender = True
        db.session.commit()
        flash('편지를 삭제했습니다.', 'info')
        return redirect(url_for('sent'))

    flash('권한이 없습니다.', 'danger')
    return redirect(url_for('home'))

# ──────────────────────────────────────────
# Routes — Admin
# ──────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    user = current_user()
    total_users = User.query.count()
    total_letters = Letter.query.count()
    recent_letters = Letter.query.order_by(Letter.sent_at.desc()).limit(10).all()
    users = User.query.order_by(User.created_at.desc()).all()

    return render_template('admin.html',
        user=user,
        total_users=total_users,
        total_letters=total_letters,
        recent_letters=recent_letters,
        users=users
    )

# ──────────────────────────────────────────
# API — unread count (for badge polling)
# ──────────────────────────────────────────

@app.route('/api/unread')
@login_required
def api_unread():
    user = current_user()
    count = Letter.query.filter_by(recipient_id=user.id, is_read=False, is_deleted_by_recipient=False).count()
    return jsonify({'unread': count})

# ──────────────────────────────────────────
# Context processor
# ──────────────────────────────────────────

@app.context_processor
def inject_globals():
    user = current_user()
    unread = 0
    if user:
        unread = Letter.query.filter_by(recipient_id=user.id, is_read=False, is_deleted_by_recipient=False).count()
    return dict(current_user=user, unread_count=unread)


# ──────────────────────────────────────────
# Init DB + seed admin
# ──────────────────────────────────────────

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@letterbox.com', is_admin=True)
            admin.set_password('admin1234')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin / admin1234")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
