from datetime import datetime
from työ import app, db, bcrypt
from flask import render_template, url_for, flash, redirect, request, session
from työ.forms import RegistrationForm, LoginForm, ThreadForm, PostForm, PasswordForm
from työ.models import User
from flask_login import login_user, current_user, logout_user, login_required, LoginManager
from sqlalchemy import text

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/home')
def home():
    sql_area=text("SELECT * FROM area WHERE is_secret = false")
    sql_private_area=text("SELECT * FROM private_area WHERE is_secret = false")
    areas = db.session.execute(sql_area).fetchall()
    private_areas = db.session.execute(sql_private_area).fetchall()
    
    return render_template('home.html', areas=areas, private_areas=private_areas)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        sql = text("SELECT id FROM \"user\" WHERE username = :username")
        existing_user = db.session.execute(sql, {'username': username,}).fetchone() 
        if existing_user:
            flash('Username is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('register'))   
        sql = text("SELECT id FROM \"user\" WHERE email = :email")
        existing_email = db.session.execute(sql, {'email': email,}).fetchone()
        if existing_email:
            flash('Email is already in use. Please enter a different one.', 'danger')
            return redirect(url_for('register'))
        sql3 = text("INSERT INTO \"user\" (username, email, password, is_admin) VALUES (:username, :email, :password, :is_admin)")
        db.session.execute(sql3, {'username': username, 'email': email, 'password': password, 'is_admin': False})
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
        sql = text("SELECT id, email, password FROM \"user\" WHERE email = :email")
        result = db.session.execute(sql, {'email': form.email.data}).fetchone()
        if result and bcrypt.check_password_hash(result.password, form.password.data):
            user = User(id=result.id, email=result.email)
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
    user_id = current_user.id
    if current_user.is_admin:
        pass
        flash("An error has occured",  "info")
    else:
        sql_delete_post = text("DELETE FROM post WHERE user_id = :user_id")
        sql_delete_ppost = text("DELETE FROM private_post WHERE user_id = :user_id")
        sql_delete_thread = text("DELETE FROM thread WHERE user_id = :user_id")
        sql_delete_pthread = text("DELETE FROM private_thread WHERE user_id = :user_id")
        sql_delete_user = text("DELETE FROM \"user\" WHERE id = :user_id")
        db.session.execute(sql_delete_post, {'user_id': user_id})
        db.session.execute(sql_delete_ppost, {'user_id': user_id})
        db.session.execute(sql_delete_thread, {'user_id': user_id})
        db.session.execute(sql_delete_pthread, {'user_id': user_id})
        db.session.execute(sql_delete_user, {'user_id': user_id})
        db.session.commit()

        flash('Your account has been deleted.', 'success')
    return redirect(url_for('home'))


@app.route("/area/<int:area_id>")
@login_required
def area(area_id):
    sql_area = text("SELECT * FROM area WHERE id = :id")
    sql_thread = text("SELECT * FROM thread WHERE area_id = :area_id")
    area = db.session.execute(sql_area, {'id': area_id}).fetchone()
    threads = db.session.execute(sql_thread, {'area_id': area_id}).fetchall()
    
    return render_template('area.html', area=area, threads=threads)

@app.route("/thread/new/<int:area_id>", methods=['GET', 'POST'])
def new_thread(area_id):
    form = ThreadForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        user_id = current_user.id
        sql_insert_thread = text("INSERT INTO thread (title, area_id, user_id) VALUES (:title, :area_id, :user_id)")
        db.session.execute(sql_insert_thread, {'title': title, 'area_id': area_id, 'user_id': user_id})
        sql_thread_id = text("SELECT id FROM thread WHERE title = :title AND area_id = :area_id AND user_id = :user_id ORDER BY id DESC LIMIT 1")
        thread_result = db.session.execute(sql_thread_id, {'title': title, 'area_id': area_id, 'user_id': user_id}).fetchone()
        thread_id = thread_result[0]
        sql_insert_post = text("INSERT INTO post (content, thread_id, user_id, timestamp) VALUES (:content, :thread_id, :user_id, CURRENT_TIMESTAMP)")
        db.session.execute(sql_insert_post, {'content': content, 'thread_id': thread_id, 'user_id': user_id})
        db.session.commit()
        flash('New thread created!', 'success')
        return redirect(url_for('area', area_id=area_id))
    
    return render_template('create_thread.html', title='New Thread', form=form)

@app.route("/thread/<int:thread_id>", methods=['GET', 'POST'])
def thread(thread_id):
    sql_thread= text("SELECT * FROM thread WHERE id = :thread_id")
    thread_result = db.session.execute(sql_thread, {"thread_id": thread_id})
    thread = thread_result.fetchone()
    if not thread:
        flash('Thread not found!', 'error')
        return redirect(url_for('index'))
    sql_user=text("SELECT p.*, u.username as username FROM post p LEFT JOIN \"user\" u ON p.user_id = u.id WHERE p.thread_id = :thread_id")
    posts_result = db.session.execute(sql_user,{"thread_id": thread_id})
    posts = posts_result.fetchall()
    form = PostForm()
    if form.validate_on_submit():
        content = form.content.data
        user_id = current_user.id if current_user.is_authenticated else None
        timestamp = datetime.utcnow() 
        sql_post=text("INSERT INTO post (content, thread_id, user_id, timestamp) VALUES (:content, :thread_id, :user_id, :timestamp)")
        db.session.execute(sql_post,{"content": content, "thread_id": thread_id, "user_id": user_id, "timestamp": timestamp})
        db.session.commit()
        flash('Your post has been added!', 'success')
        return redirect(url_for('thread', thread_id=thread_id))
    
    return render_template('thread.html', thread=thread, posts=posts, form=form)

@app.route("/account")
@login_required
def account():
    return render_template('account.html')

@app.route("/thread/<int:thread_id>/edit", methods=['GET', 'POST'])
def edit_thread(thread_id):
    sql_edit = text("SELECT * FROM thread WHERE id = :id")
    result = db.session.execute(sql_edit, {'id': thread_id})
    thread = result.fetchone()
    if thread.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this thread.', 'danger')
        return redirect(url_for('thread', thread_id=thread_id))
    form = ThreadForm()
    if form.validate_on_submit() or request.method == 'POST':
        sql_update = text("UPDATE thread SET title = :title WHERE id = :id")
        db.session.execute(sql_update, {'title': form.title.data, 'id': thread_id})
        db.session.commit()
        flash('Thread title has been updated!', 'success')
        return redirect(url_for('thread', thread_id=thread_id))
    elif request.method == 'GET':
        form.title.data = thread.title
    
    return render_template('edit_thread.html', title='Edit Thread', form=form)

@app.route("/post/<int:post_id>/edit", methods=['GET', 'POST'])
def edit_post(post_id):
    sql_edit = text("SELECT * FROM post WHERE id = :id")
    result = db.session.execute(sql_edit, {'id': post_id})
    post = result.fetchone()
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('thread', thread_id=post.thread_id))
    form = PostForm()
    if form.validate_on_submit():
        sql_update = text("UPDATE post SET content = :content WHERE id = :id")
        db.session.execute(sql_update, {'content': form.content.data, 'id': post_id})
        db.session.commit()
        flash('Post has been updated!', 'success')
        return redirect(url_for('thread', thread_id=post.thread_id))
    elif request.method == 'GET':
        form.content.data = post.content
    
    return render_template('edit_post.html', title='Edit Post', form=form)

