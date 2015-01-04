#Need to put sqlalchemy on the sys.path
import os
import sys
import random
import config as c
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
from sqlalchemy.exc import IntegrityError, OperationalError

#this is what was captured by wireshark
didl_wire = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020amz%3atr%3a9d59de5f-fdb7-4741-8a29-ccaf8d1cd34f" parentID="0006006camz%3apl%3a98eeb62c-179f-4f79-9870-11ca87bad2fe" restricted="true"><dc:title>Campaigner</dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

#original template that included {title} which doesn't seem to be necessary
didl_wire_template = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

#only format item is {id_}
didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

__all__ = ['Song', 'session', 'IntegrityError',  'OperationalError', 'didl_amazon'] #, 'conn'] #, 'select', 'join', 'and_']

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
        return "<artist={}, album={}, title={}, uri={}>".format(self.artist, self.album, self.title, self.uri)

#engine = create_engine('sqlite:///amazon_music.db', echo=True)
engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/music'.format(c.aws_id, c.aws_pw, c.aws_host), echo=True)
Base.metadata.create_all(engine) # only creates tables if they don't exist

conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

#if run from the command line will print out some information from the database
if __name__ == '__main__':

    rows = session.query(Song).count()
    print "rows = ", rows
    #image = images[random.randrange(0,L-1)]
    print "First 10"
    n=0
    songs = session.query(Song) 
    for song in songs:
        print "id=",song.id
        print "artist=",song.artist.encode('ascii', 'ignore')
        print "album=",song.album.encode('ascii', 'ignore')
        print "song title=",song.title.encode('ascii', 'ignore')
        print "sonos/amazon uri=",song.uri.encode('ascii', 'ignore')
        print "album art=",song.album_art.encode('ascii', 'ignore')
        print "---------------------------------------------------------------"
        n+=1
        if n==10:
            break
            
    print "Random 10"

    print "---------------------------------------------------------------"
    print "---------------------------------------------------------------"

    for n in range(10):
        r = random.randint(1,rows)
        #song = session.query(Song).filter(Song.id==r).one()
        song = session.query(Song).get(r)
        print "id=",song.id
        print "artist=",song.artist.encode('ascii', 'ignore')
        print "album=",song.album.encode('ascii', 'ignore')
        print "song title=",song.title.encode('ascii', 'ignore')
        print "sonos/amazon uri=",song.uri.encode('ascii', 'ignore')
        print "album art=",song.album_art.encode('ascii', 'ignore')
        print "---------------------------------------------------------------"

