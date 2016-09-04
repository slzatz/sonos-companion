'''
This is the script that can run on a raspberry pi that gets the tide data and 
posts mqtt messages that are picked up by scripts running on esp8266
neo_tides.py

https://www.worldtides.info/api?extremes&lat=41.117597&lon=-73.407897&key=a417...
Documentation at https://www.worldtides.info/apidocs

'''
import requests
import datetime
import paho.mqtt.publish as mqtt_publish
import json
from time import time,sleep
from config import tide_key

topic = "tides"
uri = "https://www.worldtides.info/api"
saugatuck_entrance = {"lat":"41.1000", "lon":"-73.3667"}
payload = {"key":tide_key}
payload.update(saugatuck_entrance)
payload.update({"extremes":""}) # this pulls high and low tide
payload.update({"start":time()-3600,"length":75000})

# These make sure that the tide data is gotten and written to neopixel feather right away
t0 = datetime.datetime.now()-datetime.timedelta(hours=10) 
t1 = datetime.datetime.now()-datetime.timedelta(minutes=20)

while True:
    if (datetime.datetime.now()-t0).seconds > 28800: #check for tide data every 8 hours
        try:
            r = requests.get(uri, params=payload)
        except Exception as e:
            print(e)
            sleep(60)
            continue
        else:
            z = r.json()
            data = z['extremes']
            print("Tide data =", data)

            t0 = datetime.datetime.now()

    if (datetime.datetime.now()-t1).seconds > 900: #update neopixels every 15 min
        for n,x in enumerate(data):
            if datetime.datetime.now().hour <= datetime.datetime.fromtimestamp(x['dt']).hour:
                break

        tides = []
        for i in (n,n+1):
            tide = data[i]
            t = datetime.datetime.fromtimestamp(tide['dt'])
            delta = t-datetime.datetime.now()
            if delta.seconds < 0:
                delta = datetime.timedelta(seconds=0)
            sec = delta.seconds
            hours = round(sec/3600)
            print("The {} tide will be in {} hours".format(tide['type'],hours))
            tides.append({"type":tide['type'], "time_delta":hours})

        mqtt_msg = json.dumps(tides)
        print("The mqtt message =", mqtt_msg)

        mqtt_publish.single(topic, mqtt_msg, hostname="54.173.234.69", retain=False, port=1883, keepalive=60)

        t1 = datetime.datetime.now()

    sleep(60)
