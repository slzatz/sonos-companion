/*************************************************** 
  This is an example for the Adafruit CC3000 Wifi Breakout & Shield

  Designed specifically to work with the Adafruit WiFi products:
  ----> https://www.adafruit.com/products/1469

  Adafruit invests time and resources providing this open source code, 
  please support Adafruit and open-source hardware by purchasing 
  products from Adafruit!

  Written by Limor Fried & Kevin Townsend for Adafruit Industries.  
  BSD license, all text above must be included in any redistribution
 ****************************************************/
 
 /*
This example does a test of the TCP client capability:
  * Initialization
  * Optional: SSID scan
  * AP connection
  * DHCP printout
  * DNS lookup
  * Optional: Ping
  * Connect to website and print out webpage contents
  * Disconnect
SmartConfig is still beta and kind of works but is not fully vetted!
It might not work on all networks!
*/
#include <Adafruit_CC3000.h>
#include <ccspi.h>
#include <SPI.h>
#include <string.h>
#include "utility/debug.h"

// These are the interrupt and control pins
#define ADAFRUIT_CC3000_IRQ   3  // MUST be an interrupt pin!
// These can be any two pins
#define ADAFRUIT_CC3000_VBAT  5
#define ADAFRUIT_CC3000_CS    10
// Use hardware SPI for the remaining pins
// On an UNO, SCK = 13, MISO = 12, and MOSI = 11
Adafruit_CC3000 cc3000 = Adafruit_CC3000(ADAFRUIT_CC3000_CS, ADAFRUIT_CC3000_IRQ, ADAFRUIT_CC3000_VBAT,
                                         SPI_CLOCK_DIVIDER); // you can change this clock speed

#define WLAN_SSID       "47SBD(2.4GHz)" //"47sbd2"//"47SBD(2.4GHz)"           // cannot be longer than 32 characters!
#define WLAN_PASS       "xxxxxxxxxx"
// Security can be WLAN_SEC_UNSEC, WLAN_SEC_WEP, WLAN_SEC_WPA or WLAN_SEC_WPA2
#define WLAN_SECURITY   WLAN_SEC_WPA2

#define IDLE_TIMEOUT_MS  3000      // Amount of time to wait (in milliseconds) with no data 
                                   // received before closing the connection.  If you know the server
                                   // you're accessing is quick to respond, you can reduce this value.

// What page to grab!
#define WEBSITE      "www.yahoo.com" //www.adafruit.com 192.168.1.149
#define WEBPAGE      "/testwifi/index.html"


/**************************************************************************/
/*!
    @brief  Sets up the HW and the CC3000 module (called automatically
            on startup)
*/
/**************************************************************************/


//uint32_t ip;


//vkey start
int analog_pin0 = A0;
int analog_pin1 = A1;
int last_key = 0;
int last_volume = 0;
//vkey end


void setup(void)
{
  //vkey start
  pinMode(analog_pin1, INPUT);
  pinMode(analog_pin0, INPUT);
  //vkey end
  
  Serial.begin(115200);
  Serial.println(F("Hello, CC3000!\n")); 

  Serial.print("Free RAM: "); Serial.println(getFreeRam(), DEC);
  
  /* Initialise the module */
  Serial.println(F("\nInitializing..."));
  if (!cc3000.begin())
  {
    Serial.println(F("Couldn't begin()! Check your wiring?"));
    while(1);
  }
  
  // Optional SSID scan
  // listSSIDResults();
  
  Serial.print(F("\nAttempting to connect to ")); Serial.println(WLAN_SSID);
  if (!cc3000.connectToAP(WLAN_SSID, WLAN_PASS, WLAN_SECURITY)) {
    Serial.println(F("Failed!"));
    while(1);
  }
   
  Serial.println(F("Connected!"));
  
  /* Wait for DHCP to complete */
  Serial.println(F("Request DHCP"));
  while (!cc3000.checkDHCP())
  {
    delay(100); // ToDo: Insert a DHCP timeout!
  }  

  /* Display the IP address DNS, Gateway, etc. */  
  while (! displayConnectionDetails()) {
    delay(1000);
  }
  
  uint32_t ip;
  ip = cc3000.IP2U32(192,168,1,149);
  
  /*ip = 0;
  // Try looking up the website's IP address
  Serial.print(WEBSITE); Serial.print(F(" -> "));
  while (ip == 0) {
    if (! cc3000.getHostByName(WEBSITE, &ip)) {
      Serial.println(F("Couldn't resolve!"));
    }
    delay(500);
  }*/

  cc3000.printIPdotsRev(ip);
  
  // Optional: Do a ping test on the website
  /*
  Serial.print(F("\n\rPinging ")); cc3000.printIPdotsRev(ip); Serial.print("...");  
  replies = cc3000.ping(ip, 5);
  Serial.print(replies); Serial.println(F(" replies"));
  */  

  /* Try connecting to the website.
     Note: HTTP/1.1 protocol is used to keep the server from closing the connection before all data is read.
  */
  //Adafruit_CC3000_Client www = cc3000.connectTCP(ip, 80);
  Adafruit_CC3000_Client www = cc3000.connectTCP(ip, 5000);
  if (www.connected()) {
    www.fastrprint(F("GET "));
    www.fastrprint(F("/b/10"));   //www.fastrprint(WEBPAGE);
    www.fastrprint(F(" HTTP/1.1\r\n"));
    //www.fastrprint(F("Host: ")); www.fastrprint(WEBSITE); www.fastrprint(F("\r\n"));
    //www.fastrprint(F("\r\n"));
    www.println();
  } else {
    Serial.println(F("Connection failed"));    
    return;
  }

  Serial.println(F("\r\nStart------------------------------------"));
  
  /* Read data until either the connection is closed, or the idle timeout is reached. */ 
  unsigned long lastRead = millis();
  while (www.connected() && (millis() - lastRead < IDLE_TIMEOUT_MS)) {
    while (www.available()) {
      char c = www.read();
      Serial.print(c);
      lastRead = millis();
    }
  }
  Serial.println(F("\r\nEnd------------------------------------"));
  
  /*delay(1000); //? necessary
  char v = 'v';
  char n = '5';
  
  Adafruit_CC3000_Client zzz = cc3000.connectTCP(ip, 5000);

  if(transmit(zzz, v, n)){
   Serial.println(F("Transmit Success"));  
  }
  delay(1000);
  
  www.close();
  zzz.close();*/

  
  /* You need to make sure to clean up after yourself or the CC3000 can freak out */
  /* the next time your try to connect ... */
  //Serial.println(F("\n\nDisconnecting"));
  //cc3000.disconnect(); //**************************************my be trouble************************************************
  
}

