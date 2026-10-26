# Quizly – Backend

Quizly turns any YouTube video into a multiple-choice quiz. A user submits a YouTube URL, and the backend downloads the audio, transcribes it locally with Whisper and lets Google Gemini generate a 10-question quiz from the transcript. The quiz is stored per user and can be listed, edited and deleted via a REST API.

This repository contains the **REST API backend** (Django + Django REST Framework). Authentication uses JWTs stored in HTTP-only cookies.

The frontend for this project can be found here:
👉 [Quizly Frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)

---

## Demo

▶️ [Demo video](https://youtu.be/Y1HgYNzrFAg) (about 1.5 minutes, pipeline waiting time shortened)

---

## Tech Stack

| | |
|---|---|
| **Framework** | Django 6.0.2 + Django REST Framework |
| **Authentication** | JWT via HTTP-only Cookies (SimpleJWT) |
| **YouTube Download** | yt-dlp (+ yt-dlp-ejs, Deno) |
| **Transcription** | OpenAI Whisper (runs locally) |
| **Quiz Generation** | Google Gemini (default: `gemini-3.8-flash`, configurable) |
| **Database** | SQLite (development) |
| **Tests** | Django `APITestCase` + `unittest.mock` |
| **Language** | Python 3.12+ (tested with 3.13) |

---

## Prerequisites

Besides Python, two **system-wide** tools are required. They are not Python packages, so `pip install -r requirements.txt` cannot install them for you.

### FFmpeg

yt-dlp uses FFmpeg to convert the downloaded audio to mp3, and Whisper uses it to read the audio file.

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

### Deno (JavaScript runtime)

YouTube requires yt-dlp to solve JavaScript challenges. For this, yt-dlp needs an external **JavaScript runtime**. **Deno** is the recommended runtime and the only one enabled by default. Without it, downloads may fail with `HTTP Error 403: Forbidden` or `Requested format is not available`. See the [yt-dlp EJS wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

```bash
# macOS
brew install deno

# Linux
curl -fsSL https://deno.land/install.sh | sh

# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex
```

Verify both installations:

```bash
ffmpeg -version
deno --version
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/BedirhanMehmetSoylu/Quizly-Backend.git
cd Quizly-Backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> `requirements.txt` only covers the Python packages. **FFmpeg** and **Deno** must be installed system-wide (see [Prerequisites](#prerequisites)).

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
WHISPER_MODEL=base
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key. Generate one with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` for local development |
| `GEMINI_API_KEY` | Get yours at https://aistudio.google.com/apikey |
| `GEMINI_MODEL` | Gemini model used for quiz generation (default: `gemini-3.8-flash`). See https://ai.google.dev/gemini-api/docs/models |
| `WHISPER_MODEL` | `tiny` · `base` · `small` · `medium` · `large` (larger = more accurate, slower) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of frontend origins |

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000`.

> Creating a quiz takes a while: for a 2–3 minute video, expect roughly 1–2 minutes (download + transcription + AI generation). On the very first request, Whisper also downloads its model (~140 MB for `base`).

---

## Tests

```bash
python manage.py test
```

The test suite covers registration, login with cookies, token refresh, logout with token blacklisting (also with an expired access cookie), quiz creation (including all error cases), listing/updating/deleting quizzes, access to other users' quizzes and unauthenticated access, as well as parsing and validation of Gemini responses.

**No API keys, no internet connection and no Whisper model are needed.** The pipeline steps (`download_audio`, `transcribe_audio`, `_call_gemini`) are replaced by mocks, and the tests run against a temporary in-memory database.

```bash
python manage.py test users     # auth tests only
python manage.py test quizzes   # quiz tests only
```

---

## API Reference

All endpoints are prefixed with `/api/`. Error responses have the form `{"detail": "..."}` (or field errors for validation failures).

| Method | Endpoint | Description | Auth | Status codes |
|--------|----------|-------------|------|--------------|
| `POST` | `/api/register/` | Register a new user | ❌ | `201` created · `400` invalid data, passwords don't match or email taken |
| `POST` | `/api/login/` | Login and receive JWT cookies | ❌ | `200` OK · `401` invalid credentials |
| `POST` | `/api/token/refresh/` | Issue a new access token cookie | ❌ (refresh cookie) | `200` OK · `401` refresh token missing, invalid or blacklisted |
| `POST` | `/api/logout/` | Blacklist refresh token and delete cookies | ❌ (refresh cookie) | `200` OK (also with an expired access cookie or no cookies at all) |
| `GET` | `/api/quizzes/` | List all quizzes of the logged-in user | ✅ | `200` OK · `401` not logged in |
| `POST` | `/api/quizzes/` | Create a quiz from a YouTube URL | ✅ | `201` created · `400` invalid URL or video unavailable/private · `401` not logged in · `502` YouTube or Gemini error · `500` server error |
| `GET` | `/api/quizzes/{id}/` | Get a quiz with all questions | ✅ | `200` OK · `401` not logged in · `403` quiz belongs to another user · `404` not found |
| `PATCH` | `/api/quizzes/{id}/` | Update title and/or description | ✅ | `200` OK · `400` blank title or empty body · `401` · `403` · `404` |
| `DELETE` | `/api/quizzes/{id}/` | Delete a quiz | ✅ | `204` deleted · `401` · `403` · `404` |

### Request bodies

**Register** – `POST /api/register/`
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "securepassword",
  "confirmed_password": "securepassword"
}
```

**Login** – `POST /api/login/`
```json
{
  "username": "john",
  "password": "securepassword"
}
```

**Create Quiz** – `POST /api/quizzes/`
```json
{
  "url": "https://www.youtube.com/watch?v=example"
}
```

**Update Quiz** – `PATCH /api/quizzes/{id}/`
```json
{
  "title": "Updated Title",
  "description": "Updated Description"
}
```

### Quiz response example

```json
{
  "id": 1,
  "title": "Quiz Title",
  "description": "Quiz Description",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "video_url": "https://www.youtube.com/watch?v=example",
  "questions": [
    {
      "id": 1,
      "question_title": "What is the capital of Germany?",
      "question_options": ["Berlin", "Munich", "Hamburg", "Frankfurt"],
      "answer": "Berlin"
    }
  ]
}
```

### Error response example

```json
{
  "detail": "The quiz could not be generated by the AI service. Please try again later."
}
```

Internal error details (e.g. raw messages from yt-dlp or Gemini) are never returned to the client. They are written to the server log instead.

---

## Authentication Flow

Authentication is handled via **JWT tokens in HTTP-only cookies**. The frontend has no direct access to the tokens.

```
POST /api/login/
  → sets access_token cookie  (valid 30 minutes)
  → sets refresh_token cookie (valid 7 days)

POST /api/token/refresh/
  → reads refresh_token cookie
  → sets new access_token cookie (valid 30 minutes)

POST /api/logout/
  → blacklists refresh_token (if present)
  → deletes both cookies
  → works without a valid access token, so an expired session can always be ended
```

Cookie lifetimes are taken from `ACCESS_TOKEN_LIFETIME` and `REFRESH_TOKEN_LIFETIME` in `SIMPLE_JWT` (`core/settings.py`).

---

## Quiz Generation Pipeline

```
YouTube URL
   ↓  yt-dlp (+ Deno for YouTube's JS challenges)
   Audio (.mp3) downloaded to a temporary directory
   ↓  OpenAI Whisper (local)
   Plain-text transcript
   ↓  Google Gemini (model from GEMINI_MODEL)
   10 questions × 4 options + title + description
   ↓  Validation + Django ORM
   Quiz saved to database and returned as JSON
```

---

## Troubleshooting

Check the server log (the terminal running `runserver`) first. Warnings from yt-dlp and the full error details of failed requests are logged there.

| Problem | Cause | Solution |
|---|---|---|
| `ffmpeg: command not found`, or quiz creation fails with a download/transcription error | FFmpeg is not installed or not on your `PATH` | Install FFmpeg (see [Prerequisites](#prerequisites)) and check with `ffmpeg -version`. Restart the terminal afterwards. |
| `502` on quiz creation, log shows `HTTP Error 403: Forbidden`, `Requested format is not available` or `No supported JavaScript runtime could be found` | YouTube changed something, yt-dlp is outdated or Deno is missing | Install Deno (`deno --version`) and update yt-dlp: `pip install -U "yt-dlp[default]"`. Then update the pinned versions of `yt-dlp` and `yt-dlp-ejs` in `requirements.txt`. |
| `400` "This video is unavailable" | The video does not exist, is private, age-restricted or region-locked | Use a public YouTube video. |
| `500` "Quiz generation is not configured on the server." | `GEMINI_API_KEY` is missing in `.env` | Add your key from https://aistudio.google.com/apikey and restart the server. |
| `502` on quiz creation, log shows `API key not valid` | The Gemini API key is invalid, expired or deleted | Create a new key at https://aistudio.google.com/apikey and update `.env`. |
| `502` on quiz creation, log shows `404 NOT_FOUND` / `model ... is no longer available` | The configured Gemini model was retired or is not available for your key | Pick a current model from https://ai.google.dev/gemini-api/docs/models and set it as `GEMINI_MODEL` in `.env`. |
| `502` on quiz creation, log shows `503 UNAVAILABLE` / `high demand` | Gemini is temporarily overloaded | Wait a moment and try again, or switch `GEMINI_MODEL` to another model. |
| Quiz creation takes very long | Long video, large `WHISPER_MODEL`, or the Whisper model is downloaded on the first run | Use a shorter video or a smaller `WHISPER_MODEL` (e.g. `tiny` or `base`). |
| Login succeeds in the frontend, but every following request returns `401` | The frontend is opened via `http://localhost:…` while it calls the API at `http://127.0.0.1:8000`. For the browser these are different sites, so the `SameSite=Lax` auth cookies are not sent. | Open the frontend via `http://127.0.0.1:5500` (same host as `API_BASE_URL` in the frontend's `shared/js/config.js`). |

---

## Known Limitations

These concern the [Quizly Frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly), which is used as provided and not modified in this project:

- **Quiz creation errors are shown generically.** The backend returns a specific message in `detail` (e.g. "This video is unavailable…"), but the frontend always shows "Error generating quiz".
- **Registration errors are shown incompletely.** The frontend only displays the `username` field error. Other errors (e.g. email already registered, passwords don't match) appear as "Register failed: undefined". The API response itself contains the correct error message.

---

## Project Structure

```
Quizly-Backend/
├── core/                       # Django project settings and root URL config
├── users/                      # Authentication app
│   ├── api/
│   │   ├── views.py            # Register, Login, Logout, Token Refresh
│   │   ├── serializers.py      # RegisterSerializer with validation
│   │   └── urls.py
│   ├── tests/
│   │   ├── helpers.py          # Shared test helpers (create_user, login)
│   │   └── test_auth.py
│   ├── authentication.py       # CookieJWTAuthentication class
│   └── utils.py                # Token generation, cookie helpers
├── quizzes/                    # Quiz management app
│   ├── api/
│   │   ├── views.py            # Quiz API views + error-to-status mapping
│   │   ├── serializers.py      # Quiz serializers
│   │   └── urls.py
│   ├── tests/
│   │   ├── helpers.py          # Quiz test data
│   │   ├── test_quiz_api.py
│   │   └── test_utils.py
│   ├── models.py               # Quiz, Question, QuestionOption
│   ├── utils.py                # YouTube → Whisper → Gemini pipeline
│   └── admin.py                # Admin panel configuration
├── .env.example                # Environment variable template
├── LICENSE
├── requirements.txt
└── manage.py
```

---

## Admin Panel

Available at `http://127.0.0.1:8000/admin/`

- View, create, edit and delete quizzes
- Edit individual questions and answer options inline
- Manage user accounts

---

## License

This project is licensed under the [MIT License](LICENSE).
