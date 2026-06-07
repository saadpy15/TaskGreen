import tkinter as tk
from tkinter import messagebox, ttk
import random
import smtplib
import mysql.connector
from email.message import EmailMessage

# Custom internal file imports
from config import DB_CONFIG, SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD
from database import init_db
from tasks import all_tasks_pool

# Initialize database mapping automatically on launch
init_db()

# State management tracking flags
daily_tasks = []
current_user = ""
user_group = ""
user_points = 0
current_theme = "light"
generated_pin = ""
pending_email_cache = ""

root = tk.Tk()
root.title("TaskGreen Desktop App")
root.geometry("1024x640")

style = ttk.Style()
style.theme_use("clam")

# Component definitions placeholders
points_lbl = None;
level_lbl = None;
id_entry = None;
task_table = None;
id_label = None
settings_title = None;
overview_box = None;
account_info_lbl = None;
email_box = None
email_lbl = None;
email_entry = None;
theme_box = None;
theme_btn = None
delete_box = None;
delete_lbl = None;
delete_entry = None
pin_lbl = None;
pin_entry = None;
verify_btn = None

profile_frame = tk.Frame(root)
main_frame = tk.Frame(root)
controls_frame = tk.LabelFrame(root)
table_frame = tk.Frame(root)
settings_frame = tk.Frame(root)


def get_level(points):
    if points >= 1000:
        return "Nature Champion 👑"
    elif points >= 500:
        return "Eco Warrior ⚔️"
    elif points >= 200:
        return "Sprout Scout 🌿"
    else:
        return "Seedling 🌱"


def pick_daily_tasks():
    global daily_tasks
    eligible_tasks = [task for task in all_tasks_pool if task["group"] == "All" or task["group"] == user_group]
    if len(eligible_tasks) >= 5:
        daily_tasks = random.sample(eligible_tasks, 5)
    else:
        daily_tasks = eligible_tasks


def refresh_table():
    if task_table is None: return
    for item in task_table.get_children(): task_table.delete(item)
    for task in daily_tasks:
        task_table.insert("", "end", values=(
            task["id"], task["task_name"], task["group"],
            task["priority"], task["points"], task["status"], task["volunteer"]
        ))


def claim_task():
    try:
        target_id = int(id_entry.get().strip())
        for task in daily_tasks:
            if task["id"] == target_id:
                if task["status"] == "Pending" and task["volunteer"] == "None":
                    task["volunteer"] = current_user
                    messagebox.showinfo("Success", f"You have successfully claimed Task #{target_id}!")
                    refresh_table()
                    id_entry.delete(0, tk.END)
                    return
                else:
                    messagebox.showerror("Error", "This task is already claimed or finished.")
                    return
        messagebox.showerror("Error", "Task ID not found in today's selection.")
    except ValueError:
        messagebox.showerror("Error", "Please enter a numerical Task ID.")


def complete_task():
    global user_points
    try:
        target_id = int(id_entry.get().strip())
        for task in daily_tasks:
            if task["id"] == target_id:
                if task["volunteer"] == current_user and task["status"] == "Pending":
                    task["status"] = "Completed"
                    user_points += task["points"]

                    conn = mysql.connector.connect(**DB_CONFIG)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET points = %s WHERE username = %s", (user_points, current_user))
                    conn.commit()
                    cursor.close()
                    conn.close()

                    if points_lbl and level_lbl:
                        points_lbl.config(text=f"Points: {user_points}")
                        level_lbl.config(text=f"Rank: {get_level(user_points)}")

                    messagebox.showinfo("🎉 Done!", f"Awesome! You earned +{task['points']} points!")
                    refresh_table()
                    id_entry.delete(0, tk.END)
                    return
                else:
                    messagebox.showerror("Error", "You can only finish pending tasks you claimed yourself.")
                    return
        messagebox.showerror("Error", "Task ID not found in today's selection.")
    except ValueError:
        messagebox.showerror("Error", "Please enter a numerical Task ID.")


