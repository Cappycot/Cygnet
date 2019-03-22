// Cappycot

// Analog/Digital Sensors
const int BTN_PIN = A0; // digitalRead() works with analog in pins.
const int PLED_IN = A1;
const int SPEAKER_5V = A4; // Speaker 5V
const int SPEAKER_IN = A5; // Speaker "GND"
const int SW_PIN = A2;
const int TI_REC = A3; // Drives low upon voice command recognition.

// Digital Outputs
const int BTN_PWR = 12;
const int MUSIC_PIN = 9;
const int PLED_OUT = 10;
const int PWR_PIN = 8;

const float ZERO_MARGIN = 0.1;
const float FIVE_MARGIN = 5.0 - ZERO_MARGIN;
const float SPKR_MARGIN = 4.0;

const float freq[3][12] = {{130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185, 196, 207.65, 220, 233.08, 246.94},
{261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392, 415.30, 440, 466.16, 493.88},
{523.25, 554.37, 587.33, 622.25, 659.26, 698.46, 739.99, 783.99, 830.61, 880, 932.33, 987.77}};
const int noteTime = 166;
const int musicNotes[] = {25, -1,
20, -1,
13, -1,
20, -1,
13, -1,
17, -1,
18};
const int numNotes = sizeof(musicNotes) / sizeof(int);

bool powerOn = false;
bool stealth = false;

byte serial = 0; // LED overrides
// Bit 0: LED override mode off (0) or on (1)
// Bit 1: Power LED off (0) or on (1)
// Bit 2: Arduino AREF LED off (0) or on (1)
// Bits 3-7: Buzzer frequency (all 0 is no frequency)

void setup() {
  // put your setup code here, to run once:
  // Serial.begin(115200);
  pinMode(BTN_PIN, INPUT);
  pinMode(BTN_PWR, OUTPUT);
  digitalWrite(BTN_PWR, HIGH);
  pinMode(MUSIC_PIN, OUTPUT);
  pinMode(PLED_OUT, OUTPUT);
  pinMode(PWR_PIN, OUTPUT);
  digitalWrite(PWR_PIN, LOW);
  pinMode(LED_BUILTIN, OUTPUT);
}

float lastVoltage = -1.0;
int thething = 0;
float pLEDDiff;
int sensorValue;
float voltage;
float voltage2;
String thestring;

void loop() {
  // put your main code here, to run repeatedly:
  delay(10);
  /*if (Serial.available()) {
    thestring = Serial.readString();
    if (thestring.compareTo("on") == 0) {
      Serial.println("Turning on.");
      digitalWrite(PWR_PIN, HIGH);
      delay(1000);
      digitalWrite(PWR_PIN, LOW);
      Serial.println("Done.");
    } else if (thestring.compareTo("off") == 0) {
      Serial.println("Turning off.");
      digitalWrite(PWR_PIN, HIGH);
      delay(1000);
      digitalWrite(PWR_PIN, LOW);
      Serial.println("Done.");
    }
  }//*/

  //if (digitalRead(BTN_PIN) == LOW)
    //Serial.println("Button pressed.");

  powerOn = analogRead(PLED_IN) * (5.0 / 1023.0) > FIVE_MARGIN;
  /* Serial.println("V (A0)");
  sensorValue = analogRead(PLED_NEG);
  voltage2 = sensorValue * (5.0 / 1023.0);
  // Serial.print(voltage2);
  // Serial.println("V (A1)");
  pLEDDiff = abs(voltage - voltage2);
  // Serial.print("A0 - A1 = ");
  // Serial.println(pLEDDiff);
  if (pLEDDiff < 1.0)
    powerOn = false;
  else if (pLEDDiff > 4.0)
    powerOn = true;*/

  if (analogRead(SPEAKER_IN) * (5.0 / 1023.0) < ZERO_MARGIN) {
    if (analogRead(SPEAKER_5V) * (5.0 / 1023.0) > SPKR_MARGIN) {
      for (int i = 0; i < numNotes; i++) {
        int note = musicNotes[i];
        if (note != -1)
          tone(MUSIC_PIN, freq[note / 12][note % 12], noteTime);
        else
          noTone(MUSIC_PIN);
        delay(noteTime);
      }
      noTone(MUSIC_PIN);
    }
  }//*/

  // Map case power switch to motherboard power switch.
  if (digitalRead(SW_PIN))
    digitalWrite(PWR_PIN, LOW);
  else
    digitalWrite(PWR_PIN, HIGH);

  if (digitalRead(TI_REC) == LOW) {
    if (!powerOn) {
      //Serial.println("Powering on...");
      digitalWrite(PWR_PIN, HIGH);
      delay(500);
      digitalWrite(PWR_PIN, LOW);
    } else {
      //Serial.println("No.");
      tone(MUSIC_PIN, freq[1][9], 100);
      delay(100);
      tone(MUSIC_PIN, freq[2][0], 100);
      delay(100);
      tone(MUSIC_PIN, freq[2][4], 100);
      delay(100);
      noTone(MUSIC_PIN);
    }
  }

  /*sensorValue = analogRead(SPEAKER_IN);
  voltage = sensorValue * (5.0 / 1023.0);
  Serial.print(voltage);
  if (voltage < 1) {
    Serial.print(" < 1");
    sensorValue = analogRead(SPEAKER_5V);
    voltage = sensorValue * (5.0 / 1023.0);
    if (voltage > 4) {
      Serial.print(" music triggered");
      delay(5000);
    }
  } else if (voltage < 2)
    Serial.print(" < 2");
  else if (voltage < 3)
    Serial.print(" < 3");
  else if (voltage < 4)
    Serial.print(" < 4");
  else if (voltage < 5)
    Serial.print(" < 5");
  else
    Serial.print(" = 5+");
  // Serial.println(digitalRead(7));
  sensorValue = analogRead(SPEAKER_5V);
  voltage = sensorValue * (5.0 / 1023.0);
  Serial.print(", ");
  Serial.print(voltage);
  if (voltage < 1)
    Serial.println(" < 1");
  else if (voltage < 2)
    Serial.println(" < 2");
  else if (voltage < 3)
    Serial.println(" < 3");
  else if (voltage < 4)
    Serial.println(" < 4");
  else if (voltage < 5)
    Serial.println(" < 5");
  else
    Serial.println(" = 5+");//*/
    
  // Check for LED override mode.
  if (serial & 1 != 0) {
    // Note to Self: The >> operator in Arduino is an unsigned right shift.
    digitalWrite(PLED_OUT, serial >> 1 & 1); // Easy to determine 0 or 1.
    digitalWrite(LED_BUILTIN, serial >> 2 & 1);
  } else {
    digitalWrite(PLED_OUT, powerOn && !stealth);
    digitalWrite(LED_BUILTIN, powerOn && !stealth);
  }
}
