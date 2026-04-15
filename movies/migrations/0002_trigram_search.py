from django.contrib.postgres.indexes import GinIndex, OpClass
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0001_initial"),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name="movie",
            index=GinIndex(
                OpClass("title", name="gin_trgm_ops"),
                name="movie_title_trgm_gin",
            ),
        ),
    ]
