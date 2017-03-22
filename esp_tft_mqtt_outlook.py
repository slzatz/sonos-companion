'''
python2.7 (because exchangelib is a python 2.7 package)
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
import paho.mqtt.publish as mqtt_publish
import json
import schedule
from time import sleep
from config import aws_mqtt_uri as aws_host, exch_name, exch_pw, email
from pytz import timezone
from datetime import datetime, timedelta
#import sys
#import os
#home = os.path.split(os.getcwd())[0]
#sys.path = sys.path + [os.path.join(home,'exchangelib')] 
from exchangelib import Account, EWSDateTime, credentials

cred = credentials.Credentials(username=exch_name, password=exch_pw)
account = Account(primary_smtp_address=email, credentials = cred, autodiscover=True, access_type=credentials.DELEGATE)
calendar = account.calendar
eastern = timezone('US/Eastern')

def outlook():
    now = datetime.now()
    if now.weekday() > 4:
        next_ = 7 - now.weekday()
    elif now.hour > 16:
        next_ = 1
    else:
        next_ = 0

    items = calendar.view(start=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_)), end=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_+1)))
    text = []
    for item in items:
        line = (item.start-timedelta(hours=4)).strftime("%I:%M").lstrip('0')+"-"+(item.end-timedelta(hours=4)).strftime("%I:%M").lstrip('0')+" "+item.subject
        # could check time and use some marker to indicate since hard to bold
        # unless there was some signal to display_info.py that a line should be bolded
        if now.hour == item.start.hour - 4:
            line = "->"+line
        text.append(line)
        print line

    date = now+timedelta(days=next_)
    data = {"header":"Schedule "+date.strftime("%a %b %d"), "text":text, "pos":6} #expects a list
    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)

schedule.every().hour.at(':04').do(outlook)
schedule.every().hour.at(':09').do(outlook)
schedule.every().hour.at(':14').do(outlook)
schedule.every().hour.at(':19').do(outlook)
schedule.every().hour.at(':24').do(outlook)
schedule.every().hour.at(':29').do(outlook)
schedule.every().hour.at(':34').do(outlook)
schedule.every().hour.at(':39').do(outlook)
schedule.every().hour.at(':44').do(outlook)
schedule.every().hour.at(':49').do(outlook)
schedule.every().hour.at(':53').do(outlook)
schedule.every().hour.at(':58').do(outlook)
#schedule.run_all()

while True:
    schedule.run_pending()
    sleep(1)


