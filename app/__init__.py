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
                        DATE TEXT, 
                        UID INTEGER, 
                        POST_NUM);"""

def is_logged_in():
    return 'username' in session.keys()

@app.route("/", methods=["GET"])
def login():
    if not os.path.exists("./blogs"):
        os.mkdir("./blogs")
        
    if is_logged_in():
        post_list = []
        uid_list = []
        db = sqlite3.connect(DB_FILE)

        c = db.cursor()
        c.execute("SELECT * FROM POSTS")
        
        for i in range(MAX_ENTRIES, -1, -1):
            # Retrieve the subsequent post 
            post = c.fetchone()

            if (post == None):
                break
            
            post_path = "./blogs/%s/%s.txt" % (post[POST_UID], post[POST_NUM])
            if os.path.exists(post_path):
                # Open the post & append it to the lists of posts
                with open(post_path, 'r') as curr_post:
                    post_list.append(curr_post.read())
                    uid_list.append(post[POST_UID])

        # Order the post_list with most recently made posts first
        post_list.reverse()
        uid_list.reverse()
        return render_template("home.html", blogs = post_list, id = uid_list)
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
    # Clears session and returns home
    session.clear()
    return redirect("/")

@app.route("/new_entry", methods=["POST", "GET"])
def new_entry():
    if is_logged_in():
        if request.method == "POST":
            db = sqlite3.connect(DB_FILE)
            c = db.cursor()

            c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (session['UID'], ))
            new_post_num = c.fetchone()[0] + 1
            new_post_path = "./blogs/%s/%s.txt" % (session['UID'], new_post_num)

            # Record the submitted new_entry data into a new .txt file
            with open(new_post_path, "w") as new_post:
                new_post.write(request.form['new_entry'])
            
            # Add the new post, author user_id, & creation time / date to the post history
            current = datetime.now()
            c.execute("INSERT INTO POSTS(Date, UID, POST_NUM) VALUES(?, ?, ?)", 
                ("%s, %s" % (date.today(), current.strftime("%H:%M:%S")), 
                session['UID'], 
                new_post_num)
            )

            c.execute("UPDATE USERS SET LAST_POST_NUM=LAST_POST_NUM+1 WHERE UID=?", (session['UID'], ))
            db.commit()
            db.close()
            return redirect("/")
        else:
            return render_template("new_entry.html")
    else:
        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def make():
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

@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit(index):
    if is_logged_in():
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
        c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID=?", (session['UID'],))
        #select last_post_num so index can be used as offset from last
        user = c.fetchone()
        if request.method == "POST":
            file = open("./blogs/{id}/{index}.txt".format(id = session['UID'], index=user[0] - index), "w")
            file.write(request.form['edit'])
            return redirect('/')
        else:
            file = open("./blogs/{id}/{index}.txt".format(id = session['UID'], index=user[0] - index), "r")
            return render_template("edit.html", text=file.read(), index=index)
    else:
        return redirect("/")

@app.route("/view")
def view():
    if is_logged_in():
        directories = []
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
        for dir in os.scandir("./blogs"):
            if (int)(dir.name) != session['UID']:
                c.execute("SELECT USERNAME FROM USERS WHERE UID=?", (dir.name,))
                directories.append(c.fetchone()[0])
        return render_template("view.html", blogs=directories)
    else:
        return redirect("/")

@app.route("/view/<username>")
def viewid(username):
    if is_logged_in():
        files = []
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
        c.execute("SELECT LAST_POST_NUM, UID FROM USERS WHERE USERNAME = ?", (username,))
        user = c.fetchone()
        for filename in range(user[0], -1, -1):
            file = open("./blogs/{id}/{filename}.txt".format(id=user[1], filename=filename))
            files.append(file.read())
        return render_template("look.html", blogs=files)
    else:
        return redirect("/")

if __name__ == "__main__":
    app.debug = True
    app.run()
