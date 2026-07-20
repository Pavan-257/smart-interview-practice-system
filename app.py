import os

import random

from datetime import date

from flask import (Flask, render_template, request, redirect, session, send_file, flash)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection, create_table, save_result
from question_bank import (
    HR_QUESTIONS,
    TECHNICAL_QUESTIONS,
    APTITUDE_QUESTIONS
)
from session_data import interview_data
from ai_evaluator import evaluate_answers
from utils import generate_otp, send_otp
from otp import otp_storage, forgot_password_otp
from pdf_report import generate_pdf
from resume_analyzer import extract_resume_text
from gemini_resume import analyze_resume
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
UPLOAD_FOLDER = "static/profile_pictures"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.getenv("SECRET_KEY", "smart_interview_secret")
RESUME_FOLDER = "uploads"

app.config["RESUME_FOLDER"] = RESUME_FOLDER
REPORT_FOLDER = os.path.join(app.root_path, "reports")
os.makedirs(REPORT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]


        conn = get_connection()
        cursor = conn.cursor()

        # -----------------------------
        # Check Admin Login
        # -----------------------------
        cursor.execute(
            "SELECT * FROM admin WHERE username=?",
            (email,)
        )

        admin = cursor.fetchone()

        if admin and check_password_hash(admin["password"], password):

            conn.close()

            session.clear()
            session["admin"] = admin["username"]

            return redirect("/admin-dashboard")

        # -----------------------------
        # Check Normal User Login
        # -----------------------------
        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        print("User Found :", user)

        if user:
            print("User Found :", user)
            print("Stored Hash :", user["password"])
            print("Entered Password :", password)
            print("Password Match :", check_password_hash(user["password"], password))

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
            return redirect("/dashboard")
        
        conn.close()

        return "Invalid Email or Password"

    return render_template("login.html")
@app.route("/dashboard")
def dashboard():

    user = session.get("username")

    if not user:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (user,)
    )

    current_user = cursor.fetchone()

    cursor.execute("""
        SELECT interview_type,
               score,
               interview_date
        FROM interview_results
        WHERE username=?
        ORDER BY interview_date DESC
    """, (user,))

    history = cursor.fetchall()

    # ---------------- Dashboard Statistics ----------------

    scores = []

    hr_count = 0
    technical_count = 0
    aptitude_count = 0

    last_interview_date = "No Interviews"

    for row in history:

        try:
            score = int(str(row["score"]).replace("%", "").strip())
            scores.append(score)
        except ValueError:
            pass

        interview = row["interview_type"].lower()

        if "hr" in interview:
            hr_count += 1

        elif "technical" in interview:
            technical_count += 1

        elif "aptitude" in interview:
            aptitude_count += 1

    if history:
        last_interview_date = history[0]["interview_date"]

    total_interviews = len(history)

    average_score = round(sum(scores) / len(scores), 1) if scores else 0

    best_score = max(scores) if scores else 0

    lowest_score = min(scores) if scores else 0

    total_reports = len(history)

    conn.close()

    return render_template(
        "dashboard.html",
        name=current_user["name"],
        history=history,

        total_interviews=total_interviews,
        average_score=average_score,
        best_score=best_score,
        lowest_score=lowest_score,

        total_reports=total_reports,

        hr_count=hr_count,
        technical_count=technical_count,
        aptitude_count=aptitude_count,

        last_interview_date=last_interview_date
    )

