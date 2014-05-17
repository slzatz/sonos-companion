/*************************************************** 
  This is a program to detect button pushes (sparkfun vkey) and potentiometer changes
  based on code from Adafruit for the CC3000 Wifi Breakout & Shield
 ****************************************************/
 
#include <Adafruit_CC3000.h>
#include <ccspi.h>
#include <SPI.h>
#include <string.h>
#include "utility/debug.h"
#include "MemoryFree.h"
#include "stuff.h"

// These are the interrupt and control pins
#define ADAFRUIT_CC3000_IRQ   3  // MUST be an interrupt pin!
// These can be any two pins
#define ADAFRUIT_CC3000_VBAT  5
#define ADAFRUIT_CC3000_CS    10
// Use hardware SPI for the remaining pins
// On an UNO, SCK = 13, MISO = 12, and MOSI = 11

Adafruit_CC3000 cc3000 = Adafruit_CC3000(ADAFRUIT_CC3000_CS, ADAFRUIT_CC3000_IRQ, ADAFRUIT_CC3000_VBAT, SPI_CLOCK_DIVIDER); // clock speed can be changed

//define WLAN_SSID, WLAN_PASS and WLAN_SECURITY in a separate file

#define IDLE_TIMEOUT_MS  3000      // Amount of time to wait (in milliseconds) with no data 
                                   // received before closing the connection.  If you know the server
                                   // you're accessing is quick to respond, you can reduce this value.


int last_a0 = 0;
int last_a1 = 0;
int last_a2 = 0;

const int tolerance = 3; 

int last_key = 0;
int last_volume = 0;
int analog_pin0 = A0;
int analog_pin1 = A1;

void setup(void)
{
  //Button initialization
pinMode(2, INPUT);
//pinMode(3, INPUT);
pinMode(4, INPUT);
//pinMode(5, INPUT);
pinMode(6, INPUT);

//? setting buttons high so press takes voltage down
digitalWrite(2, HIGH);
digitalWrite(3, HIGH);
digitalWrite(4, HIGH);
digitalWrite(5, HIGH);
digitalWrite(6, HIGH);

//LED initialization
pinMode(A4, OUTPUT);
pinMode(A5, OUTPUT);

//Potentiometer initialization - probably unnecessary if this is default
pinMode(A0, INPUT);
pinMode(A1, INPUT);
pinMode(A2, INPUT);
  
  Serial.begin(115200);

  Serial.print("Free RAM: "); Serial.println(getFreeRam(), DEC);
  
  /* Initialise the module */
  Serial.println(F("\nInitializing..."));
  if (!cc3000.begin())
  {
    Serial.println(F("Couldn't execute cc3000.begin()!"));
    while(1); // just loops continually because nothing else to do
  }
  
  Serial.print(F("\nAttempting to connect to ")); Serial.println(WLAN_SSID);
  if (!cc3000.connectToAP(WLAN_SSID, WLAN_PASS, WLAN_SECURITY)) {
    Serial.println(F("Failed to connect!"));
    while(1); // just loops continually because nothing else to do
  }
   
  Serial.println(F("Connected!"));
  
  /* Wait for DHCP to complete */
  Serial.println(F("Request DHCP"));
  while (!cc3000.checkDHCP())
  {
    delay(100); // ToDo: Insert a DHCP timeout!
  }  

  /* Display the IP address DNS, Gateway, etc. */  
  while (!displayConnectionDetails()) {
    delay(100); //1000
  }
  
  uint32_t ip;
  ip = cc3000.IP2U32(192,168,1,107); //******************************************************************* ip of server
  
  cc3000.printIPdotsRev(ip);
  
  /* Try connecting to the website.
     Note: HTTP/1.1 protocol is used to keep the server from closing the connection before all data is read but flask doesn't support
  */

  Adafruit_CC3000_Client client = cc3000.connectTCP(ip, 5000);
  if (client.connected()) {
    client.fastrprint(F("GET "));
    client.fastrprint(F("/b/1"));  //this will switch to WNYC
    client.fastrprint(F(" HTTP/1.1\r\n"));
    client.println();
  } else {
    Serial.println(F("Connection failed"));    
    return;
  }

  Serial.println(F("\r\nStart------------------------------------"));
  
  /* Read data until either the connection is closed, or the idle timeout is reached. */ 
  unsigned long lastRead = millis();
  while (client.connected() && (millis() - lastRead < IDLE_TIMEOUT_MS)) {
    while (client.available()) {
      char c = client.read();
      Serial.print(c);
      lastRead = millis();
    }
  }
  Serial.println(F("\r\nEnd------------------------------------"));
  
  /* You need to make sure to clean up after yourself or the CC3000 can freak out */
  /* the next time your try to connect ... */
  //Serial.println(F("\n\nDisconnecting"));
  //cc3000.disconnect(); //**************************************my be trouble************************************************
  
}

