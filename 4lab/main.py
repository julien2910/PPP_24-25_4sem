# pip install fastapi sqlalchemy pydantic uvicorn
# uvicorn main:app --reload

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
import crud
from database import get_db, engine, Base

app = FastAPI()

# Создаем таблицы при старте
Base.metadata.create_all(bind=engine)


# Кинотеатры
@app.get("/cinemas", response_model=List[schemas.Cinema],
         responses={
             200: {"description": "List of cinemas retrieved successfully"},
             422: {"description": "Validation error in query parameters"}
         })
def read_cinemas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if skip < 0:
        raise HTTPException(status_code=422, detail="Skip parameter cannot be negative")
    if limit <= 0 or limit > 100:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 100")
    return crud.get_cinemas(db, skip=skip, limit=limit)


@app.post("/cinemas", response_model=schemas.Cinema, status_code=201,
          responses={
              201: {"description": "Cinema created successfully"},
              400: {"description": "Invalid input data"},
              422: {"description": "Validation error"}
          })
def create_cinema(cinema: schemas.CinemaCreate, db: Session = Depends(get_db)):
    return crud.create_cinema(db=db, cinema=cinema)


@app.get("/cinemas/{cinema_id}/movies", response_model=List[schemas.Movie],
         responses={
             200: {"description": "List of movies for cinema retrieved successfully"},
             404: {"description": "Cinema not found"},
             422: {"description": "Validation error in cinema_id"}
         })
def read_cinema_movies(cinema_id: int, db: Session = Depends(get_db)):
    cinema = crud.get_cinema(db, cinema_id=cinema_id)
    if cinema is None:
        raise HTTPException(status_code=404, detail="Cinema not found")
    return crud.get_cinema_movies(db, cinema_id=cinema_id)


@app.delete("/cinemas/{cinema_id}", status_code=204,
            responses={
                204: {"description": "Cinema deleted successfully"},
                404: {"description": "Cinema not found"},
                422: {"description": "Validation error in cinema_id"}
            })
def delete_cinema(cinema_id: int, db: Session = Depends(get_db)):
    if not crud.delete_cinema(db, cinema_id=cinema_id):
        raise HTTPException(status_code=404, detail="Cinema not found")
    return None


# Фильмы
@app.get("/movies", response_model=List[schemas.Movie],
         responses={
             200: {"description": "List of movies retrieved successfully"},
             400: {"description": "Invalid cinema_id parameter"},
             422: {"description": "Validation error in query parameters"}
         })
def read_movies(cinema_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if skip < 0:
        raise HTTPException(status_code=422, detail="Skip parameter cannot be negative")
    if limit <= 0 or limit > 100:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 100")
    if cinema_id is not None and cinema_id <= 0:
        raise HTTPException(status_code=400, detail="cinema_id must be positive")
    return crud.get_movies(db, cinema_id=cinema_id, skip=skip, limit=limit)


@app.post("/movies", response_model=schemas.Movie, status_code=201,
          responses={
              201: {"description": "Movie created successfully"},
              400: {"description": "Invalid input data or cinema not found"},
              422: {"description": "Validation error"}
          })
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    cinema = crud.get_cinema(db, cinema_id=movie.cinema_id)
    if not cinema:
        raise HTTPException(status_code=400, detail="Cinema not found")
    return crud.create_movie(db=db, movie=movie)


@app.put("/movies/{movie_id}", response_model=schemas.Movie,
         responses={
             200: {"description": "Movie updated successfully"},
             400: {"description": "Invalid input data or cinema not found"},
             404: {"description": "Movie not found"},
             422: {"description": "Validation error"}
         })
def update_movie(movie_id: int, movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    # Проверяем существование кинотеатра
    cinema = crud.get_cinema(db, cinema_id=movie.cinema_id)
    if not cinema:
        raise HTTPException(status_code=400, detail="Cinema not found")

    db_movie = crud.update_movie(db, movie_id=movie_id, movie_data=movie)
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie


@app.get("/ping", responses={200: {"description": "Service is healthy"}})
def ping():
    return {"status": "ok"}
