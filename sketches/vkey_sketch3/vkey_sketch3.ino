int analog_pin0 = A0;
int analog_pin1 = A1;
int last_key = 0;
int last_volume = 0;

void setup()
{
  pinMode(analog_pin1, INPUT);
  pinMode(analog_pin0, INPUT);
  Serial.begin(9600);
  //Serial.println("Welcome to VKey example");
}

void loop() 
{
  int k;
  int b;
  
  if(checkKeys2(k)) // C++ this is implicit referencing
  {
    // Only send info when value has changed
    //Serial.print("Key pressed ="); for debugging
    Serial.print('b');
    Serial.println(k);  //implicit dereferencing of variable passed by reference
  }
  
  //int reading = analogRead(analog_pin0);
  
  if(checkVolume(b))
  {
    Serial.print('v');
    Serial.println(b);
    // 50 milliseconds seems to be a reasonable poll interval.
  }
    delay(50);
}

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