
import os
import sqlite3
import json
import re
import secrets

from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "skill_platform.db")
)

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-production"
)

app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


# --------------------------------------------------
# COMPETENCY FRAMEWORK
# --------------------------------------------------

COMPETENCIES = {
    "Statistical": [
        "Survey Design",
        "Sampling",
        "National Accounts",
        "Price Statistics",
        "Labour Statistics",
        "Agricultural Statistics",
        "Industrial Statistics",
        "SDG Indicators",
        "Metadata Standards",
        "Data Quality"
    ],

    "Technical": [
        "Python",
        "R",
        "SQL",
        "Stata",
        "SPSS",
        "SAS",
        "GIS",
        "Data Visualization",
        "AI/ML",
        "Cloud Computing",
        "APIs",
        "Open Data"
    ],

    "Digital Governance": [
        "Cybersecurity",
        "Data Privacy",
        "Digital Signatures",
        "Government Cloud",
        "Digital Public Infrastructure"
    ],

    "Behavioural & Managerial": [
        "Leadership",
        "Communication",
        "Project Management",
        "Ethics",
        "Decision Making",
        "Change Management"
    ]
}


# --------------------------------------------------
# SAMPLE COURSE CATALOGUE
# --------------------------------------------------

COURSES = [
    (
        "Introduction to Official Statistics",
        "Statistical",
        "Survey Design",
        "Beginner",
        "iGOT catalogue (prototype)"
    ),

    (
        "Sampling Methods and Survey Design",
        "Statistical",
        "Sampling",
        "Intermediate",
        "NSSTA TPAC (sample)"
    ),

    (
        "Python for Data Analysis",
        "Technical",
        "Python",
        "Beginner",
        "iGOT catalogue (prototype)"
    ),

    (
        "SQL Fundamentals for Government Data",
        "Technical",
        "SQL",
        "Beginner",
        "iGOT catalogue (prototype)"
    ),

    (
        "Data Visualization and Dashboarding",
        "Technical",
        "Data Visualization",
        "Intermediate",
        "iGOT catalogue (prototype)"
    ),

    (
        "Introduction to Artificial Intelligence",
        "Technical",
        "AI/ML",
        "Beginner",
        "iGOT catalogue (prototype)"
    ),

    (
        "Cybersecurity Awareness for Officials",
        "Digital Governance",
        "Cybersecurity",
        "Beginner",
        "iGOT catalogue (prototype)"
    ),

    (
        "Data Privacy and Responsible Data Handling",
        "Digital Governance",
        "Data Privacy",
        "Intermediate",
        "iGOT catalogue (prototype)"
    ),

    (
        "Project Management Essentials",
        "Behavioural & Managerial",
        "Project Management",
        "Beginner",
        "NSSTA TPAC (sample)"
    ),

    (
        "Ethics in Public Service",
        "Behavioural & Managerial",
        "Ethics",
        "Beginner",
        "iGOT catalogue (prototype)"
    )
]


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def db():

    if "db" not in g:

        g.db = sqlite3.connect(DB_PATH)

        # FIX: Return rows using column names
        g.db.row_factory = sqlite3.Row

        g.db.execute("PRAGMA foreign_keys=ON")

    return g.db