@app.route("/thread/<int:thread_id>/delete", methods=['POST'])
def delete_thread(thread_id):
    sql_select_thread = text("SELECT * FROM thread WHERE id = :id")
    result_thread = db.session.execute(sql_select_thread, {'id': thread_id})
    thread = result_thread.fetchone()
    if thread.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this thread.', 'danger')
        return redirect(url_for('thread', thread_id=thread_id))
    sql_delete_posts = text("DELETE FROM post WHERE thread_id = :thread_id")
    db.session.execute(sql_delete_posts, {'thread_id': thread_id})
    sql_delete_thread = text("DELETE FROM thread WHERE id = :id")
    db.session.execute(sql_delete_thread, {'id': thread_id})
    db.session.commit()
    flash('Thread has been deleted!', 'success')
    
    return redirect(url_for('area', area_id=thread.area_id))

@app.route("/post/<int:post_id>/delete", methods=['POST'])
def delete_post(post_id):
    sql_edit = text("SELECT * FROM post WHERE id = :id")
    result = db.session.execute(sql_edit, {'id': post_id})
    post = result.fetchone()
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('thread', thread_id=post.thread_id))
    sql_delete_post = text("DELETE FROM post WHERE id = :id")
    db.session.execute(sql_delete_post, {'id': post_id})
    db.session.commit()
    flash('Post has been deleted!', 'success')
    
    return redirect(url_for('thread', thread_id=post.thread_id))

