from sys import _current_frames
from flask import Flask, render_template, request, session, redirect
import os
import sqlite3
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = os.urandom(32)

# DEFINE CONSTANTS
DB_FILE = "./users.db"
MAX_ENTRIES = 20

# POST TABLE INDICES
POST_DATE = 0
POST_UID = 1
POST_NUM = 2

# DEFINE GLOBAL SQL SCRIPTS

make_user_table = """CREATE TABLE IF NOT EXISTS USERS(
                    UID INTEGER PRIMARY KEY NOT NULL,
                    USERNAME TEXT NOT NULL,
                    PASSWORD TEXT NOT NULL,
                    BLOG_NAME TEXT,
                    LAST_POST_NUM INTEGER,
                    UNIQUE (USERNAME));"""

make_post_table = """CREATE TABLE IF NOT EXISTS POSTS(
                        POST_ID INTEGER PRIMARY KEY NOT NULL,
                        DATE TEXT,
                        UID INTEGER,
                        POST_NUM INTEGER,
                        POST_TITLE TEXT);"""

def get_post_details(cursor, user_id, post_num):
    """Returns a list of post details. Formatted as [POST_TITLE, POST_DESCRIPTION, POST_DATETIME, POST_NUM]"""
    # Get the current post's title
    cursor.execute("SELECT POST_TITLE FROM POSTS WHERE UID=? AND POST_NUM=?", (user_id, post_num))
    post_title = cursor.fetchone()[0]

    # If the post doesn't have a title, make it an empty string
    if post_title == None:
        post_title = ""

    cursor.execute("SELECT DATE FROM POSTS WHERE UID=? AND POST_NUM=?", (user_id, post_num))
    post_datetime = cursor.fetchone()[0]

    # If the post doesn't have a creation date / time, make it an empty string
    if post_datetime == None:
        post_datetime = ""
    
    post_path = "./blogs/%s/%s.txt" % (user_id, post_num)

    with open(post_path, "r") as post:
        return [post_title, post.read(), post_datetime, post_num]

def is_logged_in():
    """Returns whether or not a user is logged in."""
    return 'username' in session.keys()

@app.route("/", methods=["GET"])
def home():
    """Renders a login page if the user is not logged in and displays a list of recent posts by all users if they are."""
    if not os.path.exists("./blogs"):
        os.mkdir("./blogs")

    if is_logged_in():
        post_list = [] # FORMAT: [['DESC', UID, POST_NUM], ...]
        usernames = {} # FORMAT: ['UID' : Username, ...]

        db = sqlite3.connect(DB_FILE)

        c = db.cursor()
        c.execute("SELECT * FROM POSTS ORDER BY POST_ID DESC LIMIT 20")

        for i in range(MAX_ENTRIES, -1, -1):
            # Retrieve the subsequent post
            post = c.fetchone()

            if (post == None):
                break

            post_path = "./blogs/%s/%s.txt" % (post[POST_UID], post[POST_NUM])
            if os.path.exists(post_path):
                # Open the post & append it to the lists of posts
                with open(post_path, 'r') as curr_post:
                    post_list.append([curr_post.read(), post[POST_UID], post[POST_NUM]]) # This is the post wrapper

        

        WRAPPER_DESC = 0
        WRAPPER_UID = 1
        WRAPPER_POST_NUM = 2
        WRAPPER_TITLE = 3
        WRAPPER_DATE = 4

        for post_wrapper in post_list:
            post_num = post_wrapper[WRAPPER_POST_NUM]

            # Add the UID & corresponding username to the usernames dictionary
            c.execute("SELECT USERNAME FROM USERS WHERE UID=?", (post_wrapper[WRAPPER_UID], ))
            usernames[post_wrapper[WRAPPER_UID]] = c.fetchone()[0]

            # Retrieve title for corresponding post
            c.execute("SELECT POST_TITLE FROM POSTS WHERE UID=? AND POST_NUM=?", (post_wrapper[WRAPPER_UID], post_wrapper[POST_NUM]))
            post_title = c.fetchone()[0]

            # Retrieve title for corresponding post
            c.execute("SELECT DATE FROM POSTS WHERE UID=? AND POST_NUM=?", (post_wrapper[WRAPPER_UID], post_wrapper[POST_NUM]))
            post_date = c.fetchone()[0]

            post_wrapper.append(post_title)
            post_wrapper.append(post_date)

        return render_template("home.html", blogs = post_list, usernames = usernames)
    else:
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        c.execute(make_user_table)
        c.execute(make_post_table)
        db.commit()
        db.close()

        if ('error_message' in session.keys()):
            return render_template("login.html", error_message = session.pop('error_message')) # Render & subsequently remove error message

        return render_template("login.html")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    """Authenticates a user. Throws an error if the user credentials are not found in the database."""
    if (request.method == "POST"):
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        # Select the user that matches the inputed username and password
        c.execute("SELECT * FROM USERS WHERE USERNAME=? AND PASSWORD=?", (request.form['username'], request.form['password']))
        user = c.fetchone()

        # If a user was selected, add the user to the session and return home
        if user != None:
            session['UID'] = user[0]
            session['username'] = user[1]
        else:
            # If none is selected, return an error (as user does not exist).
            session['error_message'] = "Incorrect username or password"

        db.close()
    return redirect("/")

