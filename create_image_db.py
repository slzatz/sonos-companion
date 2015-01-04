#{
#"Plumb": [{"image" : {"width": 300, "height":300}, "link":"http:...."}, {{"image" : {"width": 300, "height":300}, "link":"http:...."}]
#
#"Neil": [{"image" : {"width": 300, "height":300}, "link":"http:...."}, {{"image" : {"width": 300, "height":300}, "link":"http:...."}]
#}

#Base = declarative_base()
#
#class Song(Base):
#    __tablename__ = 'songs'
#    id = Column(Integer, primary_key=True)
#    artist = Column(String)
#    album = Column(String)
#    title = Column(String)
#    uri = Column(String)
#    album_art = Column(String)
#    __table_args__ = (UniqueConstraint('artist', 'album', 'title'),)
#    
#    def __repr__(self):
#        return "<artist={}, album={}, title={}, uri={}>".format(self.artist, self.album, self.title, self.uri)
#
##engine = create_engine('sqlite:///amazon_music.db', echo=True)
#engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/music'.format(c.aws_id, c.aws_pw, c.aws_host), echo=True)
#Base.metadata.create_all(engine) # only creates tables if they don't exist

import os
import sys
import random
import config as c
home = os.path.split(os.getcwd())[0]
sqla_dir = os.path.join(home,'sqlalchemy','lib')
sys.path = [sqla_dir] + sys.path
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
#from sqlalchemy.orm import relationship, backref 
#from sqlalchemy.sql import select,join,and_
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

__all__ = ['Artist', 'Image', 'session', 'IntegrityError',  'OperationalError', 'NoResultFound'] #, 'conn'] #, 'select', 'join', 'and_']

Base = declarative_base()

class Artist(Base):
    __tablename__ = 'artists'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    
    def __repr__(self):
        return "<artist={}>".format(self.name)

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey('artists.id'), nullable=False)
    link = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    ok = Column(Boolean, default=True)
    
    user = relationship("Artist", backref=backref('images')) 
   
    def __repr__(self):
        return "<artist_id={}; link={}; ({},{})>".format(self.artist_id, self.link, self.width, self.height)

#engine = create_engine('sqlite:///artist_images.db', echo=True)
engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/music'.format(c.aws_id, c.aws_pw, c.aws_host), echo=True)
Base.metadata.create_all(engine) # only creates tables if they don't exist

Session = sessionmaker(bind=engine)
session = Session()

if __name__ == '__main__':

    try:
      with open('artists.json', 'r') as f:
          artists = json.load(f)
    except IOError:
          print "Can't open artists.json"
          sys.exit()
    n=0
    for a in artists:
        
        try:
            artist = Artist(name=a)
            session.add(artist)
            session.commit()
        except (IntegrityError, OperationalError) as e:
            session.rollback()
            print "IntegrityError: ",e
            continue

        n+=1
   
        images = []
        for i in artists[a]:
            image = Image(link=i['link'], width=i['image']['width'],height=i['image']['height'])
            images.append(image)
            
        artist.images = images
        session.commit()

    print n, "artist records created"
