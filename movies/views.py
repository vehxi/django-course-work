from django.db.models import Avg, Q, F, Count
from django.db.models.functions import Lower, Collate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, DetailView, TemplateView, UpdateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.mail import send_mail
import openpyxl
import os
from django.conf import settings
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .models import Actor, Genre, Movie, Review
from .forms import MovieCatalogForm, ReviewForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from users.models import Profile

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class MovieListView(ListView):
    model = Movie
    template_name = 'movies/movie_list.html'
    context_object_name = 'movies'

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related('genres').all()
        query = self.request.GET.get('q', '').strip()
        sort_by = self.request.GET.get('sort', '-id')
        genre_ids = self.request.GET.getlist('genre')

        if query:
            queryset = (
                queryset
                .annotate(similarity=TrigramSimilarity('title', query))
                .filter(
                    Q(title__icontains=query) |
                    Q(similarity__gt=0.08)
                )
            )

        if sort_by == 'rating':
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).order_by(F('avg_rating').desc(nulls_last=True), '-id')
        elif sort_by == '-rating':
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__isnull=False).order_by(F('avg_rating').asc(nulls_last=True), '-id')
        elif sort_by == 'title':
            queryset = queryset.order_by(Collate(Lower('title'), 'C'))
        elif sort_by == '-id':
            queryset = queryset.order_by('-id')
        elif query:
            queryset = queryset.order_by('-similarity', 'title')

        if genre_ids:
            for gid in genre_ids:
                if gid.isdigit():
                    queryset = queryset.filter(genres__id=gid)

        return queryset.distinct() if (query or genre_ids) else queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '-id')
        context['current_genres'] = self.request.GET.getlist('genre')
        context['genres'] = Genre.objects.all().order_by('name')
        context['current_view'] = self.request.GET.get('view', 'catalog')
        
        search_q = self.request.GET.get('q', '')
        genres = self.request.GET.getlist('genre')
        context['show_recommendations'] = not bool(search_q or genres)
        
        if context['current_view'] == 'collections':
            # Лучшие
            context['col_best'] = Movie.objects.annotate(
                avg_rating=Avg('reviews__rating')
            ).order_by(F('avg_rating').desc(nulls_last=True), '-id')[:10]
            
            # Худшие
            context['col_worst'] = Movie.objects.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__isnull=False).order_by('avg_rating', '-id')[:10]
            
            # На основе интересов
            interest_based = []
            if self.request.user.is_authenticated:
                favorite_movies = self.request.user.favorite_movies.all()
                if favorite_movies.exists():
                    top_genres = Genre.objects.filter(
                        movies__in=favorite_movies
                    ).annotate(
                        fav_count=Count('movies', filter=Q(movies__in=favorite_movies))
                    ).order_by('-fav_count')[:3]
                    
                    if top_genres:
                        interest_based = Movie.objects.filter(
                            genres__in=top_genres
                        ).exclude(
                            id__in=favorite_movies.values_list('id', flat=True)
                        ).distinct().order_by('-id')[:10]
            context['col_interests'] = interest_based
            
        elif context['show_recommendations']:
            context['recommended_movies'] = Movie.objects.annotate(
                avg_rating=Avg('reviews__rating')
            ).order_by(F('avg_rating').desc(nulls_last=True), '-id')[:4]
            
        if self.request.user.is_authenticated:
            context['favorite_movie_ids'] = list(
                self.request.user.favorite_movies.values_list('id', flat=True)
            )
        else:
            context['favorite_movie_ids'] = []
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'movies/includes/movie_search_results.html',
                context,
                request=self.request,
            )
            return HttpResponse(html, **response_kwargs)
        return super().render_to_response(context, **response_kwargs)

