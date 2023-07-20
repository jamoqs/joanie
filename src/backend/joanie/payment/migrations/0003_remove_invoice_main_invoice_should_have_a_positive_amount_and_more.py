# Generated by Django 4.2.2 on 2023-07-07 15:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0002_alter_creditcard_options"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="invoice",
            name="main_invoice_should_have_a_positive_amount",
        ),
        migrations.RemoveConstraint(
            model_name="invoice",
            name="only_one_invoice_without_parent_per_order",
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("parent__isnull", True), ("total__gte", 0)),
                    ("parent__isnull", False),
                    _connector="OR",
                ),
                name="main_invoice_should_have_a_positive_amount",
                violation_error_message="Credit note should have a parent invoice.",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                condition=models.Q(("parent__isnull", True)),
                fields=("order",),
                name="only_one_invoice_without_parent_per_order",
                violation_error_message="A main invoice already exists for this order.",
            ),
        ),
    ]
