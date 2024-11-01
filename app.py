from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user, login_manager
from models import db, User, Post, Like, Comment
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/testing_blog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(16)  # Generate a random secret key

UPLOAD_FOLDER = 'static/images'  # Folder untuk menyimpan gambar
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Username dan password harus diisi.', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Username dan password harus diisi.', 'danger')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        flash('Login gagal. Silakan coba lagi.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.password = request.form['password']
        db.session.commit()
        flash('Profil berhasil diperbarui!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_profile.html')


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title or not content:
            flash('Judul dan isi postingan harus diisi.', 'danger')
            return redirect(url_for('create_post'))
        image = request.files['image']
        image_filename = None
        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        new_post = Post(title=title, content=content, image_filename=image_filename, author_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash('Postingan berhasil dibuat!', 'success')
        return redirect(url_for('index'))
    return render_template('create_post.html')

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        if not post.title or not post.content:
            flash('Judul dan isi postingan harus diisi.', 'danger')
            return redirect(url_for('edit_post', post_id=post_id))
        image = request.files['image']
        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            post.image_filename = image_filename  # Perbarui nama file gambar
        db.session.commit()
        flash('Postingan berhasil diperbarui!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Postingan berhasil dihapus!', 'success')
    return redirect(url_for('index'))

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(post_id=post.id, user_id=current_user.id).first()
    if like:
        # Jika sudah ada like, hapus like
        db.session.delete(like)
        flash('Like dihapus.', 'info')
    else:
        # Tambahkan like jika belum ada
        new_like = Like(post_id=post.id, user_id=current_user.id)
        db.session.add(new_like)
        flash('Anda menyukai postingan ini!', 'success')
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    comment_content = request.form.get('content')
    
    if comment_content:
        new_comment = Comment(post_id=post.id, user_id=current_user.id, content=comment_content)
        db.session.add(new_comment)
        db.session.commit()
        flash('Komentar berhasil ditambahkan!', 'success')
    else:
        flash('Komentar tidak boleh kosong.', 'danger')
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat tabel
    app.run(debug=True)