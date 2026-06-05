#include "Arduino.h"
#include "SoftwareSerial.h"
#include "DFRobotDFPlayerMini.h"

SoftwareSerial mySoftwareSerial(10, 11); // โค้ดแจ้งการเชื่อมต่อขา 11 กับ RX, และขา 10 กับ TX
DFRobotDFPlayerMini myDFPlayer;

void setup() {
  mySoftwareSerial.begin(9600); // ตัวเลขต้องตรงกับ baud_rate ใน VS code
  Serial.begin(9600); 

  Serial.println(F("Initializing DFPlayer ... (May take 3~5 seconds)"));
  
  if (!myDFPlayer.begin(mySoftwareSerial)) {  
    Serial.println(F("Unable to begin:"));
    Serial.println(F("1.Please recheck the connection!"));
    Serial.println(F("2.Please insert the SD card!"));
    while(true);
  }
  
  Serial.println(F("DFPlayer Mini online."));
  
  myDFPlayer.volume(15);  // โค้ดปรับความดังของลำโพง (min 0, max 30)
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    // ถ้า Python ส่งตัวอักษร '1' มา ให้เล่นไฟล์เสียงที่ชื่อ ‘0001.mp3’
    if (command == '1') {
      Serial.println("Command Received: Play Sound");
      myDFPlayer.play(1); // เล่นไฟล์ 0001.mp3
      delay(1000); 
    }
  }
}
