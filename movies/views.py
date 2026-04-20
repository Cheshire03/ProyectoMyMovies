from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from movies.models import Movie, MovieReview, Person, MovieLike, MovieCredit
from movies.forms import MovieReviewForm, MovieCommentForm
from movies.utils import get_dominant_color
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your views here.

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
    movies = Movie.objects.all()
    context = { 'movies':movies, 'message':'welcome' }
    return render(request,'movies/index.html', context=context )
    
def person(request, person_id):
    person = Person.objects.get(id=person_id)
    credits = MovieCredit.objects.filter(person=person).order_by('movie__release_date')
    context = {
        'person': person,
        'credits': credits
    }
    return render(request, 'movies/person.html', context=context)

def movie(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    bg_color = get_dominant_color(
    f"https://image.tmdb.org/t/p/w500{movie.backdrop_path}")
    credits = MovieCredit.objects.filter(
        movie=movie,
        job__name='Acting'
    ).order_by('order')[:10]
    user_liked=False
    if request.user.is_authenticated:
        user_liked = MovieLike.objects.filter(user=request.user, movie=movie).exists()
    review_form = MovieReviewForm()
    context = { 'movie':movie, 'saludo':'welcome', 'review_form':review_form ,'bg_color': bg_color, 'credits':credits, 'user_liked': user_liked, }
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
    movie = Movie.objects.get(id=movie_id)
    return render(request,'movies/reviews.html', context={'movie':movie } )

def user_reviews(request, user_id):
    user = User.objects.get(id=user_id)
    reviews = MovieReview.objects.filter(user=user).order_by('-created_at')
    context = {
        'profile_user': user,
        'reviews': reviews
    }
    return render(request, 'movies/user_reviews.html', context=context)

def add_like(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    if request.user.is_authenticated:
        like, created = MovieLike.objects.get_or_create(user=request.user, movie=movie)
        if not created:
            like.delete()
    return redirect('movie', movie_id=movie_id)
    
def add_review(request, movie_id):
    form = None
    movie = Movie.objects.get(id=movie_id)
    if request.method == 'POST':
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