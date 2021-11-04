from flask import Flask, render_template, request, session, redirect
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.urandom(32)
@app.route("/", methods=["GET"])
def login():
    if not os.path.exists("./blogs"):
        os.mkdir("./blogs")
    if 'username' in session.keys():
        files = []
        db = sqlite3.connect("users.db")
        c = db.cursor()
        c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (session['UID'],))
        for filename in range(c.fetchone()[0], -1, -1):
            if not os.path.exists("./blogs/{id}".format(id=session['UID'])):
                os.mkdir("./blogs/{id}")
            if os.path.exists("./blogs/{id}/{filename}.txt".format(id=session['UID'], filename=filename)):
                file = open("./blogs/{id}/{filename}.txt".format(id=session['UID'], filename=filename))
            else:
                c.execute("UPDATE USERS SET LAST_POST_NUM=-1 WHERE UID=?", (session['UID'],))
                break
            files.append(file.read())
        return render_template("home.html", logged=True, blogs=files)
    else:
        db = sqlite3.connect("users.db")
        c = db.cursor()
        make_user_table = ("""CREATE TABLE IF NOT EXISTS USERS(
                UID INTEGER PRIMARY KEY NOT NULL,
                USERNAME TEXT NOT NULL,
                PASSWORD TEXT NOT NULL,
                BLOG_NAME TEXT,
                LAST_POST_NUM INTEGER,
                UNIQUE (USERNAME));""")

        c.execute(make_user_table)
        db.commit()
        db.close()
        return render_template("login.html", logged=False, blogs=[], user="", id=0, passw="")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if (request.method == "POST"):
        db = sqlite3.connect("users.db")
        c = db.cursor()
        #select the user that matches the inputed username and password
        c.execute("SELECT * FROM USERS WHERE USERNAME=? AND PASSWORD=?", (request.form['username'], request.form['password']))
        user = c.fetchone()
        #if a user was selected add the user to the session and return home
        if user != None:
            session['UID'] = user[0]
            session['username'] = user[1]
            db.close()
            return redirect("/")
        db.close()
        return render_template("error.html", msg=2)
    else:
        return redirect("/")

@app.route("/logout")
def logout():
    #clears session and returns home
    session.clear()
    return redirect("/")

@app.route("/new_entry", methods=["POST", "GET"])
def new_entry():
    if 'username' in session.keys():
        if request.method == "POST":
            db = sqlite3.connect("users.db")
            c = db.cursor()
            c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (session['UID'],))
            file = open("./blogs/{id}/{text}.txt".format(id=session['UID'], text=(c.fetchone()[0] + 1)), "w")
            c.execute("UPDATE USERS SET LAST_POST_NUM=LAST_POST_NUM+1 WHERE UID=?", (session['UID'],))
            file.write(request.form['new_entry'])
            file.close()
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
        db = sqlite3.connect("users.db")
        c = db.cursor()
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
    if 'username' in session.keys():
        if request.method == "POST":
            db = sqlite3.connect("users.db")
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
    if 'username' in session.keys():
        db = sqlite3.connect("users.db")
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
    if 'username' in session.keys():
        directories = []
        db = sqlite3.connect("users.db")
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
    if 'username' in session.keys():
        files = []
        db = sqlite3.connect("users.db")
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
