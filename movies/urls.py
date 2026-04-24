from django.urls import path
from .views import *

urlpatterns = [
    path('all/',all_movies),
    path('<int:movie_id>/', movie, name='movie'),
    path('my_movies/', my_movies, name='my_movies'),
    path('person/<int:person_id>/', person, name='person'),
    path('saludo/<int:veces>/',saludo),
    path('movie_like/add/<int:movie_id>/', add_like),
    path('movie_review/add/<int:movie_id>/', add_review),
    path('search/', search, name='search'),
    path('user/<int:user_id>/', user_profile, name='user_profile'),
    path('user/<int:user_id>/reviews/', user_reviews, name='user_reviews'),
    path('movie_reviews/<int:movie_id>/', movie_reviews, name='movie_reviews'),
    path('', index)
]