# Quizly – Backend

Quizly is a REST API backend for an AI-powered quiz application. Users submit a YouTube URL, which gets automatically converted into a 10-question multiple-choice quiz – powered by Whisper AI for transcription and Google Gemini for quiz generation.

The frontend for this project can be found here:
👉 [Quizly Frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)

---

## Tech Stack

| | |
|---|---|
| **Framework** | Django 6.0.2 + Django REST Framework |
| **Authentication** | JWT via HTTP-only Cookies (SimpleJWT) |
| **YouTube Download** | yt-dlp |
| **Transcription** | OpenAI Whisper (runs locally) |
| **Quiz Generation** | Google Gemini 2.5 Flash |
| **Database** | SQLite (development) |
| **Language** | Python 3.12+ |

---

## ⚠️ FFmpeg Required

> Whisper AI requires **FFmpeg** to be installed **globally** on your system to process audio files.

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

Verify your installation:

```bash
ffmpeg -version
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

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
GEMINI_API_KEY=your_google_gemini_api_key
WHISPER_MODEL=base
```

> **GEMINI_API_KEY** – Get yours at https://aistudio.google.com/apikey  
> **WHISPER_MODEL** – `tiny` · `base` · `small` · `medium` · `large` (larger = more accurate, slower)

### 5. Apply migrations

```bash
python manage.py makemigrations
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

The API is now available at `http://127.0.0.1:8000`

---

## Project Structure

```
Quizly-Backend/
├── core/                   # Django project settings and root URL config
├── users/                  # Authentication app
│   ├── views.py            # Register, Login, Logout, Token Refresh
│   ├── serializers.py      # RegisterSerializer with validation
│   ├── utils.py            # Token generation, cookie helpers
│   ├── authentication.py   # CookieJWTAuthentication class
│   └── urls.py
├── quizzes/                # Quiz management app
│   ├── models.py           # Quiz, Question, QuestionOption
│   ├── views.py            # Quiz API views
│   ├── serializers.py      # Quiz serializers
│   ├── utils.py            # YouTube → Whisper → Gemini pipeline
│   ├── admin.py            # Admin panel configuration
│   └── urls.py
├── .env.example            # Environment variable template
├── .gitignore
├── requirements.txt
└── manage.py
```

---

## API Reference

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/register/` | Register a new user | ❌ |
| `POST` | `/api/login/` | Login and receive JWT cookies | ❌ |
| `POST` | `/api/logout/` | Logout and blacklist refresh token | ✅ |
| `POST` | `/api/token/refresh/` | Issue new access token | ❌ |

**Register** – `POST /api/users/register/`
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "securepassword",
  "confirmed_password": "securepassword"
}
```

**Login** – `POST /api/users/login/`
```json
{
  "username": "john",
  "password": "securepassword"
}
```

---

### Quizzes

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/quizzes/` | List all quizzes of the logged-in user | ✅ |
| `POST` | `/api/quizzes/` | Create a quiz from a YouTube URL | ✅ |
| `GET` | `/api/quizzes/{id}/` | Get a quiz with all questions | ✅ |
| `PATCH` | `/api/quizzes/{id}/` | Update quiz title and/or description | ✅ |
| `DELETE` | `/api/quizzes/{id}/` | Delete a quiz | ✅ |

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

**Quiz Response Example**
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

---

## Authentication Flow

Authentication is handled via **JWT tokens in HTTP-only cookies**. The frontend has no direct access to the tokens.

```
POST /login
  → sets access_token cookie  (valid 15 minutes)
  → sets refresh_token cookie (valid 7 days)

POST /token/refresh/
  → reads refresh_token cookie
  → sets new access_token cookie

POST /logout/
  → blacklists refresh_token
  → deletes both cookies
```

---

## Quiz Generation Pipeline

```
YouTube URL
   ↓  yt-dlp
   Audio (.mp3) downloaded to a temporary directory
   ↓  OpenAI Whisper (local)
   Plain-text transcript
   ↓  Google Gemini 2.5 Flash
   10 questions × 4 options + title + description
   ↓  Django ORM
   Quiz saved to database and returned as JSON
```

---

## Admin Panel

Available at `http://127.0.0.1:8000/admin/`

- View, create, edit and delete quizzes
- Edit individual questions and answer options inline
- Manage user accounts