def generate_new_daily_set():
    pick_daily_tasks()
    refresh_table()
    messagebox.showinfo("☀️ New Day!", "A fresh set of 5 random daily tasks has been generated!")


def process_account_deletion():
    global current_user
    confirm_pwd = delete_entry.get().strip()

    if not confirm_pwd:
        messagebox.showerror("Error", "Please enter your password to confirm account deletion.")
        return
    if current_user == "admin":
        messagebox.showerror("Access Denied", "The master system 'admin' profile cannot be deleted.")
        return

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (current_user,))
    record = cursor.fetchone()

    if record and record[0] == confirm_pwd:
        double_check = messagebox.askyesno("⚠️ Permanent Action",
                                           f"Are you sure you want to permanently delete '{current_user}'?")
        if double_check:
            cursor.execute("DELETE FROM users WHERE username = %s", (current_user,))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Account Erased", "Your profile has been removed. Logging out.")
            trigger_system_logout()
        else:
            cursor.close()
            conn.close()
    else:
        cursor.close()
        conn.close()
        messagebox.showerror("Error", "Incorrect password validation.")


def trigger_system_logout():
    global current_user, user_group, user_points
    current_user = "";
    user_group = "";
    user_points = 0
    profile_frame.pack_forget();
    main_frame.pack_forget();
    settings_frame.pack_forget()
    build_auth_gateway()


def toggle_theme():
    global current_theme
    if current_theme == "light":
        current_theme = "dark"
        if theme_btn: theme_btn.config(text="☀️ Switch to Light Mode", bg="#e2e8f0", fg="#0f172a")
        apply_dark_theme()
    else:
        current_theme = "light"
        if theme_btn: theme_btn.config(text="🌙 Switch to Dark Mode", bg="#1e293b", fg="white")
        apply_light_theme()


def apply_light_theme():
    root.configure(bg="#f0fdf4");
    main_frame.configure(bg="#f0fdf4");
    table_frame.configure(bg="#f0fdf4");
    settings_frame.configure(bg="#f0fdf4")
    controls_frame.configure(bg="#f0fdf4", fg="black")
    if id_label: id_label.configure(bg="#f0fdf4", fg="black")
    if id_entry: id_entry.configure(bg="white", fg="black", insertbackground="black")
    if settings_title: settings_title.configure(bg="#f0fdf4", fg="#16a34a")
    if overview_box: overview_box.configure(bg="#f0fdf4", fg="black")
    if account_info_lbl: account_info_lbl.configure(bg="#f0fdf4", fg="#1e293b")
    if email_box: email_box.configure(bg="#f0fdf4", fg="black")
    if email_lbl: email_lbl.configure(bg="#f0fdf4", fg="black")
    if email_entry: email_entry.configure(bg="white", fg="black", insertbackground="black")
    if theme_box: theme_box.configure(bg="#f0fdf4", fg="black")
    if delete_box: delete_box.configure(bg="#f0fdf4", fg="#b91c1c")
    if delete_lbl: delete_lbl.configure(bg="#f0fdf4", fg="black")
    if delete_entry: delete_entry.configure(bg="white", fg="black", insertbackground="black")
    if pin_lbl: pin_lbl.configure(bg="#f0fdf4", fg="black")
    if pin_entry: pin_entry.configure(bg="white", fg="black", insertbackground="black")
    style.configure("Treeview", background="white", foreground="black", fieldbackground="white")
    style.configure("Treeview.Heading", background="#e2e8f0", foreground="black")


