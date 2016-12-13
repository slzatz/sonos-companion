'''
This script is imported to enable access now to the AWS EC2 artist_images db
Note that urls of the form http://userserve-ak.last.fm/serve/500/55326857/Buddy+Holly.jpg 
do not seem to work and need to be replaced
The lines below may be better way to pull images (uses xlarge and face)
service = discovery.build('customsearch', 'v1',  developerKey=g_api_key, http=http)
z = service.cse().list(q=artist, start=1, imgType='face', searchType='image', imgSize='xlarge', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 
'''
#Need to put sqlalchemy on the sys.path
import os
import sys
import random
#from config import RDS_URI
from config import ec_id, ec_pw, ec_host
home = os.path.split(os.getcwd())[0]
sqla_dir = os.path.join(home,'sqlalchemy','lib')
sys.path = [sqla_dir] + sys.path

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql import func, and_ #select, join, and_
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

__all__ = ['Artist', 'Image', 'session', 'IntegrityError',  'OperationalError', 'NoResultFound', 'func', 'engine', 'and_'] 
# might also  need 'Base', 'conn', 'select', 'join', 'and_', 'create_engine', 'sessionmaker', 'engine'

Base = declarative_base()

class Artist(Base):
    __tablename__ = 'artists'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    
    images = relationship("Image", backref='artist') #, cascade="all, delete", delete-orphan")

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
    
    #artist = relationship("Artist", backref=backref('images')) 

    def __repr__(self):
        return "<artist_id={}; link={}; ({},{})>".format(self.artist_id, self.link, self.width, self.height)

engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/artist_images'.format(ec_id, ec_pw, ec_host), echo=False)
#Base.metadata.create_all(engine) # only creates tables if they don't exist

#conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

#if run from the command line will print out some information from the database
if __name__ == '__main__':


    print("Get some images")

    print("---------------------------------------------------------------")
    print("---------------------------------------------------------------")
    rows = session.query(Artist).count()
    print("Number of artists", rows)

    for n in range(5):
        r = random.randint(1, rows)
        artist = session.query(Artist).get(r)
        if artist:
            print("artist =",artist.name)
            for image in artist.images:
                print("link =",image.link)
                print("width =",image.width)
                print("height =",image.height)
                print("image ok =",image.ok)
                print("\n")

