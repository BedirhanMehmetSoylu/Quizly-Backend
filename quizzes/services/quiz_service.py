from .youtube_service import download_audio
from .whisper_service import transcribe_audio
from .gemini_service import generate_quiz_from_text

def create_quiz_from_youtube(url):
    audio_path = download_audio(url)
    transcript = transcribe_audio(audio_path)
    quiz_data = generate_quiz_from_text(transcript)
    return quiz_data