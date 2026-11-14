# Badminton Signup Manager

A small Flask + SQLite app for hosting badminton session signup pages.

## Features

- Create multiple badminton sessions from an organizer dashboard
- Shareable public URLs for each session
- Individual player signup and a waitlist when the session is full
- Maximum player capacity
- Venue/map link and downloadable calendar event
- Court list and organizer deletion controls
- SQLite database with no external database service required
- Private self-unsign links for players, with automatic waitlist promotion

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

## Hosting note: GitHub Pages vs. PythonAnywhere

GitHub Pages only serves static HTML, CSS, and JavaScript. This application uses Flask routes and SQLite writes for shared events, signups, admin authentication, and waitlists, so the complete app cannot run on GitHub Pages alone. A static-only conversion would not share signups between players.

Keep the Flask app on PythonAnywhere (or another Python host) and use GitHub Pages only for a separate static landing page, or migrate the backend to a serverless database/API such as Supabase before switching hosts. The PythonAnywhere deployment below remains the supported deployment for this repository.

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

After a player signs up, the page opens a private signup-management link. Players can edit their name or cancel their signup from that page. They should keep the link private; cancelling removes their signup and promotes the first waitlisted player when applicable.

## Important security note

Change the default admin password before publishing. This starter app intentionally keeps the admin area simple. For a larger public deployment, add CSRF protection, rate limiting, and per-organizer accounts.

## AI usage

This website was developed with assistance from AI during the design, implementation, debugging, and usability-review process.

AI assistance was used to:

- Build and refine the Flask application structure and user interface
- Add player signup, waitlist, editing, and self-unsign functionality
- Create private signup-management tokens so players can manage only their own entries
- Add event editing tools for organizers
- Improve responsive layouts for desktop, tablet, and mobile screens
- Add Apple Maps and Google Maps links
- Make URLs in event notes clickable while safely escaping other text
- Diagnose PythonAnywhere deployment errors and template/backend mismatches
- Add validation, database migration support, and syntax checks

The application code, deployment configuration, and user-facing behavior were reviewed and adjusted by the project owner. AI-generated changes should still be tested before production use, especially authentication, database migrations, and deployment settings.
