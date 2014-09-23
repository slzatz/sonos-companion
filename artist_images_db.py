#Need to put sqlalchemy on the sys.path
import os
import sys

home = os.path.split(os.getcwd())[0]
sqla_dir = os.path.join(home,'sqlalchemy','lib')
sys.path = [sqla_dir] + sys.path

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine #, and_
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref 
from sqlalchemy.sql import select,join,and_

import json

__all__ = ['Artist', 'Image', 'session', 'conn', 'select', 'join', 'and_']

#__all__ = ['Artist', 'Image', 'select', 'join', 'conn', 'and_']

Base = declarative_base()

class Artist(Base):
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    images = relationship("Image", backref='artists')

    def __repr__(self):
        return "<Artist(name={}>".format(self.name)

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey('artists.id'))
    link = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    status = Column(Boolean, default=True)

    def __repr__(self):
        return "<artist_id={}, width={}, height={}, status={}>".format(self.artist_id, self.width, self.height, self.status)

#engine = create_engine('sqlite:///:memory:', echo=True)
engine = create_engine('sqlite:///artist.db', echo=True)
Base.metadata.create_all(engine) # only creates tables if they don't exist

conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

if __name__ == '__main__':

    try:
      with open('artists.json', 'r') as f:
          artists = json.load(f)
    except IOError:
         print "no artists"
         sys.exit()

    for a in artists:
        print "artist=",a
        artist = Artist(name=a)
        session.add(artist)
        session.commit()
        image_list = []
        for i in artists[a]:
            image = Image(link=i['link'],width=i['image']['width'],height=i['image']['height'])
            image_list.append(image)
        artist.images = image_list
        session.commit()



