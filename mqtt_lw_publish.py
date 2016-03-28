# Borrowed from Andrew http://forum.micropython.org/viewtopic.php?t=1101#p6545

import lwip
from time import sleep
import network

addr = '54.173.234.69'

def mtStr(s):
  return bytes([len(s) >> 8, len(s) & 255]) + s.encode('utf-8')

def mtPacket(cmd, variable, payload):
  return bytes([cmd, len(variable) + len(payload)]) + variable + payload

def mtpConnect(name):
  return mtPacket(
           0b00010000,
           mtStr("MQTT") + # protocol name
           b'\x04' +       # protocol level
           b'\x00' +       # connect flag
           b'\xFF\xFF',    # keepalive
           mtStr(name)
  )

def mtpDisconnect():
  return bytes([0b11100000, 0b00000000])

def mtpPub(topic, data):
  return  mtPacket(0b00110001, mtStr(topic), data)

wlan = network.WLAN(network.STA_IF) 
wlan.active(True)    
wlan.connect('essid', 'password') 
print("connected =",wlan.isconnected())      

s = lwip.socket()

print('Connecting...')
s.connect(addr, 1883)
s.send(mtpConnect("sonos"))
print((s.recv(4096)))

print("Publishing...")

time.sleep(1) #10

s.send(mtpPub("sonos/nyc", b'{"action":"quieter"}'))
print((s.recv(4096)))

print('Disconnecting...')
s.send(mtpDisconnect())
s.close()
