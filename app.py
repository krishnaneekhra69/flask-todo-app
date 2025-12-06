from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret123")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST", os.getenv("DB_HOST", "localhost")),
        user=os.getenv("MYSQLUSER", os.getenv("DB_USER", "root")),
        password=os.getenv("MYSQLPASSWORD", os.getenv("DB_PASSWORD", "8839")),
        database=os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", "todoapp")),
        port=os.getenv("MYSQLPORT", 3306)
    )

# ----------------- Index -----------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM todos WHERE user_id=%s ORDER BY created_at DESC", (session["user_id"],))
    todos = cur.fetchall()
    conn.close()
    return render_template("index.html", todos=todos)

# ----------------- Register -----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"].lower()
        password = generate_password_hash(request.form["password"])
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", 
                        (name, email, password))
            conn.commit()
            flash("Registration successful!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash("Error: " + str(e), "danger")
        finally:
            conn.close()
    return render_template("register.html")

# ----------------- Login -----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out!", "info")
    return redirect(url_for("login"))

# ----------------- Add Todo -----------------
@app.route("/add", methods=["GET", "POST"])
def add():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description", "")
        created_at = datetime.now()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO todos (user_id, title, description, created_at, done) VALUES (%s, %s, %s, %s, %s)",
                    (session["user_id"], title, description, created_at, 0))
        conn.commit()
        conn.close()
        flash("Todo added!", "success")
        return redirect(url_for("index"))
    return render_template("add.html")

# ----------------- Edit Todo -----------------
@app.route("/edit/<int:todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM todos WHERE id=%s AND user_id=%s", (todo_id, session["user_id"]))
    todo = cur.fetchone()
    if not todo:
        conn.close()
        flash("Todo not found!", "danger")
        return redirect(url_for("index"))
    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description", "")
        done = 1 if request.form.get("done") == "on" else 0
        cur.execute("UPDATE todos SET title=%s, description=%s, done=%s WHERE id=%s",
                    (title, description, done, todo_id))
        conn.commit()
        conn.close()
        flash("Todo updated!", "success")
        return redirect(url_for("index"))
    conn.close()
    return render_template("edit.html", todo=todo)

# ----------------- Delete Todo -----------------
@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM todos WHERE id=%s AND user_id=%s", (todo_id, session["user_id"]))
    conn.commit()
    conn.close()
    flash("Todo deleted!", "success")
    return redirect(url_for("index"))

# ----------------- Toggle Done -----------------
@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT done FROM todos WHERE id=%s AND user_id=%s", (todo_id, session["user_id"]))
    todo = cur.fetchone()
    if todo:
        new_status = 0 if todo["done"] else 1
        cur.execute("UPDATE todos SET done=%s WHERE id=%s", (new_status, todo_id))
        conn.commit()
    conn.close()
    return redirect(url_for("index"))

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
