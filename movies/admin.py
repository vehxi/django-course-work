from django.contrib import admin
from .models import Movie, Genre, Actor, Review

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ['name']

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    search_fields = ['full_name']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'year', 'age_restriction', 'duration')
    list_filter = ('content_type', 'year', 'age_restriction')
    search_fields = ['title']
    filter_horizontal = ('genres', 'actors', 'favorited_by')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    autocomplete_fields = ['movie']
