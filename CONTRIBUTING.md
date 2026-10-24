# How we work together on GitHub

## Every time you start

1. Pull the latest changes: `git pull`
2. Look at what changed (`git log --oneline`) before you begin.

## Rules

- Work in your own area. Hardware: `firmware/` and `hardware/`. Software: `backend/`, `app/`, `ai/`, `simulator/`. Molecular: `molecular/`.
- The software teammates split the work, so we do not edit the same file at the same time.
  Say in the group chat which part you are taking.
- Make small commits with a clear message, for example "Add mold-risk alert rule".
- Pull again before you push. If git says there is a conflict, ask before overwriting someone's work.
- Changing a message name or its contents in `docs/ARCHITECTURE.md` affects the hardware team.
  Tell them first.
- Never commit passwords, Wi-Fi details or keys. They go in `.env` or `secrets.h`, which git ignores.

## Branches (optional but safer)

Each person can work on their own branch, for example `arqam/app` or `syed/backend`, and merge to `main` when it works.
