import os
import environ
import requests
import psycopg2
from datetime import datetime, date, timezone 
import sys


def add_movie(movie_id):
    env = environ.Env()
    environ.Env.read_env('.env')

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {env('API_TOKEN')}"
    }

    # Datos de la película
    r = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?language=en-US', headers=headers) 
    m = r.json()

    # Créditos
    r = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}/credits?language=en-US', headers=headers) 
    credits = r.json()

    conn = psycopg2.connect(dbname='django', host='/tmp')
    cur = conn.cursor()

    # --- JOBS ---
    actors = [(actor['name'], actor['known_for_department'], actor.get('character', ''), actor['order'], actor['id']) for actor in credits['cast'][:10]]
    crew   = [(member['name'], member['job'], '', 99, member['id']) for member in credits['crew'][:15]]
    credits_list = actors + crew

    jobs = set(job for _, job, _, _, _ in credits_list)
    sql = 'SELECT * FROM movies_job WHERE name IN %s'
    cur.execute(sql, (tuple(jobs),))
    jobs_in_db = {name for id, name in cur.fetchall()}

    jobs_to_create = [(name,) for name in jobs if name not in jobs_in_db]
    cur.executemany('INSERT INTO movies_job (name) VALUES (%s)', jobs_to_create)

    # --- PERSONS ---
    # Para cada persona en créditos, buscar sus detalles en TMDB
    persons_data = {}
    for name, job, character, order, tmdb_person_id in credits_list:
        if tmdb_person_id not in persons_data:
            pr = requests.get(f'https://api.themoviedb.org/3/person/{tmdb_person_id}?language=en-US', headers=headers)
            pd = pr.json()
            persons_data[tmdb_person_id] = {
                'name': pd.get('name', name),
                'tmdb_id': tmdb_person_id,
                'profile_path': pd.get('profile_path', ''),
                'biography': pd.get('biography', ''),
                'birthday': pd.get('birthday'),
                'deathday': pd.get('deathday'),
                'place_of_birth': pd.get('place_of_birth', ''),
            }

    for p in persons_data.values():
        sql = '''INSERT INTO movies_person 
                 (name, tmdb_id, profile_path, biography, birthday, deathday, place_of_birth)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)
                 ON CONFLICT (tmdb_id) DO UPDATE SET
                 name = EXCLUDED.name,
                 profile_path = EXCLUDED.profile_path,
                 biography = EXCLUDED.biography,
                 birthday = EXCLUDED.birthday,
                 deathday = EXCLUDED.deathday,
                 place_of_birth = EXCLUDED.place_of_birth'''
        cur.execute(sql, (
            p['name'], p['tmdb_id'], p['profile_path'],
            p['biography'], p['birthday'], p['deathday'], p['place_of_birth']
        ))

    # --- GENRES ---
    genres = [d['name'] for d in m['genres']]
    if genres:
        sql = 'SELECT * FROM movies_genre WHERE name IN %s'
        cur.execute(sql, (tuple(genres),))
        genres_in_db = {name for id, name in cur.fetchall()}

        genres_to_create = [(name,) for name in genres if name not in genres_in_db]
        cur.executemany('INSERT INTO movies_genre (name) VALUES (%s)', genres_to_create)

    # --- MOVIE ---
    date_obj = date.fromisoformat(m['release_date']) 
    date_time = datetime.combine(date_obj, datetime.min.time())
    origin_country = ','.join(m.get('origin_country', []))

    sql = '''INSERT INTO movies_movie 
             (title, overview, release_date, origin_country, running_time,
              budget, tmdb_id, revenue, poster_path, backdrop_path)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
             ON CONFLICT (tmdb_id) DO UPDATE SET
             title = EXCLUDED.title,
             overview = EXCLUDED.overview,
             release_date = EXCLUDED.release_date,
             origin_country = EXCLUDED.origin_country,
             running_time = EXCLUDED.running_time,
             budget = EXCLUDED.budget,
             revenue = EXCLUDED.revenue,
             poster_path = EXCLUDED.poster_path,
             backdrop_path = EXCLUDED.backdrop_path'''

    cur.execute(sql, (
        m['title'], m['overview'], date_time.astimezone(timezone.utc),
        origin_country, m['runtime'], m['budget'],
        movie_id, m['revenue'], m['poster_path'], m['backdrop_path']
    ))

    # --- MOVIE GENRES ---
    if genres:
        sql = '''INSERT INTO movies_movie_genres (movie_id, genre_id)
                 SELECT (SELECT id FROM movies_movie WHERE tmdb_id = %s), id
                 FROM movies_genre WHERE name IN %s
                 ON CONFLICT DO NOTHING'''
        cur.execute(sql, (movie_id, tuple(genres)))

    # --- MOVIE CREDITS ---
    for name, job, character, order, tmdb_person_id in credits_list:
        sql = '''INSERT INTO movies_moviecredit (movie_id, person_id, job_id, character, "order")
                 SELECT 
                     (SELECT id FROM movies_movie WHERE tmdb_id = %s),
                     (SELECT id FROM movies_person WHERE tmdb_id = %s),
                     (SELECT id FROM movies_job WHERE name = %s),
                     %s,
                     %s
                 ON CONFLICT DO NOTHING'''
        cur.execute(sql, (movie_id, tmdb_person_id, job, character, order))

    conn.commit()
    cur.close()
    conn.close()
    print(f'Película {m["title"]} agregada correctamente')


if __name__ == "__main__":
    add_movie(int(sys.argv[1]))