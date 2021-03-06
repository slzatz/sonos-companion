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
from exchangelib import Account, EWSDateTime, credentials, errors
from calendar import monthrange

cred = credentials.Credentials(username=exch_name, password=exch_pw)
account = Account(primary_smtp_address=email, credentials = cred, autodiscover=True, access_type=credentials.DELEGATE)
calendar = account.calendar
eastern = timezone('US/Eastern')

def outlook():
    now = datetime.now()
    highlight_hour = False
    if now.weekday() == 4 and now.hour > 21: # note this include time_zone_offset, ie 17 + 4
        inc_days = 3
    elif now.weekday() > 4:
        inc_days = 7 - now.weekday()
    elif now.hour > 21:
        inc_days = 1
    else:
        inc_days = 0
        highlight_hour = True
  
    dt = now + timedelta(inc_days)
    print "dt =",dt
    # below a problem at the end of the month
    #items = calendar.view(start=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_)), end=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_+1)))
    #below works
    #items = calendar.view(start=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_)), end=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_, now.hour+10)))

    #items = calendar.view(start=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_), 1), end=eastern.localize(EWSDateTime(now.year, now.month, now.day+next_, 23)))
    items = calendar.view(start=eastern.localize(EWSDateTime(dt.year, dt.month, dt.day, 1)), end=eastern.localize(EWSDateTime(dt.year, dt.month, dt.day, 23)))

    try:
        len(items)
    except (errors.ErrorInternalServerTransientError, errors.ErrorMailboxStoreUnavailable) as e:
        print "exchangelib error: ", e
        return
    except AttributeError as e:
        print "outlook error - would be caused by incorrect pw", e
        return

    text = []
    try:
        for item in items:
            subject = item.subject
            if "time off" in subject.lower():
                continue
            # after fall back hours = 5?
            line = (item.start-timedelta(hours=5)).strftime("%I:%M").lstrip('0')+"-"+(item.end-timedelta(hours=5)).strftime("%I:%M").lstrip('0')+" "+subject
            if "12:00-12:00" in line:
                line = "All Day Event -"+line[11:]

            #if highlight_hour and (now.hour == item.start.hour - 4):
            if highlight_hour and (now.hour == item.start.hour):
                line = "#{red}"+line
            text.append(line)
            print line
    except (errors.ErrorTimeoutExpired, errors.ErrorInternalServerTransientError) as e:
        print "exchangelib error: ", e
        return

    if not text:
        text = ["Nothing Scheduled"]
    data = {"header":"Schedule "+dt.strftime("%a %b %d"), "text":text, "pos":6, "dest":(475,470), "font size":16} #expects a list
    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)
    mqtt_publish.single('esp_tft_display', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)

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


