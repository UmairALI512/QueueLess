# QueueLess — FastAPI + PostgreSQL

## Included
Clinic registration, admin login, public clinic page, digital patient tokens, patient status page, clinic dashboard, Call Next, Call, Complete and Skip actions.

## A. Create Neon PostgreSQL
1. Create an account at https://neon.tech/
2. Create a project/database.
3. In Neon, open **Connect** and copy the connection string.
4. Keep the password private. Do not post it or upload it to GitHub.

## B. Run on Windows (CMD)
Open CMD inside the extracted QueueLess folder:

    py -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env

Open `.env` in Notepad. Replace DATABASE_URL with your Neon connection string. It should look like:

    postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require

If Neon gives `postgresql://`, change the beginning to `postgresql+psycopg://`.
Change SECRET_KEY to a long random secret. Change SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD to your own credentials. Never share `.env`.

Then run:

    uvicorn app.main:app --reload

Open http://127.0.0.1:8000
Register a clinic at `/register`, or use the seed admin details configured in `.env`.

## C. Test
1. Login to clinic dashboard.
2. Open the patient link shown in the dashboard.
3. Generate a token using a patient name.
4. Return to dashboard and click Call next.
5. Refresh the token page to see status.
6. Test Complete and Skip actions.

## D. Deploy on Vercel
This project includes a root `main.py` entrypoint and `.python-version` for Vercel's Python runtime. Vercel detects FastAPI and serves the app as a Function.

1. Push the extracted project folder to a GitHub repository. Do not upload `.env`.
2. In Vercel, choose **Add New → Project** and import that GitHub repository.
3. Vercel should detect the Python/FastAPI app. Keep the default framework/build settings; do not set a custom output directory.
4. In Project Settings → Environment Variables, add the variables below.
5. Deploy. After deployment, open the assigned `*.vercel.app` URL.
6. Test `/`, `/register`, clinic token generation, `/dashboard`, and `/health`.

Required Vercel environment variables:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables: `DATABASE_URL`, `SECRET_KEY`, `COOKIE_HTTPS_ONLY=true`
- Optional seed variables: `SEED_CLINIC_NAME`, `SEED_CLINIC_SLUG`, `SEED_ADMIN_NAME`, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`

Use a host's free tier only if it currently supports Python web services. Free tiers may sleep, limit usage, or change. Do not create a paid database at the web host; keep using Neon.

## Student-project limitations / before real clinics
This is a working academic starter, not production-certified healthcare software. Before real patient use, add CSRF protection, rate limiting, email verification, random signed patient status links, audit logs, backups, privacy policy, secure admin recovery and stronger operational monitoring. Do not collect diagnoses or sensitive medical details. Queue changes appear on patient status page after refresh. Daily token numbering follows the database/server date.
