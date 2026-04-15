from django import forms
from django.contrib.auth import get_user_model
from .models import Actor, Genre, Movie, Review
from users.models import Profile

User = get_user_model()

class ReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields['rating'].initial = ''
            self.initial['rating'] = ''

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating in (None, ''):
            raise forms.ValidationError('Выберите рейтинг.')
        return rating

    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'review-textarea', 'placeholder': 'Напишите ваше мнение о фильме...'}),
            'rating': forms.HiddenInput(), 
        }

class MovieCatalogForm(forms.ModelForm):
    new_genres = forms.CharField(
        label='Новые жанры',
        required=False,
        help_text='Через запятую, если нужного жанра еще нет в списке.',
        widget=forms.TextInput(attrs={'placeholder': 'например: драма, спорт'}),
    )
    new_actors = forms.CharField(
        label='Новые актеры',
        required=False,
        help_text='Через запятую, если нужного актера еще нет в списке.',
        widget=forms.TextInput(attrs={'placeholder': 'например: Брэд Питт, Том Круз'}),
    )

    class Meta:
        model = Movie
        fields = [
            'title',
            'content_type',
            'description',
            'year',
            'poster',
            'age_restriction',
            'duration',
            'genres',
            'actors',
        ]
        labels = {
            'title': 'Название',
            'content_type': 'Тип контента',
            'description': 'Описание',
            'year': 'Год',
            'poster': 'Постер',
            'age_restriction': 'Возрастное ограничение',
            'duration': 'Длительность',
            'genres': 'Жанры',
            'actors': 'Актеры',
        }
        help_texts = {
            'age_restriction': 'Укажи число без плюса, например 18.',
            'duration': 'Длительность в минутах.',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'genres': forms.SelectMultiple(attrs={'class': 'catalog-select'}),
            'actors': forms.SelectMultiple(attrs={'class': 'catalog-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genres'].queryset = Genre.objects.order_by('name')
        self.fields['actors'].queryset = Actor.objects.order_by('full_name')
        self.fields['genres'].required = False
        self.fields['actors'].required = False

    def save(self, commit=True):
        movie = super().save(commit=commit)
        if commit:
            self._save_new_relations(movie)
        return movie

    def save_m2m(self):
        super().save_m2m()
        if self.instance.pk:
            self._save_new_relations(self.instance)

    def _save_new_relations(self, movie):
        for name in self._split_names(self.cleaned_data.get('new_genres', '')):
            genre, _ = Genre.objects.get_or_create(name=name)
            movie.genres.add(genre)

        for full_name in self._split_names(self.cleaned_data.get('new_actors', '')):
            actor, _ = Actor.objects.get_or_create(full_name=full_name)
            movie.actors.add(actor)

    @staticmethod
    def _split_names(value):
        return [item.strip() for item in value.split(',') if item.strip()]

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password_confirm(self):
        cd = self.cleaned_data
        if cd.get('password') != cd.get('password_confirm'):
            raise forms.ValidationError('Пароли не совпадают!')
        return cd['password_confirm']

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['date_of_birth', 'photo']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'date-input'})
        }
