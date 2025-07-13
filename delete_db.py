
import os

if os.path.exists("database.db"):
    os.remove("database.db")
    print("✅ database.db deleted successfully.")
else:
    print("⚠️ database.db not found.")

