# Simulator

A program that pretends to be the ESP32 boards, so the software team can build and test
without the real parts.

It sends fake sensor readings (temperature, humidity, soil, door state) and reacts to commands
(light on, pump on, lock) using the exact same messages as the real boards, listed in
`docs/ARCHITECTURE.md`.

It also has buttons to force situations for testing: humidity too high, fire, failed unlock.

Starts in step S1 of `docs/ROADMAP.md`.
