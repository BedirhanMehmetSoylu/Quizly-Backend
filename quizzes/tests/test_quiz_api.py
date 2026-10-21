"""Tests for the quiz endpoints. The pipeline (yt-dlp, Whisper, Gemini) is mocked."""

from unittest import mock

from rest_framework import status
from rest_framework.test import APITestCase

from quizzes.models import Question, QuestionOption, Quiz
from quizzes.utils import DownloadError, VideoUnavailableError
from users.tests.helpers import create_user, login

from .helpers import make_gemini_response

VIDEO_URL = "https://www.youtube.com/watch?v=x7X9w_GIm1s"


def create_quiz(user, title="Existing Quiz") -> Quiz:
    quiz = Quiz.objects.create(title=title, description="desc", video_url=VIDEO_URL, created_by=user)
    question = Question.objects.create(quiz=quiz, question_title="Q?", answer="A")
    for text in ["A", "B", "C", "D"]:
        QuestionOption.objects.create(question=question, text=text)
    return quiz


@mock.patch("quizzes.utils.GEMINI_API_KEY", "test-key")
@mock.patch("quizzes.utils._call_gemini")
@mock.patch("quizzes.utils.transcribe_audio", return_value="A transcript about Python.")
@mock.patch("quizzes.utils.download_audio", return_value="/tmp/fake.mp3")
class QuizCreateTests(APITestCase):
    url = "/api/quizzes/"

    def setUp(self):
        self.user = create_user("alice")
        login(self.client)

    def test_create_quiz_runs_pipeline_and_saves_quiz(self, mock_download, mock_transcribe, mock_gemini):
        mock_gemini.return_value = make_gemini_response()

        response = self.client.post(self.url, {"url": VIDEO_URL}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Quiz")
        self.assertEqual(response.data["video_url"], VIDEO_URL)
        self.assertEqual(len(response.data["questions"]), 10)
        first = response.data["questions"][0]
        self.assertEqual(first["question_options"], ["A", "B", "C", "D"])
        self.assertEqual(first["answer"], "A")
        self.assertIn("created_at", first)

        quiz = Quiz.objects.get()
        self.assertEqual(quiz.created_by, self.user)
        self.assertEqual(quiz.questions.count(), 10)
        self.assertEqual(QuestionOption.objects.count(), 40)

        self.assertEqual(mock_download.call_args.args[0], VIDEO_URL)
        mock_transcribe.assert_called_once_with("/tmp/fake.mp3")
        self.assertIn("A transcript about Python.", mock_gemini.call_args.args[0])

    def test_invalid_url_returns_400_without_running_pipeline(self, mock_download, mock_transcribe, mock_gemini):
        response = self.client.post(self.url, {"url": "https://example.com/video"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data)
        mock_download.assert_not_called()

    def test_unavailable_video_returns_400(self, mock_download, mock_transcribe, mock_gemini):
        mock_download.side_effect = VideoUnavailableError("ERROR: [youtube] xyz: This video is unavailable")

        with self.assertLogs("quizzes.api.views", level="WARNING"):
            response = self.client.post(self.url, {"url": VIDEO_URL}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("[youtube]", response.data["detail"])
        self.assertFalse(Quiz.objects.exists())

    def test_youtube_download_failure_returns_502(self, mock_download, mock_transcribe, mock_gemini):
        mock_download.side_effect = DownloadError("HTTP Error 403: Forbidden")

        with self.assertLogs("quizzes.api.views", level="WARNING"):
            response = self.client.post(self.url, {"url": VIDEO_URL}, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertNotIn("403", response.data["detail"])

    def test_gemini_api_error_returns_502_without_raw_message(self, mock_download, mock_transcribe, mock_gemini):
        mock_gemini.side_effect = RuntimeError("503 UNAVAILABLE internal details")

        with self.assertLogs("quizzes.api.views", level="WARNING") as logs:
            response = self.client.post(self.url, {"url": VIDEO_URL}, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertNotIn("internal details", response.data["detail"])
        self.assertIn("internal details", logs.output[0])
        self.assertFalse(Quiz.objects.exists())

    def test_invalid_gemini_json_returns_502(self, mock_download, mock_transcribe, mock_gemini):
        mock_gemini.return_value = "this is not json"

        with self.assertLogs("quizzes", level="WARNING"):
            response = self.client.post(self.url, {"url": VIDEO_URL}, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertFalse(Quiz.objects.exists())

    def test_missing_api_key_returns_500(self, mock_download, mock_transcribe, mock_gemini):
        with mock.patch("quizzes.utils.GEMINI_API_KEY", ""), self.assertLogs("quizzes.api.views", level="WARNING"):
            response = self.client.post(self.url, {"url": VIDEO_URL}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertNotIn("GEMINI_API_KEY", response.data["detail"])
        mock_gemini.assert_not_called()

    def test_unexpected_error_returns_generic_500(self, mock_download, mock_transcribe, mock_gemini):
        mock_download.side_effect = KeyError("secret detail")

        with self.assertLogs("quizzes.api.views", level="ERROR"):
            response = self.client.post(self.url, {"url": VIDEO_URL}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detail"], "An unexpected error occurred.")


class QuizReadUpdateDeleteTests(APITestCase):
    def setUp(self):
        self.user = create_user("alice")
        self.quiz = create_quiz(self.user)
        login(self.client)

    def detail_url(self, quiz=None):
        return f"/api/quizzes/{(quiz or self.quiz).pk}/"

    def test_list_returns_only_own_quizzes(self):
        create_quiz(create_user("mallory"), title="Foreign Quiz")

        response = self.client.get("/api/quizzes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([q["title"] for q in response.data], ["Existing Quiz"])
        self.assertEqual(response.data[0]["questions"][0]["question_options"], ["A", "B", "C", "D"])

    def test_retrieve_quiz(self):
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.quiz.pk)
        self.assertEqual(len(response.data["questions"]), 1)

    def test_retrieve_missing_quiz_returns_404(self):
        response = self.client.get("/api/quizzes/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_updates_title_and_description(self):
        response = self.client.patch(
            self.detail_url(), {"title": "New Title", "description": "New desc"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, "New Title")
        self.assertEqual(self.quiz.description, "New desc")

    def test_patch_ignores_read_only_fields(self):
        response = self.client.patch(
            self.detail_url(), {"title": "New", "video_url": "https://evil.example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.video_url, VIDEO_URL)

    def test_patch_rejects_blank_title(self):
        response = self.client.patch(self.detail_url(), {"title": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_rejects_empty_body(self):
        response = self.client.patch(self.detail_url(), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_removes_quiz_and_questions(self):
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.exists())
        self.assertFalse(Question.objects.exists())
        self.assertFalse(QuestionOption.objects.exists())


class QuizPermissionTests(APITestCase):
    def setUp(self):
        self.owner = create_user("alice")
        self.quiz = create_quiz(self.owner)
        create_user("mallory")
        self.url = f"/api/quizzes/{self.quiz.pk}/"

    def test_foreign_quiz_cannot_be_read_updated_or_deleted(self):
        login(self.client, "mallory")

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.patch(self.url, {"title": "Hacked"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_403_FORBIDDEN)

        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, "Existing Quiz")

    def test_unauthenticated_requests_return_401(self):
        requests = [
            ("get", "/api/quizzes/"),
            ("post", "/api/quizzes/"),
            ("get", self.url),
            ("patch", self.url),
            ("delete", self.url),
        ]
        for method, url in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, format="json")
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Quiz.objects.filter(pk=self.quiz.pk).exists())

    def test_invalid_access_cookie_returns_401(self):
        self.client.cookies["access_token"] = "not-a-jwt"
        response = self.client.get("/api/quizzes/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