@app.route("/logout")
def logout():
    """Logs out the user, clears the session, and redirects user to the login page."""
    session.clear()
    return redirect("/")

@app.route("/my_blog", methods=["GET"])
def my_blog():
    """Renders a list of the logged in user's blog posts."""
    if is_logged_in():
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        # Retrieve user's blog name
        c.execute("SELECT BLOG_NAME FROM USERS WHERE UID = ?", (session['UID'], ))
        blog_name = c.fetchone()[0]

        if blog_name == None:
            # Redirect user to name their blog if they haven't done it yet
            return redirect("/name_blog")
        else:
            c.execute("SELECT * FROM POSTS WHERE UID = ? ORDER BY POST_ID DESC LIMIT 20", (session['UID'],))
            post = c.fetchall()
            post_list = []
            i = 0
            while (i < len(post)):
                with open("./blogs/%s/%s.txt" % (session['UID'], post[i][2]), 'r') as file:
                    post_list.append([post[i][3], file.read(), post[i][0], post[i][2]])
                i+=1
            
            return render_template("my_blog.html", blog_name = blog_name, post_list = post_list)
    else:
        return redirect("/")

@app.route("/new_entry", methods=["POST", "GET"])
def new_entry():
    """Prompts the user to enter new post details and adds it to the database."""
    if is_logged_in():
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        # Retrieve user's blog name
        c.execute("SELECT BLOG_NAME FROM USERS WHERE UID = ?", (session['UID'], ))
        blog_name = c.fetchone()[0]

        if blog_name == None:
            # Redirect user to name their blog if they haven't done it yet
            return redirect("/name_blog")
        elif request.method == "POST":

            c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (session['UID'], ))
            new_post_num = c.fetchone()[0] + 1
            new_post_path = "./blogs/%s/%s.txt" % (session['UID'], new_post_num)

            post = request.form['new_entry']
            post = post.rstrip()

            # Record the submitted new_entry data into a new .txt file
            with open(new_post_path, "w") as new_post:
                new_post.write(post)

            # Add the new post, author user_id, & creation time / date to the post history
            current = datetime.now()
            c.execute("INSERT INTO POSTS(Date, UID, POST_NUM, POST_TITLE) VALUES(?, ?, ?, ?)",
                ("%s, %s" % (date.today(), current.strftime("%H:%M:%S")),
                session['UID'],
                new_post_num,
                request.form['entry-title']
                )
            )

            c.execute("UPDATE USERS SET LAST_POST_NUM=LAST_POST_NUM+1 WHERE UID=?", (session['UID'], ))
            db.commit()
            db.close()
            return redirect("/my_blog")
        else:
            return render_template("new_entry.html")
    else:
        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Prompts a user to register for a new account & enters their new credentials into the database."""
    if request.method == "POST" and (request.form['username'] != '' and request.form['password'] != ''):

        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        c.execute("SELECT UID FROM USERS WHERE USERNAME=?", ( (request.form['username']), ) )
        user_exists = bool(c.fetchone())

        if user_exists:
            db.close()
            username_taken_error = "Username is taken."
            return render_template("register.html", error_message=username_taken_error)

        if request.form['password'] != request.form['repassword']:
            db.close()
            pass_match_error = "Passwords must match."
            return render_template("register.html", error_message=pass_match_error)

        try:
            # Add user credentials to database
            c.execute("INSERT INTO USERS(USERNAME, PASSWORD, LAST_POST_NUM) VALUES(?, ?, ?)",
                (request.form['username'], request.form['password'], -1))

            # Select newly created user
            c.execute("SELECT * FROM USERS WHERE USERNAME=? AND PASSWORD=?",
                (request.form['username'], request.form['password']))

            new_user = c.fetchone()
            os.mkdir("./blogs/%s" % (new_user[0])) # Create a blog directory to store new user's files
            session['UID'] = new_user[0]
            session['username'] = new_user[1]
        except sqlite3.IntegrityError:
            return render_template("register.html")
        db.commit()
        db.close()
        return redirect("/name_blog")
    else:
        return render_template("register.html")

@app.route("/name_blog", methods=["GET", "POST"])
def name_blog():
    """Prompts the user to name their blog."""
    if is_logged_in():
        if request.method == "POST" and request.form["blog_name"] != '':
            db = sqlite3.connect(DB_FILE)
            c = db.cursor()
            c.execute("UPDATE USERS SET BLOG_NAME=? WHERE UID=?", (request.form["blog_name"],session['UID'],))
            db.commit()
            db.close()
            return redirect("/")
        else:
            return render_template("name_blog.html")
    else:
        return redirect("/")

@app.route("/edit/<int:post_num>", methods=["GET", "POST"])
def edit(post_num):
    """Edit a user's post given a specific post number."""
    if is_logged_in():
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        # Retrieve the number of the last post the user made
        c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID=?", (session['UID'], ))
        last_post_num = c.fetchone()[0]

        post_path = "./blogs/%s/%s.txt" % (session['UID'], post_num)
        if request.method == "POST":
            c.execute("UPDATE POSTS SET POST_TITLE=? WHERE UID=? AND POST_NUM=?", (request.form['entry-title'], session['UID'], post_num))
            db.commit()
            db.close()
            postText = request.form['edit']
            postText = postText.rstrip()
            with open(post_path, "w") as post:
                post.write(postText)
            return redirect('/')
        else:
            c.execute("SELECT POST_TITLE FROM POSTS WHERE UID=? AND POST_NUM=?", (session['UID'], post_num))
            with open(post_path, "r") as post:
                title = c.fetchone()[0]
                db.close()
                return render_template("edit.html", text=post.read(), index=post_num, title = title)
    else:
        return redirect("/")

