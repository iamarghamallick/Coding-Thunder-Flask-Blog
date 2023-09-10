from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import math
import os.path

local_server = True
with open("config.json", "r") as c:
    params = json.load(c)['params']

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    """
    sno, name, msg, ph_no, email, date
    """
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=False, nullable=False)
    msg = db.Column(db.String(500), unique=False, nullable=False)
    ph_no = db.Column(db.String(10), unique=False, nullable=False)
    email = db.Column(db.String(50), unique=False, nullable=False)
    date = db.Column(db.String, unique=False, nullable=True)


class Posts(db.Model):
    """
    sno, title, slug, content, date
    """
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=False, nullable=False)
    tagline = db.Column(db.String(50), unique=False, nullable=False)
    slug = db.Column(db.String(50), unique=False, nullable=False)
    content = db.Column(db.String(1000), unique=False, nullable=False)
    img_file = db.Column(db.String(50), unique=False, nullable=False)
    date = db.Column(db.String, unique=False, nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    # Pagination Logic
    page = request.args.get('page')
    if not str(page).isdigit():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page+1)
    elif page == last:
        next = "#"
        prev = "/?page=" + str(page-1)
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page + 1)

    return render_template("index.html", params=params, posts=posts, prev=prev, next=next)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        ''' Add entry to the database '''
        name = request.form.get('name')
        email = request.form.get('email')
        ph_no = request.form.get('ph_no')
        msg = request.form.get('msg')

        entry = Contacts(name=name, ph_no=ph_no, email=email, msg=msg, date=datetime.now())

        db.session.add(entry)
        db.session.commit()

        flash("Thanks for submitting your details!", "success")

    return render_template('contact.html', params=params)


@app.route("/post")
def post():
    return render_template('post.html', params=params)


@app.route("/post/<string:post_slug>", methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


# ADMIN DASHBOARD

@app.route("/dashboard", methods=['GET', 'POST'])
def login():
    if 'user' in session and session['user'] == params['admin_username']:
        posts = Posts.query.filter_by().all()
        return render_template('dashboard.html', params=params, posts=posts)
    if request.method == 'POST':
        # REDIRECT TO ADMIN DASHBOARD
        username = request.form.get('username')
        userpass = request.form.get('pass')
        if username == params['admin_username'] and userpass == params['admin_password']:
            # set the session var
            session['user'] = username
            posts = Posts.query.filter_by().all()
            return render_template('dashboard.html', params=params, posts=posts)
        else:
            return render_template("login.html", params=params)
    else:
        return render_template("login.html", params=params)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_username']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            if sno == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tagline, img_file=img_file)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tagline
                post.img_file = img_file
                db.session.commit()

                return redirect('/edit/' + sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post, sno=sno)


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_username']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route("/upload", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_username']:
        if request.method == "POST":
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Success"


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

app.run(debug=True)
