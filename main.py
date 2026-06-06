import sys

# 1. Database setup: Tasks with Point Values, Priority, and assigned Group restrictions
tasks = [
    {"id": 1, "task_name": "Water the community garden plot", "status": "Pending", "volunteer": "None", "points": 20,
     "priority": "High", "group": "All"},
    {"id": 2, "task_name": "Empty the school recycling bins", "status": "Pending", "volunteer": "None", "points": 15,
     "priority": "Medium", "group": "EcoSeniors"},
    {"id": 3, "task_name": "Refill the local park bird feeders", "status": "Pending", "volunteer": "None", "points": 10,
     "priority": "Low", "group": "All"},
    {"id": 4, "task_name": "Clear weeds from the community pathway", "status": "Pending", "volunteer": "None",
     "points": 40, "priority": "High", "group": "GreenStreet Team"},
    {"id": 5, "task_name": "Plant new wildflower seeds by the fence", "status": "Pending", "volunteer": "None",
     "points": 30, "priority": "Medium", "group": "All"}
]

# 2. User Accounts and Scores Database
# Format: {"username": {"password": "123", "group": "EcoSeniors", "points": 0}}
users_db = {
    "admin": {"password": "password123", "group": "All", "points": 100}  # Pre-made account for testing
}

# Track overall community progress
total_community_points = 100
current_user = None  # Keeps track of who is logged in


def get_level(points):
    if points >= 1000:
        return "Nature Champion 👑"
    elif points >= 500:
        return "Eco Warrior ⚔️"
    elif points >= 200:
        return "Sprout Scout 🌿"
    else:
        return "Seedling 🌱"


# 3. Authentication System (Sign Up & Login)
while current_user is None:
    print("\n==========================================")
    print("      🔒 ECOSYNC: SECURITY PORTAL        ")
    print("==========================================")
    print("1. Log In")
    print("2. Sign Up (Create New Account)")
    print("3. Exit App")

    auth_choice = input("\nChoose an option (1-3): ").strip()

    if auth_choice == "1":
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        if username in users_db and users_db[username]["password"] == password:
            current_user = username
            print(f"\n✅ Welcome back, {current_user}! (Group: {users_db[current_user]['group']})")
        else:
            print("\n❌ Invalid username or password.")

    elif auth_choice == "2":
        new_user = input("Create Username: ").strip()
        if not new_user:
            print("Username cannot be empty!")
            continue
        if new_user in users_db:
            print("That username already exists!")
            continue

        new_pass = input("Create Password: ").strip()
        print("\n--- Available Social Groups ---")
        print("- EcoSeniors\n- GreenStreet Team\n- Independent (No group)")
        new_group = input("Enter your group name exactly as shown: ").strip()

        # Save new user to our database
        users_db[new_user] = {
            "password": new_pass,
            "group": new_group if new_group in ["EcoSeniors", "GreenStreet Team"] else "Independent",
            "points": 0
        }
        print(f"\n🎉 Account created successfully! Please log in now.")

    elif auth_choice == "3":
        print("\nGoodbye! 🌍")
        sys.exit()

# 4. Main Application Loop (Only accessible after logging in)
while True:
    print("\n==========================================")
    print(f" 🌿 ECOSYNC BOARD | User: {current_user} ({users_db[current_user]['group']}) 🌿")
    print("==========================================")
    print("1. View Tasks (Filtered for your Group)")
    print("2. Claim a Task")
    print("3. Mark a Task as Completed")
    print("4. View Volunteer Leaderboard")
    print("5. Log Out")

    choice = input("\nChoose an option (1-5): ").strip()

    user_group = users_db[current_user]["group"]

    if choice == "1":
        print("\n================ AVAILABLE TASKS ================")
        print(f"{'ID':<4} {'Task Name':<40} {'Group Restriction':<20} {'Points':<8} {'Status':<10}")
        print("-" * 88)
        for task in tasks:
            # Users can see tasks meant for 'All' OR tasks that match their specific group
            if task["group"] == "All" or task["group"] == user_group:
                print(
                    f"{task['id']:<4} {task['task_name']:<40} {task['group']:<20} {task['points']:<8} {task['status']:<10}")

    elif choice == "2":
        print("\n--- CLAIM A TASK ---")
        try:
            task_id = int(input("Enter the ID of the task you want to claim: "))
            for task in tasks:
                if task["id"] == task_id:
                    # Check if the user's group is allowed to do this task
                    if task["group"] == "All" or task["group"] == user_group:
                        if task["status"] == "Pending" and task["volunteer"] == "None":
                            task["volunteer"] = current_user
                            print(f"\n✅ Success! You have claimed: '{task['task_name']}'")
                        else:
                            print("\n❌ Error: Task is already taken!")
                    else:
                        print(f"\n❌ Access Denied: This task is locked to the '{task['group']}' group.")
        except ValueError:
            print("\n❌ Error: Please enter a valid numerical ID.")

    elif choice == "3":
        print("\n--- MARK TASK AS COMPLETED ---")
        try:
            task_id = int(input("Enter the ID of the task you finished: "))
            for task in tasks:
                if task["id"] == task_id:
                    if task["volunteer"] == current_user and task["status"] == "Pending":
                        task["status"] = "Completed"
                        earned_points = task["points"]

                        # Add points directly into the database for this specific user
                        users_db[current_user]["points"] += earned_points
                        total_community_points += earned_points

                        print(f"\n🎉 Task Completed! You earned +{earned_points} points.")
                    else:
                        print("\n❌ Error: You can only complete tasks that you personally claimed!")
        except ValueError:
            print("\n❌ Error: Invalid ID format.")

    elif choice == "4":
        print("\n================ LEADERBOARD ================")
        # Sort users based on the points inside their nested user dictionary
        sorted_users = sorted(users_db.items(), key=lambda x: x[1]["points"], reverse=True)
        print(f"{'Rank':<6} {'Volunteer':<15} {'Group':<18} {'Points':<10} {'Level':<20}")
        print("-" * 69)
        for index, (name, data) in enumerate(sorted_users, 1):
            print(f"{index:<6} {name:<15} {data['group']:<18} {data['points']:<10} {get_level(data['points'])}")

    elif choice == "5":
        print(f"\nLogging out of {current_user}...")
        current_user = None
        # This restarts the login system block
        while current_user is None:
            username = input("\nUsername to log back in: ").strip()
            password = input("Password: ").strip()
            if username in users_db and users_db[username]["password"] == password:
                current_user = username
                print(f"✅ Logged in as {current_user}!")
            else:
                print("❌ Invalid credentials.")