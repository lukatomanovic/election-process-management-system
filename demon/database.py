from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from configuration import Configuration;

engine = create_engine(Configuration.SQLALCHEMY_DATABASE_URI);
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine);

Base = declarative_base();