
int potPin = 0;

void setup()
{
  Serial.begin(9600);
}
  
void loop()
{
  int reading = analogRead(potPin);
  Serial.println(reading);
  delay(500);
}
