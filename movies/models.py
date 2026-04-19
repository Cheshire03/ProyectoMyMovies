from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

User = get_user_model()

class Genre(models.Model):
    name = models.CharField(max_length=80)
    
    def __str__(self):
        return self.name
    
class Person(models.Model):
    name = models.CharField(max_length=128)
    tmdb_id = models.IntegerField(unique=True)
    profile_path = models.URLField(blank=True, null=True)
    biography = models.TextField(blank=True)
    birthday = models.DateField(blank=True, null=True)
    deathday = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=200, blank=True, null=True)

    
    def __str__(self):
        return self.name


class Job(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=80)
    overview = models.TextField()
    origin_country = models.TextField()
    release_date = models.DateField()
    running_time = models.IntegerField()
    budget = models.IntegerField(blank=True, null=True)
    tmdb_id = models.IntegerField(unique=True)
    revenue = models.IntegerField(blank=True, null=True)
    poster_path = models.URLField(blank=True, null=True)
    backdrop_path = models.URLField(blank=True, null=True)
    genres = models.ManyToManyField(Genre)
    credits = models.ManyToManyField(Person, through='MovieCredit')

    def __str__(self):
        return f'{self.title} {self.release_date}'


class MovieCredit(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    character = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f'{self.person} - {self.job} en {self.movie}'


class MovieLike(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    movie= models.ForeignKey(Movie, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f'{self.user} - {self.movie}'

class MovieReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    review = models.TextField(blank=True)
    title = models.TextField(blank=False, null=False, default="Reseña")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} - {self.movie} ({self.rating})'
