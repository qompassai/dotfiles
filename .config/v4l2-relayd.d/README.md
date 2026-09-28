# v4l2-relayd.d — v4l2-relayd instance drop-ins (configuration reference)

## What this app is

`v4l2-relayd` ("plays GStreamer sources into v4l2loopback devices",
upstream: <https://gitlab.com/vicamo/v4l2-relayd>, AUR:
`v4l2-relayd`) creates virtual cameras: it pumps a GStreamer pipeline into
a v4l2loopback device so video-conferencing apps see a camera that can show
a test pattern, a physical webcam, or a screen capture.

## Doc references (accessed 2026-09-28)

- Upstream project (generator, template unit, default env file, daemon
  option table — all verified against the 0.2.0 tarball):
  <https://gitlab.com/vicamo/v4l2-relayd>
- AUR package git repository:
  <https://aur.archlinux.org/v4l2-relayd.git>

## User configuration mechanism

Per-instance drop-in files:

| File in this repo                              | Real location                              |
|------------------------------------------------|--------------------------------------------|
| `.config/v4l2-relayd.d/virtual-camera.conf`    | `/etc/v4l2-relayd.d/virtual-camera.conf`   |

How it works (from upstream source):

1. The systemd **generator** (`v4l2-relayd-generator`) creates a
   `v4l2-relayd@<name>.service` instance for every `*.conf` in
   `/etc/v4l2-relayd.d/` — the filename (minus `.conf`) is the instance
   name, so this file yields `v4l2-relayd@virtual-camera.service`.
2. The template unit `v4l2-relayd@.service` loads, in order,
   `EnvironmentFile=/etc/default/v4l2-relayd` (base defaults) and then
   `EnvironmentFile=-/etc/v4l2-relayd.d/%i.conf` (this drop-in; the `-`
   prefix makes it optional). Variables set here override the base
   defaults **for this instance only**.
3. The unit requires `VIDEOSRC`, `FORMAT`, `WIDTH`, `HEIGHT`, `FRAMERATE`
   and `CARD_LABEL` to be non-empty (`ExecCondition` tests) and then runs
   the daemon with `-i` (input pipeline), `-s` (splash pipeline, only when
   `SPLASHSRC` is non-empty), `-o` (output appsrc pipeline built from the
   format/geometry variables), plus `$EXTRA_OPTS` appended verbatim.

Variables (all eight documented; alphabetical in the file):

| Variable     | ELI5 / used as                                              |
|--------------|-------------------------------------------------------------|
| `CARD_LABEL` | Name tag of the virtual camera ("Virtual Camera").          |
| `EXTRA_OPTS` | Extra daemon flags (`-d` debug; the unit passes `-i/-o/-s`).|
| `FORMAT`     | Pixel format (`YUY2`).                                      |
| `FRAMERATE`  | Frames per second as a fraction (`30/1`).                   |
| `HEIGHT`     | Picture height in pixels (`720`).                           |
| `SPLASHSRC`  | Optional splash-screen GStreamer pipeline (empty = off).    |
| `VIDEOSRC`   | Where pictures come from (`videotestsrc` test pattern).     |
| `WIDTH`      | Picture width in pixels (`1280`).                           |

The daemon itself (`v4l2-relayd.c`, `GOptionEntry` table) accepts
`-D/--background`, `-d/--debug`, `-v/--version`, `-i/--input`,
`-o/--output`, `-s/--splash`.

## Validation

No systemd daemon is running here, so the file is validated structurally
as a systemd `EnvironmentFile`: every active line matches
`^[A-Za-z_][A-Za-z0-9_]*=`, and every variable name is one of the eight
the template unit consumes. (Deliberately **not** parsed as INI — it is
shell-style `KEY=VALUE` syntax.)
