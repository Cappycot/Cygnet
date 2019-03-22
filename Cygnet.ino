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

// Voltage Constants
const float ZERO_MARGIN = 0.1;
const float FIVE_MARGIN = 5.0 - ZERO_MARGIN;
const float SPKR_MARGIN = 4.0;

// Time Constants
const int PRESS_TIME = 200;
const int TICK_DELAY = 1;

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

// Runtime Variables
bool buttonPress = false; // If the stealth button is pressed.
bool powerOn = false; // Indicated by motherboard sending power through pLED.
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

// Play the tune.
void play() {
  noTone(MUSIC_PIN);
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

// Run once.
void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT);
  pinMode(BTN_PWR, OUTPUT);
  digitalWrite(BTN_PWR, HIGH); // Substitute for 5V.
  pinMode(MUSIC_PIN, OUTPUT);
  pinMode(PLED_OUT, OUTPUT);
  pinMode(PWR_PIN, OUTPUT);
  digitalWrite(PWR_PIN, LOW);
  pinMode(LED_BUILTIN, OUTPUT);
  play();
  while (digitalRead(TI_REC) == LOW); // Wait for voice recognizer chip to start up.
}

// Run continuously.
void loop() {
  // Turn on and off stealth mode.
  if (digitalRead(BTN_PIN) == LOW) {
    if (!buttonPress)
      stealth = !stealth;
    buttonPress = true;
  } else
    buttonPress = false;

  // Map case power switch to motherboard power switch.
  if (digitalRead(SW_PIN))
    digitalWrite(PWR_PIN, LOW);
  else
    digitalWrite(PWR_PIN, HIGH);

  // Performs more checks if the power is on.
  if (powerOn) {
    // Check for signal intended for speaker.
    if (analogRead(SPEAKER_IN) * (5.0 / 1023.0) < ZERO_MARGIN && analogRead(SPEAKER_5V) * (5.0 / 1023.0) > SPKR_MARGIN)
        play();
    // Check for voice command recognition.
    if (digitalRead(TI_REC) == LOW && !serialMode) {
      noTone(MUSIC_PIN);
      tone(MUSIC_PIN, freq[1][9], 100);
      delay(100);
      tone(MUSIC_PIN, freq[2][0], 100);
      delay(100);
      tone(MUSIC_PIN, freq[2][4], 100);
      delay(100);
      noTone(MUSIC_PIN);
    }
    // Check for serial input.
    while (Serial.available()) {
      serial = Serial.read(); // Just keep reading single bytes to get the latest.
      if (serial == -1) // In case there is no byte somehow.
        serial = 0;
      if (serial & 1 == 0) {
        serialMode = serial & 2 == 2;
        builtinLED = serial & 4 == 4;
        // Note to Self: The >> operator in Arduino is an unsigned right shift.
        buzzerNote = serial >> 3;
        if (!serialMode || buzzerNote == 0)
          noTone(MUSIC_PIN);
        else
          tone(MUSIC_PIN, freq[buzzerNote / 12][buzzerNote % 12]);
      } else {
        pLEDValue = serial & 254;
        if (pLEDValue >= 254)
          pLEDValue = 255;
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
    if (!powerOn)
      digitalWrite(PLED_OUT, LOW);

  // Perform less checks if the power is off.
  } else {
    digitalWrite(LED_BUILTIN, !stealth); // Stealth Indicator
    // Check for voice command recognition.
    if (digitalRead(TI_REC) == LOW) {
      digitalWrite(PWR_PIN, HIGH);
      delay(PRESS_TIME);
      digitalWrite(PWR_PIN, LOW);
    }
    // Check for power on.
    powerOn = analogRead(PLED_IN) * (5.0 / 1023.0) > FIVE_MARGIN;
  }

  delay(TICK_DELAY);
}
