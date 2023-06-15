from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, CreateUserForm, UserLoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES

##CREATE TABLE IN DB
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    #author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    #Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="blog")

class Comment(db.Model):
    __tablename__ = "comments"
    body = db.Column(db.Text, nullable=False)

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))

    # author = db.Column(db.String(250), nullable=False)
    author = relationship("User", back_populates="comments")
    blog = relationship("BlogPost", back_populates="comments")


# this needs running once to create user table
# with app.app_context():
#    db.create_all()


# this decorator can be placed on any route, then only users who have id of 1
# can access these pages, id == 1 means admin for the purposes of this exercise
def admin_only(function):
    @wraps(function)
    def wrapper():
        print('wrapper')
        if current_user.is_authenticated and current_user.id == 1:
            print("admin check passed")
            return function()
        else:
            print('abort')
            return abort(403) #, description="forbidden")
    return wrapper


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['POST', 'GET'])
def register():
    register_form = CreateUserForm()

    if register_form.validate_on_submit():

        existing_user = User.query.filter_by(email=register_form.email.data).first()
        if existing_user:
            flash("You've already signed up with that email address. Log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(register_form.password.data,
                                                          method='pbkdf2:sha256',
                                                          salt_length=8)

        # create user
        user = User(email=register_form.email.data,
                    password=hash_and_salted_password,
                    name=register_form.name.data)

        # save new user account to db
        db.session.add(user)
        db.session.commit()

        # Log in the newly registered user
        login_user(user)

        return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=register_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:

            # validate entered password from the form against password stored on db
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('Password incorrect, please try again.')
        else:
            flash('This email does not exist, please try again.')
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['GET', 'POST'])
def show_post(post_id):

    comment_form = CommentForm()
    requested_post = BlogPost.query.get(post_id)

    # save submitted comment
    if comment_form.validate_on_submit():
        new_comment = Comment(body=comment_form.comment.data,
                              author=current_user,
                              blog=requested_post)
        db.session.add(new_comment)
        db.session.commit()
        comment_form.comment.data = ""

    return render_template("post.html", post=requested_post, comment_form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@admin_only
@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data

        post.author = current_user

        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@admin_only
@app.route("/delete/<int:comment_id>")
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    db.session.delete(comment)
    db.session.commit()
    post_id = request.args.get('post_id')
    return redirect(url_for('show_post', post_id=post_id))


@admin_only
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)
