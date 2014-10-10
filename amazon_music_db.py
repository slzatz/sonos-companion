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

didl_template = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><res protocolInfo="sonos.com-http:*:audio/mp4:*" duration="0:02:46">{uri}</res><r:streamContent></r:streamContent><upnp:albumArtURI>{album_art}</upnp:albumArtURI><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><dc:creator>{artist}</dc:creator><upnp:album>{album}</upnp:album></item></DIDL-Lite>'''

#didl_template = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><res protocolInfo="sonos.com-http:*:audio/mp4:*" duration="0:02:46"></res><r:streamContent></r:streamContent><upnp:albumArtURI>{album_art}</upnp:albumArtURI><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><dc:creator>{artist}</dc:creator><upnp:album>{album}</upnp:album></item></DIDL-Lite>'''

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

# album art may start here "/getaa?s=1&amp;u=x-sonos-http%3aamz%253atr%253a898af4d3-7940-4c4b-b4ca-74e58d0e62fa.mp4%3fsid%3d26%26flags%3d32"

__all__ = ['Song', 'session', 'IntegrityError', 'didl_template'] #'conn', 'select', 'join', 'and_']

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

engine = create_engine('sqlite:///amazon_music.db', echo=True)
Base.metadata.create_all(engine) # only creates tables if they don't exist

conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

#if run from the command line will populate database from artists.json
if __name__ == '__main__':
    pass
    




