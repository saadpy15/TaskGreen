from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
import mysql.connector
import random
from datetime import date

from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = "task_green_secure_key"

# --- FLASK-MAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'saadpy15+noreply@gmail.com'
app.config['MAIL_PASSWORD'] = 'xuvdelryykikqfmt'
app.config['MAIL_DEFAULT_SENDER'] = ('TaskGreen Authentication', app.config['MAIL_USERNAME'])

mail = Mail(app)


def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        auth_plugin='caching_sha2_password'
    )


@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if "username" in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                session["username"] = user["username"]
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password match.", "error")

        except mysql.connector.Error as err:
            flash(f"Database connectivity error: {err}", "error")

    return render_template('login.html', logo_img='logo_light.png')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if "username" in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_group = request.form.get('user_group', 'All')

        if not username or not email or not password:
            flash("All fields must be completely filled out.", "error")
            return render_template('register.html', logo_img='logo_light.png')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash("That username is already registered. Please try a different name.", "error")
                cursor.close()
                conn.close()
                return render_template('register.html', logo_img='logo_light.png')

            cursor.close()
            conn.close()

            verification_code = str(random.randint(100000, 999999))
            session['temp_reg_data'] = {
                'username': username,
                'email': email,
                'password': password,
                'user_group': user_group,
                'code': verification_code
            }

            msg = Message("TaskGreen Verification Code", recipients=[email])
            msg.body = f"Hello {username},\n\nYour 6-digit registration verification code is: {verification_code}"
            mail.send(msg)

            return redirect(url_for('verify'))

        except Exception as err:
            flash(f"Error initializing registration email transmission: {err}", "error")

    return render_template('register.html', logo_img='logo_light.png')


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'temp_reg_data' not in session:
        return redirect(url_for('register'))

    if request.method == 'POST':
        user_code_input = request.form.get('verification_code')
        reg_data = session['temp_reg_data']

        if user_code_input == reg_data['code']:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, user_group, points, email) VALUES (%s, %s, %s, %s, %s)",
                    (reg_data['username'], reg_data['password'], reg_data['user_group'], 0, reg_data['email'])
                )
                conn.commit()
                cursor.close()
                conn.close()
                session.pop('temp_reg_data', None)
                flash("Account email verified successfully! Please sign in below.", "success")
                return redirect(url_for('login'))
            except mysql.connector.Error as err:
                flash(f"Database verification save transaction error: {err}", "error")
        else:
            flash("Incorrect verification code entry. Please check your inbox and try again.", "error")

    return render_template('verify.html', logo_img='logo_light.png')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if "username" not in session:
        return redirect(url_for('login'))

    username = session["username"]
    today = date.today()

    if request.method == 'POST':
        action = request.form.get('action_type')
        if action == "update_settings":
            new_email = request.form.get('verification_email')
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET email = %s WHERE username = %s", (new_email, username))
                conn.commit()
                cursor.close()
                conn.close()
                flash("Settings configuration updated successfully!", "success")
            except mysql.connector.Error as err:
                flash(f"Error recording adjustments: {err}", "error")
            return redirect(url_for('dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_group, points, email FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()

        if not user_data:
            user_data = {'user_group': 'All', 'points': 0, 'email': ''}

        cursor.execute("SELECT * FROM tasks WHERE last_activated_date = %s", (today,))
        tasks = cursor.fetchall()

        if len(tasks) < 5:
            cursor.execute(
                "UPDATE tasks SET last_activated_date = NULL WHERE last_activated_date != %s OR last_activated_date IS NULL",
                (today,))
            cursor.execute("UPDATE tasks SET status = 'Pending', volunteer = NULL WHERE status = 'Completed'")
            cursor.execute("SELECT id FROM tasks ORDER BY RAND() LIMIT 5")
            chosen_task_ids = [row['id'] for row in cursor.fetchall()]

            if chosen_task_ids:
                format_strings = ','.join(['%s'] * len(chosen_task_ids))
                cursor.execute(f"UPDATE tasks SET last_activated_date = %s WHERE id IN ({format_strings})",
                               [today] + chosen_task_ids)
                conn.commit()

            cursor.execute(
                "SELECT id, task_name, priority, points, status, volunteer FROM tasks WHERE last_activated_date = %s",
                (today,))
            tasks = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'dashboard.html',
            username=username,
            group=user_data['user_group'],
            points=user_data['points'],
            current_email=user_data['email'] if user_data['email'] else '',
            tasks=tasks,
            logo_img='logo_light.png'
        )
    except mysql.connector.Error as err:
        return f"Database Error: {err}"


@app.route('/claim-task', methods=['POST'])
def claim_task():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 401

    data = request.get_json()
    task_id = data.get('task_id')
    username = session["username"]

    if not task_id:
        return jsonify({"status": "error", "message": "No Task ID provided."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE id = %s AND last_activated_date = %s", (task_id, date.today()))
        task = cursor.fetchone()

        if not task:
            return jsonify({"status": "error", "message": "Task not active today or does not exist."}), 404
        if task['status'] != 'Pending':
            return jsonify({"status": "error", "message": f"This task is already {task['status']}."}), 400

        cursor.execute("UPDATE tasks SET status = 'Claimed', volunteer = %s WHERE id = %s", (username, task_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": f"Task {task_id} successfully claimed!"})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500


@app.route('/complete-task', methods=['POST'])
def complete_task():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 401

    data = request.get_json()
    task_id = data.get('task_id')
    username = session["username"]

    if not task_id:
        return jsonify({"status": "error", "message": "No Task ID provided."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()

        if not task:
            return jsonify({"status": "error", "message": "Task not found."}), 404
        if task['status'] != 'Claimed' or task['volunteer'] != username:
            return jsonify({"status": "error", "message": "You must claim this task before completing it."}), 400

        cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = %s", (task_id,))
        task_points = task['points']
        cursor.execute("UPDATE users SET points = points + %s WHERE username = %s", (task_points, username))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": f"Task {task_id} completed! +{task_points} points awarded."})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500


@app.route('/request-delete-code', methods=['POST'])
def request_delete_code():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 401

    username = session["username"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or not user['email']:
            return jsonify({"status": "error",
                            "message": "No validation email address found. Set an email in settings first."}), 400

        delete_code = str(random.randint(100000, 999999))
        session['account_delete_pin'] = delete_code

        msg = Message("CRITICAL: TaskGreen Account Deletion Security Code", recipients=[user['email']])
        msg.body = f"Hello {username},\n\nYou have requested to permanently delete your TaskGreen profile.\n\nYour code is: {delete_code}"
        mail.send(msg)

        return jsonify({"status": "success", "message": "Verification code dispatched."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Transmission error: {str(e)}"}), 500


@app.route('/confirm-delete-account', methods=['POST'])
def confirm_delete_account():
    if "username" not in session:
        return redirect(url_for('login'))

    user_input_pin = request.form.get('modal_delete_code')
    session_pin = session.get('account_delete_pin')
    username = session["username"]

    if not session_pin or user_input_pin != session_pin:
        flash("Invalid account erasure code verification. Action terminated.", "error")
        return redirect(url_for('dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        cursor.close()
        conn.close()

        session.clear()
        return """
        <script>
            alert("Your account records have been permanently cleared down.");
            window.location.href = "/login";
        </script>
        """
    except mysql.connector.Error as err:
        flash(f"Database erasure error: {err}", "error")
        return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)