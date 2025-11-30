#include <Wire.h>

#define I2C_ADDR        0x34
#define FRONT_PIN       2   // 前微动开关
#define BACK_PIN        3   // 后
#define LEFT_PIN        4   // 左
#define RIGHT_PIN       5   // 右

#define ADC_BAT_ADDR                  0
#define MOTOR_TYPE_ADDR               20
#define MOTOR_ENCODER_POLARITY_ADDR   21
#define MOTOR_FIXED_PWM_ADDR          31
#define MOTOR_FIXED_SPEED_ADDR        51
#define MOTOR_ENCODER_TOTAL_ADDR      60

#define MOTOR_TYPE_WITHOUT_ENCODER    0
#define MOTOR_TYPE_TT                 1
#define MOTOR_TYPE_N20                2
#define MOTOR_TYPE_JGB                3

uint8_t data[20];

// 原I2C函数不变
bool WireWriteByte(uint8_t val) {
    Wire.beginTransmission(I2C_ADDR);
    Wire.write(val);
    if (Wire.endTransmission() != 0) {
        Serial.println("WireWriteByte failed!");
        return false;
    }
    return true;
}

bool WireWriteDataArray(uint8_t reg, uint8_t *val, unsigned int len) {
    unsigned int i;
    Wire.beginTransmission(I2C_ADDR);
    Wire.write(reg);
    for (i = 0; i < len; i++) {
        Wire.write(val[i]);
    }
    if (Wire.endTransmission() != 0) {
        Serial.println("WireWriteDataArray failed!");
        return false;
    }
    return true;
}

bool WireReadDataByte(uint8_t reg, uint8_t &val) {
    if (!WireWriteByte(reg)) {
        return false;
    }
    Wire.requestFrom(I2C_ADDR, 1);
    while (Wire.available()) {
        val = Wire.read();
    }
    return true;
}

int WireReadDataArray(uint8_t reg, uint8_t *val, unsigned int len) {
    unsigned char i = 0;
    if (!WireWriteByte(reg)) {
        return -1;
    }
    Wire.requestFrom(I2C_ADDR, len);
    while (Wire.available()) {
        if (i >= len) {
            return -1;
        }
        val[i] = Wire.read();
        i++;
    }
    return i;
}

uint8_t MotorType = MOTOR_TYPE_JGB;
uint8_t MotorEncoderPolarity = 0;  // 调试时调整0/1

void setup() {
    Serial.begin(9600);
    while (!Serial);
    Serial.println("Arduino car control with 4-directional collision avoidance started...");

    // 四个微动开关初始化：输入 + 内部上拉
    pinMode(FRONT_PIN, INPUT_PULLUP);
    pinMode(BACK_PIN, INPUT_PULLUP);
    pinMode(LEFT_PIN, INPUT_PULLUP);
    pinMode(RIGHT_PIN, INPUT_PULLUP);
    Serial.println("Collision pins (2-5) initialized (PULLUP).");

    Wire.begin();
    delay(200);

    if (WireWriteDataArray(MOTOR_TYPE_ADDR, &MotorType, 1)) {
        Serial.println("Motor type set: JGB");
    } else {
        Serial.println("Failed to set motor type!");
    }
    delay(5);
    if (WireWriteDataArray(MOTOR_ENCODER_POLARITY_ADDR, &MotorEncoderPolarity, 1)) {
        Serial.println("Encoder polarity set: 0");
    } else {
        Serial.println("Failed to set polarity!");
    }
    delay(2000);
    Serial.println("Setup completed! Ready for commands.");
}

int8_t car_stop[4] = {0, 0, 0, 0};  // 停止

void set_motor_speeds(int8_t speeds[4]) {
    Serial.print("Setting speeds: [");
    for (int i = 0; i < 4; i++) {
        Serial.print(speeds[i]);
        if (i < 3) Serial.print(", ");
    }
    Serial.println("]");
    
    if (WireWriteDataArray(MOTOR_FIXED_SPEED_ADDR, (uint8_t*)speeds, 4)) {
        Serial.println("Speeds set OK!");
    } else {
        Serial.println("Failed to set speeds!");
    }
}