@app.teardown_appcontext
def close_db(error=None):

    conn = g.pop("db", None)

    if conn is not None:
        conn.close()


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def init_db():

    with sqlite3.connect(DB_PATH) as con:

        # FIX: Required for user["id"] and other named access
        con.row_factory = sqlite3.Row

        con.executescript("""

        CREATE TABLE IF NOT EXISTS users(

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'learner',
            designation TEXT DEFAULT '',
            department TEXT DEFAULT '',
            experience INTEGER DEFAULT 0,
            qualification TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP

        );


        CREATE TABLE IF NOT EXISTS competencies(

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            skill TEXT NOT NULL,
            current_level INTEGER NOT NULL DEFAULT 1,
            target_level INTEGER NOT NULL DEFAULT 3,

            UNIQUE(user_id, skill),

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE

        );


        CREATE TABLE IF NOT EXISTS quizzes(

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source_file TEXT NOT NULL,
            questions TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE

        );


        CREATE TABLE IF NOT EXISTS results(

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            answers TEXT NOT NULL,
            completed_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(quiz_id)
            REFERENCES quizzes(id),

            FOREIGN KEY(user_id)
            REFERENCES users(id)

        );


        CREATE TABLE IF NOT EXISTS audit(

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP

        );

        """)


        # Create default administrator

        admin_user = con.execute(
            "SELECT id FROM users WHERE email=?",
            ("admin@skill.gov",)
        ).fetchone()

        if not admin_user:

            con.execute(
                """
                INSERT INTO users
                (name,email,password,role,designation,department)
                VALUES(?,?,?,?,?,?)
                """,

                (
                    "Platform Administrator",
                    "admin@skill.gov",
                    generate_password_hash("Admin@123"),
                    "admin",
                    "Administrator",
                    "DIID"
                )
            )


        # Create default learner

        learner_user = con.execute(
            "SELECT id FROM users WHERE email=?",
            ("learner@skill.gov",)
        ).fetchone()

        if not learner_user:

            con.execute(
                """
                INSERT INTO users
                (name,email,password,role,designation,department,
                experience,qualification)
                VALUES(?,?,?,?,?,?,?,?)
                """,

                (
                    "Demo Learner",
                    "learner@skill.gov",
                    generate_password_hash("Learner@123"),
                    "learner",
                    "Statistical Officer",
                    "MoSPI",
                    2,
                    "Graduate"
                )
            )


        con.commit()


        # Seed competency framework for existing learners

        learners = con.execute(
            "SELECT id FROM users WHERE role='learner'"
        ).fetchall()

        for user in learners:

            for domain, skills in COMPETENCIES.items():

                for skill in skills:

                    con.execute(
                        """
                        INSERT OR IGNORE INTO competencies
                        (user_id,domain,skill,current_level,target_level)
                        VALUES(?,?,?,?,?)
                        """,

                        (
                            user["id"],
                            domain,
                            skill,
                            1,
                            3
                        )
                    )

        con.commit()


# --------------------------------------------------
# AUDIT LOG
# --------------------------------------------------

def audit(action, details=""):

    actor = session.get("email", "system")

    db().execute(
        """
        INSERT INTO audit(actor,action,details)
        VALUES(?,?,?)
        """,

        (actor, action, details)
    )

    db().commit()


# --------------------------------------------------
# LOGIN AUTHENTICATION
# --------------------------------------------------

def login_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if not session.get("user_id"):

            return redirect(url_for("login"))

        return fn(*args, **kwargs)

    return wrapper


# --------------------------------------------------
# ROLE-BASED ACCESS CONTROL
# --------------------------------------------------

