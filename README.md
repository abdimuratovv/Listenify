# Listenify

Listenify is an English listening and pronunciation practice application. Learners listen to level-appropriate audio, record their own voices, and choose whether to submit a recording for written feedback. Teachers manage materials, groups, access restrictions, and reviews in the same application.

The interface is currently in Uzbek. This repository contains an MVP under active development; see [Release status](#release-status) before deploying it.

## Features

- Email/password accounts, server-side sessions, password reset, and student/admin roles.
- A searchable audio library with three level bands, scripts, versioned materials, and private media streaming.
- Server-validated listening attempts with interval coverage, elapsed-time checks, and idempotent completion. This measures verified playback events; it cannot prove that a person was paying attention.
- Browser microphone recording, local preview, retryable upload, private recordings, and optional submission for review.
- Group and individual level restrictions, group transfers that preserve results, account blocking, and manual 1–5 reviews with required comments.
- A responsive interface based on the approved Listenify logo and photographic glass direction, with reduced-motion and reduced-transparency options.

## Stack

| Component | Technology |
| --- | --- |
| Backend | Python 3.12+, Django 5.2, Django ORM |
| Frontend | React, TypeScript, Vite |
| Database | SQLite for local development; PostgreSQL for production |
| Media | Private local filesystem, authenticated byte-range streaming, `ffprobe` validation |
| Tests | Django test runner, Playwright/Chromium; PostgreSQL concurrency tests |

The frontend and API share an origin in the production build. During development, Vite proxies `/api` to Django.

## Requirements

- Python 3.12 or newer.
- Node.js 22.12 or newer and npm.
- FFmpeg with `ffprobe` available on `PATH`.
- PostgreSQL for production and database concurrency tests. SQLite is used when `DATABASE_URL` is not set.

Check your environment with `python --version`, `node --version`, `npm --version`, and `ffprobe -version`.

## Quick start

Clone the repository, open a terminal in its root, and create a virtual environment. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

On macOS or Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python` and use `cp .env.example .env`.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). `createsuperuser` prompts for the first administrator's email, name, and password; there is no default administrator password. Sign in as that administrator, open **Admin maydoni → Audiolar → Audio qo‘shish**, and add an audio file and script. Select **E’lon qilingan** to make the material available to eligible students. The initial database is empty.

For frontend development, run `npm run dev` in `frontend/` while Django is running on port 8000, then visit the Vite URL. Set `PUBLIC_ORIGIN` in `.env` to the URL you use for password-reset links. Re-run `npm run build` to update the frontend served by Django.

## Configuration

Copy [`.env.example`](.env.example) to `.env` and adjust it for the environment. Existing process environment variables take precedence over `.env` values.

| Variable | Purpose |
| --- | --- |
| `DEBUG` | Use `1` only for local development; set `0` for deployment. |
| `SECRET_KEY` | Unique Django signing key; required when `DEBUG=0`. |
| `ALLOWED_HOSTS` | Comma-separated permitted hostnames. |
| `PUBLIC_ORIGIN` | Public application origin used in reset links and trusted CSRF origins. |
| `DATABASE_URL` | PostgreSQL URL; omit to use local SQLite. |
| `DB_SSLMODE` | PostgreSQL SSL mode, appropriate to your provider and network. |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` | SMTP transport settings. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP credentials and sender address. |
| `TRUST_PROXY_PROTO` | Set to `1` only when a trusted proxy strips and replaces `X-Forwarded-Proto`. |

Local password reset uses Django's console email backend: the reset link is printed in the server terminal, not sent by email. Configure SMTP before expecting email delivery. Secrets, local databases, virtual environments, uploads, and build output are excluded from Git.

Media limits are 100 MiB / 30 minutes for library audio and 50 MiB / 10 minutes for recordings. Upload size is checked during multipart parsing and again during media validation. Configure an equivalent request-body limit at the reverse proxy to reject oversized requests before they reach the application.

## Development and tests

Install the additional test dependencies and browser:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\ruff.exe check backend manage.py
.\.venv\Scripts\ruff.exe format --check backend manage.py
cd frontend
npm ci
npm run build
npm run format:check
cd ..
.\.venv\Scripts\python.exe manage.py test backend.core.tests.test_domain
.\.venv\Scripts\python.exe manage.py test backend.core.tests.test_browser
```

On macOS or Linux, use `.venv/bin/python` and `.venv/bin/ruff` for these commands.

For PostgreSQL concurrency tests, configure `DATABASE_URL` to a disposable PostgreSQL instance whose user can create a test database, then run:

```powershell
.\.venv\Scripts\python.exe manage.py test backend.core.tests.test_domain backend.core.tests.test_concurrency
```

SQLite skips PostgreSQL-specific locking tests; passing SQLite tests does not establish PostgreSQL concurrency behavior. The browser suite uses a separate test database, synthetic audio, and Chromium's fake microphone. It writes screenshots to the ignored `artifacts/` directory. Physical microphone and cross-browser testing remain necessary.

The GitHub Actions workflow provisions PostgreSQL, builds the frontend, and runs the Django and Chromium suites. A workflow file does not imply that remote CI has already run.

## Deployment and operations

Use PostgreSQL, HTTPS, a persistent private media directory, and a production WSGI server. Set `DEBUG=0`, provide a strong `SECRET_KEY`, configure `ALLOWED_HOSTS`, `PUBLIC_ORIGIN`, database TLS, and SMTP, and run database migrations. For Windows, the included Waitress dependency can serve `backend.config.wsgi:application` behind a trusted HTTPS reverse proxy. Do not expose Django's development server to the internet.

The private media directory must not be served as a public static directory. This implementation stores media on one local filesystem; multiple application instances require a shared persistent volume or a storage adapter. Each download is authorized by the application, but bytes already delivered to a browser cannot be recalled.

Run `python manage.py cleanup_media` on a schedule, such as every five minutes. It retries failed file deletions, removes abandoned uploads older than one day, and expires stale listening attempts. Back up the database and media directory together and test restoration. Monitor failed cleanup jobs, disk capacity, and upload traffic.

## Project structure

```text
backend/config/                 Django settings, URL routing, WSGI
backend/core/                   Models, access policy, listening, media, views, tests
frontend/src/                   React application and styles
docs/brand/                     Approved logo reference and usage notes
docs/superpowers/specs/         Product specification and visual references
docs/plans/                     Implementation plan and historical validation
docs/reviews/                   Review notes
```

## Release status

The main flows are implemented. Local PostgreSQL backend/concurrency and Chromium checks have passed; details and remaining limitations are recorded in [the validation notes](docs/plans/2026-11-02-listenify-validation.md). Before public deployment, repeat verification in the target environment, test real microphones and target browsers, review media rights, configure production services, and run a security and operational review.

## Contributing

Open an issue describing the change before substantial work. Keep secrets and personal recordings out of commits, preserve the approved source assets, and run the relevant backend and frontend checks. For behavior that depends on transactions or concurrent requests, include PostgreSQL coverage.

## License

The source code is available under the [MIT License](LICENSE). The original logo, photographs, and other supplied visual assets should be reviewed separately for ownership and third-party usage rights before public distribution.
