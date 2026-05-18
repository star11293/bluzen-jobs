# Bluzen Healthcare Staffing - Job Board

Job board for Bluzen Healthcare Staffing. Lives at `jobs.bluzenhealthcarestaffing.com`.
The marketing site at the root domain is separate (Netlify, hands off).

## Stack

- Django 5.x monolith
- Postgres (Render) in prod, SQLite locally
- Tailwind CSS + HTMX (added next session)
- SendGrid for transactional email (via django-anymail)
- Cloudinary for resume uploads
- WhiteNoise for static files
- Gunicorn on Render

## Local setup

```bash
# 1. Clone and enter
git clone <your-repo-url>
cd bluzen_jobs

# 2. Virtual env
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 3. Install deps
pip install -r requirements.txt

# 4. Env
cp .env.example .env
# Open .env and set DJANGO_SECRET_KEY to anything long and random.

# 5. Migrate and create superuser
python manage.py migrate
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

Visit http://127.0.0.1:8000/ for the placeholder home page, and
http://127.0.0.1:8000/admin/ for the Django admin.

## Settings layout

- `config/settings/base.py` - shared
- `config/settings/dev.py`  - DEBUG=True, SQLite, console email. Default when running `manage.py`.
- `config/settings/prod.py` - DEBUG=False, Postgres, SendGrid, Cloudinary, security headers. Used by gunicorn/Render.

To force a specific settings module:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
```

## Deploying to Render

1. Push this repo to GitHub.
2. In Render, click "New" -> "Blueprint" and point it at the repo.
   Render reads `render.yaml` and provisions the web service + Postgres DB.
3. Set these env vars in the Render dashboard:
   - `DJANGO_ALLOWED_HOSTS` -> `jobs.bluzenhealthcarestaffing.com,bluzen-jobs.onrender.com`
   - `SENDGRID_API_KEY` -> from SendGrid dashboard
   - `CLOUDINARY_URL` -> from Cloudinary dashboard, format: `cloudinary://api_key:api_secret@cloud_name`
4. After first deploy, open a Render shell and run `python manage.py createsuperuser`.
5. In Render's custom domains section, add `jobs.bluzenhealthcarestaffing.com`.
   In GoDaddy DNS, add a CNAME record pointing `jobs` to the Render service hostname.

## Project structure

```
bluzen_jobs/
├── manage.py
├── requirements.txt
├── render.yaml
├── .env.example
├── .gitignore
├── README.md
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── accounts/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── managers.py
│   ├── models.py
│   ├── urls.py
│   └── migrations/
├── jobs/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py        (stubbed, filled in next session)
│   ├── urls.py
│   └── migrations/
├── templates/
│   └── home.html
└── static/
```

## What's done

- [x] Project skeleton
- [x] Settings split (base / dev / prod)
- [x] Custom User model with email login + role field
- [x] EmployerProfile and JobSeekerProfile
- [x] Django admin registered for User and profiles
- [x] Render blueprint
- [x] Production settings: WhiteNoise, SendGrid, Cloudinary, security headers

## Next session

- [ ] JobPosting and JobApplication models (with the right defaults this time)
- [ ] Registration + login views using ModelForms
- [ ] Job list / detail / apply views with HTMX
- [ ] Tailwind setup (django-tailwind or CDN to start)
- [ ] First deploy to Render
- [ ] Connect the subdomain

## Bugs from the last build that this scaffold prevents

- Models indentation - clean inheritance from `AbstractBaseUser`, no class-level chaos.
- Custom admin portal - we use Django admin. The `UserAdmin` subclass means the role field shows up in the standard admin without a parallel UI.
- Status='pending' / is_active=False with no approval flow - `JobPosting.status` will default to PUBLISHED, not pending. Moderation can be added later as a separate concern.
- Manual form handling - models are ModelForm-ready (no weird field types).
- Messages as errors - to be addressed when we wire up views (use `messages.success` consistently, not `messages.add_message(request, 40, ...)`).