@app.route("/discover")
def discover():
    """Lists the blogs of all users."""
    if is_logged_in():
        user_list = []
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        # Scan through the list of users and append usernames to user_list if they aren't the user that is logged in
        for user_folder in os.scandir("./blogs"):
            if (int)(user_folder.name) != session['UID']:
                c.execute("SELECT BLOG_NAME FROM USERS WHERE UID=?", (user_folder.name, ))
                blog_name = c.fetchone()[0]

                if blog_name != None:
                    c.execute("SELECT USERNAME FROM USERS WHERE UID=?", (user_folder.name, ))
                    user_list.append([c.fetchone()[0], blog_name])
                
        return render_template("discover.html", user_list = user_list)
    else:
        return redirect("/")

@app.route("/view/<username>")
def view_user(username):
    """Renders the blog of a specified user."""
    if is_logged_in():
        post_list = []
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        # Retrieve UID from specified username
        c.execute("SELECT UID FROM USERS WHERE USERNAME = ?", (username, ))
        user_id = c.fetchone()[0]

        # Retrieve last_post_num from specified UID
        c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (user_id, ))
        last_post_num = c.fetchone()

        if (last_post_num == None):
            return render_template("blog.html", post_list = post_list)
        else:
            last_post_num = last_post_num[0]
    
        # Retrieve blog title from specified username
        c.execute("SELECT BLOG_NAME FROM USERS WHERE UID = ?", (user_id, ))
        blog_name = c.fetchone()[0]

        for post_num in range(last_post_num, -1, -1): # Start from the last post & decrement as you go
            post_list.append(get_post_details(c, user_id, post_num))
        return render_template("blog.html", post_list = post_list, username = username, blog_name = blog_name)
    else:
        return redirect("/")

@app.route("/about", methods=["GET"])
def about():
    if is_logged_in():
        return render_template("about.html")
    else:
        return redirect("/")


@app.errorhandler(404)
def page_not_found(e):
    """Returns an error page if a page is not found."""
    return render_template("error.html")

if __name__ == "__main__":
    app.debug = True
    app.run()