@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    # Total Users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Total Interviews
    cursor.execute("SELECT COUNT(*) FROM interview_results")
    total_interviews = cursor.fetchone()[0]

    # Average Score
    cursor.execute("SELECT score FROM interview_results")

    scores = []

    for row in cursor.fetchall():

        try:
            scores.append(
                int(str(row["score"]).replace("%", "").strip())
            )
        except ValueError:
            pass

    average_score = round(sum(scores) / len(scores), 1) if scores else 0
    # Highest Score
    highest_score = max(scores) if scores else 0

    # Lowest Score
    lowest_score = min(scores) if scores else 0

    # Total Reports
    total_reports = total_interviews

    # Active Users
    cursor.execute("""
    SELECT COUNT(DISTINCT username)
    FROM interview_results
    """)

    active_users = cursor.fetchone()[0]

    # Today's Interviews
    today = date.today().isoformat()

    cursor.execute("""
    SELECT COUNT(*)
    FROM interview_results
    WHERE DATE(interview_date)=?
    """, (today,))

    today_interviews = cursor.fetchone()[0]

    # Interview Distribution
    cursor.execute("""
    SELECT interview_type,
    COUNT(*) AS total
    FROM interview_results
    GROUP BY interview_type
    """)

    interview_types = cursor.fetchall()

    labels = []
    values = []

    for row in interview_types:
        labels.append(row["interview_type"])
        values.append(row["total"])

    # User List
    search = request.args.get("search", "")

    if search:

        cursor.execute("""
        SELECT
            id,
            name,
            email,
            mobile,
            username,
            age
        FROM users

        WHERE

        name LIKE ?
        OR email LIKE ?
        OR username LIKE ?
        OR mobile LIKE ?

        ORDER BY id DESC
    """,

    (
        f"%{search}%",
        f"%{search}%",
        f"%{search}%",
        f"%{search}%"
    ))

    else:

        cursor.execute("""
        SELECT
            id,
            name,
            email,
            mobile,
            username,
            age
        FROM users
        ORDER BY id DESC
    """)

    users = cursor.fetchall()

    # -----------------------------
    # Latest Interview Scores
    # -----------------------------
    cursor.execute("""
    SELECT username, score
    FROM interview_results
    ORDER BY interview_date DESC
    LIMIT 10
    """)

    score_data = cursor.fetchall()

    score_labels = []
    score_values = []

    for row in score_data:

        score_labels.append(row["username"])

        try:
           score_values.append(
            int(str(row["score"]).replace("%", "").strip())
           )
        except ValueError:
            score_values.append(0)
    # Recent Activity
    cursor.execute("""
    SELECT
        username,
        interview_type,
        score,
        interview_date
    FROM interview_results
    ORDER BY interview_date DESC
    LIMIT 10
    """)

    recent_activity = cursor.fetchall()
    conn.close()

    return render_template(
    "admin_dashboard.html",

    total_users=total_users,
    total_interviews=total_interviews,
    average_score=average_score,
    highest_score=highest_score,
    lowest_score=lowest_score,
    total_reports=total_reports,
    today_interviews=today_interviews,
    active_users=active_users,
    users=users,
    search=search,
    labels=labels,
    values=values,
    score_labels=score_labels,
    score_values=score_values,
    recent_activity=recent_activity
)
@app.route("/admin/user/<int:user_id>")
def admin_view_user(user_id):

    if "admin" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    # User details
    cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    # Interview history
    cursor.execute("""
        SELECT
            interview_type,
            score,
            feedback,
            interview_date
        FROM interview_results
        WHERE username=?
        ORDER BY interview_date DESC
    """, (user["username"],))

    interviews = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_user.html",
        user=user,
        interviews=interviews
    )
@app.route("/admin/delete-user/<int:user_id>")
def delete_user(user_id):

    if "admin" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    # Get username before deleting
    cursor.execute(
        "SELECT username FROM users WHERE id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user:

        username = user["username"]

        # Delete interview history
        cursor.execute(
            "DELETE FROM interview_results WHERE username=?",
            (username,)
        )

        # Delete user
        cursor.execute(
            "DELETE FROM users WHERE id=?",
            (user_id,)
        )

        conn.commit()

    conn.close()

    return redirect("/admin-dashboard")

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "username" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    username = session["username"]

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        email = request.form["email"]
        age = request.form["age"]

        cursor.execute("""
            UPDATE users
            SET
                name=?,
                mobile=?,
                email=?,
                age=?
            WHERE username=?
        """, (name, mobile, email, age, username))

        conn.commit()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "username" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    username = session["username"]

    # Get current user information
    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        age = request.form["age"]

        filename = user["profile_picture"]

        picture = request.files.get("profile_picture")

        if picture and picture.filename != "":

            filename = secure_filename(picture.filename)

            picture.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        cursor.execute("""
            UPDATE users
            SET
                name=?,
                email=?,
                mobile=?,
                age=?,
                profile_picture=?
            WHERE username=?
        """,
        (
            name,
            email,
            mobile,
            age,
            filename,
            username
        ))

        conn.commit()

        return redirect("/profile")

    conn.close()

    return render_template(
        "edit_profile.html",
        user=user
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        email = request.form["email"]
        age = int(request.form["age"])
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        print("\n===== REGISTER REQUEST =====")
        print("Name     :", name)
        print("Mobile   :", mobile)
        print("Email    :", email)
        print("Username :", username)
        print("============================\n")
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? OR username=?",
            (email, username)
        )

        existing_user = cursor.fetchone()
        print("Database result:", existing_user)
        conn.close()

        if existing_user:
            return "Email or Username already exists."

        if age < 18 or age > 60:
            return "Age must be between 18 and 60"

        if password != confirm_password:
            return "Passwords do not match"
        hashed_password = generate_password_hash(password)

        otp = generate_otp()

        otp_storage[email] = {
            "otp": otp,
            "user_data": {
                "name": name,
                "mobile": mobile,
                "email": email,
                "age": age,
                "username": username,
                "password": hashed_password
            }
        }

        send_otp(email, otp)

        session["otp_email"] = email

        return redirect("/verify-otp")

    return render_template("register.html")
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if request.method == "POST":

        otp = request.form["otp"]

        # Get the latest email stored
        email = session.get("otp_email")

        if not email:
            return "OTP Session Expired. Please register again."

        print("Entered OTP :", otp)
        print("Stored OTP  :", otp_storage[email]["otp"])
        print("Email       :", email)
        if otp_storage[email]["otp"] == otp:

            user = otp_storage[email]["user_data"]

            try:
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO users
                (name, mobile, email, age, username, password)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user["name"],
                    user["mobile"],
                    user["email"],
                    user["age"],
                    user["username"],
                    user["password"]
                ))

                conn.commit()

            except Exception as e:
                return str(e)

            finally:
                conn.close()

            del otp_storage[email]

            return redirect("/")

        return "Invalid OTP"

    return render_template("verify_otp.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if not user:
            return "Email not registered."

        otp = generate_otp()

        forgot_password_otp[email] = otp

        session["reset_email"] = email

        send_otp(email, otp)

        return redirect("/reset-password")

    return render_template("forgot_password.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if request.method == "POST":

        otp = request.form["otp"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            return "Passwords do not match."

        email = session.get("reset_email")

        if not email:
            return "Session expired."

        print("Session Email :", email)
        print("Entered OTP  :", otp)
        print("Stored OTP   :", forgot_password_otp.get(email))

        if forgot_password_otp.get(email) != otp:
            return "Invalid OTP."

        conn = get_connection()
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)

        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hashed_password, email)
        )

        conn.commit()
        conn.close()

        del forgot_password_otp[email]
        session.pop("reset_email", None)

        return redirect("/")

    return render_template("reset_password.html")

