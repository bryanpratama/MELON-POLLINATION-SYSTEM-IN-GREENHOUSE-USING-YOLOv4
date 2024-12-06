#include <Wire.h>
#include <RTClib.h>
#include <Servo.h>

RTC_DS1307 rtc;
Servo myservo;
int pos = 0;
int increment = 1;
int delayTime = 350;
unsigned long previousServoMillis = 0;
unsigned long previousSerialMillis = 0;
bool servoStopped = false;
bool relayOn = false;
unsigned long servoStopMillis = 0;
unsigned long servoStopDuration = 5000;
int lastPosition = 0;
bool canReceiveOne = true;
unsigned long lastReceiveOneTime = 0;
unsigned long receiveOneDelay = 10000;  // Delay 10 detik
const int relayPin = A1;
int servoPin = 3;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  rtc.begin();
  myservo.attach(servoPin, 544, 2500);
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, HIGH); 

  // Jika RTC belum diatur
  // rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
}

void loop() {
  DateTime now = rtc.now();
  unsigned long currentMillis = millis();

  // Menerima perintah angka 1 melalui Serial
  if (Serial.available()) {
    int command = Serial.parseInt();

    if (command == 1 && canReceiveOne) {
      servoStopped = true;
      relayOn = true;
      servoStopMillis = currentMillis;
      lastPosition = pos;
      canReceiveOne = false;
      lastReceiveOneTime = currentMillis;
    }
  }

  if (now.hour() >= 6 && now.hour() < 7) {

    if (!servoStopped && currentMillis - previousServoMillis >= delayTime) {
      myservo.write(pos);

      pos += increment;
      if (pos >= 180 || pos <= 0) {
        increment *= -1;
      }

      previousServoMillis = currentMillis;
    }

    digitalWrite(relayPin, relayOn ? LOW : HIGH);  
  } else {
    // Servo berhenti
    myservo.write(lastPosition);
    digitalWrite(relayPin, HIGH);  
    pos = 0;
  }

  // Cek apakah servo dalam kondisi berhenti
  if (servoStopped && currentMillis - servoStopMillis >= servoStopDuration) {
    servoStopped = false;
    relayOn = false;
  }

  // Cek apakah sudah dapat menerima angka 1 kembali setelah delay 10 detik
  if (!canReceiveOne && currentMillis - lastReceiveOneTime >= receiveOneDelay) {
    canReceiveOne = true;
  }

  // Tampilkan waktu pada Serial Monitor setiap detik
  if (currentMillis - previousSerialMillis >= 1000) {
    Serial.print(now.year(), DEC);
    Serial.print('/');
    Serial.print(now.month(), DEC);
    Serial.print('/');
    Serial.print(now.day(), DEC);
    Serial.print(' ');
    Serial.print(now.hour(), DEC);
    Serial.print(':');
    Serial.print(now.minute(), DEC);
    Serial.print(':');
    Serial.print(now.second(), DEC);
    Serial.println();

    previousSerialMillis = currentMillis;
  }
}
