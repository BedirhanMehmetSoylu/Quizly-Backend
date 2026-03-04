"""
Admin configuration for Quiz, Question and QuestionOption models.
"""

from django.contrib import admin
from .models import Quiz, Question, QuestionOption


class QuestionOptionInline(admin.TabularInline):
    """Inline editor for answer options within a question."""

    model = QuestionOption
    extra = 0


class QuestionInline(admin.StackedInline):
    """Inline editor for questions within a quiz."""

    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin view for quizzes – supports editing title, description and video URL."""

    list_display = ["id", "title", "created_by", "created_at"]
    list_filter = ["created_by", "created_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin view for questions – supports editing title and correct answer."""

    list_display = ["id", "quiz", "question_title", "answer"]
    list_filter = ["quiz"]
    search_fields = ["question_title"]
    inlines = [QuestionOptionInline]


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    """Admin view for individual answer options."""

    list_display = ["id", "question", "text"]
    list_filter = ["question__quiz"]