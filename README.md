# HostelFix - Smart Hostel Complaint Management System

HostelFix is a Flask + MySQL web app for hostel students to submit and track complaints, and for wardens/admins to assign work and update complaint status.

## Features

- Student registration and login
- Complaint submission with category, priority, description, and optional image upload
- Student status tracking page
- Admin dashboard with complaint totals, pending/resolved counts, and category-wise counts
- Admin assignment to maintenance staff
- Status updates: Pending, In Progress, Resolved

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

If your Python cannot see user-installed packages, install them locally:

```bash
python -m pip install --target .vendor -r requirements.txt
```

2. Create the MySQL database:

```bash
mysql -u root -p < schema.sql
```

3. Optional database environment variables:

```bash
set MYSQL_HOST=localhost
set MYSQL_USER=root
set MYSQL_PASSWORD=your_password
set MYSQL_DATABASE=hostelfix
set MYSQL_PORT=3306
```

4. Run the app:

```bash
python app.py
```

5. Open:

```text
http://127.0.0.1:5000
```

## Demo Accounts

- Admin: `admin@hostelfix.com`
- Staff: `staff@hostelfix.com`
- Password for both: `admin123`

Students can register from the login page.