// 麦克纳姆轮速度计算 (vx, vy, omega: int, 单位脉冲/10ms; r=10 缩放)
void calculate_mecanum(int vx, int vy, int omega, int8_t speeds[4]) {
    int r = 10;  // 轮距缩放因子，调整以匹配实际
    speeds[0] = constrain(vx + vy + omega * r, -127, 127);  // FL
    speeds[1] = constrain(vx - vy - omega * r, -127, 127);  // FR
    speeds[2] = constrain(vx - vy + omega * r, -127, 127);  // RL
    speeds[3] = constrain(vx + vy - omega * r, -127, 127);  // RR
}

// 检查四个碰撞并调整vx/vy
void check_collisions(int &vx, int &vy, int &omega) {
    bool front_blocked = (digitalRead(FRONT_PIN) == LOW);
    bool back_blocked = (digitalRead(BACK_PIN) == LOW);
    bool left_blocked = (digitalRead(LEFT_PIN) == LOW);
    bool right_blocked = (digitalRead(RIGHT_PIN) == LOW);
    
    // 打印禁用状态（调试）
    Serial.print("Collision status: F="); Serial.print(front_blocked ? "X" : "O");
    Serial.print(" B="); Serial.print(back_blocked ? "X" : "O");
    Serial.print(" L="); Serial.print(left_blocked ? "X" : "O");
    Serial.print(" R="); Serial.print(right_blocked ? "X" : "O"); Serial.println();
    
    // 调整vx: 前禁用 → vx <=0; 后禁用 → vx >=0
    if (front_blocked && vx > 0) {
        vx = 0;
        Serial.println("COLLISION_FRONT");
        delay(50);  // 去抖
        while (digitalRead(FRONT_PIN) == LOW) {
            delay(100);
            Serial.println("Waiting for front switch reset...");
        }
        Serial.println("Front switch reset.");
    }
    if (back_blocked && vx < 0) {
        vx = 0;
        Serial.println("COLLISION_BACK");
        delay(50);
        while (digitalRead(BACK_PIN) == LOW) {
            delay(100);
            Serial.println("Waiting for back switch reset...");
        }
        Serial.println("Back switch reset.");
    }
    
    // 调整vy: 左禁用 → vy >=0; 右禁用 → vy <=0
    if (left_blocked && vy < 0) {
        vy = 0;
        Serial.println("COLLISION_LEFT");
        delay(50);
        while (digitalRead(LEFT_PIN) == LOW) {
            delay(100);
            Serial.println("Waiting for left switch reset...");
        }
        Serial.println("Left switch reset.");
    }
    if (right_blocked && vy > 0) {
        vy = 0;
        Serial.println("COLLISION_RIGHT");
        delay(50);
        while (digitalRead(RIGHT_PIN) == LOW) {
            delay(100);
            Serial.println("Waiting for right switch reset...");
        }
        Serial.println("Right switch reset.");
    }
    
    // omega不受影响（允许旋转逃脱）
}

void loop() {
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        
        if (cmd.startsWith("V ")) {
            // 解析 "V vx vy omega"
            int firstSpace = cmd.indexOf(' ', 2);
            int secondSpace = cmd.indexOf(' ', firstSpace + 1);
            if (firstSpace > 0 && secondSpace > firstSpace) {
                int vx = cmd.substring(2, firstSpace).toInt();
                int vy = cmd.substring(firstSpace + 1, secondSpace).toInt();
                int omega = cmd.substring(secondSpace + 1).toInt();
                
                Serial.print("Received: V "); Serial.print(vx); Serial.print(" "); 
                Serial.print(vy); Serial.print(" "); Serial.println(omega);
                
                // 检查碰撞并调整vx/vy
                check_collisions(vx, vy, omega);
                
                int8_t speeds[4];
                calculate_mecanum(vx, vy, omega, speeds);
                set_motor_speeds(speeds);
            } else {
                Serial.println("Invalid command format!");
            }
        } else {
            Serial.println("Unknown command: " + cmd);
        }
    }
    
    delay(100);  // 循环间隔
}