from työ import app, db
from flask import render_template, url_for, flash, redirect, request, session
from työ.forms import RegistrationForm, LoginForm, ThreadForm, PostForm, PasswordForm
from työ.models import User, Area, Thread, Post, PrivateArea, PrivatePost, PrivateThread 
from flask_login import login_user, current_user, logout_user, login_required, LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/home')
def home():
    areas = Area.query.filter_by(is_secret=False).all()
    private_areas = PrivateArea.query.filter_by(is_secret=False).all()
    return render_template('home.html', areas=areas, private_areas=private_areas)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and form.email.data == user.email and form.password.data == user.password:
            login_user(user)
            flash('You have been logged in!', 'success')
            return redirect(url_for('account'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user
    related_threads = Thread.query.filter_by(user_id=user.id).all()
    try:
        for thread in related_threads:
            thread.user_id = None
            db.session.add(thread)
        db.session.delete(user)
        db.session.commit()       
        flash('Your account has been deleted.', 'success')
        return redirect(url_for('home'))
    except Exception:
        db.session.rollback()
        flash('An error occurred while deleting your account.', 'error')
        return redirect(url_for('home'))


@app.route("/area/<int:area_id>")
def area(area_id):
    area = Area.query.get_or_404(area_id)
    if area.is_secret and current_user not in area.authorized_users:
        flash('You do not have access to this area.', 'danger')
        return redirect(url_for('home'))
    threads = Thread.query.filter_by(area_id=area_id).all()
    return render_template('area.html', area=area, threads=threads)

@app.route("/thread/new/<int:area_id>", methods=['GET', 'POST'])
@login_required
def new_thread(area_id):
    form = ThreadForm()
    if form.validate_on_submit():
        thread = Thread(title=form.title.data, area_id=area_id, user_id=current_user.id)
        post = Post(content=form.content.data, thread=thread, user_id=current_user.id)
        db.session.add(thread)
        db.session.add(post)
        db.session.commit()
        flash('New thread created!', 'success')
        return redirect(url_for('area', area_id=area_id))
    return render_template('create_thread.html', title='New Thread', form=form)

@app.route("/thread/<int:thread_id>", methods=['GET', 'POST'])
def thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    posts = Post.query.filter_by(thread_id=thread_id).all()
    form = PostForm()
    if form.validate_on_submit():
        post = Post(content=form.content.data, thread_id=thread_id, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been added!', 'success')
        return redirect(url_for('thread', thread_id=thread_id))
    return render_template('thread.html', thread=thread, posts=posts, form=form)

@app.route("/account")
@login_required
def account():
    return render_template('account.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/thread/<int:thread_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    if thread.user_id != current_user.id:
        flash('You do not have permission to edit this thread.', 'danger')
        return redirect(url_for('thread', thread_id=thread_id))
    form = ThreadForm()
    if form.validate_on_submit() or request.method == 'POST':
        thread.title = form.title.data
        db.session.commit()
        flash('Thread title has been updated!', 'success')
        return redirect(url_for('thread', thread_id=thread_id))
    elif request.method == 'GET':
        form.title.data = thread.title
    return render_template('edit_thread.html', title='Edit Thread', form=form)

@app.route("/post/<int:post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('thread', thread_id=post.thread_id))
    form = PostForm()
    if form.validate_on_submit():
        post.content = form.content.data
        db.session.commit()
        flash('Post has been updated!', 'success')
        return redirect(url_for('thread', thread_id=post.thread_id))
    elif request.method == 'GET':
        form.content.data = post.content
    return render_template('edit_post.html', title='Edit Post', form=form)

@app.route("/thread/<int:thread_id>/delete", methods=['POST'])
@login_required
def delete_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    if thread.user_id != current_user.id:
        flash('You do not have permission to delete this thread.', 'danger')
        return redirect(url_for('thread', thread_id=thread_id))
    db.session.delete(thread)
    db.session.commit()
    flash('Thread has been deleted!', 'success')
    return redirect(url_for('area', area_id=thread.area_id))

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('thread', thread_id=post.thread_id))
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted!', 'success')
    return redirect(url_for('thread', thread_id=post.thread_id))

@app.route("/password", methods=['GET', 'POST'])
def password():
    form = PasswordForm()
    if session.get('has_access'):
        area = PrivateArea.query.first()
        flash('Welcome back!', 'success')
        return redirect(url_for('private_area', private_area_id=area.id))
    if current_user.is_authenticated and current_user.is_admin:
        area = PrivateArea.query.first() 
        flash('You may enter!', 'success')
        return redirect(url_for('private_area', private_area_id=area.id))
    flash("Please enter the password.", "info")
    if form.validate_on_submit():
        area = PrivateArea.query.filter_by(password=form.password.data).first()
        if area and form.password.data == area.password:
            session['has_access'] = True
            flash('You have passed the test!', 'success')
            return redirect(url_for('private_area', private_area_id=area.id))
        else:
            flash('Login Unsuccessful. Please check password', 'danger') 
    return render_template('password.html', title='Password', form=form)


@app.route("/private_area/<int:private_area_id>")
@login_required
def private_area(private_area_id):
    area = PrivateArea.query.get_or_404(private_area_id)
    if area.is_secret and current_user not in area.authorized_users:
        flash('You do not have access to this area.', 'danger')
        return redirect(url_for('home'))
    threads = PrivateThread.query.filter_by(area_id=private_area_id).all()
    return render_template('private_area.html', private_area=area, threads=threads)


@app.route("/private_thread/new/<int:private_area_id>", methods=['GET', 'POST'])
@login_required
def new_private_thread(private_area_id):
    form = ThreadForm()
    if form.validate_on_submit():
        thread = PrivateThread(title=form.title.data, area_id=private_area_id, user_id=current_user.id)
        db.session.add(thread)
        db.session.commit() 
        post = PrivatePost(content=form.content.data, private_thread_id=thread.id, user_id=current_user.id, private_area_id=private_area_id)
        db.session.add(post)
        db.session.commit()
        flash('New thread created!', 'success')
        return redirect(url_for('private_area', private_area_id=private_area_id))
    return render_template('create_private_thread.html', title='New Thread', form=form)


@app.route("/private_thread/<int:private_thread_id>", methods=['GET', 'POST'])
@login_required
def private_thread(private_thread_id):
    thread = PrivateThread.query.get_or_404(private_thread_id)
    posts = PrivatePost.query.filter_by(private_thread_id=private_thread_id).all()
    form = PostForm()
    if form.validate_on_submit():
        post = PrivatePost(content=form.content.data, private_thread_id=private_thread_id, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been added!', 'success')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))
    return render_template('private_thread.html', thread=thread, posts=posts, form=form)

@app.route("/private_thread/<int:private_thread_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_private_thread(private_thread_id):
    thread = PrivateThread.query.get_or_404(private_thread_id)
    if thread.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this thread.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))
    
    form = ThreadForm()
    if form.validate_on_submit() or request.method == 'POST':
        thread.title = form.title.data
        db.session.commit()
        flash('Thread title has been updated!', 'success')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))
    elif request.method == 'GET':
        form.title.data = thread.title
    
    return render_template('edit_private_thread.html', title='Edit Thread', form=form, private_thread_id=private_thread_id)


@app.route("/private_post/<int:private_post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_private_post(private_post_id):
    post = PrivatePost.query.get_or_404(private_post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
    
    form = PostForm()
    if form.validate_on_submit():
        post.content = form.content.data
        db.session.commit()
        flash('Post has been updated!', 'success')
        return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
    elif request.method == 'GET':
        form.content.data = post.content
    
    return render_template('edit_private_post.html', title='Edit Post', form=form, private_post_id=private_post_id)


@app.route("/private_thread/<int:private_thread_id>/delete", methods=['POST'])
@login_required
def delete_private_thread(private_thread_id):
    thread = PrivateThread.query.get_or_404(private_thread_id)
    if thread.user_id != current_user.id:
        flash('You do not have permission to delete this thread.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))
    db.session.delete(thread)
    db.session.commit()
    flash('Thread has been deleted!', 'success')
    return redirect(url_for('private_area', private_area_id=thread.area_id))


@app.route("/private_post/<int:private_post_id>/delete", methods=['POST'])
@login_required
def delete_private_post(private_post_id):
    post = PrivatePost.query.get_or_404(private_post_id)
    if post.user_id != current_user.id:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted!', 'success')
    return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
