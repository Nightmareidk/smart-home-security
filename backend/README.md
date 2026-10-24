# Backend

The server on the laptop. It will:

- receive messages from the boards and the AI programs (MQTT),
- save readings and events in a database,
- apply the alert rules (intrusion, fire, mold risk, thirsty plant),
- send live updates to the app,
- send phone notifications.

Starts in step S1 of `docs/ROADMAP.md`.