def role_required(role):

    def deco(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            if not session.get("user_id"):

                return redirect(url_for("login"))

            if session.get("role") != role:

                flash(
                    "You do not have permission to access that page.",
                    "error"
                )

                return redirect(url_for("dashboard"))

            return fn(*args, **kwargs)

        return wrapper

    return deco


# --------------------------------------------------
# GLOBAL TEMPLATE VARIABLES
# --------------------------------------------------

@app.context_processor
def inject_globals():

    return {
        "current_user": session.get("name"),
        "current_role": session.get("role")
    }


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def index():

    if session.get("user_id"):

        return redirect(url_for("dashboard"))

    return render_template("index.html")


# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        if not name or not email or len(password) < 8:

            flash(
                "Enter all details. Password must contain at least 8 characters.",
                "error"
            )

            return redirect(url_for("register"))

        try:

            cur = db().execute(
                """
                INSERT INTO users(name,email,password,role)
                VALUES(?,?,?,'learner')
                """,

                (
                    name,
                    email,
                    generate_password_hash(password)
                )
            )

            uid = cur.lastrowid

            for domain, skills in COMPETENCIES.items():

                for skill in skills:

                    db().execute(
                        """
                        INSERT INTO competencies
                        (user_id,domain,skill,current_level,target_level)
                        VALUES(?,?,?,?,?)
                        """,

                        (
                            uid,
                            domain,
                            skill,
                            1,
                            3
                        )
                    )

            db().commit()

            audit("REGISTER", email)

            flash(
                "Account created. Please sign in.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash(
                "That email address is already registered.",
                "error"
            )

    return render_template("register.html")


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        user = db().execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and check_password_hash(
            user["password"],
            request.form.get("password", "")
        ):

            session.clear()

            session.update(
                user_id=user["id"],
                name=user["name"],
                email=user["email"],
                role=user["role"]
            )

            audit("LOGIN", email)

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
@login_required
def logout():

    audit("LOGOUT")

    session.clear()

    return redirect(url_for("index"))


# --------------------------------------------------
# LEARNER DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    uid = session["user_id"]

    rows = db().execute(
        """
        SELECT *
        FROM competencies
        WHERE user_id=?
        ORDER BY domain,skill
        """,

        (uid,)
    ).fetchall()

    total = len(rows)

    gaps = sum(
        1 for r in rows
        if r["current_level"] < r["target_level"]
    )

    avg = (
        round(
            sum(r["current_level"] for r in rows) / total,
            1
        )
        if total else 0
    )

    recent = db().execute(
        """
        SELECT r.*,q.title
        FROM results r
        JOIN quizzes q ON q.id=r.quiz_id
        WHERE r.user_id=?
        ORDER BY r.completed_at DESC
        LIMIT 5
        """,

        (uid,)
    ).fetchall()

    return render_template(
        "dashboard.html",
        rows=rows,
        total=total,
        gaps=gaps,
        avg=avg,
        recent=recent
    )


# --------------------------------------------------
# LEARNER PROFILE
# --------------------------------------------------

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    user = db().execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    if request.method == "POST":

        try:

            experience = max(
                0,
                int(request.form.get("experience", 0) or 0)
            )

        except ValueError:

            experience = 0

        db().execute(
            """
            UPDATE users
            SET designation=?,
                department=?,
                experience=?,
                qualification=?
            WHERE id=?
            """,

            (
                request.form.get("designation", ""),
                request.form.get("department", ""),
                experience,
                request.form.get("qualification", ""),
                session["user_id"]
            )
        )

        db().commit()

        audit(
            "PROFILE_UPDATE",
            "Profile details updated"
        )

        flash(
            "Profile updated.",
            "success"
        )

        return redirect(url_for("profile"))

    return render_template(
        "profile.html",
        user=user
    )


# --------------------------------------------------
# COMPETENCY ASSESSMENT
# --------------------------------------------------

@app.route("/assessment", methods=["GET", "POST"])
@login_required
def assessment():

    uid = session["user_id"]

    if request.method == "POST":

        rows = db().execute(
            "SELECT id FROM competencies WHERE user_id=?",
            (uid,)
        ).fetchall()

        for row in rows:

            try:

                val = int(
                    request.form.get(str(row["id"]), 1)
                )

            except (TypeError, ValueError):

                val = 1

            val = max(1, min(5, val))

            db().execute(
                """
                UPDATE competencies
                SET current_level=?
                WHERE id=? AND user_id=?
                """,

                (
                    val,
                    row["id"],
                    uid
                )
            )

        db().commit()

        audit(
            "COMPETENCY_ASSESSMENT",
            "Self-assessment submitted"
        )

        flash(
            "Competency assessment saved and skill gaps recalculated.",
            "success"
        )

        return redirect(url_for("gaps"))

    rows = db().execute(
        """
        SELECT *
        FROM competencies
        WHERE user_id=?
        ORDER BY domain,skill
        """,

        (uid,)
    ).fetchall()

    return render_template(
        "assessment.html",
        rows=rows,
        domains=COMPETENCIES
    )


# --------------------------------------------------
# SKILL GAP ANALYSIS
# --------------------------------------------------

@app.route("/gaps")
@login_required
def gaps():

    rows = db().execute(
        """
        SELECT *
        FROM competencies
        WHERE user_id=?
        ORDER BY domain,skill
        """,

        (session["user_id"],)
    ).fetchall()

    gap_rows = [
        r for r in rows
        if r["current_level"] < r["target_level"]
    ]

    return render_template(
        "gaps.html",
        rows=gap_rows,
        all_rows=rows
    )


# --------------------------------------------------
# PERSONALIZED COURSE RECOMMENDATIONS
# --------------------------------------------------

@app.route("/courses")
@login_required
def courses():

    rows = db().execute(
        "SELECT * FROM competencies WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    weak = {
        r["skill"]
        for r in rows
        if r["current_level"] < r["target_level"]
    }

    recs = [
        c for c in COURSES
        if c[2] in weak
    ]

    return render_template(
        "courses.html",
        courses=recs,
        weak=weak
    )


# --------------------------------------------------
# TEXT EXTRACTION FROM UPLOADED MATERIAL
# --------------------------------------------------

def extract_text(path, ext):

    if ext == "txt":

        with open(
            path,
            encoding="utf-8",
            errors="ignore"
        ) as file:

            return file.read()

    if ext == "pdf":

        try:

            from pypdf import PdfReader

            return "\n".join(
                page.extract_text() or ""
                for page in PdfReader(path).pages
            )

        except Exception:

            return ""

    if ext == "docx":

        try:

            from docx import Document

            return "\n".join(
                p.text
                for p in Document(path).paragraphs
            )

        except Exception:

            return ""

    return ""


# --------------------------------------------------
# AUTOMATIC MCQ GENERATION
# --------------------------------------------------

def generate_questions(text, count=5):

    # Extractive NLP baseline

    sentences = [
        re.sub(r"\s+", " ", s).strip()
        for s in re.split(r"(?<=[.!?])\s+|\n+", text)
        if len(s.split()) >= 7
    ]

    stop = {
        "the",
        "and",
        "that",
        "with",
        "from",
        "this",
        "into",
        "their",
        "which",
        "using",
        "data",
        "system"
    }

    questions = []

    for sentence in sentences:

        words = re.findall(
            r"\b[A-Za-z][A-Za-z-]{3,}\b",
            sentence
        )

        candidates = [
            w for w in words
            if w.lower() not in stop
        ]

        if not candidates:
            continue

        answer = max(
            candidates,
            key=len
        )

        prompt = re.sub(
            r"\b" + re.escape(answer) + r"\b",
            "________",
            sentence,
            count=1
        )

        distractors = []

        for w in candidates:

            if (
                w.lower() != answer.lower()
                and w.lower() not in [
                    x.lower() for x in distractors
                ]
            ):

                distractors.append(w)

            if len(distractors) == 3:
                break

        while len(distractors) < 3:

            distractors.append(
                ["Sampling", "Statistics", "Governance"][
                    len(distractors)
                ]
            )

        opts = [answer] + distractors[:3]

        # Deterministic option shuffle

        shift = len(prompt) % 4

        opts = opts[shift:] + opts[:shift]

        questions.append({

            "question": prompt,

            "options": opts,

            "answer": opts.index(answer),

            "explanation": (
                f"The uploaded material states: {sentence}"
            )

        })

        if len(questions) >= count:
            break

    return questions


# --------------------------------------------------
# DOCUMENT UPLOAD AND QUIZ CREATION
# --------------------------------------------------

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():

    if request.method == "POST":

        f = request.files.get("material")

        if not f or not f.filename:

            flash(
                "Choose a PDF, DOCX or TXT file.",
                "error"
            )

            return redirect(url_for("upload"))

        filename = secure_filename(f.filename)

        ext = (
            filename.rsplit(".", 1)[-1].lower()
            if "." in filename
            else ""
        )

        if ext not in ALLOWED_EXTENSIONS:

            flash(
                "Only PDF, DOCX and TXT files are supported.",
                "error"
            )

            return redirect(url_for("upload"))

        safe = f"{secrets.token_hex(8)}_{filename}"

        path = os.path.join(
            UPLOAD_DIR,
            safe
        )

        f.save(path)

        content = extract_text(
            path,
            ext
        )

        questions = generate_questions(content)

        if not questions:

            os.remove(path)

            flash(
                "Could not extract enough text. Try a text-based PDF, DOCX or TXT with complete sentences.",
                "error"
            )

            return redirect(url_for("upload"))

        cur = db().execute(
            """
            INSERT INTO quizzes
            (user_id,title,source_file,questions)
            VALUES(?,?,?,?)
            """,

            (
                session["user_id"],
                f"Quiz: {filename}",
                filename,
                json.dumps(questions)
            )
        )

        db().commit()

        audit(
            "QUIZ_GENERATED",
            filename
        )

        flash(
            f"Generated {len(questions)} questions from your material.",
            "success"
        )

        return redirect(
            url_for(
                "take_quiz",
                quiz_id=cur.lastrowid
            )
        )

    return render_template("upload.html")


# --------------------------------------------------
# QUIZ AND EVALUATION
# --------------------------------------------------

@app.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def take_quiz(quiz_id):

    quiz = db().execute(
        """
        SELECT *
        FROM quizzes
        WHERE id=? AND user_id=?
        """,

        (
            quiz_id,
            session["user_id"]
        )
    ).fetchone()

    if not quiz:

        flash(
            "Quiz not found.",
            "error"
        )

        return redirect(url_for("dashboard"))

    qs = json.loads(
        quiz["questions"]
    )

    if request.method == "POST":

        answers = {}

        score = 0

        for i, q in enumerate(qs):

            selected = request.form.get(
                f"q{i}"
            )

            try:

                selected = int(selected)

            except (TypeError, ValueError):

                selected = -1

            answers[str(i)] = selected

            if selected == q["answer"]:

                score += 1

        db().execute(
            """
            INSERT INTO results
            (quiz_id,user_id,score,total,answers)
            VALUES(?,?,?,?,?)
            """,

            (
                quiz_id,
                session["user_id"],
                score,
                len(qs),
                json.dumps(answers)
            )
        )

        db().commit()

        audit(
            "QUIZ_SUBMITTED",
            f"{score}/{len(qs)}"
        )

        return render_template(
            "result.html",
            score=score,
            total=len(qs),
            questions=qs,
            answers=answers
        )

    return render_template(
        "quiz.html",
        quiz=quiz,
        questions=qs
    )


# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------

@app.route("/admin")
@role_required("admin")
def admin():

    users = db().execute(
        """
        SELECT id,name,email,designation,department
        FROM users
        WHERE role='learner'
        ORDER BY name
        """
    ).fetchall()

    total = db().execute(
        """
        SELECT COUNT(*) n
        FROM users
        WHERE role='learner'
        """
    ).fetchone()["n"]

    stats = db().execute(
        """
        SELECT COUNT(*) n,
        AVG(score*100.0/total) avg
        FROM results
        """
    ).fetchone()

    gaps = db().execute(
        """
        SELECT COUNT(*) n
        FROM competencies
        WHERE current_level<target_level
        """
    ).fetchone()["n"]

    audit_rows = db().execute(
        """
        SELECT *
        FROM audit
        ORDER BY id DESC
        LIMIT 12
        """
    ).fetchall()

    return render_template(
        "admin.html",
        users=users,
        total=total,
        stats=stats,
        gaps=gaps,
        audit_rows=audit_rows
    )


# --------------------------------------------------
# HEALTH CHECK API
# --------------------------------------------------

@app.route("/health")
def health():

    return {
        "status": "ok",
        "service": "Skill Intelligence Platform"
    }, 200


# --------------------------------------------------
# COMPETENCY API
# --------------------------------------------------

@app.route("/api/competencies")
@login_required
def api_competencies():

    rows = db().execute(
        """
        SELECT domain,skill,current_level,target_level
        FROM competencies
        WHERE user_id=?
        """,

        (session["user_id"],)
    ).fetchall()

    return {
        "competencies": [
            dict(r) for r in rows
        ]
    }


# --------------------------------------------------
# FILE SIZE ERROR HANDLER
# --------------------------------------------------

@app.errorhandler(413)
def too_large(e):

    flash(
        "File is too large. Maximum upload size is 12 MB.",
        "error"
    )

    return redirect(url_for("upload"))


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

with app.app_context():

    init_db()


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
