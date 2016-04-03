from machine import Pin
import mqtt_lw_publish as p
from time import sleep_ms

p0 = Pin(0, Pin.IN)
p2 = Pin(2, Pin.IN)

def run():
  p.wlan_connect()
  while 1:
    if not p0.value():
      p.publish('sonos/ct', '{"action":"louder"}')
    if not p2.value():
      p.publish('sonos/ct', '{"action":"quieter"}')

    sleep_ms(100)

run()
