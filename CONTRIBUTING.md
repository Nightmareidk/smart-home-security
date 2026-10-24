# How we work together on GitHub

## Every time you start

1. Pull the latest changes: `git pull`
2. Look at what changed (`git log --oneline`) before you begin.

## Rules

- Work in your own area. Hardware: `firmware/` and `hardware/`. Software: `backend/`, `frontend/`, `ai/`, `simulator/`. Molecular: `molecular/`.
- The software teammates split the work, so we do not edit the same file at the same time.
  Say in the group chat which part you are taking.
- Make small commits with a clear message, for example "Add mold-risk alert rule".
- Pull again before you push. If git says there is a conflict, ask before overwriting someone's work.
- Changing a message name or its contents in `docs/ARCHITECTURE.md` affects the hardware team.
  Tell them first.
- Never commit passwords, Wi-Fi details or keys. They go in `.env` or `secrets.h`, which git ignores.

## Branches (optional but safer)

Each person can work on their own branch, for example `arqam/app` or `syed/backend`, and merge to `main` when it works.

## Versions

We are in beta, so versions are called **Beta 1.0**, **Beta 1.1**, **Beta 1.2** and so on.

- A normal update (a new feature or a set of fixes) goes up by one step: 1.0 to 1.1 to 1.2.
- A major update (a big change, for example the first version with real hardware, or a new look) goes up to the next whole number: 2.0, then 3.0.

Every release:

1. Change the number in `VERSION`, `backend/app/version.py` and `frontend/app.json` (`1.1` is written `1.1.0` in app.json).
2. Add an entry at the top of `CHANGELOG.md`.
3. Take new screenshots into `screenshots/v<number>/`.
4. Commit, then tag it: `git tag v1.1` and `git push --tags`.

## Folders

`frontend/` is the phone app, `backend/` is the server, `screenshots/` has pictures of each version.
