"""Tests for parsing and validating Gemini responses."""

import copy
import json

from django.test import SimpleTestCase

from quizzes.utils import GeminiError, _parse_gemini_response, _validate_quiz_data

from .helpers import make_quiz_data


class ParseGeminiResponseTests(SimpleTestCase):
    def test_parses_plain_json(self):
        data = make_quiz_data()
        self.assertEqual(_parse_gemini_response(json.dumps(data)), data)

    def test_strips_json_code_fence(self):
        raw = '```json\n{"title": "T"}\n```'
        self.assertEqual(_parse_gemini_response(raw), {"title": "T"})

    def test_strips_plain_code_fence(self):
        raw = '```\n{"title": "T"}\n```'
        self.assertEqual(_parse_gemini_response(raw), {"title": "T"})

    def test_invalid_json_raises_gemini_error(self):
        for raw in ["", "not json", '{"title": "T"', "```json\n{broken}\n```"]:
            with self.subTest(raw=raw), self.assertLogs("quizzes.utils", level="ERROR"):
                with self.assertRaises(GeminiError):
                    _parse_gemini_response(raw)


class ValidateQuizDataTests(SimpleTestCase):
    def test_valid_data_passes(self):
        _validate_quiz_data(make_quiz_data())

    def assertInvalid(self, data):
        with self.assertRaises(GeminiError):
            _validate_quiz_data(data)

    def test_rejects_non_dict(self):
        self.assertInvalid(["not", "a", "dict"])

    def test_rejects_missing_top_level_keys(self):
        for key in ["title", "description", "questions"]:
            with self.subTest(key=key):
                data = make_quiz_data()
                del data[key]
                self.assertInvalid(data)

    def test_rejects_empty_or_wrong_type_questions(self):
        for questions in [[], "not a list", None]:
            with self.subTest(questions=questions):
                data = make_quiz_data()
                data["questions"] = questions
                self.assertInvalid(data)

    def test_rejects_question_missing_fields(self):
        for key in ["question_title", "question_options", "answer"]:
            with self.subTest(key=key):
                data = make_quiz_data()
                del data["questions"][3][key]
                self.assertInvalid(data)

    def test_rejects_question_that_is_not_a_dict(self):
        data = make_quiz_data()
        data["questions"][0] = "What is Python?"
        self.assertInvalid(data)

    def test_rejects_answer_not_in_options(self):
        data = make_quiz_data()
        data["questions"][0]["answer"] = "Z"
        self.assertInvalid(data)

    def test_does_not_modify_input(self):
        data = make_quiz_data()
        original = copy.deepcopy(data)
        _validate_quiz_data(data)
        self.assertEqual(data, original)