void loop(void)
{
  int k;
  int v;
  int fm;
  
  const char vol = 'v';
  const char but = 'b';
  const char mem = 'm';
  
  if(checkKeys2(k)) // C++ this is implicit referencing
  {
    // Only send info when value has changed
    //Serial.print("Key pressed ="); for debugging
    Serial.print('b');
    Serial.println(k);  //implicit dereferencing of variable passed by reference
    
  uint32_t ip;
  ip = cc3000.IP2U32(192,168,1,107); //*************************************************************needs to be the right ip
  
  Adafruit_CC3000_Client client = cc3000.connectTCP(ip, 5000);
  
  delay(100);
  
    if(k<11){ 
      if(transmit(client, but, k)){                 
      Serial.println(F("Transmit Success"));  
      }
   }
  
    if(k==11){
    fm = freeMemory();
    if(transmit(client, mem, fm)){                 
     Serial.println(fm);  
    }
   }
  
    if(k==12){
    Serial.println(F("\n\nDisconnecting"));
    cc3000.disconnect();
    }
  
 Serial.println(F("\r\nStart------------------------------------"));
  /* Read data until either the connection is closed, or the idle timeout is reached. */ 
  unsigned long lastRead = millis();
  while (client.connected() && (millis() - lastRead < IDLE_TIMEOUT_MS)) {
    while (client.available()) {
      char c = client.read();
      Serial.print(c);
      lastRead = millis();
    }
  }
  Serial.println(F("\r\nEnd------------------------------------"));   
    
  //needed to give time to transmission - may not need to explicitly close since they seem to be closed by Flask returning http 1.0 (won't keep alive)
  delay(50);
  client.close();
  
  }
  
  //int reading = analogRead(analog_pin0);
  
  if(checkVolume(v))
  {
    Serial.print('v');
    Serial.println(v);
    
    uint32_t ip;
    ip = cc3000.IP2U32(192,168,1,107);  //*************************************************************needs to be the right ip
  
  Adafruit_CC3000_Client client = cc3000.connectTCP(ip, 5000);
    
  if(transmit(client, vol, v)){                 
  Serial.println(F("Transmit Success"));  
  }
  
  Serial.println(F("\r\nStart------------------------------------"));
  /* Read data until either the connection is closed, or the idle timeout is reached. */ 
  unsigned long lastRead = millis();
  while (client.connected() && (millis() - lastRead < IDLE_TIMEOUT_MS)) {
    while (client.available()) {
      char c = client.read();
      Serial.print(c);
      lastRead = millis();
    }
  }
  Serial.println(F("\r\nEnd------------------------------------"));

  //needed to give time to transmission - may not need to explicitly close since they seem to be closed by Flask returning http 1.0 (won't keep alive)
  delay(50);
  client.close();
  }
    
delay(50); 
 
 

}

/**************************************************************************/
/*!
    @brief  Begins an SSID scan and prints out all the visible networks
*/
/**************************************************************************/

void listSSIDResults(void)
{
  uint8_t valid, rssi, sec, index;
  char ssidname[33]; 

  index = cc3000.startSSIDscan();

  Serial.print(F("Networks found: ")); Serial.println(index);
  Serial.println(F("================================================"));

  while (index) {
    index--;

    valid = cc3000.getNextSSID(&rssi, &sec, ssidname);
    
    Serial.print(F("SSID Name    : ")); Serial.print(ssidname);
    Serial.println();
    Serial.print(F("RSSI         : "));
    Serial.println(rssi);
    Serial.print(F("Security Mode: "));
    Serial.println(sec);
    Serial.println();
  }
  Serial.println(F("================================================"));

  cc3000.stopSSIDscan();
}

/**************************************************************************/
/*!
    @brief  Tries to read the IP address and other connection details
*/
/**************************************************************************/
bool displayConnectionDetails(void)
{
  uint32_t ipAddress, netmask, gateway, dhcpserv, dnsserv;
  
  if(!cc3000.getIPAddress(&ipAddress, &netmask, &gateway, &dhcpserv, &dnsserv))
  {
    Serial.println(F("Unable to retrieve the IP Address!\r\n"));
    return false;
  }
  else
  {
    Serial.print(F("\nIP Addr: ")); cc3000.printIPdotsRev(ipAddress);
    Serial.print(F("\nNetmask: ")); cc3000.printIPdotsRev(netmask);
    Serial.print(F("\nGateway: ")); cc3000.printIPdotsRev(gateway);
    Serial.print(F("\nDHCPsrv: ")); cc3000.printIPdotsRev(dhcpserv);
    Serial.print(F("\nDNSserv: ")); cc3000.printIPdotsRev(dnsserv);
    Serial.println();
    return true;
  }
}

