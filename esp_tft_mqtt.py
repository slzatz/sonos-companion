'''
python3
This script gathers information about things like weather and tides using Web apis
and then sends that information in an mqtt message with topic "esp_tft" 
The format is {"header":"Tides", "text":"The next high tide is ...", "pos":2}
pos is the position on the tft screen and is 0, 1, 2 etc
Information may be tides, stock prices, news, weather
The mqtt message is picked up by the esp8266 + feather tft
The script is esp_display_info.py
Schedule.every().hour.at(':00').do(job)
https://www.worldtides.info/api?extremes&lat=41.117597&lon=-73.407897&key=a417...
Documentation at https://www.worldtides.info/apidocs
Need to use the following for To Dos and Facts
random.choice(seq)- Return a random element from the non-empty sequence seq. If seq is empty, raises IndexError.
random.shuffle(x)
'''
import os
import sys
home = os.path.split(os.getcwd())[0]
#sys.path = [os.path.join(home, 'twitter')] + sys.path
sys.path =  sys.path + [os.path.join(home,'sqlalchemy','lib')] + [os.path.join(home, 'twitter')] + [os.path.join(home, 'mylistmanager3')]  ############################################
from operator import itemgetter
from itertools import cycle
import requests
import datetime
import paho.mqtt.publish as mqtt_publish
import json
import schedule
from time import time,sleep
import twitter
from config import tide_key, news_key, aws_mqtt_uri as aws_host, slz_twitter_oauth_token, slz_twitter_oauth_token_secret, slz_twitter_CONSUMER_KEY, slz_twitter_CONSUMER_SECRET
from lmdb_p import * ######################################################################
import html
from functools import partial

tides_uri = 'https://www.worldtides.info/api'
news_uri = 'https://newsapi.org/v1/articles'
news_sources = ['the-wall-street-journal', 'new-scientist', 'techcrunch', 'the-new-york-times', 'ars-technica', 'reddit-r-all']
news_source = cycle(news_sources)

publish = partial(mqtt_publish.single, 'esp_tft', hostname=aws_host, retain=False, port=1883, keepalive=60)

twit = twitter.Twitter(auth=twitter.OAuth(slz_twitter_oauth_token, slz_twitter_oauth_token_secret, slz_twitter_CONSUMER_KEY, slz_twitter_CONSUMER_SECRET))

session = remote_session

def twitter_feed():
    # pos = 1
    z = twit.statuses.home_timeline()
    tweets = ["{} - {}".format(x['user']['screen_name'],html.unescape(x['text'].split('https')[0])) for x in z] #could just use ['user']['name']
    print(datetime.datetime.now())
    print(repr(tweets).encode('ascii', 'ignore'))
    data = {"header":"twitter", "text":tweets, "pos":1} #expects a list
    #mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    publish(payload=json.dumps(data))

def news():
    #pos = 1
    #https://newsapi.org/v1/articles?source=techcrunch&apiKey=...
    #source = 'the-wall-street-journal'
    payload = {"apiKey":news_key, "source":next(news_source), "sortBy":"top"}

    try:
        r = requests.get(news_uri, params=payload)

    #except requests.exceptions.ConnectionError as e:
    except Exception as e:
        print("Exception in news", e)
        return

    z = r.json()
    articles = [html.unescape(x['title']) for x in z['articles']]
    print(datetime.datetime.now())
    print(repr(articles).encode('ascii', 'ignore'))
    header = z.get('source', 'no source').replace('-', ' ').title()
    data = {"header":header,"text":articles, "pos":1} #expects a list
    #mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    publish(payload=json.dumps(data))

def weather():
    #pos = 0

    #Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    #Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
    
    try:
        r = requests.get("http://api.wunderground.com/api/6eeded444749b8ec/forecast/q/10011.json")
    except Exception as e:
        print("Exception in weather", e)
        return
    
    z = r.json()
    if not 'forecast' in z:
        print("'forecast' not in result of weather request")
        return

    forecast = z['forecast']['txt_forecast']['forecastday']

    # if before 3 pm get today report and tomorrow report otherwise get tonight and tomorrow
    reports = (1,2) if datetime.datetime.now().hour > 15 else (0,2)
    text = []
    for n in reports:
       text.append(forecast[n]['title'] + ': ' + forecast[n]['fcttext'])
    print(datetime.datetime.now())
    print(repr(text).encode('ascii', 'ignore'))
    data = {"header":"Weather", "text":text, "pos":0}
    #mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    publish(payload=json.dumps(data))

