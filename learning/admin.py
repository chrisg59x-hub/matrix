from django.contrib import admin

from .models import (
    Badge,
    Choice,
    Department,
    JobRole,
    LevelDef,
    Module,
    ModuleAttempt,
    Question,
    RecertRequirement,
    RoleAssignment,
    RoleSkill,
    Skill,
    SupervisorSignoff,
    Team,
    TeamMember,
    UserBadge,
    XPEvent,
)

admin.site.register(JobRole)
admin.site.register(Skill)
admin.site.register(RoleSkill)
admin.site.register(ModuleAttempt)
admin.site.register(XPEvent)
admin.site.register(SupervisorSignoff)
admin.site.register(RecertRequirement)
admin.site.register(LevelDef)
admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(Department)
admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(RoleAssignment)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("module", "order", "qtype", "points", "text")
    list_filter = ("module", "qtype")
    inlines = [ChoiceInline]


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Module)

class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "skill",
        "pass_mark",
        "question_pool_count",
        "shuffle_questions",
        "shuffle_choices",
        "negative_marking",
        "require_viewed",
        "active",
    )
    inlines = [QuestionInline]  # then open Question to add choices