@app.route("/password", methods=['GET', 'POST'])
@login_required
def password():
    form = PasswordForm()
    if session.get('has_access'):
        sql_area = text("SELECT * FROM private_area LIMIT 1")
        area = db.session.execute(sql_area).fetchone()
        flash('Welcome back!', 'success')
        return redirect(url_for('private_area', private_area_id=area.id))
    if current_user.is_admin:
        sql_area = text("SELECT * FROM private_area LIMIT 1")
        area = db.session.execute(sql_area).fetchone() 
        flash('You may enter!', 'success')
        return redirect(url_for('private_area', private_area_id=area.id))
    flash("Please enter the password.", "info")
    if form.validate_on_submit():
        sql_area = text("SELECT * FROM private_area WHERE password = :password LIMIT 1")
        area = db.session.execute(sql_area, {'password': form.password.data}).fetchone()
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
    sql_area = text("SELECT * FROM private_area WHERE id = :id")
    area = db.session.execute(sql_area, {'id': private_area_id}).fetchone()    
    sql_threads = text("SELECT * FROM private_thread WHERE area_id = :area_id")
    threads = db.session.execute(sql_threads, {'area_id': private_area_id}).fetchall()
    
    return render_template('private_area.html', private_area=area, threads=threads)

@app.route("/private_thread/new/<int:private_area_id>", methods=['GET', 'POST'])
def new_private_thread(private_area_id):
    form = ThreadForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        user_id = current_user.id
        sql_insert_thread = text("INSERT INTO private_thread (title, area_id, user_id) VALUES (:title, :area_id, :user_id)")
        db.session.execute(sql_insert_thread, {'title': title, 'area_id': private_area_id, 'user_id': user_id})
        sql_thread_id = text("SELECT id FROM private_thread WHERE title = :title AND area_id = :area_id AND user_id = :user_id ORDER BY id DESC LIMIT 1")
        thread_result = db.session.execute(sql_thread_id, {'title': title, 'area_id': private_area_id, 'user_id': user_id}).fetchone()
        thread_id = thread_result[0]
        sql_insert_post = text("INSERT INTO private_post (content, private_thread_id, user_id, timestamp) VALUES (:content, :private_thread_id, :user_id, CURRENT_TIMESTAMP)")
        db.session.execute(sql_insert_post, {'content': content, 'private_thread_id': thread_id, 'user_id': user_id})
        db.session.commit()
        flash('New thread created!', 'success')
        return redirect(url_for('private_area', private_area_id=private_area_id))
    
    return render_template('create_private_thread.html', title='New Thread', form=form)