def apply_dark_theme():
    root.configure(bg="#0f172a");
    main_frame.configure(bg="#0f172a");
    table_frame.configure(bg="#0f172a");
    settings_frame.configure(bg="#0f172a")
    controls_frame.configure(bg="#1e293b", fg="white")
    if id_label: id_label.configure(bg="#1e293b", fg="white")
    if id_entry: id_entry.configure(bg="#334155", fg="white", insertbackground="white")
    if settings_title: settings_title.configure(bg="#0f172a", fg="#4ade80")
    if overview_box: overview_box.configure(bg="#1e293b", fg="white")
    if account_info_lbl: account_info_lbl.configure(bg="#1e293b", fg="white")
    if email_box: email_box.configure(bg="#1e293b", fg="white")
    if email_lbl: email_lbl.configure(bg="#1e293b", fg="white")
    if email_entry: email_entry.configure(bg="#334155", fg="white", insertbackground="white")
    if theme_box: theme_box.configure(bg="#1e293b", fg="white")
    if delete_box: delete_box.configure(bg="#1e293b", fg="#f87171")
    if delete_lbl: delete_lbl.configure(bg="#1e293b", fg="white")
    if delete_entry: delete_entry.configure(bg="#334155", fg="white", insertbackground="white")
    if pin_lbl: pin_lbl.configure(bg="#1e293b", fg="white")
    if pin_entry: pin_entry.configure(bg="#334155", fg="white", insertbackground="white")
    style.configure("Treeview", background="#1e293b", foreground="white", fieldbackground="#1e293b")
    style.configure("Treeview.Heading", background="#334155", foreground="white")


def send_verification_email():
    global generated_pin, pending_email_cache
    new_email = email_entry.get().strip()
    if "@" not in new_email or "." not in new_email:
        messagebox.showerror("Error", "Please enter a valid email address.")
        return
    if SENDER_EMAIL == "YOUR_EMAIL@gmail.com":
        messagebox.showwarning("Setup Required", "Please configure your credentials in config.py first!")
        return

    pending_email_cache = new_email
    generated_pin = str(random.randint(100000, 999999))
    try:
        msg = EmailMessage()
        msg['Subject'] = "TaskGreen Profile Verification Code"
        msg['From'] = SENDER_EMAIL
        msg['To'] = pending_email_cache
        msg.set_content(
            f"Hello Eco-Volunteer!\n\nYour secret configuration token verification code is: {generated_pin}")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        messagebox.showinfo("Verification Sent", f"A validation token has been successfully emailed to {new_email}.")
        pin_lbl.pack(anchor="w", pady=(10, 2));
        pin_entry.pack(anchor="w", pady=2);
        verify_btn.pack(anchor="w", pady=5)
    except Exception as e:
        messagebox.showerror("Network error", f"Could not send email securely.\n\nDetails: {e}")


def confirm_verification_pin():
    global generated_pin, pending_email_cache
    user_pin_input = pin_entry.get().strip()
    if user_pin_input == generated_pin and generated_pin != "":
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET email = %s, email_verified = 1 WHERE username = %s",
                       (pending_email_cache, current_user))
        conn.commit()
        cursor.close();
        conn.close()

        update_account_display()
        messagebox.showinfo("Account Connected", "🎉 Verification Successful!")
        pin_entry.delete(0, tk.END);
        pin_lbl.pack_forget();
        pin_entry.pack_forget();
        verify_btn.pack_forget();
        email_entry.delete(0, tk.END)
        generated_pin = "";
        pending_email_cache = ""
    else:
        messagebox.showerror("Access Denied", "Incorrect verification code.")


def update_account_display():
    if account_info_lbl:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT email, email_verified FROM users WHERE username = %s", (current_user,))
        record = cursor.fetchone()
        cursor.close();
        conn.close()
        if record:
            email, verified = record
            status_tag = " Verified ✅" if verified == 1 else " Not Linked 🛑"
            account_info_lbl.config(
                text=f"👤 Username: {current_user}\n\n👥 Group Circle: {user_group}\n\n📧 Linked Email: {email}{status_tag}")


def show_settings():
    main_frame.pack_forget();
    update_account_display()
    if delete_entry: delete_entry.delete(0, tk.END)
    settings_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)


def show_dashboard():
    settings_frame.pack_forget();
    main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20);
    refresh_table()


def process_login():
    global current_user, user_group, user_points, auth_window
    user = login_user_entry.get().strip()
    pwd = login_pass_entry.get().strip()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT password, user_group, points FROM users WHERE username = %s", (user,))
    record = cursor.fetchone()
    cursor.close();
    conn.close()

    if record and record[0] == pwd:
        current_user = user;
        user_group = record[1];
        user_points = record[2]
        pick_daily_tasks();
        auth_window.destroy();
        build_main_app()
    else:
        messagebox.showerror("Error", "Invalid username or password.")


