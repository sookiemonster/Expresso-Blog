from flask import Flask, render_template, request, session, redirect
import os, sqlite3

# FILE & TABLES
USER_TABLE = "USERS"
DB_FILE = "users.db"

# DB ROW INDEXING
UID = 0
USERNAME = 1
LAST_POST_NUM = 2

app = Flask(__name__)
app.secret_key = os.urandom(32)

def is_logged_in():
    return bool(session.get('username')) == True

@app.route("/", methods=["GET"])
def home():
    if is_logged_in():
        return render_template("home.html") # Render home if user is logged in
    return render_template("login.html") # Render login page if not logged in

@app.route("/auth", methods=["GET", "POST"])
def auth():
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    make_user_table = """CREATE TABLE IF NOT EXISTS %s(
                UID INTEGER PRIMARY KEY NOT NULL,
                USERNAME TEXT NOT NULL,
                PASSWORD TEXT NOT NULL,
                BLOG_NAME TEXT
                LAST_POST_NUM INTEGER, 
                UNIQUE (USERNAME));""" % (USER_TABLE)
                
    c.execute(make_user_table)
    
    client_username = request.form['username']
    client_password = request.form['password']

    c.execute("SELECT * FROM %s WHERE username=? AND password=?" % (USER_TABLE), (client_username, client_password))
    user_info = c.fetchone()
    
    if user_info != None:
        session['username'] = user_info[USERNAME]
        db.close()
        return redirect("/")
    db.close()
    return render_template("error.html", msg=1)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/my_blog", methods=["GET"])
def user_blog():
    # Retrieve & render user's blog if they are logged in
    if is_logged_in():
        files = []
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        get_UID = "SELECT UID FROM %s WHERE USERNAME = %s" % (USER_TABLE, session['username'])
        c.execute(get_UID)
        uid = c.fetchone()

        get_last_post_num = "SELECT LAST_POST_NUM FROM %s WHERE id = %s" % (USER_TABLE, uid)
        c.execute(get_last_post_num)
        last_post_num = c.fetchone()

        for post_num in range(last_post_num, -1, -1): # Descend from the last post to 0
            post = open("./blogs/%s/%s.txt".format(uid, post_num))
            files.append(post.read())

        return render_template("home.html", blogs=files)
    else:
        return redirect("/")
    
@app.route("/new_entry", methods=["POST", "GET"])
def new_entry():
    if is_logged_in():
        if request.method == "POST":
            db = sqlite3.connect(DB_FILE)
            c = db.cursor()

            get_UID = "SELECT UID FROM ? WHERE USERNAME = ?", (USER_TABLE, session['username'])
            c.execute(get_UID)
            uid = c.fetchone()

            get_last_post_num = "SELECT LAST_POST_NUM FROM ? WHERE UID = ?", (USER_TABLE, uid)
            c.execute(get_last_post_num)
            last_post_num = c.fetchone()

            new_post_route = "./blogs/%s/%s.txt" % (uid, last_post_num)
            file = open(new_post_route, "w")

            c.execute("UPDATE %s SET LAST_POST_NUM=LAST_POST_NUM+1 WHERE UID = ?" % (USER_TABLE, uid))
            file.write(request.form['new_entry'])
            file.close()
            db.commit()
            db.close()
            return redirect("/my_blog")
        else:
            return render_template("new_entry.html")
    else:
        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        client_username = request.form['username']
        client_password = request.form['password']

        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        make_user_table = """CREATE TABLE IF NOT EXISTS %s(
            UID INTEGER PRIMARY KEY NOT NULL,
            USERNAME TEXT NOT NULL,
            PASSWORD TEXT NOT NULL,
            BLOG_NAME TEXT
            LAST_POST_NUM INTEGER, 
            UNIQUE (USERNAME));""" % (USER_TABLE)
            
        c.execute(make_user_table)

        # list_users = 

        try:
            # Add user credentials to database
            c.execute("INSERT INTO %s(USERNAME, PASSWORD) VALUES(?, ?)" % (USER_TABLE), 
                (client_username, client_password))
            
            # Select newly created user
            c.execute("SELECT * FROM %s WHERE USERNAME=? AND PASSWORD=?" % (USER_TABLE), 
                (client_username, client_password))

            new_user = c.fetchone()
            os.makedirs("./blogs/%s" % (new_user[0])) # Create a blog directory to store new user's files
        except sqlite3.IntegrityError:
            return render_template("register.html", taken=True)
        db.commit()
        db.close()
        return redirect("/")
    else:
        return render_template("register.html", taken=False)


@app.route("/edit/<int:post_num>", methods=["GET", "POST"])
def edit(post_num):
    if is_logged_in():
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        get_UID = "SELECT UID FROM %s WHERE USERNAME = ?" % (USER_TABLE), (session['username'])
        c.execute(get_UID)
        uid = c.fetchone()

        get_last_post_num = "SELECT LAST_POST_NUM FROM %s WHERE UID = ?" % (USER_TABLE), (uid)
        c.execute(get_last_post_num)
        last_post_num = c.fetchone()

        if request.method == "POST":
            file = open("./blogs/%s/%s.txt".format(uid, post_num), "w")
            file.write(request.form['edit'])
            return redirect('/')
        else:
            file = open("./blogs/%s/%s.txt" % (uid, post_num), "r")
            return render_template("edit.html", text=file.read(), index=post_num)
    else:
        redirect("/")

if __name__ == "__main__":
    app.debug = True
    app.run()
