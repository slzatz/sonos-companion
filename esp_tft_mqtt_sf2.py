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

millnames = ['','k','M'] #,' Billion',' Trillion']
prev_forecast = [] # used to pick up the forecast around 1:30 am for comparisons

def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    s = '{:.1f}{}' if millidx > 1 else '{:.0f}{}'
    #return '{:.1f}{}'.format(n / 10**(3 * millidx), millnames[millidx])
    return s.format(n / 10**(3 * millidx), millnames[millidx])

#schedule.every().day.at("10:30").do(job) # 1:30 am to 2am - need this to get the start of the day sales forcast to compare to
def sales_forecast():
    s = requests.Session()
    r = s.get("https://login.salesforce.com/?un={}&pw={}".format(sf_id, sf_pw))
    r = s.get("https://na3.salesforce.com/00O50000003OCM5?view=d&snip&export=1&enc=UTF-8&xf=csv")
    
    content = r.content.decode('UTF-8')
    df = pd.read_csv(StringIO(content))
    sm = df.sum(axis=0)
    expected_amount = millify(sm['Amount Open Expected'])
    forecast = millify(sm['Current Forecast'])
    closed = millify(sm['Amount Closed'])
    print("Expected Amount: ", expected_amount)
    print("Forecast: ", forecast)
    print("Closed: ", closed)
    if prev_forecast:
        color = '{green}' if sm['Current Forecast'] > prev_forecast[0] else '{red}' if sm['Current Forecast'] < prev_forecast[0] else '{}'
    else:
        color ='{}'

    data = {"header":"Forecast",
            "text":["expected amount: {}".format(expected_amount),
                    "forecast: {}{}".format(color,forecast),
                    "closed: {}".format(closed)], 
                    "dest":(1600,900),
                    "pos":5} 

    mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_host, retain=False, port=1883, keepalive=60)

# gets the forecast at 1:30 am every morning
def get_previous_forecast():
    s = requests.Session()
    r = s.get("https://login.salesforce.com/?un={}&pw={}".format(sf_id, sf_pw))
    r = s.get("https://na3.salesforce.com/00O50000003OCM5?view=d&snip&export=1&enc=UTF-8&xf=csv")
    content = r.content.decode('UTF-8')
    df = pd.read_csv(StringIO(content))
    sm = df.sum(axis=0)
    prev_forecast.clear()
    prev_forecast.append(sm['Current Forecast'])

def top_opportunities():
    s = requests.Session()
    r = s.get("https://login.salesforce.com/?un={}&pw={}".format(sf_id, sf_pw))
    r = s.get("https://na3.salesforce.com/00O50000003OCM5?view=d&snip&export=1&enc=UTF-8&xf=csv")
    
    content = r.content.decode('UTF-8')
    df = pd.read_csv(StringIO(content))

    result = df.sort_values(["Current Forecast"], ascending=False)
    fc = []
    for x in range(8):
        row = result.iloc[x]
        if row["Amount Open Expected"] == 0:
            continue
        fc.append([row["Brand Level"][:26],millify(row["Amount Open Expected"]),row["Likely Probability in Quarter"],millify(row["Current Forecast"]),row["WebMD Segment (Oppty)"][4:]])
    headers=["Brand", "EA", "%", "Fcast", "Segment"]
    fc_formatted = tabulate(fc, headers).split("\n")

    #result = df.sort_values(["Amount Closed"], ascending=False) #this works but doesn't group same brand/same segment which below does
    result = df.groupby(["Brand Level", "WebMD Segment (Oppty)"]).sum().sort_values(by=["Amount Closed"], ascending=False)
    closed = []
    for x in range(8):
        row = result.iloc[x]
        # immedately below works for the non-grouped results and below that when grouping
        #closed.append([row["Brand Level"][:26],millify(row["Amount Closed"]),row["WebMD Segment (Oppty)"][4:]])
        closed.append([row.name[0][:26], millify(row[3]), row.name[1][4:].strip()])
    headers=["Brand", "Closed", "Segment"]
    closed_formatted = tabulate(closed, headers).split("\n")

    data = {"header":"Opportunities and Closed",
            "text":[''] + fc_formatted + [''] + closed_formatted, #blank lines cause a line feed
            "font size":16,
            "font type":"monospace",
            "bullets":False,
            "antialias":False, # makes monospace more readable
            "dest":(400,30),
            "pos":11}

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

schedule.every().hour.at(':01').do(top_opportunities)
schedule.every().hour.at(':06').do(top_opportunities)
schedule.every().hour.at(':11').do(top_opportunities)
schedule.every().hour.at(':16').do(top_opportunities)
schedule.every().hour.at(':21').do(top_opportunities)
schedule.every().hour.at(':26').do(top_opportunities)
schedule.every().hour.at(':31').do(top_opportunities)
schedule.every().hour.at(':36').do(top_opportunities)
schedule.every().hour.at(':41').do(top_opportunities)
schedule.every().hour.at(':46').do(top_opportunities)
schedule.every().hour.at(':51').do(top_opportunities)
schedule.every().hour.at(':56').do(top_opportunities)

schedule.every().day.at("1:30").do(get_previous_forecast)
#schedule.run_all()

while True:
    schedule.run_pending()
    sleep(1)


