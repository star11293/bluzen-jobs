# Deploying Bluzen Jobs to Render

End-to-end guide. Should take about 45 minutes the first time.

## What you'll need

Free accounts on:

- **Render** (web host + Postgres) — https://render.com
- **SendGrid** (transactional email) — https://sendgrid.com
- **Cloudinary** (resume file storage) — https://cloudinary.com

And:

- Access to the GoDaddy DNS records for `bluzenhealthcarestaffing.com` (to point the subdomain).

## Step 1 — SendGrid setup

1. Sign up at https://signup.sendgrid.com. Free tier gives you 100 emails/day, plenty for now.
2. Verify your sender. Two paths:
   - **Single Sender Verification** (faster): Settings → Sender Authentication → "Verify a Single Sender". Use `Andrew@bluzenhealthcarestaffing.com` or similar. SendGrid emails that address, click the link.
   - **Domain Authentication** (better long-term, requires more DNS work): same menu, "Authenticate Your Domain". Skip this for now.
3. Create an API key: Settings → API Keys → "Create API Key". Name it `bluzen-jobs-prod`. Permissions: **Full Access** (or "Mail Send" minimum). Copy the key — SendGrid only shows it once.
4. Save the key somewhere safe. You'll paste it into Render in Step 4.

## Step 2 — Cloudinary setup

1. Sign up at https://cloudinary.com. Free tier: 25 GB storage, plenty for resumes.
2. After signup, you land on the dashboard. Look for **Account Details** → **API Environment variable**.
3. It'll look like: `CLOUDINARY_URL=cloudinary://123456789:abcDef@your-cloud-name`. Copy that whole value (just the part after `=`).
4. Save it next to your SendGrid key.

## Step 3 — Push the latest code to GitHub

Confirm your local repo has everything committed:

```bash
cd ~/Downloads/bluzen_jobs
git status            # should say "nothing to commit, working tree clean"
git log --oneline -5  # confirm your latest commits are there
git push              # if there's anything unpushed
```

## Step 4 — Render Blueprint deploy

The `render.yaml` in the repo tells Render exactly how to provision everything.

1. Log in to Render. From the dashboard, click **New** → **Blueprint**.
2. **Connect a repository**. Pick `star11293/bluzen-jobs`. Authorize Render to read your repo if prompted.
3. Render reads `render.yaml` and shows you a preview: one web service (`bluzen-jobs`) and one database (`bluzen-jobs-db`). Click **Apply**.
4. Render asks you to fill in the values for the env vars marked `sync: false`. Set:
   - `DJANGO_ALLOWED_HOSTS` → `jobs.bluzenhealthcarestaffing.com,bluzen-jobs.onrender.com`
     (The second one is what Render gives you by default; you'll set up the first one in Step 6.)
   - `SITE_BASE_URL` → `https://jobs.bluzenhealthcarestaffing.com`
   - `SENDGRID_API_KEY` → paste the key from Step 1.
   - `CLOUDINARY_URL` → paste the URL from Step 2.
5. Click **Apply**. Render starts building.

First build takes ~5 minutes (installing Python deps, running collectstatic, migrating Postgres). Watch the deploy logs to make sure nothing blows up.

## Step 5 — Create your superuser

Once the deploy is green, you need an admin user to access `/admin/`.

1. In the Render dashboard, open the `bluzen-jobs` web service.
2. Click **Shell** in the left sidebar (Render gives you a one-off shell into the running container).
3. Run:

   ```
   python manage.py createsuperuser
   ```

4. Enter email, password, password confirm. Done.
5. Visit `https://bluzen-jobs.onrender.com/admin/` and log in. Confirm Users, Jobs, Profiles are all there.

## Step 6 — Custom subdomain

This points `jobs.bluzenhealthcarestaffing.com` at the Render service.

**In Render:**

1. `bluzen-jobs` service → **Settings** → **Custom Domains** → **Add Custom Domain**.
2. Enter `jobs.bluzenhealthcarestaffing.com`.
3. Render shows you a CNAME target like `bluzen-jobs.onrender.com`. Copy it.

**In GoDaddy DNS:**

1. Log into GoDaddy. Find `bluzenhealthcarestaffing.com` → DNS Management.
2. Add a new **CNAME** record:
   - **Type**: `CNAME`
   - **Name**: `jobs`
   - **Value**: paste the CNAME target from Render (`bluzen-jobs.onrender.com`)
   - **TTL**: 1 hour (or default)
3. Save. DNS propagates in 5-60 minutes.

**Back in Render:**

After DNS resolves, Render automatically issues a Let's Encrypt SSL cert. The custom domain card will turn green.

Open `https://jobs.bluzenhealthcarestaffing.com` in your browser. You should see the home page, with a real cert.

## Step 7 — Smoke test the live site

1. Visit the home page. Sign up as a test job seeker.
2. Log out, sign up as a test employer. Post a test job.
3. Log out, log in as the job seeker. Apply to the test job.
4. Check both emails arrive (the seeker's confirmation goes to whatever address you used; the employer notification goes to the employer's email).
5. Log in as the employer, check the dashboard shows 1 application.
6. Delete the test users from `/admin/` once you're satisfied.

## Step 8 — Update the marketing site link

The current `bluzenhealthcarestaffing.com` site has an "Apply Now" button pointing at the dead Heroku URL. Update it to `https://jobs.bluzenhealthcarestaffing.com`. That's a one-line edit in the `index.html` of the marketing repo.

## After deploy

- **Memory**: Render free tier sleeps the service after 15 minutes of inactivity. The first hit after a sleep takes ~30 seconds to wake up. Acceptable for an MVP, but worth bumping to a paid plan once there's real traffic.
- **Free Postgres** on Render expires after 30 days. You'll need to either upgrade the DB or migrate to another free Postgres host (Neon, Supabase) before then.
- **Logs**: Render service → Logs tab. Useful when something breaks.
- **Redeploys**: every `git push` to `main` triggers an auto-deploy. Watch the build logs the first few times.

## Troubleshooting

**Build fails on `collectstatic`** → usually a typo in `CLOUDINARY_URL`. Check the env var.

**500 error after deploy** → check Logs. Most common cause: a missing env var. The `prod.py` settings will fail loudly if `DJANGO_ALLOWED_HOSTS`, `SECRET_KEY`, or `SENDGRID_API_KEY` are missing.

**"DisallowedHost" error** → the hostname you're hitting isn't in `DJANGO_ALLOWED_HOSTS`. Add it and redeploy.

**Emails not arriving** → check spam first. If still missing, check Render logs for SMTP errors. If SendGrid says "Sender not verified", revisit Step 1.

**Cert not issued for custom domain** → DNS hasn't propagated yet. Wait 15-30 more minutes, then click "Refresh" in Render's Custom Domains UI.
