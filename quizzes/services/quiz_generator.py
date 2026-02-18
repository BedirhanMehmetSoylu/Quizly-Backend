import json
import re
import google.generativeai as genai
from django.conf import settings


def generate_quiz_from_youtube(video_url: str) -> dict:
    genai.configure(api_key=settings.GEMINI_API_KEY)

    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    Create a multiple choice quiz based on this YouTube video:
    {video_url}

    Return ONLY valid JSON in this exact format:

    {{
      "title": "Quiz title",
      "description": "Short description",
      "questions": [
        {{
          "question_title": "Question text",
          "question_options": [
            "Option 1",
            "Option 2",
            "Option 3",
            "Option 4"
          ],
          "answer": "Correct option exactly as written above"
        }}
      ]
    }}

    Do NOT prefix options with A., B., C., or D.
    No explanations. No markdown. Only JSON.
    """

    response = model.generate_content(prompt)

    raw_text = response.text.strip()

    raw_text = re.sub(r"^```json", "", raw_text)
    raw_text = re.sub(r"^```", "", raw_text)
    raw_text = re.sub(r"```$", "", raw_text)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise Exception("AI did not return valid JSON.")

    return parsed
