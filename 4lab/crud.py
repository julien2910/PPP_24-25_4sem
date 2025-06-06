from sqlalchemy.orm import Session
import schemas
import models

def get_cinemas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cinema).offset(skip).limit(limit).all()

def create_cinema(db: Session, cinema: schemas.CinemaCreate):
    db_cinema = models.Cinema(**cinema.model_dump())
    db.add(db_cinema)
    db.commit()
    db.refresh(db_cinema)
    return db_cinema

def get_cinema(db: Session, cinema_id: int):
    return db.query(models.Cinema).filter(models.Cinema.id == cinema_id).first()

def delete_cinema(db: Session, cinema_id: int):
    cinema = db.query(models.Cinema).filter(models.Cinema.id == cinema_id).first()
    if cinema:
        db.delete(cinema)
        db.commit()
        return True
    return False

def get_cinema_movies(db: Session, cinema_id: int):
    return db.query(models.Movie).filter(models.Movie.cinema_id == cinema_id).all()

def get_movies(db: Session, cinema_id: int | None = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Movie)
    if cinema_id:
        query = query.filter(models.Movie.cinema_id == cinema_id)
    return query.offset(skip).limit(limit).all()

def create_movie(db: Session, movie: schemas.MovieCreate):
    db_movie = models.Movie(**movie.model_dump())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

def get_movie(db: Session, movie_id: int):
    return db.query(models.Movie).filter(models.Movie.id == movie_id).first()

def update_movie(db: Session, movie_id: int, movie_data: schemas.MovieCreate):
    db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if db_movie:
        for key, value in movie_data.model_dump().items():
            setattr(db_movie, key, value)
        db.commit()
        db.refresh(db_movie)
        return db_movie
    return None