def process_signup():
    user = signup_user_entry.get().strip()
    pwd = signup_pass_entry.get().strip()
    group = group_combobox.get()

    if not user or not pwd:
        messagebox.showerror("Error", "Fields cannot be empty!");
        return
    if len(user) < 3 or len(user) > 16:
        messagebox.showerror("Incomplete Form", "Username must be between 3 and 16 characters long.");
        return
    if len(pwd) < 8 or len(pwd) > 20:
        messagebox.showerror("Incomplete Form", "Password must be between 8 and 20 characters long.");
        return

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, user_group) VALUES (%s, %s, %s)", (user, pwd, group))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully! You can log in now.")
        signup_user_entry.delete(0, tk.END);
        signup_pass_entry.delete(0, tk.END)
    except mysql.connector.IntegrityError:
        messagebox.showerror("Error", "Username already exists!")
    finally:
        cursor.close();
        conn.close()


def build_main_app():
    global points_lbl, level_lbl, id_entry, task_table, id_label, settings_title, overview_box
    global account_info_lbl, email_box, email_lbl, email_entry, theme_box, theme_btn, delete_box, delete_lbl, delete_entry
    global pin_lbl, pin_entry, verify_btn, profile_frame, main_frame, controls_frame, table_frame, settings_frame

    profile_frame = tk.Frame(root, bg="#16a34a", width=220, height=550)
    profile_frame.pack(side="left", fill="y");
    profile_frame.pack_propagate(False)

    tk.Label(profile_frame, text="🌿 TASKGREEN", font=("Arial", 16, "bold"), fg="white", bg="#16a34a").pack(pady=20)
    tk.Label(profile_frame, text=f"User: {current_user}", font=("Arial", 12), fg="white", bg="#16a34a").pack(pady=5)
    tk.Label(profile_frame, text=f"Group: {user_group}", font=("Arial", 11, "italic"), fg="white", bg="#16a34a").pack(
        pady=2)

    points_lbl = tk.Label(profile_frame, text=f"Points: {user_points}", font=("Arial", 12, "bold"), fg="#fef08a",
                          bg="#16a34a")
    points_lbl.pack(pady=20)

    level_lbl = tk.Label(profile_frame, text=f"Rank: {get_level(user_points)}", font=("Arial", 11), fg="white",
                         bg="#16a34a")
    level_lbl.pack(pady=5)

    tk.Button(profile_frame, text="📋 Daily Dashboard", command=show_dashboard, bg="#22c55e", fg="white",
              font=("Arial", 10, "bold"), bd=0, cursor="hand2").pack(fill="x", pady=5, padx=10)
    tk.Button(profile_frame, text="⚙️ Settings Menu", command=show_settings, bg="#22c55e", fg="white",
              font=("Arial", 10, "bold"), bd=0, cursor="hand2").pack(fill="x", pady=5, padx=10)
    tk.Button(profile_frame, text="🚪 System Logout", command=trigger_system_logout, bg="#dc2626", fg="white",
              font=("Arial", 10, "bold"), bd=0, cursor="hand2").pack(fill="x", side="bottom", pady=20, padx=10)

    main_frame = tk.Frame(root, bg="#f0fdf4")
    main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    controls_frame = tk.LabelFrame(main_frame, text=" Today's Active Tasks (5 Selected) ", bg="#f0fdf4",
                                   font=("Arial", 10, "bold"))
    controls_frame.pack(fill="x", pady=10)

    id_label = tk.Label(controls_frame, text="Enter Task ID:", bg="#f0fdf4", font=("Arial", 11))
    id_label.pack(side="left", padx=10, pady=15)
    id_entry = tk.Entry(controls_frame, width=8, font=("Arial", 11))
    id_entry.pack(side="left", padx=5)

    tk.Button(controls_frame, text="Claim Task", command=claim_task, bg="#3b82f6", fg="white",
              font=("Arial", 10, "bold"), padx=10).pack(side="left", padx=10)
    tk.Button(controls_frame, text="Mark Completed", command=complete_task, bg="#16a34a", fg="white",
              font=("Arial", 10, "bold"), padx=10).pack(side="left", padx=5)
    tk.Button(controls_frame, text="☀️ New Day Refresh", command=generate_new_daily_set, bg="#eab308", fg="black",
              font=("Arial", 10, "bold"), padx=10).pack(side="right", padx=10)

    table_frame = tk.Frame(main_frame, bg="#f0fdf4")
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "name", "group", "priority", "pts", "status", "assigned")
    task_table = ttk.Treeview(table_frame, columns=columns, show="headings")

    task_table.heading("id", text="ID");
    task_table.column("id", minwidth=40, width=50, stretch=False, anchor="center")
    task_table.heading("name", text="Eco Task Description");
    task_table.column("name", minwidth=250, width=320, stretch=True)
    task_table.heading("group", text="Group Restriction");
    task_table.column("group", minwidth=120, width=150, stretch=False, anchor="center")
    task_table.heading("priority", text="Priority");
    task_table.column("priority", minwidth=70, width=85, stretch=False, anchor="center")
    task_table.heading("pts", text="Points");
    task_table.column("pts", minwidth=60, width=75, stretch=False, anchor="center")
    task_table.heading("status", text="Status");
    task_table.column("status", minwidth=80, width=95, stretch=False, anchor="center")
    task_table.heading("assigned", text="Volunteer");
    task_table.column("assigned", minwidth=90, width=110, stretch=False, anchor="center")
    task_table.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=task_table.yview)
    task_table.configure(yscrollcommand=scrollbar.set);
    scrollbar.pack(side="right", fill="y")

    settings_frame = tk.Frame(root, bg="#f0fdf4")
    settings_title = tk.Label(settings_frame, text="⚙️ Account & Application Settings", font=("Arial", 16, "bold"),
                              bg="#f0fdf4", fg="#16a34a")
    settings_title.pack(anchor="w", pady=10)

    overview_box = tk.LabelFrame(settings_frame, text=" Account Profile Data ", font=("Arial", 10, "bold"), padx=15,
                                 pady=15, bg="#f0fdf4")
    overview_box.pack(fill="x", pady=5)
    account_info_lbl = tk.Label(overview_box, justify="left", font=("Arial", 11), text="", bg="#f0fdf4")
    account_info_lbl.pack(anchor="w")

    email_box = tk.LabelFrame(settings_frame, text=" Account Management Actions ", font=("Arial", 10, "bold"), padx=15,
                              pady=15, bg="#f0fdf4")
    email_box.pack(fill="x", pady=5)
    email_lbl = tk.Label(email_box, text="Link New Email Address:", font=("Arial", 11), bg="#f0fdf4")
    email_lbl.pack(anchor="w", pady=2)

    email_action_row = tk.Frame(email_box);
    email_action_row.pack(anchor="w", pady=5)
    email_entry = tk.Entry(email_action_row, width=30, font=("Arial", 11));
    email_entry.pack(side="left", padx=2)
    tk.Button(email_action_row, text="Send Verification Code", command=send_verification_email, bg="#3b82f6",
              fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)

    pin_lbl = tk.Label(email_box, text="Enter 6-Digit Code:", font=("Arial", 11, "bold"), bg="#f0fdf4")
    pin_entry = tk.Entry(email_box, width=15, font=("Arial", 11))
    verify_btn = tk.Button(email_box, text="Verify & Connect Account", command=confirm_verification_pin, bg="#16a34a",
                           fg="white", font=("Arial", 10, "bold"))

    theme_box = tk.LabelFrame(settings_frame, text=" Application Display Settings ", font=("Arial", 10, "bold"),
                              padx=15, pady=15, bg="#f0fdf4")
    theme_box.pack(fill="x", pady=5)
    theme_btn = tk.Button(theme_box, text="🌙 Switch to Dark Mode", command=toggle_theme, bg="#1e293b", fg="white",
                          font=("Arial", 11, "bold"), width=22, pady=5)
    theme_btn.pack(anchor="w")

    delete_box = tk.LabelFrame(settings_frame, text=" ⚠️ Danger Zone ", font=("Arial", 10, "bold"), labelanchor="n",
                               fg="#b91c1c", bg="#f0fdf4", padx=15, pady=15)
    delete_box.pack(fill="x", pady=10)
    delete_lbl = tk.Label(delete_box, text="To permanently delete your profile, confirm password:", font=("Arial", 10),
                          bg="#f0fdf4")
    delete_lbl.pack(side="left", padx=5)
    delete_entry = tk.Entry(delete_box, width=18, show="*", font=("Arial", 11));
    delete_entry.pack(side="left", padx=10)
    tk.Button(delete_box, text="Delete Account Permanently", command=process_account_deletion, bg="#dc2626", fg="white",
              font=("Arial", 10, "bold")).pack(side="left", padx=5)

    if current_theme == "dark":
        apply_dark_theme()
    else:
        apply_light_theme()
    refresh_table()


