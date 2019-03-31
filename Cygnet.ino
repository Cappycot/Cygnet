/*
 * Am I supposed to give this shit a license?
 * 
 * Cappycot
 */
// Analog/Digital Sensors
const int BTN_PIN = A0; // digitalRead() works with analog in pins.
const int PLED_IN = A1; // Check if motherboard is driving current through PLED.
const int SPEAKER_5V = A4; // Speaker 5V
const int SPEAKER_IN = A5; // Speaker "GND"
const int SW_PIN = A2; // Case Power Switch
const int TI_REC = A3; // Drives low upon voice command recognition.


// Digital Outputs
const int BTN_PWR = 12;
const int MUSIC_PIN = 9;
const int PLED_OUT = 10;
const int PWR_PIN = 8;


// Voltage Constants
const float ZERO_MARGIN = 0.1;
const float FIVE_MARGIN = 5.0 - ZERO_MARGIN;
const float SPKR_MARGIN = 4.0;


// Buzzer Tones
const float freq[4][12] = {{130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185, 196, 207.65, 220, 233.08, 246.94},
{261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392, 415.30, 440, 466.16, 493.88}, // A440 is 21
{523.25, 554.37, 587.33, 622.25, 659.26, 698.46, 739.99, 783.99, 830.61, 880, 932.33, 987.77},
{1046.50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}};
const int musicNoteTime = 166;
const int musicNotes[] = {25, -1,
20, -1,
13, -1,
20, -1,
13, -1,
17, -1,
18};
const int numMusicNotes = sizeof(musicNotes) / sizeof(int);
const int alarmNoteTime = 114;
const int alarmNotes[] = {29, 29, 29, 29,
26, 26, 28, 28,
28, 28, 33, 33,
33, 33, 33, 33,

26, 26, 26, 26,
22, 22, 24, 24,
24, 24, 17, 17,
17, 17, 19, 21,

22, 22, 21, 21,
22, 22, 24, 24,
24, 24, 28, 28,
28, -1, 28, 28,

28, -1, 29, -1,
29, 29, 29, 29,
29, 29, 29, 29,
29, -1, 29, 31,

32, 32, 32, 32,
29, 29, 31, 31,
31, 31, 36, 36,
36, 36, 36, 36,

29, 29, 27, 27,
25, 25, 27, 27,
27, 27, 20, 20,
20, 20, 20, 20,

25, 25, 25, 25,
25, 25, 25, -1,
25, 25, 25, 27,
27, 27, 29, -1,

29, 29, 29, 29,
29, 29, 28, 26,
28, 28, 28, 28,
28, 28, 28, 28};
const int numAlarmNotes = sizeof(alarmNotes) / sizeof(int);


// Runtime Variables
bool buttonPress = false; // If the stealth button is pressed.
bool powerOn = false; // Indicated by motherboard sending power through pLED.
bool powerPress = false; // If the power button is pressed.
bool stealth = false; // Disables pin 13 and power LEDs.
int serial = 0;
// Serial Bits:
// Bit 0: 0 to modify serial parameters, 1 to modify power LED value
// Bit 1: LED override (serial) mode off (0) or on (1)
// Bit 2: Arduino pin 13 LED off (0) or on (1)
// Bits 3-7: Buzzer frequency (all 0 is no frequency)
bool serialMode = false;
bool builtinLED = true;
int buzzerNote = 0;
int pLEDValue = 255;


// Emulate power button being pressed.
const int PRESS_TIME = 200;
void pressPower() {
  if (powerOn) // TODO: Remove line once semantics check out.
    return;
  digitalWrite(PWR_PIN, HIGH);
  delay(PRESS_TIME);
  digitalWrite(PWR_PIN, LOW);
}


// Alarm Variables
unsigned long alarmHalfDay = 0;
unsigned long alarmHour = 0;
unsigned long alarmMinute = 0;
unsigned long alarmSecond = 0;
unsigned long currentMillis = 0;
unsigned long initialMillis = 0;
unsigned long targetMillis = 0;
// Check if enough time has elapsed. Window can be up to approximately 49 days.
bool timeTarget() {
  currentMillis = millis();
  return (initialMillis < targetMillis || currentMillis < initialMillis) && currentMillis > targetMillis;
}
bool alarmOn = false;
void alarm() {
  if (!timeTarget())
    return;
  int currentNote = 0;
  int note;
  pressPower();
  while (true) {
    if (timeTarget()) {
      note = alarmNotes[currentNote];
      if (note != -1)
        tone(MUSIC_PIN, freq[note / 12][note % 12]);
      else
        noTone(MUSIC_PIN);
      initialMillis = millis();
      targetMillis = initialMillis + alarmNoteTime;
      currentNote++;
      currentNote %= numAlarmNotes;
      /*if (currentNote == numAlarmNotes) {
        currentNote = 0;
      }//*/
    }
    digitalWrite(PLED_OUT, millis() % 1000 < 500); // Alarm Indicator
    if (digitalRead(BTN_PIN) == LOW) {
      buttonPress = true;
      break;
    } else if (digitalRead(SW_PIN) == LOW) {
      powerPress = true;
      break;
    } else if (digitalRead(TI_REC) == LOW)
      break;
  }
  alarmOn = false;
  noTone(MUSIC_PIN);
}


// Play the tune.
void music() {
  noTone(MUSIC_PIN);
  int note;
  for (int i = 0; i < numMusicNotes; i++) {
    note = musicNotes[i];
    if (note != -1)
      tone(MUSIC_PIN, freq[note / 12][note % 12], musicNoteTime);
    else
      noTone(MUSIC_PIN);
    delay(musicNoteTime);
  }
  noTone(MUSIC_PIN);
}


