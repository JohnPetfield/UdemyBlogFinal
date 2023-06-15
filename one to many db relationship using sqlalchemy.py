
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    
    # This will act like a List of BlogPost objects attached to each User. 
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    
class BlogPost(db.Model):
	# table fields (not relevant to the example)
    __tablename__ = "blog_posts"
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
	# when working with a blogpost object, it will have a author field,
	# author will be a user object. so we can say blog_post.author.name
    author = relationship("User", back_populates="posts")
   