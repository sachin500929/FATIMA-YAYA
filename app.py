import os
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify, abort, send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fyfy-secret-2024-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fyfy.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO = {'mp4', 'webm', 'mov'}
ALLOWED_AUDIO = {'mp3', 'wav', 'ogg', 'm4a'}
ALLOWED_ALL = ALLOWED_IMAGE | ALLOWED_VIDEO | ALLOWED_AUDIO

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# ── Models ────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin      = db.Column(db.Boolean, default=False)
    avatar        = db.Column(db.String(300), default='')
    bio           = db.Column(db.String(300), default='')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    posts         = db.relationship('Post', backref='author', lazy='dynamic',
                                    foreign_keys='Post.user_id',
                                    cascade='all, delete-orphan')

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)


class Post(db.Model):
    __tablename__ = 'posts'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body       = db.Column(db.Text, default='')
    media_url  = db.Column(db.String(400), default='')
    media_type = db.Column(db.String(20), default='')   # image/video/audio/link
    link_url   = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes      = db.relationship('Like', backref='post', lazy='dynamic',
                                 cascade='all, delete-orphan')
    comments   = db.relationship('Comment', backref='post', lazy='dynamic',
                                 cascade='all, delete-orphan')

    def like_count(self): return self.likes.count()
    def liked_by(self, user): return self.likes.filter_by(user_id=user.id).first() is not None
    def comment_count(self): return self.comments.count()


class Like(db.Model):
    __tablename__ = 'likes'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)


class Comment(db.Model):
    __tablename__ = 'comments'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id    = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author     = db.relationship('User', backref='comments')


class Event(db.Model):
    __tablename__ = 'events'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    location    = db.Column(db.String(300), default='')
    map_query   = db.Column(db.String(300), default='')
    event_date  = db.Column(db.DateTime, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'))


# ── Helpers ───────────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ALL

def get_media_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_IMAGE: return 'image'
    if ext in ALLOWED_VIDEO: return 'video'
    if ext in ALLOWED_AUDIO: return 'audio'
    return ''

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def save_upload(file):
    if not file or file.filename == '':
        return None, None
    if not allowed_file(file.filename):
        return None, None
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    file.save(path)
    return fname, get_media_type(file.filename)

def seed_admin():
    admin = User.query.filter_by(email='sachin@123').first()
    if not admin:
        admin = User(name='Sachin (Admin)', email='sachin@123', is_admin=True)
        admin.set_password('@1234sachin')
        db.session.add(admin)
        db.session.commit()

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for('feed'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        if not name or not email or not password:
            flash('All fields are required.', 'error')
        elif password != confirm:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash('Welcome to Fatima Youth Federation!', 'success')
            return redirect(url_for('feed'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ── Feed routes ───────────────────────────────────────────────────────────────
@app.route('/feed')
@login_required
def feed():
    page  = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('feed.html', posts=posts)

@app.route('/post/create', methods=['POST'])
@login_required
def create_post():
    body     = request.form.get('body', '').strip()
    link_url = request.form.get('link_url', '').strip()
    file     = request.files.get('media')
    media_url, media_type = save_upload(file)

    if not body and not media_url and not link_url:
        flash("Post can't be empty.", 'error')
        return redirect(url_for('feed'))

    post = Post(
        user_id    = current_user.id,
        body       = body,
        media_url  = media_url or '',
        media_type = media_type or ('link' if link_url else ''),
        link_url   = link_url,
    )
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    if post.media_url:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.media_url))
        except OSError:
            pass
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(request.referrer or url_for('feed'))

# ── Like (AJAX) ───────────────────────────────────────────────────────────────
@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    post    = Post.query.get_or_404(post_id)
    existing = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post_id))
        liked = True
    db.session.commit()
    return jsonify({'liked': liked, 'count': post.like_count()})

# ── Comments (AJAX) ───────────────────────────────────────────────────────────
@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    Post.query.get_or_404(post_id)
    body = request.json.get('body', '').strip()
    if not body:
        return jsonify({'error': 'Empty comment'}), 400
    c = Comment(user_id=current_user.id, post_id=post_id, body=body)
    db.session.add(c)
    db.session.commit()
    return jsonify({
        'id'        : c.id,
        'body'      : c.body,
        'author'    : c.author.name,
        'avatar'    : c.author.avatar,
        'created_at': c.created_at.strftime('%b %d, %Y %H:%M'),
    })

@app.route('/post/<int:post_id>/comments')
@login_required
def get_comments(post_id):
    post = Post.query.get_or_404(post_id)
    data = [{
        'id'        : c.id,
        'body'      : c.body,
        'author'    : c.author.name,
        'avatar'    : c.author.avatar,
        'created_at': c.created_at.strftime('%b %d, %Y %H:%M'),
        'can_delete': current_user.is_admin or c.user_id == current_user.id,
    } for c in post.comments.order_by(Comment.created_at.asc())]
    return jsonify(data)

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    c = Comment.query.get_or_404(comment_id)
    if c.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'success': True})

# ── Profile ───────────────────────────────────────────────────────────────────
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user  = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    return render_template('profile.html', profile_user=user, posts=posts)

@app.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    current_user.name = request.form.get('name', current_user.name).strip()
    current_user.bio  = request.form.get('bio', current_user.bio).strip()
    avatar = request.files.get('avatar')
    if avatar and avatar.filename:
        fname, _ = save_upload(avatar)
        if fname:
            current_user.avatar = fname
    db.session.commit()
    flash('Profile updated!', 'success')
    return redirect(url_for('profile', user_id=current_user.id))

# ── Events ────────────────────────────────────────────────────────────────────
@app.route('/events')
@login_required
def events():
    all_events = Event.query.order_by(Event.event_date.asc()).all()
    now = datetime.utcnow()
    upcoming = [e for e in all_events if e.event_date >= now]
    past     = [e for e in all_events if e.event_date < now]
    return render_template('events.html', upcoming=upcoming, past=past)

@app.route('/events/create', methods=['POST'])
@login_required
@admin_required
def create_event():
    title       = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    location    = request.form.get('location', '').strip()
    map_query   = request.form.get('map_query', location).strip()
    date_str    = request.form.get('event_date', '')
    try:
        event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('events'))
    ev = Event(title=title, description=description, location=location,
               map_query=map_query, event_date=event_date, created_by=current_user.id)
    db.session.add(ev)
    db.session.commit()
    flash('Event created!', 'success')
    return redirect(url_for('events'))

@app.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    ev = Event.query.get_or_404(event_id)
    db.session.delete(ev)
    db.session.commit()
    flash('Event deleted.', 'success')
    return redirect(url_for('events'))

# ── Admin panel ───────────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users       = User.query.order_by(User.created_at.desc()).all()
    posts       = Post.query.order_by(Post.created_at.desc()).all()
    total_likes = Like.query.count()
    total_coms  = Comment.query.count()
    return render_template('admin.html', users=users, posts=posts,
                           total_likes=total_likes, total_coms=total_coms)

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash("You can't delete yourself.", 'error')
        return redirect(url_for('admin_panel'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.name} deleted.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'is_admin': user.is_admin, 'name': user.name})

# ── Media serve (already via static, but explicit route for clarity) ──────────
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, msg='Access Denied'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, msg='Page Not Found'), 404

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 100 MB.', 'error')
    return redirect(url_for('feed'))

# ── Init & run ────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    seed_admin()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
