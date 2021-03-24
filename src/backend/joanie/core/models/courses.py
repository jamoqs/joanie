"""
Declare and configure the models for the courses part
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from parler import models as parler_models


class Organization(parler_models.TranslatableModel):
    """
    Organization model represents and records entities that manage courses.
    It could be a university or a training company for example.
    It's required to create course page in cms.
    It will allow to validate user enrollment to course or not, depending on various criteria.
    """

    code = models.CharField(_("code"), unique=True, max_length=100)
    translations = parler_models.TranslatedFields(
        title=models.CharField(_("title"), max_length=255)
    )

    class Meta:
        db_table = "joanie_organization"
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    def __str__(self):
        return (
            f"[{self.code}] {self.safe_translation_getter('title', any_language=True)}"
        )


class Course(parler_models.TranslatableModel):
    """
    Course model represents and records a course in the cms catalog.
    A new course created will initialize a cms page.
    """

    code = models.CharField(_("reference to cms page"), max_length=100, unique=True)
    translations = parler_models.TranslatedFields(
        title=models.CharField(_("title"), max_length=255)
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name=_("organization"),
        on_delete=models.PROTECT,
    )

    class Meta:
        db_table = "joanie_course"
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")

    def __str__(self):
        return self.safe_translation_getter("title", any_language=True)


class CourseRun(parler_models.TranslatableModel):
    """
    Course run represents and records the occurrence of a course between a start
    and an end date.
    """

    # link to lms resource
    resource_link = models.CharField(
        _("resource link"), max_length=200, blank=True, null=True
    )
    translations = parler_models.TranslatedFields(
        title=models.CharField(_("title"), max_length=255)
    )
    # availability period
    start = models.DateTimeField(_("course start"))
    end = models.DateTimeField(_("course end"))
    # enrollment allowed period
    enrollment_start = models.DateTimeField(_("enrollment date"), null=True)
    enrollment_end = models.DateTimeField(_("enrollment end"), null=True)

    class Meta:
        db_table = "joanie_course_run"
        verbose_name = _("Course run")
        verbose_name_plural = _("Course runs")

    def __str__(self):
        return (
            f"Run \"{self.safe_translation_getter('title', any_language=True)}\" "
            f"[{self.start:%Y-%m-%d} to {self.end:%Y-%m-%d}]"
        )
