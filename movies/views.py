from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from movies.models import Movie, MovieReview, Person, MovieLike, MovieCredit
from movies.forms import MovieReviewForm, MovieCommentForm
from movies.utils import get_dominant_color
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your views here.

def get_simple_recommendations(exclude_id=None, limit=8):
    qs = Movie.objects.order_by('-release_date')
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    return qs[:limit]

def all_movies(request):
    movies=Movie.objects.all()
    context={'movies':movies,'message':'welcome'}
    return render(request,'movies/allmovies.html',context=context)

def saludo(request,veces):
    saludo='Hola ' *veces
    personas = Person.objects.all()
    context={'saludo':saludo,'lista':personas}
    return render(request,'movies/saludo.html',context=context)

def index(request):
    movies = Movie.objects.order_by('-release_date')
    recommended_movies = get_simple_recommendations(limit=8)
    context = { 'movies':movies,'recommended_movies': recommended_movies, 'message':'welcome' }
    return render(request,'movies/index.html', context=context )
    
def person(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    credits = MovieCredit.objects.filter(person=person).order_by('movie__release_date')
    context = {
        'person': person,
        'credits': credits
    }
    return render(request, 'movies/person.html', context=context)

def movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    bg_color = "#000000"
    if movie.backdrop_path:
        try:
            bg_color = get_dominant_color(
                f"https://image.tmdb.org/t/p/w500{movie.backdrop_path}"
            )
        except Exception:
            pass

    credits = MovieCredit.objects.filter(
        movie=movie,
        job__name='Acting'
    ).order_by('order')[:10]
    recommended_movies = get_simple_recommendations(exclude_id=movie.id, limit=6)
    user_liked=False
    if request.user.is_authenticated:
        user_liked = MovieLike.objects.filter(user=request.user, movie=movie).exists()
    review_form = MovieReviewForm()
    context = { 'movie':movie, 'saludo':'welcome', 'review_form':review_form ,'bg_color': bg_color, 'credits':credits, 'user_liked': user_liked, 'recommended_movies': recommended_movies}
    return render(request,'movies/movie.html', context=context )

def my_movies(request):
    liked_movies = MovieLike.objects.filter(user=request.user).order_by('-created_at')
    recent_reviews = MovieReview.objects.filter(user=request.user).order_by('-created_at')[:4]
    context = {
        'liked_movies': liked_movies,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'movies/my_movies.html', context=context)

def movie_reviews(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    return render(request,'movies/reviews.html', context={'movie':movie } )

def user_reviews(request, user_id):
    user = get_object_or_404(User, id=user_id)
    reviews = MovieReview.objects.filter(user=user).order_by('-created_at')
    context = {
        'profile_user': user,
        'reviews': reviews
    }
    return render(request, 'movies/user_reviews.html', context=context)

def add_like(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.user.is_authenticated:
        like, created = MovieLike.objects.get_or_create(user=request.user, movie=movie)
        if not created:
            like.delete()
    return redirect('movie', movie_id=movie_id)
    
def add_review(request, movie_id):
    form = None
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponse(status=403)
        form = MovieReviewForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']
            title  = form.cleaned_data['title']
            review = form.cleaned_data['review']
            movie_review = MovieReview(
                    movie=movie,
                    rating=rating,
                    title=title,
                    review=review,
                    user=request.user)
            movie_review.save()
            return HttpResponse(status=204,
                                headers={'HX-Trigger': 'listChanged'})
    else:
        form = MovieReviewForm()
        return render(request,
                  'movies/movie_review_form.html',
                  {'movie_review_form': form, 'movie':movie})