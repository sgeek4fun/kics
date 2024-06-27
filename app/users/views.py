import functools
from flask import Blueprint, request, flash, render_template, redirect, url_for, session, g
from werkzeug.security import check_password_hash, generate_password_hash
from app.db import get_db
from app.utils import form_errors, validate

bp = Blueprint('users', __name__)

@bp.route('/register', methods=('GET', 'POST'))
def register():
  db = get_db()
  if request.method == 'POST':
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    if username and email and password:
        hash_password = generate_password_hash(password)
        query = """--sql
        INSERT INTO users (`username`, `email`, `password`) VALUES ('%s', '%s', '%s')""" %(username, email, hash_password)
        db.execute(query)
        db.commit()
        flash('Account was created', 'success')
        return redirect(url_for('users.login'))
    
    # handle errors
    fields = form_errors('username', 'email', 'password')
    errors = validate(fields, username, email, password)
    
    return render_template('users/register.html', errors=errors)

  return render_template('users/register.html', errors=None)

@bp.route('/login', methods=('GET', 'POST'))
def login():
   db = get_db()
   if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']

    user = db.execute("""--sql
    SELECT * FROM users WHERE email = ? or username = ?""", (email, email)).fetchone()
    if user is None or not check_password_hash(user['password'], password):
      flash('The email address or password you entered is incorrect', 'danger')
      return redirect(url_for('users.login'))
    
    session.clear()
    session['user_id'] = user['id']
    return redirect(url_for('blog.posts'))

   return render_template('users/login.html')

@bp.route('/logout', methods=('GET',))
def logout():
  session.clear()
  flash('You logged out', category='success')
  return redirect(url_for('users.login'))

@bp.before_app_request
def load_auth_user():
  user_id = session.get('user_id')
  if user_id is None:
    g.user = None
  else:
    db = get_db()
    user = db.execute("""--sql
    SELECT * FROM users WHERE id = ?""", (user_id,)).fetchone()
    g.user = user

def login_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if g.user is None:
      return redirect(url_for('users.login'))
    return view(**kwargs)
  return wrapped_view