@app.route("/hr-interview", methods=["GET", "POST"])
def hr_interview():

    user = session.get("username")

    if not user:
        return redirect("/")

    if user not in interview_data:

        questions = HR_QUESTIONS[1:]
        random.shuffle(questions)

        interview_data[user] = {
            "questions": [HR_QUESTIONS[0]] + questions,
            "current": 0,
            "answers": []
        }

    data = interview_data[user]

    # Safety check
    if data["current"] >= len(data["questions"]):
        del interview_data[user]
        return redirect("/dashboard")

    if request.method == "POST":

       answer = request.form.get("answer", "").strip()

    if answer == "":
        data["answers"].append("NO_ANSWER")
    else:
        data["answers"].append(answer)
        data["current"] += 1

        if data["current"] >= len(data["questions"]):

            result = evaluate_answers(
                data["questions"],
                data["answers"]
            )

            save_result(
                user,
                "HR Interview",
                result["score"],
                result["feedback"]
            )

            os.makedirs(REPORT_FOLDER, exist_ok=True)

            filename = os.path.join(
                REPORT_FOLDER,
                f"{user}_HR_Report.pdf"
            )

            generate_pdf(
                filename,
                user,
                "HR Interview",
                result["score"],
                result["feedback"]
            )

            del interview_data[user]

            return render_template(
                "result.html",
                score=result["score"],
                feedback=result["feedback"],
                filename=f"{user}_HR_Report.pdf"
            )

    if data["current"] >= len(data["questions"]):
        return redirect("/dashboard")

    return render_template(
    "hr_interview.html",
    question=data["questions"][data["current"]],
    number=data["current"] + 1,
    total=len(data["questions"])
)
@app.route("/technical-interview", methods=["GET", "POST"])
def technical_interview():

    user = session.get("username")

    if not user:
        return redirect("/")

    from session_data import technical_data

    if user not in technical_data:

        questions = TECHNICAL_QUESTIONS[:]
        random.shuffle(questions)

        technical_data[user] = {
            "questions": questions,
            "current": 0,
            "answers": []
        }

    data = technical_data[user]

    if data["current"] >= len(data["questions"]):
        del technical_data[user]
        return redirect("/dashboard")

    if request.method == "POST":

        answer = request.form["answer"]

        data["answers"].append(answer)

        data["current"] += 1

        if data["current"] >= len(data["questions"]):

            result = evaluate_answers(
                data["questions"],
                data["answers"]
            )

            save_result(
                user,
                "Technical Interview",
                result["score"],
                result["feedback"]
            )

            os.makedirs(REPORT_FOLDER, exist_ok=True)

            filename = os.path.join(
                REPORT_FOLDER,
                f"{user}_Technical_Report.pdf"
            )

            generate_pdf(
                filename,
                user,
                "Technical Interview",
                result["score"],
                result["feedback"]
            )

            del technical_data[user]

            return render_template(
                "result.html",
                score=result["score"],
                feedback=result["feedback"],
                filename=f"{user}_Technical_Report.pdf"
            )

    if data["current"] >= len(data["questions"]):
        return redirect("/dashboard")

    return render_template(
    "technical_interview.html",
    question=data["questions"][data["current"]],
    number=data["current"] + 1,
    total=len(data["questions"])
)

