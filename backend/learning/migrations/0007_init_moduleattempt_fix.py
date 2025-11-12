import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0006_remove_moduleattempt_answers_and_more"),  # adjust if your previous file differs
        ("accounts", "0001_initial"),
    ]

    operations = [
        # If 'created_at' does not exist yet (it likely doesn't), add it with a real default
        migrations.AddField(
            model_name="moduleattempt",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        # If 'user' is missing or you reverted it: add as NULLable (no default)
        migrations.AddField(
            model_name="moduleattempt",
            name="user",
            field=models.ForeignKey(
                related_name="module_attempts",
                null=True,
                blank=True,
                on_delete=models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # If completed_at/score/passed already exist, leave them out.
        # If they don't exist yet in your DB, add them too similarly:
        # migrations.AddField(... completed_at ...),
        # migrations.AddField(... score ...),
        # migrations.AddField(... passed ...),
    ]
