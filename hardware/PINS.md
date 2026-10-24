# Pin map

To be filled in during Phase 0. Fill in the pin numbers once the boards are on the table.

Rules to remember:

- Analog sensors (MQ-2, soil sensors, the microphone) must go on ADC1 pins on the ESP32-S3, and
  the same idea on the C3: pins that still work when Wi-Fi is on.
- The T-Display S3 uses many pins for its screen, so only about 12 are free. The fingerprint sensor
  needs 2 and a 4x4 keypad needs 8. A 3x4 keypad needs 7.
- Keep high-power parts (lock, pump, humidifier, heater) on relays with their own power supply.

## Door node (ESP32-S3 T-Display)

| Part | Pins | Pin numbers |
|---|---|---|
| Fingerprint AS608 | 2 (serial) | |
| Keypad | 7 or 8 | |
| Lock relay | 1 | |
| Buzzer | 1 | |

## Plant node (ESP32-C3 Super Mini)

| Part | Pins | Pin numbers |
|---|---|---|
| BME680 | 2 (I2C) | |
| Soil sensor 1 and 2 | 2 (analog) | |
| MAX9814 microphone | 1 (analog) | |
| Pump relay | 1 | |
| Grow light and lamp relay | 1 or 2 | |
| Humidifier, fan relay | 1 or 2 | |
| MQ-2, flame sensor | 2 | |
