from django.contrib import admin
from django.db.models import Count
from .models import Quiz, Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = (
        "question_title",
        "question_options",
        "answer",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("created_at", "updated_at")
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "user",
        "is_completed",
        "score",
        "question_count",
        "created_at",
    )

    list_filter = (
        "is_completed",
        "created_at",
        "user",
    )

    search_fields = (
        "title",
        "description",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [QuestionInline]

    ordering = ("-created_at",)

    list_select_related = ("user",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _question_count=Count("questions")
        )

    def question_count(self, obj):
        return obj._question_count

    question_count.short_description = "Questions"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "question_title",
        "quiz",
        "created_at",
    )

    list_filter = (
        "quiz",
        "created_at",
    )

    search_fields = (
        "question_title",
        "quiz__title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = ("quiz",)