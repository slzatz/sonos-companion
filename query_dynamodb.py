'''
Uses flywheel, which is a library that has a sqlalchemy-like syntax, to query the Amazon DynamoDB database
that I am scrobbling songs to in programs like tft_sonos_instagram.py.
Probably should decide if that is the right place to scrobble or should just have a scrobbling script
'''
from datetime import datetime, timedelta
from flywheel import Model, Field, Engine # NUMBER

class scrobble(Model):
    artist = Field(hash_key=True)
    ts = Field(data_type=datetime, range_key=True)
    album = Field()
    title = Field()
    date = Field()
    scrobble = Field() #should have made this NUMBER, int

    def __init__(self, artist, ts, title, album, date, scrobble):
        self.artist = artist
        self.ts = ts
        self.album = album
        self.title = title
        self.date = date
        self.scrobble = scrobble

engine = Engine()
#engine.connect_to_host(host='localhost', port=8000)
engine.connect_to_region('us-east-1')

engine.register(scrobble)

# uncomment the following if you actually want to create the database for the first time
#engine.create_schema() 

# below is an example of how you would write to the the DynamoDB if you wanted to create a record
# in tft_sonos_instagram.py I am using boto but if it was using flywheel, it would look like the following
#z = scrobble("Patty Griffin", datetime.now(), "Making Pies", "Children Running through it", "Date: 1234", "14")
#engine.save(z)

days = input("How many days do you want to go back? ")

# scan may be slow but not looking for this to be particularly fast and can't query with no hash key
z = engine.scan(scrobble).filter(scrobble.ts > datetime.now()-timedelta(days=int(days))).all()
y = [(x.ts, x.title, x.artist, x.album[:40]) for x in z]
y.sort(key = lambda x:x[0], reverse=True)

for x in y:
    #print((x[0]-timedelta(hours=4)).strftime("%a %I %M"),x[1],' - ',x[2])
    #print("{}: {} - {}".format(*x))
    print("{}: {} - {} - {}".format((x[0]-timedelta(hours=4)).strftime("%a %I:%M%p"), x[1], x[2], x[3]))

