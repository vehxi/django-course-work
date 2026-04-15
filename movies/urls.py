from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.MovieListView.as_view(), name='movie_list'),
    path('movie/<int:pk>/', views.MovieDetailView.as_view(), name='movie_detail'),
    path('movie/<int:pk>/add_review/', views.AddReviewView.as_view(), name='add_review'),
    path('movie/<int:pk>/toggle_favorite/', views.ToggleFavoriteView.as_view(), name='toggle_favorite'),
    
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
    path('profile/catalog/', views.CatalogManageView.as_view(), name='catalog_manage'),
    path('profile/catalog/movie/add/', views.CatalogMovieCreateView.as_view(), name='catalog_movie_add'),
    path('profile/catalog/movie/<int:pk>/edit/', views.CatalogMovieUpdateView.as_view(), name='catalog_movie_edit'),
    path('profile/catalog/movie/<int:pk>/delete/', views.CatalogMovieDeleteView.as_view(), name='catalog_movie_delete'),
    
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='movie_list'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]