@app.route("/aptitude-interview", methods=["GET", "POST"])
def aptitude_interview():

    user = session.get("username")
    if not user:
        return redirect("/")

    from session_data import aptitude_data

    if user not in aptitude_data:

        questions = APTITUDE_QUESTIONS[:]
        random.shuffle(questions)

        aptitude_data[user] = {
            "questions": questions,
            "current": 0,
            "answers": []
        }

    data = aptitude_data[user]
    if data["current"] >= len(data["questions"]):
        del aptitude_data[user]
        return redirect("/dashboard")

    if request.method == "POST":

        answer = request.form["answer"]

        data["answers"].append(answer)

        data["current"] += 1

        if data["current"] >= len(data["questions"]):

            result = evaluate_answers(
                data["questions"],
                data["answers"]
            )

            save_result(
                user,
                "Aptitude Interview",
                result["score"],
                result["feedback"]
            )

            filename = os.path.join(
                REPORT_FOLDER,
                f"{user}_Aptitude_Report.pdf"
            )

            generate_pdf(
                filename,
                user,
                "Aptitude Interview",
                result["score"],
                result["feedback"]
            )

            session["last_report"] = filename
            del aptitude_data[user]

            return render_template(
                "result.html",
                score=result["score"],
                feedback=result["feedback"],
                filename=f"{user}_Aptitude_Report.pdf"
            )

    if data["current"] >= len(data["questions"]):
        return redirect("/dashboard")

    return render_template(
    "aptitude_interview.html",
    question=data["questions"][data["current"]],
    number=data["current"] + 1,
    total=len(data["questions"])
)
@app.route("/download-report/<filename>")
def download_report(filename):

    filepath = os.path.join(REPORT_FOLDER, filename)

    if not os.path.exists(filepath):
        return "Report not found."

    return send_file(
        filepath,
        as_attachment=True
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/analytics")
def analytics():

    user = session.get("username")

    if not user:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT interview_type,
               score,
               interview_date
        FROM interview_results
        WHERE username=?
        ORDER BY interview_date DESC
    """, (user,))

    results = cursor.fetchall()

    scores = []

    for row in results:
        try:
            score = int(str(row["score"]).replace("%", "").strip())
            scores.append(score)
        except ValueError:
            pass

    total_interviews = len(results)

    average_score = round(sum(scores)/len(scores),2) if scores else 0

    highest_score = max(scores) if scores else 0

    lowest_score = min(scores) if scores else 0

    conn.close()

    labels = []
    chart_scores = []

    for row in results:
        labels.append(row["interview_type"])

        try:
           chart_scores.append(
            int(str(row["score"]).replace("%", "").strip())
            )
        except:
          chart_scores.append(0)

    return render_template(
        "analytics.html",
        results=results,
        total_interviews=total_interviews,
        average_score=average_score,
        highest_score=highest_score,
        lowest_score=lowest_score,
        labels=labels,
        chart_scores=chart_scores
    )

@app.route("/resume", methods=["GET", "POST"])
def resume():

    if "username" not in session:
        return redirect("/")

    resume_text = ""
    resume_score = 0
    skills_found = []
    ai_report = ""

    if request.method == "POST":

        file = request.files["resume"]

        if file.filename != "":

            filename = secure_filename(file.filename)

            filepath = os.path.join(
                app.config["RESUME_FOLDER"],
                filename
            )

            file.save(filepath)

            resume_text = extract_resume_text(filepath)
            
            ai_report = analyze_resume(resume_text)
            skills_database = [

                "python",
                "java",
                "c",
                "c++",
                "html",
                "css",
                "javascript",
                "flask",
                "sql",
                "sqlite",
                "mysql",
                "machine learning",
                "artificial intelligence",
                "nlp",
                "data structures",
                "algorithms",
                "git",
                "github"
            ]

            for skill in skills_database:

                if skill.lower() in resume_text.lower():
                    skills_found.append(skill)

            resume_score = min(len(skills_found) * 5 + 20, 100)

    return render_template(
    "resume.html",
    score=resume_score,
    skills=skills_found,
    resume_text=resume_text,
    ai_report=ai_report
    )

if __name__ == "__main__":
    create_table()
    app.run(host="0.0.0.0", port=5000, debug=True) 