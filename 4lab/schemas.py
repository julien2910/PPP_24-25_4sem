# schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional

class CinemaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the cinema")
    address: str = Field(..., min_length=1, max_length=200, description="Address of the cinema")

class CinemaCreate(CinemaBase):
    pass

class Cinema(CinemaBase):
    id: int = Field(..., description="Unique identifier of the cinema")

    class Config:
        from_attributes = True

class MovieBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the movie")
    genre: str = Field(..., min_length=1, max_length=50, description="Genre of the movie")
    cinema_id: int = Field(..., gt=0, description="ID of the cinema where the movie is shown")

class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    id: int = Field(..., description="Unique identifier of the movie")

    class Config:
        from_attributes = True