void loop(void)
{
 
  int k;
  int v;
  
  char vol = 'v';
  char but = 'b';
  
  if(checkKeys2(k)) // C++ this is implicit referencing
  {
    // Only send info when value has changed
    //Serial.print("Key pressed ="); for debugging
    Serial.print('b');
    Serial.println(k);  //implicit dereferencing of variable passed by reference
    
  // I think the issue is that cc3000 is being disconnected in the setup loop - what I need is button 12 to disconnect the cc3000 so it exits cleanly
  uint32_t ip;
  ip = cc3000.IP2U32(192,168,1,149);
  
  Adafruit_CC3000_Client xyz = cc3000.connectTCP(ip, 5000);
  
  delay(100);
  if (xyz.connected()) {
  Serial.println(F("xyz is connected")); 
  }
  else {
  Serial.println(F("xyz is *******not********** connected")); 
  }  
    
  //k
  if(transmit(xyz, but, k)){                 
  Serial.println(F("Transmit Success"));  
  }
  
  //********************************************************************** new **********************************
  Serial.println(F("\r\nStart------------------------------------"));
  /* Read data until either the connection is closed, or the idle timeout is reached. */ 
  unsigned long lastRead = millis();
  while (xyz.connected() && (millis() - lastRead < IDLE_TIMEOUT_MS)) {
    while (xyz.available()) {
      char c = xyz.read();
      Serial.print(c);
      lastRead = millis();
    }
  }
  Serial.println(F("\r\nEnd------------------------------------"));
  //********************************************************************** new **********************************
  
  //needed to give time to transmission - may not need to explicitly close since they seem to be closed by Flask returning http 1.0 (won't keep alive)
  delay(50);
  xyz.close();
  
  if(k==12){
    Serial.println(F("\n\nDisconnecting"));
    cc3000.disconnect();
  }
  }
  
  //int reading = analogRead(analog_pin0);
  
  if(checkVolume(v))
  {
    Serial.print('v');
    Serial.println(v);
    
    uint32_t ip;
    ip = cc3000.IP2U32(192,168,1,149);
  
  Adafruit_CC3000_Client xyz = cc3000.connectTCP(ip, 5000);
    
  if(transmit(xyz, vol, v)){                 
  Serial.println(F("Transmit Success"));  
  }
  
  //********************************************************************** new **********************************
  Serial.println(F("\r\nStart------------------------------------"));
  /* Read data until either the connection is closed, or the idle timeout is reached. */ 
  unsigned long lastRead = millis();
  while (xyz.connected() && (millis() - lastRead < IDLE_TIMEOUT_MS)) {
    while (xyz.available()) {
      char c = xyz.read();
      Serial.print(c);
      lastRead = millis();
    }
  }
  Serial.println(F("\r\nEnd------------------------------------"));
  //********************************************************************** new **********************************
  
  //needed to give time to transmission - may not need to explicitly close since they seem to be closed by Flask returning http 1.0 (won't keep alive)
  delay(50);
  xyz.close();
  }
    
delay(50); //50
 
 

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
    z.fastrprint(F("GET "));
    //z.fastrprint(F("/b/5"));
    z.fastrprint(F("/"));
    z.print(t);  // size_t Adafruit_CC3000_Client::fastrprint(const char *str)
    z.fastrprint(F("/"));
    z.print(num);
    z.fastrprint(F(" HTTP/1.1\r\n"));
    //z.fastrprint(F("Host: ")); z.fastrprint(WEBSITE); z.fastrprint(F("\r\n"));
    //z.fastrprint(F("\r\n"));
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
  int value;
  
  // Read the input voltage
  value = analogRead(analog_pin1);

  // convert voltage to a key number
  kk = voltageToKey(value);
  
  // Check to see if current key number is different than last seen 
  if((kk != last_key) && (kk!=0))
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
  const int tolerance = 10; 
  b = analogRead(analog_pin0);
   if( abs(b - last_volume) > tolerance )
   //if(b != last_volume)
   {
     last_volume = b; 
     return true;
   }
   
   return false;
}  
