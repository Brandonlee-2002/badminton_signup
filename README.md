# Badminton Signup Manager

A small Flask + SQLite app for hosting badminton session signup pages on PythonAnywhere.

## Features

- Create multiple badminton sessions from an organizer dashboard
- Shareable public URLs for each session
- Individual player signup and a waitlist when the session is full
- Maximum player capacity
- Venue/map link and downloadable calendar event
- Court list and organizer deletion controls
- SQLite database with no external database service required

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ADMIN_PASSWORD='use-a-strong-password'
export SECRET_KEY='use-a-long-random-secret'
python app.py
```

Open `http://127.0.0.1:5000`, then select **Organizer**. The SQLite database is created automatically.

## Deploy on PythonAnywhere

1. Upload this folder to `/home/YOUR_USERNAME/badminton_signup`.
2. Open a PythonAnywhere Bash console:

   ```bash
   cd ~/badminton_signup
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Open the **Web** tab and create a new Flask web app using Python 3.12.
4. Set the source code directory to:

   ```text
   /home/YOUR_USERNAME/badminton_signup
   ```

5. Open the WSGI configuration file and change the username in `wsgi.py`, then use the contents of this project’s `wsgi.py` as the WSGI file.
6. In the WSGI file, replace both placeholder values:

   ```python
   os.environ.setdefault("ADMIN_PASSWORD", "your-strong-admin-password")
   os.environ.setdefault("SECRET_KEY", "your-long-random-secret")
   ```

7. In the **Web** tab, set the virtualenv to:

   ```text
   /home/YOUR_USERNAME/badminton_signup/venv
   ```

8. Reload the web app.

Visit `/admin` on your new PythonAnywhere URL, sign in, and create the first session. Set the maximum number of players, then share the generated public session URL with the badminton group. Once the capacity is reached, new players are automatically placed on the waitlist. When an organizer removes a confirmed player from the admin dashboard, the first waitlisted player is promoted automatically.

## Important security note

Change the default admin password before publishing. This starter app intentionally keeps the admin area simple. For a larger public deployment, add CSRF protection, rate limiting, and per-organizer accounts.
