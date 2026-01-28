import sqlite3
import json
import hashlib
import os

# --- CRITICAL CHANGE FOR RAILWAY PERSISTENCE ---
# We check if we are running on Railway (using a common env var) or local
# If on Railway, store in the persistent volume mount point '/app/data'
if os.environ.get("RAILWAY_ENVIRONMENT"):
    DB_FOLDER = "/app/data"
else:
    DB_FOLDER = "."  # Local testing

# Ensure folder exists (locally)
os.makedirs(DB_FOLDER, exist_ok=True)

DB_NAME = os.path.join(DB_FOLDER, "signet.db")
# -----------------------------------------------

def init_db():
    """Initializes the database with Users and Profiles tables."""
    conn = sqlite3.connect(DB_NAME)
    # ... (Rest of the file remains exactly the same)
