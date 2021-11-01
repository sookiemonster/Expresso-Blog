from flask import Flask, render_template, request, session, redirect
import os, sqlite3

# FILENAMES
DB_FILE = "users.db"

# CREATE USERS 
make_user_table = """CREATE TABLE IF NOT EXISTS USERS(
                UID INTEGER PRIMARY KEY NOT NULL,
                USERNAME TEXT NOT NULL,
                PASSWORD TEXT NOT NULL,
                BLOG_NAME TEXT,
                LAST_POST_NUM INTEGER, 
                UNIQUE (USERNAME));"""

# DB ROW INDEXING
UID = 0
USERNAME = 1
LAST_POST_NUM = 2

app = Flask(__name__)
app.secret_key = os.urandom(32)

def is_logged_in():
    """Returns whether a user is logged in or not."""
    return bool(session.get('id')) == True

#NOT WORKING RIGHT NOW
# def column_is_empty(cursor, user_id, column):
#     """Returns whether a specified database column is empty"""
#     cursor.execute("SELECT UID FROM USERS WHERE UID = ? AND '%s' IS NULL" % (column), (user_id, ))
#     return bool(cursor.fetchone())

def get_username(cursor, user_id): 
    """Returns the username of a given user_id"""
    cursor.execute("SELECT USERNAME FROM USERS WHERE UID = ?", (user_id, )) # Comma is needed after user_id (creates a single element tuple)
    return cursor.fetchone()

def get_last_post_num(cursor, user_id):
    """Returns the last post number of a given user_id"""
    cursor.execute("SELECT LAST_POST_NUM FROM USERS WHERE UID = ?", (user_id, )) # Comma is needed after user_id (creates a single element tuple)
    return cursor.fetchone()[0] #Get the first item of the returned tuple

@app.route("/", methods=["GET"])
def home():
    if is_logged_in():
        posts = []
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        last_post_num = get_last_post_num(c, session['id'])

        for post_num in range(last_post_num, -1, -1): # Descend from the last post to 0
            post = open("./blogs/%s/%s.txt" % ((session['id']), post_num))
            posts.append(post.read()) # Append each subsequent entry to posts

        return render_template("home.html", blogs=posts) # Render home if user is logged in
    return render_template("login.html") # Render login page if not logged in

@app.route("/auth", methods=["GET", "POST"])
def auth():
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
                
    c.execute(make_user_table)
    
    client_username = request.form['username']
    client_password = request.form['password']

    c.execute("SELECT * FROM USERS WHERE username=? AND password=?", (client_username, client_password))
    user_info = c.fetchone()
    
    if user_info != None:
        session['id'] = user_info[UID]
        db.close()
        return redirect("/")
    db.close()
    return render_template("error.html", msg=1)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        client_username = request.form['username']
        client_password = request.form['password']

        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
            
        c.execute(make_user_table)

        try:
            # Add user credentials to database
            c.execute("INSERT INTO USERS(USERNAME, PASSWORD) VALUES(?, ?)", 
                (client_username, client_password))
            
            # Select newly created user
            c.execute("SELECT * FROM USERS WHERE USERNAME=? AND PASSWORD=?", 
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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/") 

@app.route("/my_blog", methods=["GET"])
def user_blog():
    # Retrieve & render user's blog if they are logged in
    if is_logged_in():
        posts = []
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        last_post_num = get_last_post_num(c, session['id'])

        for post_num in range(last_post_num, -1, -1): # Descend from the last post to 0
            post = open("./blogs/%s/%s.txt" % ((session['id']), post_num))
            posts.append(post.read()) # Append each subsequent entry to posts

        return render_template("home.html", blogs=posts)
    else:
        return redirect("/") # Redirect user to login if they aren't logged in
    
@app.route("/new_entry", methods=["POST", "GET"])
def new_entry():
    if is_logged_in():
        if request.method == "POST":
            db = sqlite3.connect(DB_FILE)
            c = db.cursor()

            # print("IS EMPTY: %s" % (column_is_empty(c, session['id'], "LAST_POST_NUM")))    
            last_post_num = get_last_post_num(c, session['id'])

            if last_post_num == None:
                last_post_num = 0
                c.execute("UPDATE USERS SET LAST_POST_NUM = 0 WHERE UID = ?", (str(session['id'])))
            else: 
                last_post_num += 1
                c.execute("UPDATE USERS SET LAST_POST_NUM = LAST_POST_NUM +1  WHERE UID = ?", (str(session['id'])))

            new_post_route = "./blogs/%s/%s.txt" % (session['id'], last_post_num)
            file = open(new_post_route, "w")

            file.write(request.form['new_entry'])
            file.close()
            db.commit()
            db.close()
            return redirect("/my_blog")
        else:
            return render_template("new_entry.html")
    else:
        return redirect("/") # Redirect user to login if they aren't logged in

@app.route("/edit/<int:post_num>", methods=["GET", "POST"])
def edit(post_num):
    if is_logged_in():
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        last_post_num = get_last_post_num(c, session['id'])
        
        if request.method == "POST":
            # Update the desired blog entry with changes
            file = open("./blogs/%s/%s.txt" % (session['id'], post_num), "w")
            file.write(request.form['edit'])
            return redirect('/my_blog')
        else:
            # Prompt the user to edit the desired blog entry
            file = open("./blogs/%s/%s.txt" % (session['id'], post_num), "r")
            return render_template("edit.html", text=file.read(), index=post_num)
    else:
        redirect("/") # Redirect user to login if they aren't logged in

if __name__ == "__main__":
    app.debug = True
    app.run()