@app.route("/private_thread/<int:private_thread_id>", methods=['GET', 'POST'])
def private_thread(private_thread_id):
    sql_thread = text("SELECT * FROM private_thread WHERE id = :private_thread_id")
    thread_result = db.session.execute(sql_thread, {"private_thread_id": private_thread_id})
    thread = thread_result.fetchone()
    sql_posts = text("SELECT p.*, u.username as username FROM private_post p LEFT JOIN \"user\" u ON p.user_id = u.id WHERE p.private_thread_id = :private_thread_id")
    posts_result = db.session.execute(sql_posts, {"private_thread_id": private_thread_id})
    posts = posts_result.fetchall()
    form = PostForm()
    if form.validate_on_submit():
        content = form.content.data
        user_id = current_user.id
        timestamp = datetime.utcnow()
        sql_post = text("INSERT INTO private_post (content, private_thread_id, user_id, timestamp) VALUES (:content, :private_thread_id, :user_id, :timestamp)")
        db.session.execute(sql_post, {"content": content, "private_thread_id": private_thread_id, "user_id": user_id, "timestamp": timestamp})
        db.session.commit()
        flash('Your post has been added!', 'success')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))

    return render_template('private_thread.html', thread=thread, posts=posts, form=form)

@app.route("/private_thread/<int:private_thread_id>/edit", methods=['GET', 'POST'])
def edit_private_thread(private_thread_id):
    sql_edit = text("SELECT * FROM private_thread WHERE id = :id")
    result = db.session.execute(sql_edit, {'id': private_thread_id})
    thread = result.fetchone()
    if thread.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this thread.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))
    form = ThreadForm()
    if form.validate_on_submit() or request.method == 'POST':
        sql_update = text("UPDATE private_thread SET title = :title WHERE id = :id")
        db.session.execute(sql_update, {'title': form.title.data, 'id': private_thread_id})
        db.session.commit()
        flash('Thread title has been updated!', 'success')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))
    elif request.method == 'GET':
        form.title.data = thread.title
    
    return render_template('edit_private_thread.html', title='Edit Thread', form=form, private_thread_id=private_thread_id)


@app.route("/private_post/<int:private_post_id>/edit", methods=['GET', 'POST'])
def edit_private_post(private_post_id):
    sql_edit = text("SELECT * FROM private_post WHERE id = :id")
    result = db.session.execute(sql_edit, {'id': private_post_id})
    post = result.fetchone()
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
    form = PostForm()
    if form.validate_on_submit():
        sql_update = text("UPDATE private_post SET content = :content WHERE id = :id")
        db.session.execute(sql_update, {'content': form.content.data, 'id': private_post_id})
        db.session.commit()
        flash('Post has been updated!', 'success')
        return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
    elif request.method == 'GET':
        form.content.data = post.content

    return render_template('edit_post.html', title='Edit Post', form=form)

@app.route("/private_thread/<int:private_thread_id>/delete", methods=['POST'])
def delete_private_thread(private_thread_id):
    sql_select_thread = text("SELECT * FROM private_thread WHERE id = :id")
    result_thread = db.session.execute(sql_select_thread, {'id': private_thread_id})
    thread = result_thread.fetchone()
    if thread.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this thread.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=private_thread_id))
    sql_delete_posts = text("DELETE FROM private_post WHERE private_thread_id = :thread_id")
    db.session.execute(sql_delete_posts, {'thread_id': private_thread_id})
    sql_delete_thread = text("DELETE FROM private_thread WHERE id = :id")
    db.session.execute(sql_delete_thread, {'id': private_thread_id})
    db.session.commit()
    flash('Thread has been deleted!', 'success')
    
    return redirect(url_for('private_area', private_area_id=thread.area_id))

@app.route("/private_post/<int:private_post_id>/delete", methods=['POST'])
def delete_private_post(private_post_id):
    sql_edit = text("SELECT * FROM private_post WHERE id = :id")
    result = db.session.execute(sql_edit, {'id': private_post_id})
    post = result.fetchone()
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
    sql_delete_post = text("DELETE FROM private_post WHERE id = :id")
    db.session.execute(sql_delete_post, {'id': private_post_id})
    db.session.commit()
    flash('Post has been deleted!', 'success')
   
    return redirect(url_for('private_thread', private_thread_id=post.private_thread_id))