// ****** Added by sz ****************************
bool transmit (Adafruit_CC3000_Client z, char t, int num) {
  Serial.println(F("\r\nIn transmit"));   
  if (z.connected()) {
    Serial.println(F("z is connected"));  
    z.fastrprint(F("GET ")); // size_t Adafruit_CC3000_Client::fastrprint(const char *str)
    z.fastrprint(F("/"));
    z.print(t);  //////////////////////////////////////
    z.fastrprint(F("/"));
    z.print(num);//////////////////////////////////////
    z.fastrprint(F(" HTTP/1.1\r\n"));
    z.println();
    return true;
  } 
    else {
    Serial.println(F("Connection failed"));    
    return false;
  }
}
//below to end all vkey

bool checkKeys2 (int &kk) //this may be done this way only in C++ - I think the C version is checkKeys2 (int *k) and then *k = voltageToKey(value)
{

//////////
//Button Input

kk = 0;

// Read button D2:
boolean d2Pressed = digitalRead(2);
if (d2Pressed == 0){
Serial.print("Button 2 = ");
Serial.println(d2Pressed); 

// Turn off left LED
digitalWrite(A4, LOW);

// Turn off right LED
digitalWrite(A5, LOW);

kk = 1;

}
/*D3 is used by CC3000
// Read button D3:
boolean d3Pressed = digitalRead(3);
if (d3Pressed == 0){
Serial.print("Button 3 = ");
Serial.println(d3Pressed); 

// Turn off left LED
digitalWrite(A4, LOW);

// Turn on right LED
digitalWrite(A5, HIGH);

}*/

// Read button D4:
boolean d4Pressed = digitalRead(4);
if (d4Pressed == 0){
Serial.print("Button 4 = ");
Serial.println(d4Pressed); 

// Turn on left LED
digitalWrite(A4, HIGH);

// Turn off right LED
digitalWrite(A5, LOW);

kk = 2;

}

/* D5 is used by CC3000
// Read button D5:
boolean d5Pressed = digitalRead(5);
if (d5Pressed == 0){
Serial.print("Button 5 = ");
Serial.println(d5Pressed); 

// Turn on left LED
digitalWrite(A4, HIGH);

// Turn on right LED
digitalWrite(A5, HIGH);

}*/

// Read button D6:
boolean d6Pressed = digitalRead(6);
if (d6Pressed == 0){
Serial.print("Button 6 = ");
Serial.println(d6Pressed); 

kk = 3;

}



//////////////////
  //int value;
  
  // Read the input voltage
  //value = analogRead(analog_pin1);

  // convert voltage to a key number
  //kk = voltageToKey(value);
  
  // Check to see if current key number is different than last seen 
  //if((kk != last_key) && (kk!=0))
  if(kk!=0) // I wanted to be able to hit the memory check repeatedly
  {
    // Update value in last_key
    //Serial.print("Voltage ="); for debugging
    //Serial.println(value); //for debugging
    last_key = kk; 
    return true;
  }
  
  return false;
}

int voltageToKey(int v) 
{
   // below are for 5v starting for 3.3V is adj=26 step=58 top=721, not sure what low (any value below that doesn't register)
   int adj = 19; //17
   int step = 41; //40
   int top = 510; //496;
   int low = 30;

   int j;
  
  if( (v < low) || (v > top) )
  {
    // Value somehow is in invalid range - equation doesn't apply
    j = 0;
  }
  else
  {
    // Apply the calculation based on the appropriate constants for the voltage
    j = 12 - ((v - adj)/step); 
  }
  
  return j;
}

bool checkVolume(int &b)
{
  
int a0 = analogRead(A0); 

/*if( abs(a0 - last_a0) > tolerance )
   {
     last_a0 = a0; 
     Serial.print("Volume A0 = ");
     Serial.println(a0);
   }
*/
/*
// Read A1 potentiometer:

int a1 = analogRead(A1);
if( abs(a1 - last_a1) > tolerance )
  {
    last_a1 = a1;
    Serial.print("Volume A1 ="); 
    Serial.println(a1); 
  }
  
int a2 = analogRead(A2);
if( abs(a2 - last_a2) > tolerance )
  {
    last_a2 = a2;
    Serial.print("Volume A2 ="); 
    Serial.println(a2); 
  }
 
*/ 
  
  //const int tolerance = 10; 
  //b = analogRead(analog_pin0);
  b = a0;
   if( abs(b - last_volume) > tolerance )
   {
     last_volume = b; 
     return true;
   }
   
   return false;
}  
