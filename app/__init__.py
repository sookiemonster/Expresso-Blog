from flask import Flask, render_template, request, session
import sqlite3

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    '''
    db = sqlite3.connect("users.db")
    c = db.cursor()
    if 'username' in session.keys() and 'password' in session.keys():
        c.execute("SELECT * FROM USER WHERE username=? AND password=?", (session['username'], session['password']))
        user = c.fetchone()
        if user != None:
            print("It got here")
            #only if the code was right will we send them to success.html
            return render_template("success.html", 
                username = session['username'], 
                password = session['password'])
                '''
    
        
    return render_template("start.html")
@app.route("/auth", methods=["GET", "POST"])
def auth():
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("SELECT * FROM USER WHERE username=? AND password=?", (request.form['username'], request.form['password']))
    user = c.fetchone()
    if user != None:
        return render_template("response.html")
    return render_template("failure.html")
@app.route("/make_account", methods=["GET", "POST"])
def make():
    db = sqlite3.connect("users.db")
    c = db.cursor()
    try:
        c.execute("INSERT INTO user(username, password) VALUES(?, ?)", (request.form['username'], request.form['password']))
    except sqlite3.IntegrityError:
        return render_template("failure.html")
    db.commit()
    db.close()
    return render_template("login.html")

if __name__ == "__main__":
    app.debug = True
    app.run()
