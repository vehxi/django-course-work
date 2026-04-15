from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0002_trigram_search"),
    ]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="content_type",
            field=models.CharField(
                choices=[("movie", "Фильм"), ("series", "Сериал")],
                default="movie",
                max_length=10,
            ),
        ),
    ]
