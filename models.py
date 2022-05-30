from sqlalchemy import Boolean, Column, Integer, String

from database import Base

class RamenReviews(Base):
    __tablename__ = "ramenReviews"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Country = Column(String)
    Brand = Column(String)	
    Type = Column(String)
    Package = Column(String)
    Rating =  Column(Integer)
    Complete = Column(Boolean, default=True)