def tides():
    #pos = 0
    saugatuck_entrance = {"lat":"41.1000", "lon":"-73.3667"}
    payload = {"key":tide_key}
    payload.update(saugatuck_entrance)
    payload.update({"extremes":""}) # this pulls high and low tide
    payload.update({"start":time()-3600,"length":75000})
    
    try:
        r = requests.get(tides_uri, params=payload)
    except Exception as e:
        print(e)
        return

    z = r.json()
    extremes = z['extremes']
    #print("Tide extremes =", extremes.encode('ascii', 'ignore'))

    tides = []
    for n,x in enumerate(extremes):
        print("n =", n)
        print("x =", x)
        tide = extremes[n]
        t = datetime.datetime.fromtimestamp(tide['dt'])
        delta = t-datetime.datetime.now()
        print("delta.seconds =",delta.seconds)
        print("delta =",delta)
        if delta.total_seconds() < 0:
            continue
        sec = delta.seconds
        hours = round(sec/3600)
        print("{} tide in {} hours".format(tide['type'], hours))
        tides.append("{} tide in {} hours".format(tide['type'], hours))

    data = {"header":"Tides", "text":tides, "pos":0}
    #mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    publish(payload=json.dumps(data))

def stock_quote():
    #pos = 2
    uri = "https://query.yahooapis.com/v1/public/yql" 
    payload = {'q':'select * from yahoo.finance.quotes where symbol in ("WBMD")', "format":"json", "env":"store://datatables.org/alltableswithkeys"}
    r = requests.get(uri, params=payload)
    z = r.json()
    #print(z)
    try:
        quote = z['query']['results']['quote']
    except Exception as e:
        print("Exception in WebMD stock quote:", e)
        return
    results = "{} {} EBITDA:{} Market Cap: {}".format(quote['LastTradePriceOnly'], quote['ChangeinPercent'], quote['EBITDA'], quote['MarketCapitalization']) 
    print(datetime.datetime.now())
    print(results.encode('ascii', 'ignore'))
    data = {"header":"WBMD", "text":[results], "pos":2} #expects a list
    #mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    publish(payload=json.dumps(data))


def todos():
    #pos = 3
    #tasks = session.query(Task).join(Context).filter(and_(Context.title == 'work', Task.priority == 3, Task.star == True, Task.completed == None)).order_by(desc(Task.modified))
    tasks = session.query(Task).join(Context).filter(and_(Context.title == 'work', Task.priority == 3, Task.completed == None)).order_by(desc(Task.modified))
    #titles = [task.title for task in tasks]
    titles = ['#'+task.title if task.star else task.title for task in tasks]
    print(datetime.datetime.now())
    print(repr(titles).encode('ascii', 'ignore'))

    data = {"header":"To Do", "text":titles, "pos":3} #expects a list
    #mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    publish(payload=json.dumps(data))

def facts():
    #pos = 3
    tasks = session.query(Task).join(Context).filter(and_(Context.title == 'memory aid', Task.priority == 3, Task.star == True, Task.completed == None)).order_by(desc(Task.modified))
    titles = [task.title for task in tasks]
    print(datetime.datetime.now())
    print(repr(titles).encode('ascii', 'ignore'))

    data = {"header":"Facts", "text":titles, "pos":3} #expects a list
    #mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    publish(payload=json.dumps(data))

#schedule.every(30).minutes.do(weather)
schedule.every().hour.at(':07').do(tides)
#schedule.every().hour.at(':17').do(tides)
#schedule.every().hour.at(':27').do(tides)
schedule.every().hour.at(':37').do(tides)
#schedule.every().hour.at(':47').do(tides)
#schedule.every().hour.at(':57').do(tides)

schedule.every().hour.at(':03').do(weather)
schedule.every().hour.at(':13').do(weather)
schedule.every().hour.at(':23').do(weather)
schedule.every().hour.at(':33').do(weather)
schedule.every().hour.at(':43').do(weather)
schedule.every().hour.at(':53').do(weather)

schedule.every().hour.at(':05').do(news)
schedule.every().hour.at(':15').do(news)
schedule.every().hour.at(':25').do(news)
schedule.every().hour.at(':35').do(news)
schedule.every().hour.at(':45').do(news)
schedule.every().hour.at(':55').do(news)

schedule.every().hour.at(':02').do(stock_quote)
schedule.every().hour.at(':12').do(stock_quote)
schedule.every().hour.at(':22').do(stock_quote)
schedule.every().hour.at(':32').do(stock_quote)
schedule.every().hour.at(':42').do(stock_quote)
schedule.every().hour.at(':52').do(stock_quote)

schedule.every().hour.at(':00').do(twitter_feed)
schedule.every().hour.at(':10').do(twitter_feed)
schedule.every().hour.at(':20').do(twitter_feed)
schedule.every().hour.at(':30').do(twitter_feed)
schedule.every().hour.at(':40').do(twitter_feed)
schedule.every().hour.at(':50').do(twitter_feed)

schedule.every().hour.at(':01').do(todos)
schedule.every().hour.at(':11').do(todos)
schedule.every().hour.at(':21').do(todos)
schedule.every().hour.at(':31').do(todos)
schedule.every().hour.at(':41').do(todos)
schedule.every().hour.at(':51').do(todos)

schedule.every().hour.at(':08').do(facts)
schedule.every().hour.at(':18').do(facts)
schedule.every().hour.at(':28').do(facts)
schedule.every().hour.at(':38').do(facts)
schedule.every().hour.at(':48').do(facts)
schedule.every().hour.at(':58').do(facts)
#schedule.run_all()

while True:
    schedule.run_pending()
    sleep(1)


