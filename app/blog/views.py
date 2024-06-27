from flask import (
  g, Blueprint, render_template, request, flash, url_for, redirect, current_app, abort)
from werkzeug.utils import secure_filename
from app.db import get_db
from app.users.views import login_required
from app.utils import form_errors, validate
from datetime import datetime
from app.blog.tags import create_tags, update_tags, get_tags
from app.blog.utils import pagination, slugify
import markdown

bp = Blueprint('blog', __name__)

@bp.app_template_filter("markdown")
def convert_markdown(content):
   return markdown.markdown(content, extensions=['codehilite'])

@bp.app_template_filter("dateformat")
def format_date(date):
   return date.strftime('%a %d %B %Y')

def save_image(image_file):
  filename = secure_filename(image_file.filename)
  image_url =current_app.config['UPLOAD_DIR'] / filename
  image_file.save(image_url)
  return filename

@bp.route('/')
def posts():
  user = g.user
  db = get_db()
  now = datetime.now()

  search =  request.args.get('q') # get url params 

  # Post queries
  count_query = """--sql
  SELECT COUNT(*) FROM posts WHERE posts.publish <= '%s' AND posts.publish !=''""" %now
  # Retrive all published post
  query = f"""--sql
  SELECT * FROM posts WHERE posts.publish <= '%s' AND posts.publish !=''""" %now

  if search: # modify queries for search
     search_query = f"""--sql
     (posts.title LIKE '%{search}%' OR posts.body LIKE '%{search}%')"""
     query += f"""--sql
     AND {search_query}"""
     count_query += f"""--sql
     AND {search_query}"""

  # Admin query: Retrive all posts
  if user is not None and user['is_admin']:
      # Admin user post queries
      count_query = """--sql
      SELECT COUNT(*) FROM posts"""
      query = """--sql
      SELECT * FROM posts"""
      if search: # modify admin user post queries for search
         query += f"""--sql
         WHERE {search_query}"""
         count_query += f"""--sql
         WHERE {search_query}"""
  
  # Pagination
  page = request.args.get('page') or 1
  post_count = db.execute(count_query).fetchone()[0]
  paginate = pagination(post_count, int(page))
         
  # pagination query
  p_query = """--sql
  ORDER BY `created` DESC LIMIT %s OFFSET %s""" %(paginate['per_page'], paginate['offset'])

  
  # Retrieve all posts
  post_list  = db.execute(f"{query} {p_query}").fetchall()
  return render_template('index.html', posts=post_list, date=now.date(), paginator=paginate)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def post_create():
    # if user is not admin return redirect
    if not g.user['is_admin']:
       return redirect(url_for('blog.posts'))
    db = get_db()
   # error handler dictionary
    if request.method == 'POST':
      # Retrieve post data
      title = request.form['title']
      image = request.files['image']
      slug = slugify(title)
      body = request.form['body']
      tags = request.form.get('tags', None)
      publish = request.form.get('publish', None)

      # Check for errors
      fields = form_errors('title', 'body', 'tags', 'image')
      errors = validate(fields, title, body, tags, image)

      if title and body and tags and image: # If data valid create post
          # save image
          filename = save_image(image)
          # create post
          query = """--sql
          INSERT INTO posts (title, image, slug, body, publish, user_id) 
          VALUES ('%s', '%s', '%s', "%s", '%s', %s)""" %(title, filename, slug, body, publish, g.user['id'])
          db.execute(query)
          db.commit()
          # Get created post
          post = db.execute("""--sql
          SELECT id FROM posts WHERE slug=?""", (slug,)).fetchone()
          create_tags(tags.split(','), post['id']) # create tags for post
          flash(f'{title} was created', category='success')
          return redirect(url_for('blog.post_detail', slug=slug))
      return render_template('blog/form.html', post=None, errors=errors, title='Create Post')
    return render_template('blog/form.html', post=None, errors=None, title='Create Post')

@bp.route('/<slug>', methods=('GET', 'POST'))
def post_detail(slug):
    db = get_db()
    post = db.execute("""--sql
    SELECT * FROM posts WHERE slug = ? """, (slug,)).fetchone()
    if post is None:
       abort(404)
       
    if g.user:
       user_id = g.user['id']
    post_id = post['id']

    comments = db.execute("""--sql
    SELECT * FROM comments INNER JOIN users ON user_id = users.id WHERE post_id = ?""", (post_id,)).fetchall()

    if request.method == 'POST':
       comment = request.form['comment']
       if comment:
        query = """--sql
        INSERT INTO comments (body,user_id,post_id) VALUES ('%s', %s, %s)""" %(comment, user_id, post_id)
        db.execute(query)
        db.commit()
        flash('Your comment was created', category='success')
        return redirect(url_for('blog.post_detail', slug=slug))

    if post is None:
       abort(404)
    tags = get_tags(post['id'])
    return render_template('blog/detail.html', post=post, tags=tags, comments=comments)

@bp.route('/<slug>/edit', methods=('GET', 'POST'))
@login_required
def post_edit(slug):
  if not g.user['is_admin']:
    return redirect(url_for('blog.posts'))
  db = get_db()

  post = db.execute("""--sql
  SELECT * FROM posts WHERE slug = ?""", (slug,)).fetchone()
  tags = get_tags(post['id'])

  if request.method == 'POST':
    title = request.form['title']
    post_slug = slugify(title)
    body = request.form['body']
    tags = request.form.get('tags', None)
    publish = request.form.get('publish', None)

    if title and body and tags:
       image_file = request.files['image']
       if image_file:
          filename  = save_image(image_file)
          db.execute("""--sql
          UPDATE posts SET image = ? WHERE slug = ?""", (filename, slug))
          db.commit()

       query = """--sql
       UPDATE posts SET title='%s', slug='%s', body="%s", publish='%s' WHERE slug = '%s'""" %(title, slugify(title), body, publish, slug)
       db.execute(query)
       db.commit()
       post_id = db.execute("""--sql
       SELECT id FROM posts WHERE slug = ?""", (slugify(title),)).fetchone()[0]
       update_tags(tags.split(','), post_id) # update the slug
       flash(f'{title} was updated', category='success')
       return redirect(url_for('blog.post_detail', slug=post_slug))
    # handle errors
    fields = form_errors('title', 'body', 'tags')
    errors = validate(fields, title, body, tags)
    return render_template('blog/form.html', errors=errors, post=post, title='Edit Post')

  return render_template('blog/form.html', errors=None, post=post, tags=tags, title='Edit Post')

@bp.route('/<slug>/delete')
@login_required
def post_delete(slug):
    # Remove post from database
    db = get_db()
    db.execute("""--sql
    DELETE FROM posts WHERE slug = ?""", (slug,))
    flash('Post was deleted', category='danger')
    return redirect(url_for('blog.posts'))

@bp.route('/preview', methods=('GET', 'POST'))
def post_preview():
   if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']
    tags = request.form['tags']
    publish = request.form['publish']
    date = publish
    if title and body:
      if publish:
        date = datetime.strptime(publish, '%Y-%m-%d').date()
      post = {
          'title': title,
          'body': body,
          'publish': date,
      }
      return render_template('blog/detail.html', post=post, tags=tags.split(','))
    flash('Nothing to preview', category='danger')
    return redirect(url_for('blog.post_create'))