"""
Helper functions for the quiz creation pipeline:
  1. Download audio from YouTube (yt-dlp)
  2. Transcribe audio (Whisper)
  3. Generate quiz data (Gemini)
  4. Save quiz to database
"""

import json
import logging
import os
import re
import tempfile

from google import genai
from google.genai import types
import whisper
import yt_dlp

from .models import Quiz, Question, QuestionOption

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")


class QuizPipelineError(Exception):
    """Base class for all errors raised by the quiz creation pipeline."""


class VideoUnavailableError(QuizPipelineError):
    """The video does not exist, is private or the URL is not supported."""


class DownloadError(QuizPipelineError):
    """YouTube could not be reached or refused the download."""


class TranscriptionError(QuizPipelineError):
    """Whisper could not transcribe the audio."""


class GeminiError(QuizPipelineError):
    """The Gemini API failed or returned unusable data."""


class ConfigurationError(QuizPipelineError):
    """A required setting (e.g. the API key) is missing."""

GEMINI_PROMPT_TEMPLATE = """
You are a quiz creation assistant.
Based on the following transcript, create exactly 10 multiple-choice questions.
Each question must have exactly 4 answer options, with exactly 1 correct answer.
Also generate a concise quiz title (max 80 chars) and a short description (max 200 chars).
Return ONLY valid JSON in this exact structure:
{{
  "title": "<quiz title>",
  "description": "<quiz description>",
  "questions": [
    {{
      "question_title": "<question text>",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"
    }}
  ]
}}
The "answer" field must be the exact text of the correct option from "question_options".
Transcript:
\"\"\"
{transcript}
\"\"\"
"""


class _YtDlpLogger:
    """Forward yt-dlp output to Python logging instead of stdout."""

    def debug(self, msg):
        logger.debug(msg)

    def info(self, msg):
        logger.info(msg)

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        logger.error(msg)


def _build_ydl_opts(output_dir: str) -> dict:
    """Return yt-dlp options for mp3 audio extraction."""
    return {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}],
        "quiet": True,
        "logger": _YtDlpLogger(),
    }


def download_audio(youtube_url: str, output_dir: str) -> str:
    """Download audio from a YouTube URL and return the mp3 file path."""
    try:
        with yt_dlp.YoutubeDL(_build_ydl_opts(output_dir)) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
    except yt_dlp.utils.DownloadError as exc:
        cause = exc.exc_info[1] if exc.exc_info else None
        if isinstance(cause, yt_dlp.utils.ExtractorError) and cause.expected:
            raise VideoUnavailableError(str(exc)) from exc
        raise DownloadError(str(exc)) from exc
    audio_path = os.path.join(output_dir, f"{info['id']}.mp3")
    if not os.path.exists(audio_path):
        raise DownloadError(f"Audio file not found at {audio_path} (is ffmpeg installed?)")
    return audio_path


def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file with Whisper and return the plain-text transcript."""
    try:
        result = whisper.load_model(WHISPER_MODEL_SIZE).transcribe(audio_path, fp16=False)
        text = result.get("text", "").strip()
        if not text:
            raise ValueError("Whisper returned an empty transcript.")
        return text
    except Exception as exc:
        raise TranscriptionError(f"Could not transcribe {audio_path}: {exc}") from exc


def _call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the raw response text."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return response.text.strip()


def _parse_gemini_response(raw: str) -> dict:
    """Strip code fences and parse JSON from a Gemini response."""
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned invalid JSON: %s", raw[:500])
        raise GeminiError(f"Gemini returned invalid JSON: {exc}") from exc


def _validate_quiz_data(data: dict) -> None:
    """Validate the structure of the Gemini quiz response."""
    if not isinstance(data, dict):
        raise GeminiError("Gemini response is not a JSON object.")
    required_keys = {"title", "description", "questions"}
    if not required_keys.issubset(data):
        raise GeminiError(f"Missing keys in Gemini response: {required_keys - data.keys()}")
    if not isinstance(data["questions"], list) or not data["questions"]:
        raise GeminiError("Gemini response contains no questions.")
    for i, q in enumerate(data["questions"]):
        if not isinstance(q, dict) or not {"question_title", "question_options", "answer"}.issubset(q):
            raise GeminiError(f"Question {i} is missing required fields.")
        if q["answer"] not in q["question_options"]:
            raise GeminiError(f"Question {i}: answer is not in question_options.")


def generate_quiz_data(transcript: str) -> dict:
    """Send the transcript to Gemini and return the validated quiz dict."""
    if not GEMINI_API_KEY:
        raise ConfigurationError("GEMINI_API_KEY is not set in the environment.")
    try:
        prompt = GEMINI_PROMPT_TEMPLATE.format(transcript=transcript)
        raw = _call_gemini(prompt)
    except Exception as exc:
        raise GeminiError(f"Gemini API call failed (model {GEMINI_MODEL}): {exc}") from exc
    data = _parse_gemini_response(raw)
    _validate_quiz_data(data)
    return data


def _create_questions(quiz: Quiz, questions_data: list) -> None:
    """Persist questions and their options for a quiz."""
    for q_data in questions_data:
        question = Question.objects.create(
            quiz=quiz,
            question_title=q_data["question_title"],
            answer=q_data["answer"],
        )
        for option_text in q_data["question_options"]:
            QuestionOption.objects.create(question=question, text=option_text)


def save_quiz_to_db(data: dict, youtube_url: str, user) -> Quiz:
    """Create and return a Quiz with all questions and options saved to the DB."""
    quiz = Quiz.objects.create(
        title=data["title"],
        description=data.get("description", ""),
        video_url=youtube_url,
        created_by=user,
    )
    _create_questions(quiz, data["questions"])
    return quiz


def create_quiz_from_youtube(youtube_url: str, user) -> Quiz:
    """Full pipeline: YouTube URL → transcription → Gemini → Quiz saved in DB."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        logger.info("Downloading audio for %s", youtube_url)
        audio_path = download_audio(youtube_url, tmp_dir)
        logger.info("Transcribing audio at %s", audio_path)
        transcript = transcribe_audio(audio_path)
    logger.info("Generating quiz via Gemini (transcript length: %d chars)", len(transcript))
    quiz_data = generate_quiz_data(transcript)
    logger.info("Saving quiz '%s' to database", quiz_data.get("title"))
    return save_quiz_to_db(quiz_data, youtube_url, user)