// Short A-C-E Tone
void acknowledge() {
  noTone(MUSIC_PIN);
  tone(MUSIC_PIN, freq[1][9], 100);
  delay(100);
  tone(MUSIC_PIN, freq[2][0], 100);
  delay(100);
  tone(MUSIC_PIN, freq[2][4], 100);
  delay(100);
  noTone(MUSIC_PIN);
}


// Run once.
void setup() {
  Serial.begin(115200); // 
  pinMode(BTN_PIN, INPUT);
  pinMode(BTN_PWR, OUTPUT);
  digitalWrite(BTN_PWR, HIGH); // Substitute for 5V.
  pinMode(MUSIC_PIN, OUTPUT);
  pinMode(PLED_OUT, OUTPUT);
  pinMode(PWR_PIN, OUTPUT);
  digitalWrite(PWR_PIN, LOW);
  pinMode(LED_BUILTIN, OUTPUT);
  music();
  while (digitalRead(TI_REC) == LOW); // Wait for voice recognizer chip to start up.
}


// Run continuously.
void loop() {
  // Turn on and off stealth mode.
  if (digitalRead(BTN_PIN) == LOW) {
    if (!buttonPress) {
      noTone(MUSIC_PIN);
      if (alarmOn || serialMode) {
        if (alarmOn) {
          acknowledge();
          alarmOn = false;
        }
        serialMode = false;
      } else
        stealth = !stealth;
    }
    buttonPress = true;
  } else
    buttonPress = false;

  // Map case power switch to motherboard power switch.
  if (digitalRead(SW_PIN) == LOW) {
    if (!powerPress) {
      if (!powerOn)
        alarmOn = false;
      digitalWrite(PWR_PIN, HIGH);
    }
    powerPress = true;
  } else {
    digitalWrite(PWR_PIN, LOW);
    powerPress = false;
  }

  // Performs more checks if the power is on.
  if (powerOn) {
    // Check for signal intended for speaker.
    if (analogRead(SPEAKER_IN) * (5.0 / 1023.0) < ZERO_MARGIN && analogRead(SPEAKER_5V) * (5.0 / 1023.0) > SPKR_MARGIN)
      music();

    // Check for voice command recognition.
    if (digitalRead(TI_REC) == LOW && !serialMode)
      acknowledge();

    // Check for serial input.
    while (Serial.available()) { // Just keep reading single bytes to get the latest.
      serial = Serial.read();
      if (serial == -1) // In case there is no byte somehow.
        serial = 0;
      if ((serial & 31) == 0) { // XXX00000: Serial Indicators
        serialMode = (serial & 32) == 32;
        builtinLED = (serial & 64) == 64;
        alarmOn = (serial & 128) == 128;
        if (alarmOn) {
          initialMillis = millis();
          targetMillis = initialMillis + alarmSecond * 1000UL;
          targetMillis += alarmMinute * 60000UL;
          targetMillis += alarmHour * 3600000UL;
          targetMillis += alarmHalfDay * 43200000UL;
          alarmSecond = 0;
          alarmMinute = 0;
          alarmHour = 0;
          alarmHalfDay = 0;
          acknowledge();
        }
      } else if ((serial & 3) == 3) { // XXXXXX11: PLED Power
        pLEDValue = (serial & 252) + 3;
        if (pLEDValue == 3)
          pLEDValue = 0;
      } else if ((serial & 3) == 1) // XXXXXX01: Alarm Second
        alarmSecond = serial >> 2;
      else if ((serial & 3) == 2) // XXXXXX10: Alarm Minute
        alarmMinute = serial >> 2;
      else {
        if ((serial & 7) == 4) { // XXXXX100: Buzzer Note
          buzzerNote = serial >> 3;
          if (!serialMode || buzzerNote == 0)
            noTone(MUSIC_PIN);
          else
            tone(MUSIC_PIN, freq[buzzerNote / 12][buzzerNote % 12]);
        } else if ((serial & 15) == 8) // XXXX1000: Alarm Hour
          alarmHour = serial >> 4;
        else // XXX10000: Alarm Half-day
          alarmHalfDay = serial >> 5;
      }
    }
    
    // Check for LED override mode.
    if (serialMode) {
      digitalWrite(LED_BUILTIN, builtinLED);
      analogWrite(PLED_OUT, pLEDValue);
    } else {
      digitalWrite(LED_BUILTIN, !stealth); // Stealth Indicator
      digitalWrite(PLED_OUT, !stealth);
    }

    // Check for power off.
    powerOn = analogRead(PLED_IN) * (5.0 / 1023.0) > FIVE_MARGIN;
    if (!powerOn) {
      noTone(MUSIC_PIN);
      serialMode = false;
    }

  // Perform less checks if the power is off.
  } else {
    digitalWrite(LED_BUILTIN, !stealth); // Stealth Indicator
    digitalWrite(PLED_OUT, alarmOn && millis() % 2000 < 1000); // Alarm Indicator
    // Check for voice command recognition.
    if (digitalRead(TI_REC) == LOW) {
      alarmOn = false;
      pressPower();
    } else if (alarmOn) {
      if (timeTarget())
        alarm();
    }
    // Check for power on.
    powerOn = analogRead(PLED_IN) * (5.0 / 1023.0) > FIVE_MARGIN;
  }
}
