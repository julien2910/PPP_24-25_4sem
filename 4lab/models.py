from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Cinema(Base):
    __tablename__ = "cinemas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)

    movies = relationship("Movie", back_populates="cinema", cascade="all, delete")

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    cinema_id = Column(Integer, ForeignKey("cinemas.id", ondelete="CASCADE"))

    cinema = relationship("Cinema", back_populates="movies")