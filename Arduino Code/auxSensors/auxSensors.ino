#include <ESP32Servo.h>

const int SERVO_PIN = 19;
const int PIR_PIN = 13;
const int BUZZER_PIN = 14;

// -- PAN Configuration --
const unsigned long panDurationMs = 2100UL;
const int startAngle = 30;
const int endAngle = 180;
const unsigned long minRetriggerDelay = 1000UL; // min ms for next trigger

// -- PIR Configuration --
const unsigned long pirDebounceMs = 500UL;  // debounce time for PIR signal

Servo myServo;
bool panActive = false;
unsigned long panStartMillis = 0;
unsigned long lastPIRAcceptedAt = 0;

void setup() {
  Serial.begin(115200);

  pinMode(PIR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.println("Starting the system......");

  // Attach servo and optionally set pulse range for SG90 (500-2500us typical)
  myServo.setPeriodHertz(50); // 50 Hz for standard servos
  myServo.attach(SERVO_PIN); // minUs, maxUs - tune if needed
  myServo.write(startAngle); // home position
}

unsigned long lastPirReadChangeAt = 0;
int lastPirRaw = LOW;

// Modular PIR logic: debounce only (no hold); returns true once per accepted trigger
bool isPIRTriggered() {
  int raw = digitalRead(PIR_PIN);

  // If reading changed, record the time and wait for it to stabilize
  if (raw != lastPirRaw) {
    lastPirRaw = raw;
    lastPirReadChangeAt = millis();
    return false; // wait until stable
  }

  // If not stable long enough, ignore
  if (millis() - lastPirReadChangeAt < pirDebounceMs) {
    return false;
  }

  // Stable reading: accept HIGH (motion) if retrigger delay elapsed
  if (raw == HIGH) {
    if (millis() - lastPIRAcceptedAt >= minRetriggerDelay) {
      lastPIRAcceptedAt = millis();
      return true;
    } else {
      return false; // too soon to retrigger
    }
  }

  // LOW (no motion)
  return false;
}

// Starts the pan cycle (set panActive and record time)
void startPanSequence() {
  if (!panActive) {
    panActive = true;
    panStartMillis = millis();
    Serial.println("Pan started");
  }
}

// Call in loop to update servo position while panActive (non-blocking)
void updatePan() {
  if (!panActive) return;

  unsigned long elapsed = millis() - panStartMillis;

  // Full sequence is: forward (0->180) in panDurationMs then backward (180->0) in panDurationMs
  unsigned long fullCycle = panDurationMs * 2UL;
  if (elapsed >= fullCycle) {
    // Completed cycle
    myServo.write(startAngle);
    panActive = false;
    Serial.println("Pan completed");
    return;
  }

  // Calculate current angle
  if (elapsed < panDurationMs) {
    // Forward phase: 0 -> 180
    float progress = (float)elapsed / (float)panDurationMs; // 0.0 .. <1.0
    int angle = startAngle + (int)((endAngle - startAngle) * progress);
    myServo.write(angle);
  } else {
    // Backward phase: 180 -> 0
    float progress = (float)(elapsed - panDurationMs) / (float)panDurationMs; // 0.0 .. <1.0
    int angle = endAngle - (int)((endAngle - startAngle) * progress);
    myServo.write(angle);
  }
}

void loop() {

  // Check PIR trigger (modular)
  if (isPIRTriggered()) {
    Serial.println("PIR accepted -> starting pan");
    startPanSequence();
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
  }

  updatePan();

  delay(20); // short delay to keep CPU sane (and keep servo updated smoothly)
}
