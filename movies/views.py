from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from movies.models import Movie, MovieReview, Person, MovieLike
from movies.forms import MovieReviewForm, MovieCommentForm
from movies.utils import get_dominant_color

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
    
def movie(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    bg_color = get_dominant_color(
    f"https://image.tmdb.org/t/p/w500{movie.backdrop_path}")
    review_form = MovieReviewForm()
    context = { 'movie':movie, 'saludo':'welcome', 'review_form':review_form ,'bg_color': bg_color }
    return render(request,'movies/movie.html', context=context )

def movie_reviews(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    return render(request,'movies/reviews.html', context={'movie':movie } )

def add_like(request, movie_id):
    form= None
    movie= Movie.objects.get(id=movie_id)

    if request.method == 'POST':
        form = MovieCommentForm(request.POST)
        if form.is_valid():
            review = form.cleaned_data['review']
            movie_like = MovieLike(
                    movie=movie,
                    review=review,
                    user=request.user)
            movie_like.save()
            return HttpResponseRedirect('/movies/')
    else:
        form = MovieCommentForm()
        return render(request,
                  'movies/movie_comment_form.html',
                  {'form': form, 'movie':movie})
    
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