from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from movies.models import Movie, MovieReview, Person, MovieLike, MovieCredit, Genre
from movies.forms import MovieReviewForm, MovieCommentForm
from movies.utils import get_dominant_color
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, Count, Avg
import random


User = get_user_model()
# Create your views here.

def get_recommended_homepage(limit=8):
    from django.db.models import Count, Avg

    return Movie.objects.annotate(
        num_likes=Count('movielike', distinct=True),
        avg_rating=Avg('moviereview__rating')
    ).filter(
        avg_rating__isnull=False  # solo películas con al menos una reseña
    ).order_by('-num_likes', '-avg_rating')[:limit]

def get_simple_recommendations(movie, exclude_id=None, limit=8):
    genre_ids = movie.genres.values_list('id', flat=True)
    
    qs = Movie.objects.filter(genres__id__in=genre_ids)
    
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    
    qs = qs.annotate(
        shared_genres=Count('genres', filter=Q(genres__id__in=genre_ids))
    ).order_by('-shared_genres', '-release_date').distinct()
    
    return qs[:limit]

def allmovies(request):
    genres = Genre.objects.all().order_by('name')
    years = Movie.objects.dates('release_date', 'year', order='DESC')
    movies = Movie.objects.order_by('-release_date')
    context = {'movies': movies, 'genres': genres, 'years': [d.year for d in years]}
    return render(request, 'movies/allmovies.html', context)

def allmovies_filter(request):
    genre_id = request.GET.get('genre')
    year = request.GET.get('year')
    sort = request.GET.get('sort', 'recent')

    movies = Movie.objects.all()

    if genre_id:
        movies = movies.filter(genres__id=genre_id)
    if year:
        movies = movies.filter(release_date__year=year)
    if sort == 'recent':
        movies = movies.order_by('-release_date')
    elif sort == 'likes':
        movies = movies.annotate(num_likes=Count('movielike')).order_by('-num_likes')
    elif sort == 'rating':
        movies = movies.annotate(avg_rating=Avg('moviereview__rating')).order_by('-avg_rating')

    movies = movies.distinct()
    return render(request, 'movies/partials/movie_grid.html', {'movies': movies})

def saludo(request,veces):
    saludo='Hola ' *veces
    personas = Person.objects.all()
    context={'saludo':saludo,'lista':personas}
    return render(request,'movies/saludo.html',context=context)

def index(request):
    movies = Movie.objects.order_by('-release_date')
    recommended_movies = get_recommended_homepage(limit=8)

    random_movie = None
    if movies.exists():
        random_movie = random.choice(list(movies))

    context = {
        'movies': movies,
        'recommended_movies': recommended_movies,
        'random_movie': random_movie
    }

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
    ).select_related('person', 'job').order_by('order')[:10]
    crew = MovieCredit.objects.filter(
        movie=movie
    ).exclude(
        job__name='Acting'
    ).select_related('person', 'job').order_by('job__name')
    recommended_movies = get_simple_recommendations(movie=movie, exclude_id=movie.id, limit=6)
    user_liked=False
    avg_rating = movie.moviereview_set.aggregate(avg=Avg('rating'))['avg']
    review_count = movie.moviereview_set.count()
    if request.user.is_authenticated:
        user_liked = MovieLike.objects.filter(user=request.user, movie=movie).exists()
    review_form = MovieReviewForm()
    context = { 'movie':movie, 'saludo':'welcome', 'review_form':review_form ,'bg_color': bg_color, 'credits': credits,
    'crew': crew, 'user_liked': user_liked, 'budget': f"${movie.budget:,}" if movie.budget else None,
        'revenue': f"${movie.revenue:,}" if movie.revenue else None, 'recommended_movies': recommended_movies, 'avg_rating': round(avg_rating) if avg_rating else None,
    'review_count': review_count,}
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

def search(request):
    query = request.GET.get('search', '')
    movies = []
    if query:
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(title__trigram_similar=query)
        ).annotate(
            similarity=TrigramSimilarity('title', query)
        ).filter(
            Q(title__icontains=query) | Q(similarity__gt=0.1)
        ).order_by('-similarity').distinct()
    return render(request, 'movies/search.html', {
        'movies': movies,
        'search_value': query
    })

def user_profile(request, user_id):
    profile_user = User.objects.get(id=user_id)
    liked_movies = MovieLike.objects.filter(user=profile_user).order_by('-created_at')
    reviews = MovieReview.objects.filter(user=profile_user).order_by('-created_at')
    
    is_own_profile = request.user == profile_user
    is_following = False
    if request.user.is_authenticated and not is_own_profile:
        from users.models import Follow
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    context = {
        'profile_user': profile_user,
        'liked_movies': liked_movies,
        'reviews': reviews,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
    }
    return render(request, 'movies/user_profile.html', context=context)