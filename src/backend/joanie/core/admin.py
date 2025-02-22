"""
Core application admin
"""

from django.contrib import admin, messages
from django.contrib.admin.options import csrf_protect_m
from django.contrib.auth import admin as auth_admin
from django.http import HttpResponseRedirect
from django.urls import re_path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from admin_auto_filters.filters import AutocompleteFilter
from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from django_object_actions import DjangoObjectActions, takes_instance_or_queryset
from parler.admin import TranslatableAdmin

from joanie.core import forms, helpers, models
from joanie.core.enums import PRODUCT_TYPE_CERTIFICATE_ALLOWED

ACTION_NAME_GENERATE_CERTIFICATES = "generate_certificates"
ACTION_NAME_CANCEL = "cancel"


def summarize_certification_to_user(request, count):
    """
    Display a message after generate_certificates command has been launched
    """
    if count == 0:
        messages.warning(
            request,
            _("No certificates have been generated."),
        )
    else:
        messages.success(
            request,
            ngettext_lazy(  # pylint: disable=no-member
                "{:d} certificate has been generated.",
                "{:d} certificates have been generated.",
                count,
            ).format(count),
        )


# Admin filters


class RequiredFilterMixin:
    """Make filter required ie don't show any results until it has a value."""

    def queryset(self, request, queryset):
        """Don't return any results until a value is selected in the filter."""
        if self.value():
            return super().queryset(request, queryset)

        return super().queryset(request, queryset).none()


class CourseFilter(AutocompleteFilter):
    """Filter on a "course" foreign key."""

    title = _("Course")
    field_name = "course"


class ProductFilter(AutocompleteFilter):
    """Filter on a "product" foreign key."""

    title = _("Product")
    field_name = "product"


class OrganizationFilter(AutocompleteFilter):
    """Filter on an "organization" foreign key."""

    title = _("Organization")
    field_name = "organization"


class OwnerFilter(AutocompleteFilter):
    """Filter on an "owner" foreign key."""

    title = _("Owner")
    field_name = "owner"


class RequiredOwnerFilter(RequiredFilterMixin, AutocompleteFilter):
    """Required filter on an "owner" foreign key."""

    title = _("Owner")
    field_name = "owner"


class RequiredUserFilter(RequiredFilterMixin, AutocompleteFilter):
    """Required filter on an "user" foreign key."""

    title = _("User")
    field_name = "user"


class CourseRunFilter(AutocompleteFilter):
    """Filter on a "course_run" foreign key."""

    title = _("Course run")
    field_name = "course_run"


# Admin registers


@admin.register(models.CertificateDefinition)
class CertificateDefinitionAdmin(TranslatableAdmin):
    """Admin class for the CertificateDefinition model"""

    list_display = ("name", "title")


