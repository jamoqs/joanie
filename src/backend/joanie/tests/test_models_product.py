"""
Test suite for products models
"""
from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from djmoney.money import Money
from moneyed import EUR

from joanie.core import factories, models
from joanie.core.enums import PRODUCT_TYPE_CERTIFICATE


class ProductModelsTestCase(TestCase):
    """Test suite for the Product model."""

    def test_models_product_price_format(self):
        """
        The price field should be a money object with an amount property
        which is a Decimal and a currency property which is a
        Currency object.
        """
        product = factories.ProductFactory(price=23)
        self.assertEqual(product.price, Money("23.00", "EUR"))
        self.assertEqual(product.price.amount, D("23.00"))
        self.assertEqual(product.price.currency, EUR)

    def test_models_product_course_runs_unique(self):
        """A product can only be linked once to a given course run."""
        relation = factories.ProductCourseRelationFactory()
        with self.assertRaises(IntegrityError):
            factories.ProductCourseRelationFactory(
                course=relation.course, product=relation.product
            )

    def test_models_product_course_runs_relation_sorted_by_position(self):
        """The product/course relation should be sorted by position."""
        product = factories.ProductFactory()
        factories.ProductCourseRelationFactory.create_batch(5, product=product)

        expected_courses = list(
            p.course for p in models.ProductCourseRelation.objects.order_by("position")
        )

        ordered_courses = list(product.target_courses.order_by("product_relations"))
        self.assertEqual(ordered_courses, expected_courses)

    def test_model_order_create_certificate(self):
        """Generate a certificate for a product order"""

        course = factories.CourseFactory()
        product = factories.ProductFactory(
            courses=[course],
            type=PRODUCT_TYPE_CERTIFICATE,
            certificate_definition=factories.CertificateDefinitionFactory(),
        )
        order = factories.OrderFactory(product=product)

        order.create_certificate()
        self.assertEqual(models.Certificate.objects.count(), 1)
        certificate = models.Certificate.objects.first()
        document_context = certificate.get_document_context()
        blue_square_base64 = (
            "data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgY"
            "PgPAAEDAQAIicLsAAAAAElFTkSuQmCC"
        )
        self.assertEqual(
            document_context["course"]["organization"]["logo"],
            blue_square_base64,
        )
        self.assertEqual(
            document_context["course"]["organization"]["signature"],
            blue_square_base64,
        )

    def test_models_product_course_runs_relation_course_runs(self):
        """
        It's possible to restrict a course to use some course runs but if course runs
        linked does not rely on the relation course, a ValidationError should be raised.
        """
        course = factories.CourseFactory(
            course_runs=factories.CourseRunFactory.create_batch(1)
        )
        product = factories.ProductFactory(target_courses=[course])
        course_relation = product.course_relations.get(course=course)

        course_run = factories.CourseRunFactory.create_batch(1)

        with self.assertRaises(ValidationError) as context:
            with transaction.atomic():
                course_relation.course_runs.set(course_run)

        self.assertEqual(
            str(context.exception),
            "{'course_runs': ['Course runs to link does not relies on the relation course.']}",
        )

        self.assertEqual(course_relation.course_runs.count(), 0)

        with transaction.atomic():
            course_relation.course_runs.set(course.course_runs.all())

        self.assertEqual(course_relation.course_runs.count(), 1)
