#Need to put sqlalchemy on the sys.path
import os
import sys

home = os.path.split(os.getcwd())[0]
sqla_dir = os.path.join(home,'sqlalchemy','lib')
sys.path = [sqla_dir] + sys.path

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String #, Boolean, ForeignKey
#from sqlalchemy.orm import relationship, backref 
#from sqlalchemy.sql import select,join,and_
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError

import json

__all__ = ['Song', 'session', 'IntegrityError'] #'conn', 'select', 'join', 'and_']

Base = declarative_base()

class Song(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key=True)
    artist = Column(String)
    album = Column(String)
    title = Column(String)
    uri = Column(String)
    album_art = Column(String)
    __table_args__ = (UniqueConstraint('artist', 'album', 'title'),)
    
    def __repr__(self):
        return "<artist={}, album={}, track={}, uri={}>".format(self.artist, self.album, self.title, self.uri)

engine = create_engine('sqlite:///amazon_music.db', echo=True)
Base.metadata.create_all(engine) # only creates tables if they don't exist

conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

#if run from the command line will populate database from artists.json
if __name__ == '__main__':
    pass