class ExportMoviesView(MovieListView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Гарантируем наличие рейтинга для экспорта
        queryset = queryset.annotate(export_rating=Avg('reviews__rating'))
        
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Каталог фильмов'
        
        headers = ['ID', 'Название', 'Год', 'Длительность (мин)', 'Возраст', 'Жанры', 'Рейтинг']
        sheet.append(headers)
        
        # Стилизация заголовков
        for cell in sheet[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            
        for movie in queryset:
            genres_str = ', '.join([g.name for g in movie.genres.all()])
            rating = movie.export_rating
            rating_str = f"{rating:.1f}" if rating else "Нет оценок"
            
            sheet.append([
                movie.id,
                movie.title,
                movie.year,
                movie.duration,
                f"{movie.age_restriction}+",
                genres_str,
                rating_str
            ])
            
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="movies_catalog.xlsx"'
        workbook.save(response)
        
        return response

class ExportMoviesPDFView(MovieListView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = queryset.annotate(export_rating=Avg('reviews__rating'))
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="movies_report.pdf"'
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Roboto-Regular.ttf')
        pdfmetrics.registerFont(TTFont('Roboto', font_path))
        
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle', 
            parent=styles['Title'], 
            fontName='Roboto',
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#222222')
        )
        elements.append(Paragraph("Отчет: Каталог фильмов", title_style))
        
        data = [['ID', 'Название', 'Год', 'Длительность (мин)', 'Возраст', 'Жанры', 'Рейтинг']]
        
        cell_style = ParagraphStyle('Normal_Roboto', fontName='Roboto', fontSize=10)
        
        for movie in queryset:
            genres_str = ', '.join([g.name for g in movie.genres.all()])
            rating = f"{movie.export_rating:.1f}" if movie.export_rating else "Нет оценок"
            
            data.append([
                str(movie.id),
                Paragraph(movie.title, cell_style),
                str(movie.year),
                str(movie.duration),
                f"{movie.age_restriction}+",
                Paragraph(genres_str, cell_style),
                rating
            ])
            
        if len(data) == 1:
            data.append(["", "Нет данных по выбранным фильтрам", "", "", "", "", ""])
            
        # Ширины колонок для ландшафтного A4 (ширина ~842)
        table = Table(data, colWidths=[30, 200, 40, 110, 55, 260, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4f4f4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Roboto'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response

class MovieDetailView(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = ReviewForm()
        context['reviews'] = self.object.reviews.select_related('user', 'user__profile').order_by('-created_at')
        
        is_favorite = False
        if self.request.user.is_authenticated:
            is_favorite = self.object.favorited_by.filter(id=self.request.user.id).exists()
        context['is_favorite'] = is_favorite
        
        return context

class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(
                user=request.user, movie=movie,
                defaults={'rating': form.cleaned_data['rating'], 'text': form.cleaned_data['text']}
            )
        return redirect('movie_detail', pk=pk)

class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        if movie.favorited_by.filter(id=request.user.id).exists():
            movie.favorited_by.remove(request.user)
        else:
            movie.favorited_by.add(request.user)

        next_url = request.POST.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect('movie_detail', pk=pk)

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'movies/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        favorite_movies = self.request.user.favorite_movies.prefetch_related('genres').all()
        context['favorite_movies'] = favorite_movies
        context['favorite_movie_ids'] = list(favorite_movies.values_list('id', flat=True))
        context['reviews_count'] = self.request.user.reviews.count()
        return context

class CatalogManageView(StaffRequiredMixin, ListView):
    model = Movie
    template_name = 'movies/catalog_manage.html'
    context_object_name = 'movies'

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related('genres', 'actors').order_by('-id')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = (
                queryset
                .annotate(similarity=TrigramSimilarity('title', query))
                .filter(
                    Q(title__icontains=query) |
                    Q(similarity__gt=0.08) |
                    Q(genres__name__icontains=query) |
                    Q(actors__full_name__icontains=query)
                )
                .order_by('-similarity', 'title')
                .distinct()
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        view_mode = self.request.GET.get('view', 'list')
        context['view_mode'] = view_mode if view_mode in {'list', 'grid'} else 'list'
        context['movies_count'] = Movie.objects.count()
        context['genres_count'] = Genre.objects.count()
        context['actors_count'] = Actor.objects.count()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'movies/includes/catalog_manage_results.html',
                context,
                request=self.request,
            )
            return HttpResponse(html, **response_kwargs)
        return super().render_to_response(context, **response_kwargs)

class CatalogMovieCreateView(StaffRequiredMixin, CreateView):
    model = Movie
    form_class = MovieCatalogForm
    template_name = 'movies/catalog_movie_form.html'
    success_url = reverse_lazy('catalog_manage')

class CatalogMovieUpdateView(StaffRequiredMixin, UpdateView):
    model = Movie
    form_class = MovieCatalogForm
    template_name = 'movies/catalog_movie_form.html'
    success_url = reverse_lazy('catalog_manage')

class CatalogMovieDeleteView(StaffRequiredMixin, DeleteView):
    model = Movie
    template_name = 'movies/catalog_movie_confirm_delete.html'
    success_url = reverse_lazy('catalog_manage')

class RegisterView(View):
    def get(self, request):
        return render(request, 'registration/register.html', {'form': UserRegistrationForm()})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            
            # Отправка системного уведомления
            send_mail(
                subject='Добро пожаловать в КИНОТЕКА!',
                message=f'Здравствуйте, {new_user.username}!\n\nСпасибо за регистрацию в нашей системе "Учет фильмов". Теперь вы можете оставлять отзывы, ставить оценки и собирать свои коллекции!\n\nС уважением,\nКоманда КИНОТЕКА',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[new_user.email],
                fail_silently=False,
            )
            
            return redirect('login')
        return render(request, 'registration/register.html', {'form': form})

class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)
        return render(request, 'registration/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=profile, data=request.POST, files=request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
            
        return render(request, 'registration/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})
