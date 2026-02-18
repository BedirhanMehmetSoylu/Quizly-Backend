import google.generativeai as genai
from django.conf import settings
import json

genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_quiz_from_text(text):

    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    Create a quiz based on the following transcript.
    Return valid JSON in this format:

    {{
      "title": "...",
      "description": "...",
      "questions": [
        {{
          "question_title": "...",
          "question_options": ["A", "B", "C", "D"],
          "answer": "A"
        }}
      ]
    }}

    Transcript:
    {text}
    """

    response = model.generate_content(prompt)

    return json.loads(response.text)
