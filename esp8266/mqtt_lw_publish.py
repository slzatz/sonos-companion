# Borrowed from Andrew http://forum.micropython.org/viewtopic.php?t=1101#p6545
# config will need ssid, pw, hostname,
import network
import socket
import ubinascii
#import lwip
from time import sleep
from config import host, ssid, pw

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

def wlan_connect(essid=ssid, password=pw):
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(essid, password)
    while not wlan.isconnected():
      pass
  print('network config:', wlan.ifconfig())     

def publish(topic, payload=None, hostname=host, port=1883, client_id="abc"):
  s = socket.socket()
  #print('Connecting to MQTT broker...')
  s.connect((hostname, port))
  s.send(mtpConnect(client_id))
  print(ubinascii.hexlify(s.recv(500)))
  #print("Publishing...")
  sleep(2) #10
  s.send(mtpPub(topic, payload)) #b'{"action":"quieter"}'))
  #sleep(4)
  #print(ubinascii.hexlify(s.recv(4096)))
  #print('Disconnecting...')
  s.send(mtpDisconnect())
  s.close()
  print('sent {}:{}'.format(topic, payload))

#wlan_connect(ssid, pw)
