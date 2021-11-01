from flask import Flask, render_template, request, session, redirect
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.urandom(32)
@app.route("/", methods=["GET"])
def login():
    if 'username' in session.keys() and 'password' in session.keys():
        files = []
        db = sqlite3.connect("users.db")
        c = db.cursor()
        c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (session['UID'],))
        for filename in range(c.fetchone()[0], -1, -1):
            file = open("./blogs/{id}/{filename}.txt".format(id=session['UID'], filename=filename))
            files.append(file.read())
        return render_template("home.html", logged=True, blogs=files, user=session['username'], id=session['UID'], passw=session['password'])
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
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("SELECT * FROM USERS WHERE USERNAME=? AND PASSWORD=?", (request.form['username'], request.form['password']))
    user = c.fetchone()
    if user != None:
        session['UID'] = user[0]
        session['username'] = user[1]
        session['password'] = user[2]
        db.close()
        return redirect("/")
    db.close()
    return render_template("error.html", msg=1)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/new_entry", methods=["POST", "GET"])
def new_entry():
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


@app.route("/register", methods=["GET", "POST"])
def make():
    if request.method == "POST":
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
        except sqlite3.IntegrityError:
            return render_template("register.html", taken=True)
        db.commit()
        db.close()
        return redirect("/")
    else:
        return render_template("register.html", taken=False)
@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit(index):
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID=?", (session['UID'],))
    user = c.fetchone()
    if request.method == "POST":
        file = open("./blogs/{id}/{index}.txt".format(id = session['UID'], index=user[0] - index), "w")
        file.write(request.form['edit'])
        return redirect('/')
    else:
        file = open("./blogs/{id}/{index}.txt".format(id = session['UID'], index=user[0] - index), "r")
        return render_template("edit.html", text=file.read(), index=index)
@app.route("/view")
def view():
    directories = []
    for dir in os.scandir("./blogs/"):
        directories.append(dir)
    return render_template("view.html", items=directories)
@app.route("/view/<int:UID>")
def viewid(UID):
    files = []
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (session['UID'],))
    for filename in range(c.fetchone()[0], -1, -1):
        file = open("./blogs/{id}/{filename}.txt".format(id=session['UID'], filename=filename))
        files.append(file.read())
    return render_template("look.html", items=files)

if __name__ == "__main__":
    app.debug = True
    app.run()
