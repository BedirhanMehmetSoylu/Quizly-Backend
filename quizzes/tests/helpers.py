"""Quiz test data in the format Gemini is asked to produce."""

import json


def make_quiz_data(num_questions: int = 10) -> dict:
    """Return a valid quiz dict in the format Gemini is asked to produce."""
    return {
        "title": "Test Quiz",
        "description": "A quiz for testing.",
        "questions": [
            {
                "question_title": f"Question {i}?",
                "question_options": ["A", "B", "C", "D"],
                "answer": "A",
            }
            for i in range(num_questions)
        ],
    }


def make_gemini_response(data: dict | None = None) -> str:
    """Return a raw Gemini response string (JSON text)."""
    return json.dumps(data if data is not None else make_quiz_data())
