#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

const char* WIFI_SSID = "Janardhana Rao";
const char* WIFI_PASS = "Madhavi#888";

WebServer server(80);

const int SERVO_PIN = 19;
const int PIR_PIN = 13;
const int BUZZER_PIN = 14;
const int IR_PIN = 18; // IR Sensor Pin

// --- New Global Variable ---
// Assume IR sensor is active LOW (LOW when object detected)
volatile bool irObjectDetected = false; 

// -- PAN Configuration --
const unsigned long panDurationMs = 2100UL;
const int startAngle = 30;
const int endAngle = 180;
const unsigned long minRetriggerDelay = 1000UL; // min ms for next trigger

// -- PIR Configuration --
const unsigned long pirDebounceMs = 500UL; // debounce time for PIR signal

Servo myServo;
bool panActive = false;
unsigned long panStartMillis = 0;
unsigned long lastPIRAcceptedAt = 0;

unsigned long lastPirReadChangeAt = 0;
int lastPirRaw = LOW;

void startPanSequence() {
 if (!panActive) {
  panActive = true;
  panStartMillis = millis();
  Serial.println("Pan started");
 }
}

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
  // Forward phase: startAngle -> endAngle
  float progress = (float)elapsed / (float)panDurationMs; // 0.0 .. <1.0
  int angle = startAngle + (int)((endAngle - startAngle) * progress);
  myServo.write(angle);
 } else {
  // Backward phase: endAngle -> startAngle
  float progress = (float)(elapsed - panDurationMs) / (float)panDurationMs; // 0.0 .. <1.0
  int angle = endAngle - (int)((endAngle - startAngle) * progress);
  myServo.write(angle);
 }
}

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

// -------- HTTP handlers --------
void handleRoot() {
 String html = "<!doctype html><html><head><meta charset='utf-8'><title>ESP32 Pan Server</title>";
  // Add auto-refresh to see the IR status change
  html += "<meta http-equiv='refresh' content='1'></head><body>"; 
  
 html += "<h2>ESP32 Pan Control</h2>";
 html += "<p><a href=\"/status\">/status</a> (json)</p>";
 html += "<p><a href=\"/trigger\">/trigger</a> (start pan)</p>";
 html += "<p><a href=\"/stop\">/stop</a> (stop pan)</p>";
  
  // --- CONDITIONAL IR PRINTING (MODIFIED) ---
  html += "<h3>IR Sensor Status:</h3>";
  if (irObjectDetected) {
    // Print this when the IR sensor is triggered (LOW)
    html += "<p style='color: red; font-size: 1.2em;'>⚠️ **Activity Detected**</p>";
  } else {
    // Print this when no object is detected (HIGH)
    html += "<p style='color: green;'>No Activity Detected</p>";
  }
  // --- END IR PRINTING ---

 html += "</body></html>";
 
 server.send(200, "text/html", html);
}

void sendJsonStatus() {
 // build small JSON with key fields
 int pirState = digitalRead(PIR_PIN);
 int irState = digitalRead(IR_PIN); // Read current IR state
 int servoAngle = myServo.read(); // should return last written angle
 unsigned long now = millis();


 String payload = "{";
 payload += "\"panActive\":";
 payload += (panActive ? "true" : "false");
 payload += ",";

 payload += "\"pirState\":";
 payload += (pirState == HIGH ? "\"HIGH\"" : "\"LOW\"");
 payload += ",";
  
  // Include IR state in JSON response
 payload += "\"irState\":";
 payload += (irState == LOW ? "\"DETECTED\"" : "\"CLEAR\"");
 payload += ",";

 payload += "\"lastPIRAcceptedAt\":";
 payload += String(lastPIRAcceptedAt);
 payload += ",";

 payload += "\"now\":";
 payload += String(now);
 payload += ",";

 payload += "\"servoAngle\":";
 payload += String(servoAngle);
 payload += "}";

 server.send(200, "application/json", payload);
}

void handleStatus() {
 sendJsonStatus();
  // Note: The /status handler is primarily for JSON data. 
  // It should be changed to use sendJsonStatus() only. The original code's 
  // mix of JSON/HTML in this function was confusing, so I've simplified it
  // back to its JSON purpose and ensured the IR logic is in handleRoot.
}

void handleTrigger() {
 // trigger pan sequence via HTTP
 startPanSequence();
 // Optionally buzz briefly to indicate remote trigger
 digitalWrite(BUZZER_PIN, HIGH);
 delay(100);
 digitalWrite(BUZZER_PIN, LOW);

 server.send(200, "application/json", "{\"result\":\"pan_triggered\"}");
}

void handleStop() {
 // stop pan immediately
 panActive = false;
 myServo.write(startAngle);
 server.send(200, "application/json", "{\"result\":\"pan_stopped\"}");
}

void handleNotFound() {
 server.send(404, "text/plain", "Not found");
}

// -------- Setup & Loop --------
void setup() {
 Serial.begin(115200);

 pinMode(PIR_PIN, INPUT);
 pinMode(BUZZER_PIN, OUTPUT);
 pinMode(IR_PIN, INPUT); // IR Pin is configured as an input
 digitalWrite(BUZZER_PIN, LOW);

 Serial.println("Starting the system......");

 // Attach servo and optionally set pulse range for SG90 (500-2500us typical)
 myServo.setPeriodHertz(50); // 50 Hz for standard servos
 myServo.attach(SERVO_PIN); // minUs, maxUs - tune if needed
 myServo.write(startAngle); // home position

 // --- WiFi ---
 Serial.printf("Connecting to WiFi '%s' ...\n", WIFI_SSID);
 WiFi.mode(WIFI_STA);
 WiFi.begin(WIFI_SSID, WIFI_PASS);

 unsigned long wifiStart = millis();
 const unsigned long wifiTimeout = 15000UL; // 15s timeout
 while (WiFi.status() != WL_CONNECTED && (millis() - wifiStart) < wifiTimeout) {
  delay(250);
  Serial.print(".");
 }
 if (WiFi.status() == WL_CONNECTED) {
  Serial.println("");
  Serial.print("Connected. IP: ");
  Serial.println(WiFi.localIP());
 } else {
  Serial.println("");
  Serial.println("WiFi connect failed or timed out. Continuing offline (server will not start).");
 }

 // --- HTTP server setup (only start if WiFi connected) ---
 if (WiFi.status() == WL_CONNECTED) {
  server.on("/", handleRoot);
  server.on("/status", handleStatus);
  server.on("/trigger", handleTrigger);
  server.on("/stop", handleStop);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("HTTP server started on port 80");
 }
}

void loop() {
 // handle HTTP client (non-blocking)
 if (WiFi.status() == WL_CONNECTED) {
  server.handleClient();
 }

  // --- IR SENSOR CHECK (NEW) ---
  // Assuming IR sensor is active LOW (LOW when object is detected)
  if (digitalRead(IR_PIN) == LOW) {
    irObjectDetected = true;
  } else {
    irObjectDetected = false;
  }
  // ---------------------------

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