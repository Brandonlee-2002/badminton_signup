import os
import sys

project_home = "/home/YOUR_PYTHONANYWHERE_USERNAME/badminton_signup"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("ADMIN_PASSWORD", "replace-this-password")
os.environ.setdefault("SECRET_KEY", "replace-this-with-a-long-random-value")
from app import app as application
