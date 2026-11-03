# Face recognition

Tells the house **who is at the camera**. Known people are reported by name and show as **Home** in the app.
Unknown faces are reported with no name (an intruder alert when the system is armed).

Everything stays on the laptop. Only 128 numbers per photo are saved (not the photo), in `ai/face/data/`, which git ignores.

## Set up (once)

```bash
cd ai/face
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python get_models.py        # downloads two small models (about 39 MB)
```

## Add people (with their written consent)

```bash
.venv\Scripts\python enrol.py add sara --source 0               # takes 6 photos from the webcam
.venv\Scripts\python enrol.py add sara --images a.jpg b.jpg c.jpg
.venv\Scripts\python enrol.py list
.venv\Scripts\python enrol.py delete sara                       # anyone can ask for this at any time
```

It asks you to confirm consent before saving. Add `--can-unlock` only for people who may open the door by face.

## Run it

```bash
.venv\Scripts\python main.py --source 0 --show                  # webcam with a preview window
.venv\Scripts\python main.py --source http://<camera-ip>/stream # the ESP32-CAM
.venv\Scripts\python main.py --source 0 --allow-unlock          # also open the door for people allowed to
```

(`--allow-unlock` needs the server token: set `HOME_API_TOKEN`.)

## How it decides

- A face is turned into 128 numbers. It is compared with the saved people. A similarity of **0.45 or more** names the person (`--match`).
- Opening the door needs **0.6 or more** (`--unlock-match`), **3 matches in a row** (`--frames`), a person enrolled with `--can-unlock`, and `--allow-unlock`. It is **off by default**.
- A person must be seen in 3 pictures in a row before anything is reported, and the same thing is not repeated for 5 seconds.

## Honest limits

- A simple face system **can be fooled by a photo or a video of a face**. Fingerprint and PIN stay the strong ways in. Test it with a printed photo and write down what happens.
- Poor light, hats, masks and strong angles lower the score. Enrol in the same place and light the door will have, and add a few photos with small head turns.
- Real accuracy has to be measured with the team: the sample-photo checks here only show it works, not how good it is in your hallway.

## Files

| File | What it does |
|---|---|
| `engine.py` | Finds faces and turns them into numbers (OpenCV models) |
| `matcher.py` | Compares faces (tested) |
| `store.py` | Saves enrolled people, with consent (tested) |
| `enrol.py` | Add, list and delete people |
| `main.py` | Watches a camera and reports who it sees |
| `get_models.py` | Downloads the models |
| `tests/` | `python -m pytest tests` |
