#Need to put sqlalchemy on the sys.path
import os
import sys
import random
import argparse
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

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('-e', '--echo', action='store_true', help="Echo SQL=True") #default is opposite of action
args = parser.parse_args()

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

engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/music'.format(c.aws_id, c.aws_pw, c.aws_host), echo=args.echo)
#engine = create_engine('sqlite:///amazon_music.db', echo=True)

#Base.metadata.create_all(engine) # only creates tables if they don't exist
conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

if __name__ == '__main__':

    rows = session.query(Song).count()
    print "\nrows = {}\n".format(rows)

    for n in range(10):
        r = random.randint(1,rows)
        song = session.query(Song).get(r)
        if song:
            print song.id
            print song.artist.encode('ascii', 'ignore')
            print song.album.encode('ascii', 'ignore')
            print song.title.encode('ascii', 'ignore')
            print song.uri.encode('ascii', 'ignore')
            print song.album_art.encode('ascii', 'ignore')
            i = song.uri.find('amz')
            ii = song.uri.find('.')
            id_ = song.uri[i:ii]
            print id_.encode('ascii', 'ignore')
            print "---------------------------------------------------------------"
