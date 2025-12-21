// FishCar Arduino 控制程序（基于调试成功版本）
// 协议: 串口接收 `V <vx> <vy> <omega>` 指令，返回状态行 `STATUS front=0 back=0 left=0 right=0`

#include <Wire.h>

#define I2C_ADDR        0x34
#define FRONT_PIN       2
#define BACK_PIN        3
#define LEFT_PIN        4
#define RIGHT_PIN       5

#define MOTOR_TYPE_ADDR               20
#define MOTOR_ENCODER_POLARITY_ADDR   21
#define MOTOR_FIXED_SPEED_ADDR        51

#define MOTOR_TYPE_JGB                3

uint8_t motorType = MOTOR_TYPE_JGB;
uint8_t motorEncoderPolarity = 0;  // 可根据电机线序调整

bool wireWriteData(uint8_t reg, uint8_t* val, unsigned int len) {
  Wire.beginTransmission(I2C_ADDR);
  Wire.write(reg);
  for (unsigned int i = 0; i < len; i++) {
    Wire.write(val[i]);
  }
  return Wire.endTransmission() == 0;
}

void publishStatus(bool front, bool back, bool left, bool right) {
  Serial.print("STATUS front=");
  Serial.print(front ? 1 : 0);
  Serial.print(" back=");
  Serial.print(back ? 1 : 0);
  Serial.print(" left=");
  Serial.print(left ? 1 : 0);
  Serial.print(" right=");
  Serial.println(right ? 1 : 0);
}

void setMotorSpeeds(int8_t speeds[4]) {
  if (wireWriteData(MOTOR_FIXED_SPEED_ADDR, (uint8_t*)speeds, 4)) {
    Serial.println("SPEED OK");
  } else {
    Serial.println("SPEED ERR");
  }
}

void calculateMecanum(int vx, int vy, int omega, int8_t speeds[4]) {
  const int r = 10;
  speeds[0] = constrain(vx + vy + omega * r, -127, 127);  // FL
  speeds[1] = constrain(vx - vy - omega * r, -127, 127);  // FR
  speeds[2] = constrain(vx - vy + omega * r, -127, 127);  // RL
  speeds[3] = constrain(vx + vy - omega * r, -127, 127);  // RR
}

void applyCollisionGuards(int& vx, int& vy) {
  bool front = (digitalRead(FRONT_PIN) == LOW);
  bool back = (digitalRead(BACK_PIN) == LOW);
  bool left = (digitalRead(LEFT_PIN) == LOW);
  bool right = (digitalRead(RIGHT_PIN) == LOW);

  if (front && vy > 0) {
    vy = 0;
    Serial.println("COLLISION_FRONT");
  }
  if (back && vy < 0) {
    vy = 0;
    Serial.println("COLLISION_BACK");
  }
  if (left && vx < 0) {
    vx = 0;
    Serial.println("COLLISION_LEFT");
  }
  if (right && vx > 0) {
    vx = 0;
    Serial.println("COLLISION_RIGHT");
  }

  publishStatus(front, back, left, right);
}

void setup() {
  Serial.begin(9600);
  while (!Serial) {}

  pinMode(FRONT_PIN, INPUT_PULLUP);
  pinMode(BACK_PIN, INPUT_PULLUP);
  pinMode(LEFT_PIN, INPUT_PULLUP);
  pinMode(RIGHT_PIN, INPUT_PULLUP);

  Wire.begin();
  delay(200);
  wireWriteData(MOTOR_TYPE_ADDR, &motorType, 1);
  delay(5);
  wireWriteData(MOTOR_ENCODER_POLARITY_ADDR, &motorEncoderPolarity, 1);

  publishStatus(false, false, false, false);
  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.startsWith("V ")) {
      int first = cmd.indexOf(' ', 2);
      int second = cmd.indexOf(' ', first + 1);
      if (first > 0 && second > first) {
        int vx = cmd.substring(2, first).toInt();
        int vy = cmd.substring(first + 1, second).toInt();
        int omega = cmd.substring(second + 1).toInt();

        applyCollisionGuards(vx, vy);

        int8_t speeds[4];
        calculateMecanum(vx, vy, omega, speeds);
        setMotorSpeeds(speeds);
      } else {
        Serial.println("CMD ERR");
      }
    } else if (cmd == "PING") {
      publishStatus(
        digitalRead(FRONT_PIN) == LOW,
        digitalRead(BACK_PIN) == LOW,
        digitalRead(LEFT_PIN) == LOW,
        digitalRead(RIGHT_PIN) == LOW
      );
      Serial.println("PONG");
    } else {
      Serial.println("UNKNOWN");
    }
  }

  delay(20);
}