@admin.register(models.Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin class for the Certificate model"""

    list_display = ("order", "owner", "issued_on")
    readonly_fields = ("order", "issued_on", "owner", "certificate_definition")

    def owner(self, obj):  # pylint: disable=no-self-use
        """Retrieve the owner of the certificate from the related order."""
        return obj.order.owner


class CourseProductRelationInline(admin.StackedInline):
    """Admin class for the CourseProductRelation model"""

    form = forms.CourseProductRelationAdminForm
    model = models.Course.products.through
    extra = 0
    autocomplete_fields = ["product"]


class CourseCourseRunsInline(admin.TabularInline):
    """Admin class for the CourseCourseRunsInline"""

    model = models.CourseRun
    show_change_link = True

    readonly_fields = (
        "title",
        "resource_link",
        "enrollment_start",
        "enrollment_end",
        "start",
        "end",
        "is_listed",
        "is_gradable",
    )
    fields = (
        "title",
        "resource_link",
        "enrollment_start",
        "enrollment_end",
        "start",
        "end",
        "is_listed",
        "is_gradable",
    )
    extra = 0


@admin.register(models.Course)
class CourseAdmin(DjangoObjectActions, TranslatableAdmin):
    """Admin class for the Course model"""

    actions = (ACTION_NAME_GENERATE_CERTIFICATES,)
    autocomplete_fields = ["organizations"]
    change_actions = (ACTION_NAME_GENERATE_CERTIFICATES,)
    change_form_template = "joanie/admin/translatable_change_form_with_actions.html"
    list_display = ("code", "title", "state")
    readonly_fields = ("course_runs",)
    filter_horizontal = ("products",)
    inlines = (CourseCourseRunsInline, CourseProductRelationInline)
    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "code",
                    "title",
                    "cover",
                )
            },
        ),
        (
            _("Organizations"),
            {
                "description": _("Select organizations that author this course."),
                "fields": ("organizations",),
            },
        ),
    )
    search_fields = ["code", "title"]

    @takes_instance_or_queryset
    def generate_certificates(self, request, queryset):  # pylint: disable no-self-use
        """
        Custom action to generate certificates for a collection of courses
        passed as a queryset
        """
        certificate_generated_count = helpers.generate_certificates_for_orders(
            models.Order.objects.filter(course__in=queryset)
        )

        summarize_certification_to_user(request, certificate_generated_count)


@admin.register(models.CourseRun)
class CourseRunAdmin(TranslatableAdmin):
    """Admin class for the CourseRun model"""

    actions = ("mark_as_gradable",)
    autocomplete_fields = ["course"]
    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "id",
                    "course",
                    "title",
                    "resource_link",
                    "is_gradable",
                    "is_listed",
                    "languages",
                    "enrollment_start",
                    "enrollment_end",
                    "start",
                    "end",
                )
            },
        ),
    )
    list_display = (
        "title",
        "resource_link",
        "start",
        "end",
        "state",
        "is_gradable",
        "is_listed",
    )
    list_filter = [CourseFilter, "is_gradable", "is_listed"]
    readonly_fields = ("id",)
    search_fields = ["resource_link", "title", "course__code", "course__title"]

    @admin.action(description=_("Mark course run as gradable"))
    def mark_as_gradable(self, request, queryset):  # pylint: disable=no-self-use
        """Mark selected course runs as gradable"""
        queryset.update(is_gradable=True)


@admin.register(models.Organization)
class OrganizationAdmin(TranslatableAdmin):
    """Admin class for the Organization model"""

    list_display = ("code", "title")
    search_fields = ["code", "title"]


@admin.register(models.User)
class UserAdmin(auth_admin.UserAdmin):
    """Admin class for the User model"""

    list_display = (
        "username",
        "email",
        "language",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("email", "language")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("language",)
    readonly_update_fields = ("username",)

    def get_readonly_fields(self, request, obj=None):
        """
        Make some fields readonly on update to avoid changing them by mistake
        """
        if obj is None:
            return self.readonly_fields

        return self.readonly_fields + self.readonly_update_fields


class ProductTargetCourseRelationInline(SortableInlineAdminMixin, admin.TabularInline):
    """Admin class for the ProductTargetCourseRelation model"""

    autocomplete_fields = ["course"]
    form = forms.ProductTargetCourseRelationAdminForm
    model = models.Product.target_courses.through
    extra = 0


@admin.register(models.Product)
class ProductAdmin(
    DjangoObjectActions,
    SortableAdminBase,
    TranslatableAdmin,
):  # pylint: disable=too-many-ancestors
    """Admin class for the Product model"""

    change_form_template = "joanie/admin/translatable_change_form_with_actions.html"
    list_display = ("title", "type", "price")
    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "id",
                    "type",
                    "title",
                    "description",
                    "call_to_action",
                    "price",
                    "certificate_definition",
                    "related_courses",
                )
            },
        ),
    )
    inlines = (ProductTargetCourseRelationInline,)
    list_filter = ["type"]
    readonly_fields = (
        "id",
        "related_courses",
    )
    actions = (ACTION_NAME_GENERATE_CERTIFICATES,)
    change_actions = (ACTION_NAME_GENERATE_CERTIFICATES,)
    search_fields = ["title"]

    def get_change_actions(self, request, object_id, form_url):
        """
        Remove the generate_certificates action from list of actions
        if the product instance is not certifying
        """
        actions = super().get_change_actions(request, object_id, form_url)
        actions = list(actions)

        if not self.model.objects.filter(
            pk=object_id, type__in=PRODUCT_TYPE_CERTIFICATE_ALLOWED
        ).exists():
            actions.remove(ACTION_NAME_GENERATE_CERTIFICATES)

        return actions

    def get_urls(self):
        """
        Add url to trigger certificate generation for a course - product couple.
        """
        url_patterns = super().get_urls()

        return [
            re_path(
                r"^(?P<product_id>.+)/generate-certificates/(?P<course_code>.+)/$",
                self.admin_site.admin_view(self.generate_certificates_for_course),
                name=ACTION_NAME_GENERATE_CERTIFICATES,
            )
        ] + url_patterns

    @takes_instance_or_queryset
    def generate_certificates(self, request, queryset):  # pylint: disable=no-self-use
        """
        Custom action to generate certificates for a collection of products
        passed as a queryset
        """
        certificate_generated_count = helpers.generate_certificates_for_orders(
            models.Order.objects.filter(product__in=queryset)
        )

        summarize_certification_to_user(request, certificate_generated_count)

    def generate_certificates_for_course(
        self, request, product_id, course_code
    ):  # pylint: disable=no-self-use
        """
        A custom action to generate certificates for a course - product couple.
        """
        certificate_generated_count = helpers.generate_certificates_for_orders(
            models.Order.objects.filter(
                product__id=product_id, course__code=course_code
            )
        )

        summarize_certification_to_user(request, certificate_generated_count)

        return HttpResponseRedirect(
            reverse("admin:core_product_change", args=(product_id,))
        )

    @admin.display(description="Related courses")
    def related_courses(self, obj):  # pylint: disable=no-self-use
        """
        Retrieve courses related to the product
        """
        return self.get_related_courses_as_html(obj)

    @staticmethod
    def get_related_courses_as_html(obj):  # pylint: disable=no-self-use
        """
        Get the html representation of the product's related courses
        """
        related_courses = obj.courses.all()
        is_certifying = obj.type in PRODUCT_TYPE_CERTIFICATE_ALLOWED

        if related_courses:
            items = []
            for course in obj.courses.all():
                change_course_url = reverse(
                    "admin:core_course_change",
                    args=(course.id,),
                )

                raw_html = (
                    '<li style="margin-bottom: 1rem">'
                    f"<a href='{change_course_url}'>{course.code} | {course.title}</a>"
                )

                if is_certifying:
                    # Add a button to generate certificate
                    generate_certificates_url = reverse(
                        f"admin:{ACTION_NAME_GENERATE_CERTIFICATES}",
                        kwargs={"product_id": obj.id, "course_code": course.code},
                    )

                    raw_html += (
                        f'<a style="margin-left: 1rem" class="button" href="{generate_certificates_url}">'  # noqa pylint: disable=line-too-long
                        f'{_("Generate certificates")}'
                        "</a>"
                    )

                raw_html += "</li>"
                items.append(raw_html)

            return format_html(f"<ul style='margin: 0'>{''.join(items)}</ul>")

        return "-"


@admin.register(models.Order)
class OrderAdmin(DjangoObjectActions, admin.ModelAdmin):
    """Admin class for the Order model"""

    actions = (ACTION_NAME_CANCEL, ACTION_NAME_GENERATE_CERTIFICATES)
    autocomplete_fields = ["course", "organization", "owner", "product"]
    change_actions = (ACTION_NAME_GENERATE_CERTIFICATES,)
    list_display = ("id", "organization", "owner", "product", "state")
    list_filter = [OwnerFilter, OrganizationFilter, ProductFilter, "state"]
    readonly_fields = ("state", "total", "invoice", "certificate")
    search_fields = ["course__title", "organization__title"]

    @admin.action(description=_("Cancel selected orders"))
    def cancel(self, request, queryset):  # pylint: disable=no-self-use
        """Cancel orders"""
        for order in queryset:
            order.cancel()

    @takes_instance_or_queryset
    def generate_certificates(self, request, queryset):  # pylint: disable=no-self-use
        """
        Custom action to launch generate_certificates management commands
        over the order selected
        """
        certificate_generated_count = helpers.generate_certificates_for_orders(queryset)
        summarize_certification_to_user(request, certificate_generated_count)

    def invoice(self, obj):  # pylint: disable=no-self-use
        """Retrieve the root invoice related to the order."""
        invoice = obj.invoices.get(parent__isnull=True)

        return format_html(
            (
                "<a href='"
                f"{reverse('admin:payment_invoice_change', args=(invoice.id,))}"
                "'>"
                f"{str(invoice)}"
                "</a>"
            )
        )


@admin.register(models.Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin class for the Enrollment model"""

    autocomplete_fields = ["course_run", "user"]
    list_display = ("user", "course_run", "state")
    list_filter = [RequiredUserFilter, CourseRunFilter, "state"]
    list_select_related = ("user", "course_run")

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        """
        Add instruction to explain that, due to the RequiredUserFilter, no results will be
        shown until the view is filtered for a specific user.
        """
        extra_context = extra_context or {}
        extra_context["subtitle"] = _("To get results, choose a user on the right")
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin class for the Address model"""

    autocomplete_fields = ["owner"]
    list_display = (
        "title",
        "full_name",
        "address",
        "postcode",
        "city",
        "country",
        "is_main",
        "owner",
    )
    list_filter = [RequiredOwnerFilter, "is_main"]
    list_select_related = ["owner"]
    search_fields = ["title", "first_name", "last_name", "address", "postcode", "city"]

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        """
        Add instruction to explain that, due to the RequiredOwnerFilter, no results will be
        shown until the view is filtered for a specific owner.
        """
        extra_context = extra_context or {}
        extra_context["subtitle"] = _("To get results, choose an owner on the right")
        return super().changelist_view(request, extra_context=extra_context)
