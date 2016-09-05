'''
Note there is no database connection between song.artist and artist but I think that's OK
songs table came first and no real reason to connect them to artist since often artists
are coming from Pandora or equivalent and not from my database of songs
Note that urls of the form http://userserve-ak.last.fm/serve/500/55326857/Buddy+Holly.jpg 
do not seem to work and need to be replaced
The lines below may be better way to pull images (uses xlarge and face)
service = discovery.build('customsearch', 'v1',  developerKey=g_api_key, http=http)
z = service.cse().list(q=artist, start=1, imgType='face', searchType='image', imgSize='xlarge', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 
NOTE:  I have added a playlist so I can create them (although need a tool to do that) but haven't actually created the table
'''
#Need to put sqlalchemy on the sys.path
import os
import sys
import random
import config as c
home = os.path.split(os.getcwd())[0]
sqla_dir = os.path.join(home,'sqlalchemy','lib')
sys.path = [sqla_dir] + sys.path

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
#from sqlalchemy.sql import select,join,and_
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

#This is now defined in tft_sonos.py but not in sonos_lcd_no_server3.py
#only format item is {id_}
didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

__all__ = ['Base','Artist', 'Image', 'session', 'IntegrityError',  'OperationalError', 'NoResultFound', 'didl_amazon', 'engine', 'create_engine', 'sessionmaker'] #, 'conn'] #, 'select', 'join', 'and_', 'Song']

Base = declarative_base()

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
    
    #user = relationship("Artist", backref=backref('images')) 
    artist = relationship("Artist", backref=backref('images')) 
   
    def __repr__(self):
        return "<artist_id={}; link={}; ({},{})>".format(self.artist_id, self.link, self.width, self.height)

#association_table = Table('association', Base.metadata,
#    Column('playlist_id', Integer, ForeignKey('playlists.id')),
#    Column('song_id', Integer, ForeignKey('songs.id'))

#class Playlist(Base):
#    __tablename__ = 'playlists'
#    id = Column(Integer, primary_key=True)
#    songs = relationship("Song", secondary=association_table)
#
#engine = create_engine('sqlite:///amazon_music.db', echo=True)
engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/music'.format(c.aws_id, c.aws_pw, c.aws_host), echo=False)
#Base.metadata.create_all(engine) # only creates tables if they don't exist

#conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

#if run from the command line will print out some information from the database
#if __name__ == '__main__':
#
#    rows = session.query(Song).count()
#    print "rows = ", rows
#    #image = images[random.randrange(0,L-1)]
#    print "First 10"
#    n=0
#    songs = session.query(Song) 
#    for song in songs:
#        print "id=",song.id
#        print "artist=",song.artist.encode('ascii', 'ignore')
#        print "album=",song.album.encode('ascii', 'ignore')
#        print "song title=",song.title.encode('ascii', 'ignore')
#        print "sonos/amazon uri=",song.uri.encode('ascii', 'ignore')
#        print "album art=",song.album_art.encode('ascii', 'ignore')
#        print "---------------------------------------------------------------"
#        n+=1
#        if n==10:
#            break
#            
#    print "Random 10"
#
#    print "---------------------------------------------------------------"
#    print "---------------------------------------------------------------"
#
#    for n in range(10):
#        r = random.randint(1,rows)
#        #song = session.query(Song).filter(Song.id==r).one()
#        song = session.query(Song).get(r)
#        # some songs may have been deleted so not every potential id will be valid
#        if song:
#            print "id=",song.id
#            print "artist=",song.artist.encode('ascii', 'ignore')
#            print "album=",song.album.encode('ascii', 'ignore')
#            print "song title=",song.title.encode('ascii', 'ignore')
#            print "sonos/amazon uri=",song.uri.encode('ascii', 'ignore')
#            print "album art=",song.album_art.encode('ascii', 'ignore')
#            print "---------------------------------------------------------------"
#
#    print "Get some images"
#
#    print "---------------------------------------------------------------"
#    print "---------------------------------------------------------------"
#    rows = session.query(Artist).count()
#    print "Number of artists", rows
#
#    for n in range(5):
#        r = random.randint(1, rows)
#        artist = session.query(Artist).get(r)
#        if artist:
#            print artist.name
#            for image in artist.images:
#                print image.link
#                print image.width
#                print image.height
#                print image.ok
#
