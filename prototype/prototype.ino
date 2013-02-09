#include <Average.h>
// record the last 10 readings of the 16 analog inputs
int analogvalues[16][10] = {0};
// what number was the last read analoginput pin
int lastread = -1;
// The current index
int index = 0;

void checkAnalog(){
  lastread++;
  if (lastread == 16){
   lastread = 0;
   index++; 
  }
  if (index == 10){
   index = 0;
  }
  analogvalues[lastread][index] = analogRead(lastread);
  // increment lastread +1
  // if lastread now equals 16, reset to 0 and increament index
  // if index now equals 10, reset to 0
  // read analog pin and place in analogvalues[lastread][index]
}

void setup() {
    Serial.begin(115200);
    Serial.setTimeout(20);

    int cmd = readData();
    for (int i = 0; i < cmd; i++) {
        pinMode(readData(), OUTPUT);
    }
}

void loop() {
    switch (readData()) {
        case 0 :
            //set digital low
            digitalWrite(readData(), LOW); break;
        case 1 :
            //set digital high
            digitalWrite(readData(), HIGH); break;
        case 2 :
            //get digital value
            Serial.println(digitalRead(readData())); break;
        case 3 :
            // set analog value
            analogWrite(readData(), readData()); break;
        case 4 :
            //read analog value
            Serial.println(maximum(analogvalues[readData()],10));
    }
}

char readData() {
    Serial.println("w");
    while(1) {
        if(Serial.available() > 0) {
            return Serial.parseInt();
        }
        checkAnalog();
    }
}
