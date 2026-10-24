# Firmware

Code for the ESP32 boards. Open the sketches in the Arduino IDE.

| Folder | Board | Job |
|---|---|---|
| `door-node/` | ESP32-S3 T-Display | Fingerprint, keypad, lock, buzzer, status screen |
| `plant-node/` | ESP32-C3 Super Mini | BME680, soil sensors, pump, lights, fan, humidifier, clap microphone |
| `cam-node/` | ESP32-CAM | Sends the camera picture to the laptop |

Wi-Fi name, password and the server address go in a `secrets.h` file in each sketch folder.
That file is ignored by git, so it never gets uploaded.
