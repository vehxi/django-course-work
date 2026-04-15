from django.db import models
from django.conf import settings
from django.db.models import Avg
from django.contrib.postgres.indexes import GinIndex, OpClass

class Genre(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Actor(models.Model):
    full_name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.full_name

class Movie(models.Model):
    class ContentType(models.TextChoices):
        MOVIE = "movie", "Фильм"
        SERIES = "series", "Сериал"

    title = models.CharField(max_length=255)
    content_type = models.CharField(
        max_length=10,
        choices=ContentType.choices,
        default=ContentType.MOVIE,
    )
    description = models.TextField()
    year = models.PositiveIntegerField(default=2025)
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    age_restriction = models.PositiveIntegerField(default=18)
    duration = models.PositiveIntegerField(default=120)
    
    genres = models.ManyToManyField(Genre, related_name='movies')
    actors = models.ManyToManyField(Actor, related_name='movies')
    favorited_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='favorite_movies', 
        blank=True
    )

    class Meta:
        indexes = [
            GinIndex(
                OpClass("title", name="gin_trgm_ops"),
                name="movie_title_trgm_gin",
            ),
        ]

    def __str__(self):
        return self.title

    def get_average_rating(self):
        result = self.reviews.aggregate(average=Avg('rating'))
        if result['average'] is not None:
            return round(result['average'], 1)
        return 0.0

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=10)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
