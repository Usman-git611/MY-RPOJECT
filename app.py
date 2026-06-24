import os
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENDOR_DIR = BASE_DIR / ".vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from db import Database


UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "hostelfix-dev-secret-key")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

UPLOAD_DIR.mkdir(exist_ok=True)
db = Database()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    if "user_id" not in session:
        return None
    return {
        "id": session["user_id"],
        "name": session["name"],
        "email": session["email"],
        "role": session["role"],
    }


@app.context_processor
def inject_user():
    return {"current_user": current_user(), "now": datetime.now()}


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please login to continue.", "warning")
                return redirect(url_for("login"))
            if role and user["role"] != role:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("dashboard_redirect"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


@app.route("/")
def home():
    if current_user():
        return redirect(url_for("dashboard_redirect"))
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard_redirect"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    hostel = request.form.get("hostel", "").strip()
    room_no = request.form.get("room_no", "").strip()

    if not all([name, email, password, hostel, room_no]):
        flash("Please fill all registration fields.", "warning")
        return redirect(url_for("login"))

    existing = db.fetch_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        flash("An account with this email already exists.", "warning")
        return redirect(url_for("login"))

    db.execute(
        """
        INSERT INTO users (name, email, password_hash, role, hostel, room_no)
        VALUES (%s, %s, %s, 'student', %s, %s)
        """,
        (name, email, generate_password_hash(password), hostel, room_no),
    )
    flash("Registration successful. You can login now.", "success")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required()
def dashboard_redirect():
    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    if session["role"] == "staff":
        return redirect(url_for("staff_dashboard"))
    return redirect(url_for("student_dashboard"))


@app.route("/student")
@login_required("student")
def student_dashboard():
    complaints = db.fetch_all(
        """
        SELECT c.*, u.name AS assigned_staff_name
        FROM complaints c
        LEFT JOIN users u ON c.assigned_to = u.id
        WHERE c.student_id = %s
        ORDER BY c.created_at DESC
        """,
        (session["user_id"],),
    )
    stats = {
        "total": len(complaints),
        "pending": sum(1 for item in complaints if item["status"] == "Pending"),
        "progress": sum(1 for item in complaints if item["status"] == "In Progress"),
        "resolved": sum(1 for item in complaints if item["status"] == "Resolved"),
    }
    return render_template("student_dashboard.html", complaints=complaints, stats=stats)


@app.route("/complaints/new", methods=["GET", "POST"])
@login_required("student")
def submit_complaint():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        image = request.files.get("image")
        image_filename = None

        if not all([title, category, description]):
            flash("Title, category, and description are required.", "warning")
            return redirect(url_for("submit_complaint"))

        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Please upload a valid image file.", "warning")
                return redirect(url_for("submit_complaint"))
            filename = secure_filename(image.filename)
            image_filename = f"{session['user_id']}_{int(datetime.now().timestamp())}_{filename}"
            image.save(UPLOAD_DIR / image_filename)

        complaint_id = db.execute(
            """
            INSERT INTO complaints
                (student_id, title, category, description, priority, image_filename, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
            """,
            (session["user_id"], title, category, description, priority, image_filename),
        )
        flash(f"Complaint HF-{complaint_id:04d} submitted successfully.", "success")
        return redirect(url_for("track_complaint", complaint_id=complaint_id))

    categories = ["Water Leakage", "Electrical", "Wi-Fi", "Furniture", "Cleanliness", "Other"]
    return render_template("submit_complaint.html", categories=categories)


@app.route("/complaints/<int:complaint_id>")
@login_required()
def track_complaint(complaint_id):
    complaint = db.fetch_one(
        """
        SELECT c.*, s.name AS student_name, s.hostel, s.room_no, staff.name AS assigned_staff_name
        FROM complaints c
        JOIN users s ON c.student_id = s.id
        LEFT JOIN users staff ON c.assigned_to = staff.id
        WHERE c.id = %s
        """,
        (complaint_id,),
    )
    if not complaint:
        flash("Complaint not found.", "danger")
        return redirect(url_for("dashboard_redirect"))

    if session["role"] == "student" and complaint["student_id"] != session["user_id"]:
        flash("You can only view your own complaints.", "danger")
        return redirect(url_for("student_dashboard"))

    return render_template("track_complaint.html", complaint=complaint)


@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    status_filter = request.args.get("status", "All")
    category_filter = request.args.get("category", "All")

    clauses = []
    params = []
    if status_filter != "All":
        clauses.append("c.status = %s")
        params.append(status_filter)
    if category_filter != "All":
        clauses.append("c.category = %s")
        params.append(category_filter)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    complaints = db.fetch_all(
        f"""
        SELECT c.*, s.name AS student_name, s.hostel, s.room_no, staff.name AS assigned_staff_name
        FROM complaints c
        JOIN users s ON c.student_id = s.id
        LEFT JOIN users staff ON c.assigned_to = staff.id
        {where_sql}
        ORDER BY c.created_at DESC
        """,
        tuple(params),
    )
    stats = db.dashboard_stats()
    staff = db.fetch_all("SELECT id, name FROM users WHERE role = 'staff' ORDER BY name")
    categories = db.fetch_all("SELECT category, COUNT(*) AS total FROM complaints GROUP BY category")
    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        stats=stats,
        staff=staff,
        categories=categories,
        status_filter=status_filter,
        category_filter=category_filter,
    )


@app.route("/staff")
@login_required("staff")
def staff_dashboard():
    complaints = db.fetch_all(
        """
        SELECT c.*, s.name AS student_name, s.hostel, s.room_no
        FROM complaints c
        JOIN users s ON c.student_id = s.id
        WHERE c.assigned_to = %s
        ORDER BY c.created_at DESC
        """,
        (session["user_id"],),
    )
    return render_template("staff_dashboard.html", complaints=complaints)


@app.route("/staff/complaints/<int:complaint_id>/update", methods=["POST"])
@login_required("staff")
def staff_update_complaint(complaint_id):
    status = request.form.get("status")
    admin_note = request.form.get("admin_note", "").strip()

    if status not in {"In Progress", "Resolved"}:
        flash("Staff can only mark complaints as In Progress or Resolved.", "warning")
        return redirect(url_for("staff_dashboard"))

    db.execute(
        """
        UPDATE complaints
        SET status = %s,
            admin_note = %s,
            resolved_at = CASE WHEN %s = 'Resolved' THEN CURRENT_TIMESTAMP ELSE NULL END
        WHERE id = %s AND assigned_to = %s
        """,
        (status, admin_note, status, complaint_id, session["user_id"]),
    )
    flash(f"Complaint HF-{complaint_id:04d} updated.", "success")
    return redirect(url_for("staff_dashboard"))


@app.route("/admin/complaints/<int:complaint_id>/update", methods=["POST"])
@login_required("admin")
def update_complaint(complaint_id):
    status = request.form.get("status")
    assigned_to = request.form.get("assigned_to") or None
    admin_note = request.form.get("admin_note", "").strip()

    if status not in {"Pending", "In Progress", "Resolved"}:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("admin_dashboard"))

    db.execute(
        """
        UPDATE complaints
        SET status = %s,
            assigned_to = %s,
            admin_note = %s,
            resolved_at = CASE WHEN %s = 'Resolved' THEN CURRENT_TIMESTAMP ELSE NULL END
        WHERE id = %s
        """,
        (status, assigned_to, admin_note, status, complaint_id),
    )
    flash(f"Complaint HF-{complaint_id:04d} updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/uploads/<path:filename>")
@login_required()
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
