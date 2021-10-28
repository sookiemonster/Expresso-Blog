from flask import Flask, render_template, request, session, redirect
import sqlite3

app = Flask(__name__)
@app.route("/", methods=["GET"])
def login():
    return render_template("home.html", logged=False)

@app.route("/<id>/<username>/<password>", methods=["GET"])
def index(id, username, password):
    return render_template("home.html", logged=True)
    
@app.route("/auth", methods=["GET", "POST"])
def auth():
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("SELECT * FROM USER WHERE username=? AND password=?", (request.form['username'], request.form['password']))
    user = c.fetchone()
    if user != None:
        return redirect("/<{id}>/<{username}>/<{password}>".format(id=user[0], username=user[1], password=user[2]))
    return render_template("error.html")

@app.route("/register", methods=["GET", "POST"])
def make():
    if request.method == "POST":
        db = sqlite3.connect("users.db")
        c = db.cursor()
        try:
            c.execute("INSERT INTO user(username, password, blog_name) VALUES(?, ?, ?)", (request.form['username'], request.form['password'], request.form['display']))
        except sqlite3.IntegrityError:
            return render_template("register.html", taken=True)
        db.commit()
        db.close()
        return redirect("/")
    else:
        return render_template("register.html", taken=False)

if __name__ == "__main__":
    app.debug = True
    app.run()
