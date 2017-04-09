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
import pandas as pd
import requests
from tabulate import tabulate
import math
import paho.mqtt.publish as mqtt_publish
import json
import schedule
from time import sleep
from config import aws_mqtt_uri as aws_host, sf_id, sf_pw
import csv
from io import StringIO

millnames = ['','k','M',' Billion',' Trillion']

def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.1f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

def sales_forecast():
    s = requests.Session()
    r = s.get("https://login.salesforce.com/?un={}&pw={}".format(sf_id, sf_pw))
    r = s.get("https://na3.salesforce.com/00O50000003OCM5?view=d&snip&export=1&enc=UTF-8&xf=csv")
    
    content = r.content.decode('UTF-8')
    #sf_data = csv.reader(StringIO(content))

    #df = pd.read_csv('sf_report.csv')
    df = pd.read_csv(StringIO(content))
    sm = df.sum(axis=0)
    expected_amount = millify(sm['Amount Open Expected'])
    forecast = millify(sm['Current Forecast'])
    closed = millify(sm['Amount Closed'])
    print("Expected Amount: ", expected_amount)
    print("Forecast: ", forecast)
    print("Closed: ", closed)

    data = {"header":"Forecast",
            "text":["expected amount: {}".format(expected_amount),
                    "forecast: {}".format(forecast),
                    "closed: {}".format(closed)], 
                    "pos":5} 

    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)


schedule.every().hour.at(':03').do(sales_forecast)
schedule.every().hour.at(':08').do(sales_forecast)
schedule.every().hour.at(':13').do(sales_forecast)
schedule.every().hour.at(':18').do(sales_forecast)
schedule.every().hour.at(':23').do(sales_forecast)
schedule.every().hour.at(':28').do(sales_forecast)
schedule.every().hour.at(':33').do(sales_forecast)
schedule.every().hour.at(':38').do(sales_forecast)
schedule.every().hour.at(':43').do(sales_forecast)
schedule.every().hour.at(':48').do(sales_forecast)
schedule.every().hour.at(':53').do(sales_forecast)
schedule.every().hour.at(':58').do(sales_forecast)
#schedule.run_all()

while True:
    schedule.run_pending()
    sleep(1)