def build_auth_gateway():
    global auth_window, login_user_entry, login_pass_entry, signup_user_entry, signup_pass_entry, group_combobox
    auth_window = tk.Frame(root, bg="#f0fdf4");
    auth_window.place(relx=0, rely=0, relwidth=1, relheight=1)

    tk.Label(auth_window, text="🔒 TASKGREEN: SECURITY PORTAL", font=("Arial", 16, "bold"), fg="#16a34a",
             bg="#f0fdf4").pack(pady=25)
    columns_frame = tk.Frame(auth_window, bg="#f0fdf4");
    columns_frame.pack(pady=10)

    login_frame = tk.LabelFrame(columns_frame, text=" Returning Users: Login ", font=("Arial", 11, "bold"),
                                bg="#f0fdf4", padx=15, pady=15)
    login_frame.pack(side="left", padx=20, fill="both")
    tk.Label(login_frame, text="Username:", bg="#f0fdf4").pack(anchor="w", pady=2)
    login_user_entry = tk.Entry(login_frame, width=20, font=("Arial", 11));
    login_user_entry.pack(pady=5)
    tk.Label(login_frame, text="Password:", bg="#f0fdf4").pack(anchor="w", pady=2)
    login_pass_entry = tk.Entry(login_frame, width=20, show="*", font=("Arial", 11));
    login_pass_entry.pack(pady=5)
    tk.Button(login_frame, text="Log In", command=process_login, bg="#16a34a", fg="white", font=("Arial", 10, "bold"),
              width=15).pack(pady=15)

    signup_frame = tk.LabelFrame(columns_frame, text=" New Volunteers: Sign Up ", font=("Arial", 11, "bold"),
                                 bg="#f0fdf4", padx=15, pady=15)
    signup_frame.pack(side="right", padx=20, fill="both")
    tk.Label(signup_frame, text="Choose Username:", bg="#f0fdf4").pack(anchor="w", pady=2)
    signup_user_entry = tk.Entry(signup_frame, width=20, font=("Arial", 11));
    signup_user_entry.pack(pady=5)
    tk.Label(signup_frame, text="Choose Password:", bg="#f0fdf4").pack(anchor="w", pady=2)
    signup_pass_entry = tk.Entry(signup_frame, width=20, show="*", font=("Arial", 11));
    signup_pass_entry.pack(pady=5)
    tk.Label(signup_frame, text="Select Social Circle Group:", bg="#f0fdf4").pack(anchor="w", pady=2)
    group_combobox = ttk.Combobox(signup_frame, values=["Independent", "EcoSeniors", "GreenStreet Team"],
                                  state="readonly", width=18, font=("Arial", 10))
    group_combobox.set("Independent");
    group_combobox.pack(pady=5)
    tk.Button(signup_frame, text="Create Account", command=process_signup, bg="#3b82f6", fg="white",
              font=("Arial", 10, "bold"), width=15).pack(pady=15)


build_auth_gateway()
root.mainloop()