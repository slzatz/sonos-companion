from machine import Pin
import mqtt_lw_publish as p
from time import sleep_ms

p0 = Pin(0, Pin.IN)
p2 = Pin(2, Pin.IN)

def run():
  p.wlan_connect()
  n = 0
  while 1:
    if not p0.value():
      p.publish('sonos/ct', '{"action":"louder"}')
    if not p2.value():
      p.publish('sonos/ct', '{"action":"quieter"}')

    sleep_ms(100)

    n+=1
    if n = 10:
      socket.send('GET /sonos_track HTTP/1.0\r\n\r\n')
      z = s.recv(4096)
      print(z)
      n = 0
    else:
      sleep_ms()

run()
