# --- MYSQL SERVER CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "user": "taskgreen_user",
    "password": "TaskGreenPass123!",  # Ensure this matches your MySQL setup
    "database": "task_green_db",
    "auth_plugin": "caching_sha256_password"
}

# --- SMTP LIVE EMAIL CONFIGURATION ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "YOUR_EMAIL@gmail.com"     # Replace with your Gmail account
SENDER_PASSWORD = "YOUR_APP_PASSWORD"     # Replace with your generated App Password