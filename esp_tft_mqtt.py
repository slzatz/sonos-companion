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

'''
import os
import sys
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'twitter')] + sys.path
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

tide_uri = 'https://www.worldtides.info/api'
news_uri = 'https://newsapi.org/v1/articles'
sources = ['the-wall-street-journal', 'new-scientist', 'techcrunch', 'the-new-york-times', 'ars-technica', 'reddit-r-all']
source = cycle(sources)

twit = twitter.Twitter(auth=twitter.OAuth(slz_twitter_oauth_token, slz_twitter_oauth_token_secret, slz_twitter_CONSUMER_KEY, slz_twitter_CONSUMER_SECRET))

def twitter_feed():
    z = twit.statuses.home_timeline()
    tweets = ["{} - {}".format(x['user']['screen_name'],x['text'].split('https')[0]) for x in z] #could just use ['user']['name']
    print(datetime.datetime.now())
    print(repr(tweets).encode('ascii', 'ignore'))
    data = {"header":"twitter", "text":tweets, "pos":1} #expects a list
    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)

def news():
    #pos = 1
    #https://newsapi.org/v1/articles?source=techcrunch&apiKey=...
    #source = 'the-wall-street-journal'
    payload = {"apiKey":news_key, "source":next(source), "sortBy":"top"}

    try:
        r = requests.get(news_uri, params=payload)

    #except requests.exceptions.ConnectionError as e:
    except Exception as e:
        print("Exception in news", e)
        return

    z = r.json()
    articles = [x['title'] for x in z['articles']]
    print(datetime.datetime.now())
    print(repr(articles).encode('ascii', 'ignore'))
    data = {"header":z.get('source', 'no source'),"text":articles, "pos":1} #expects a list
    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)

def weather():
    # pos = 0
    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
    
    try:
        r = requests.get("http://api.wunderground.com/api/6eeded444749b8ec/forecast/q/10011.json")
        #m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
        #m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']

    #except requests.exceptions.ConnectionError as e:
    except Exception as e:
        #print "ConnectionError in request in display_weather: ", e
        print("Exception in weather", e)
        return
    
    z = r.json()
    if not 'forecast' in z:
        print("'forecast' not in result of weather request")
        return

    forecast = z['forecast']['txt_forecast']['forecastday']
    #f0 = forecast[0]['title'] + ': ' + forecast[0]['fcttext']
    #f1 = forecast[1]['title'] + ': ' + forecast[1]['fcttext']
    #f2 = forecast[2]['title'] + ': ' + forecast[2]['fcttext']

    # if before 3 pm get today report and tomorrow report otherwise get tonight and tomorrow
    reports = (1,2) if datetime.datetime.now().hour > 15 else (0,2)
    text = []
    for n in reports:
       text.append(forecast[n]['title'] + ': ' + forecast[n]['fcttext'])
    print(datetime.datetime.now())
    print(repr(text).encode('ascii', 'ignore'))
    data = {"header":"Weather", "text":text, "pos":0}
    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)

def tides():
    uri = 'https://www.worldtides.info/api'
    saugatuck_entrance = {"lat":"41.1000", "lon":"-73.3667"}
    payload = {"key":tide_key}
    payload.update(saugatuck_entrance)
    payload.update({"extremes":""}) # this pulls high and low tide
    payload.update({"start":time()-3600,"length":75000})
    
    try:
        r = requests.get(uri, params=payload)
    except Exception as e:
        print(e)
        return

    z = r.json()
    data = z['extremes']
    #print("Tide data =", data.encode('ascii', 'ignore'))

    tides = []
    for n,x in enumerate(data):
        print("n =", n)
        print("x =", x)
        tide = data[n]
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

    data1 = {"header":"Tides", "text":tides, "pos":1}
    print(data1)
    mqtt_publish.single('esp_tft', json.dumps(data1), hostname=aws_host, retain=False, port=1883, keepalive=60)

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
    results = "{} {} {} {}".format(quote['LastTradePriceOnly'], quote['ChangeinPercent'], quote['EBITDA'], quote['MarketCapitalization']) 
    print(datetime.datetime.now())
    print(results.encode('ascii', 'ignore'))
    data = {"header":"WebMD Stock Quote", "text":[results], "pos":2} #expects a list
    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)

#schedule.every(30).minutes.do(weather)
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
#schedule.run_all()

while True:
    schedule.run_pending()
    sleep(1)


