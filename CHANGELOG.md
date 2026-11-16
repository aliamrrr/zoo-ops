# Changelog

All notable changes to Zoo Ops. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-11-16

### Added

- **Zoo Ops [Hard]**: a real FastAPI service (`hard/`) with ten tickets and acceptance tests.
- **Zoo Ops [Hard++]**: a deterministic distributed simulation (`hardpp/`) with ten
  interview-grade tickets.
- **The Blueprint**: in both hard modes, place each pattern on the architecture before it ships.
- One-command launchers: `zoo.cmd` (Windows) and `zoo.sh` (macOS, Linux, WSL). The first run
  sets everything up, then asks which mode to play.
- Docker: `docker compose up` plays with your files mounted; the image runs as a non-root user.
- The `zoo` command: `zoo` alone asks for a mode, `zoo play hard`, a free port is found when
  8000 is taken, the browser opens on the Windows side under WSL.
- Starter guards: CI fails when a solution reaches `main`.
- Architecture notes, decision records and a guide to writing levels in `docs/`.

### Changed

- Classic is described by `levels/zoo-mode.json`, like the hard modes, and every mode runs
  through one `ModeRuntime` interface.
- `zoo reset` restores from the commit you started from, without tags.
- The front end is split by responsibility (`js/world/`, `js/game/`, `css/`).
- Dependencies live in `pyproject.toml` only; `requirements.txt`, `install.sh` and
  `install.ps1` are gone.
- CI covers Python 3.11 to 3.13 on Linux, macOS and Windows, the launchers and the image.

### Fixed

- Unicode sprites and progress bars no longer crash on older Windows consoles.
- One hard ticket whose tests do not import no longer hides the results of the others.

## [0.1.0]

- Zoo Ops Classic: ten levels, the live zoo, the stations and the terminal test bench.

[1.0.0]: https://github.com/aliamrrr/zoo-ops/releases/tag/v1.0.0
