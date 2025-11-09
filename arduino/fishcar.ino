#include <ArduinoJson.h>

struct MotorPins {
  uint8_t pwm;
  uint8_t dir;
};

MotorPins motorFL{3, 2};
MotorPins motorFR{5, 4};
MotorPins motorRL{6, 7};
MotorPins motorRR{9, 8};

const uint8_t switchFront = A0;
const uint8_t switchRear  = A1;
const uint8_t switchLeft  = A2;
const uint8_t switchRight = A3;

float vx = 0.0f;
float vy = 0.0f;
float omega = 0.0f;
bool active = false;
unsigned long lastCommand = 0;
const unsigned long watchdogMs = 500;

StaticJsonDocument<256> doc;

void setup() {
  Serial.begin(115200);
  setupMotor(motorFL);
  setupMotor(motorFR);
  setupMotor(motorRL);
  setupMotor(motorRR);

  pinMode(switchFront, INPUT_PULLUP);
  pinMode(switchRear, INPUT_PULLUP);
  pinMode(switchLeft, INPUT_PULLUP);
  pinMode(switchRight, INPUT_PULLUP);
}

void loop() {
  readSerial();
  applyWatchdog();
  applyLimitSwitches();
  driveMecanum();
  publishStatus();
}

void setupMotor(const MotorPins &motor) {
  pinMode(motor.pwm, OUTPUT);
  pinMode(motor.dir, OUTPUT);
}

void readSerial() {
  if (!Serial.available()) {
    return;
  }
  String payload = Serial.readStringUntil('\n');
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    return;
  }
  if (doc.containsKey("type")) {
    lastCommand = millis();
    return;
  }
  vx = doc["vx"] | 0.0;
  vy = doc["vy"] | 0.0;
  omega = doc["omega"] | 0.0;
  active = doc["active"] | false;
  lastCommand = millis();
}

void applyWatchdog() {
  if (millis() - lastCommand > watchdogMs) {
    vx = vy = omega = 0.0f;
    active = false;
  }
}

void applyLimitSwitches() {
  if (digitalRead(switchFront) == LOW && vy > 0) {
    vy = 0.0f;
  }
  if (digitalRead(switchRear) == LOW && vy < 0) {
    vy = 0.0f;
  }
  if (digitalRead(switchLeft) == LOW && vx < 0) {
    vx = 0.0f;
  }
  if (digitalRead(switchRight) == LOW && vx > 0) {
    vx = 0.0f;
  }
}

void driveMecanum() {
  float fl = vy + vx + omega;
  float fr = vy - vx - omega;
  float rl = vy - vx + omega;
  float rr = vy + vx - omega;

  setMotor(motorFL, fl);
  setMotor(motorFR, fr);
  setMotor(motorRL, rl);
  setMotor(motorRR, rr);
}

void setMotor(const MotorPins &motor, float value) {
  int pwm = constrain(int(fabs(value) * 255), 0, 255);
  digitalWrite(motor.dir, value >= 0 ? HIGH : LOW);
  analogWrite(motor.pwm, active ? pwm : 0);
}

void publishStatus() {
  static unsigned long lastSend = 0;
  if (millis() - lastSend < 100) {
    return;
  }
  lastSend = millis();
  StaticJsonDocument<128> status;
  status["limits"]["front"] = digitalRead(switchFront) == LOW;
  status["limits"]["rear"]  = digitalRead(switchRear) == LOW;
  status["limits"]["left"]  = digitalRead(switchLeft) == LOW;
  status["limits"]["right"] = digitalRead(switchRight) == LOW;
  serializeJson(status, Serial);
  Serial.println();
}

