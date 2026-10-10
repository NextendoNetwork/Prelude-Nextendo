# Prelude

**Support the maintainer of Prelude**: [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/P5W228IFAC)

**Prelude** is the Nintendo Switch homebrew that switches your console between the
[Nextendo Network](https://nextendo.network) and Nintendo's official servers.

It is a small `.nro` you run from the homebrew menu. You pick a mode, it applies the change and
reboots. Nothing is permanent: you can switch back whenever you want.

```
        Which network do you want to load?
        [ NEXTENDO ]     [ NINTENDO ]
```

- **Nextendo mode**: redirects Nintendo traffic to the Nextendo servers and provisions everything
  the console needs to trust them.
- **Nintendo mode**: removes every component Prelude installed and hands the console back to
  Nintendo, with Atmosphère's own telemetry blocking restored.

## Features

### A complete settings app

- Follows the console's system theme (HOME menu / Settings look, including light/dark mode).
- In-app language selection: English, Español, Português, Français, 中文.
- Background music, decoded with mpg123: no SDL2, the `.nro` is ~35% smaller than before.
- **Self-updating**: checks GitHub releases at launch and can download and replace the `.nro` it is
  running from (any SD path, not just `/switch/`). Stale bundled mods (see below) are detected and
  offered as an update too.

### Online games, out of the box

One switch to Nextendo mode and these are configured with the proper hosts and patches:

- **Mario Kart 8 Deluxe**: NEX secure-server routed to the production machine, plus a **country
  flag installer** (110 flags) that builds the ExeFS patch locally, no download needed.
- **Super Smash Bros. Ultimate**: optional **SSBU Online Deluxe quickplay mod** (L button),
  bundled in the `.nro` with its full dependency stack (ARCropolis, smashline, Skyline plugins...)
  and a toggle for the mod's own overclock if you already run sys-clk / Horizon OC.
- **Splatoon 2**: BCAT online schedule installer via LayeredFS (no save-data tricks, no network
  needed at install time).
- **Splatoon 3**: NPLN (gRPC/HTTP2) hosts plus the certificate ExeFS patches required by the
  game's bundled BoringSSL, with a dedicated **status screen** showing whether the installed
  patches match the ones this build ships and what to do after a game update.
- **Super Mario Bros. 35**: official BCAT event installer **plus an optional Special Battle**
  (27 merged events, 119 queues), installed on demand because its ExeFS patch *replaces* the normal
  35-player battle instead of adding to it.
- **Super Mario Bros. Wonder**: ExeFS patches (certificate + peer name) shipped for everyone;
  harmless if you don't own the game (Atmosphère matches by build ID).
- **Metal Gear Solid: Peace Walker**: ExeFS patches (certificate bypass in `mgspwcertbypass/`)
  deployed automatically under Nextendo mode.
- **Crash Team Racing: Nitro-Fueled**: ExeFS patches (`dwctrfriendlookup/` and `dwctrtrustcertbypass/`)
  deployed automatically under Nextendo mode, with Demonware DNS redirection (`*.demonware.net`).
- **Diablo III: Eternal Collection**: Demonware hosts redirection configured for private servers
  (no ExeFS patches required).
- **Minecraft Dungeons II** (1.1.1.0): ExeFS listen-host patch (`dungeons2-nextendo/`) so the party
  leader's game hosts the session, plus PlayFab, Minecraft and Xbox Live redirection. The Xbox Live
  lines apply to every game while Nextendo mode is on.
- **Nintendo Account Link fallback**: targeted `ssl:s` Client-PKI fallback (`network_mitm` v2)
  for blanked PRODINFO / emuMMC consoles, allowing account linking on Nextendo without error `0x167B`.
- Explicit per-game NEX entries for Mario Tennis Aces, ARMS, Luigi's Mansion 3, Animal Crossing,
  Strikers and Nintendo Switch Sports, on top of the `g2*` wildcard.

### Privacy & reversibility

- Telemetry blocked **in both modes** (Atmosphère's native defaults are merged, not replaced).
- Nintendo mode removes the whole certificate-trust stack (CA bundle, `disable_ca_verification`,
  `rootCA.pem`) and purges the logs that could leak the server IP: no `.bak`, no debug logs.
- PRODINFO handled per mode: real device certificate under Nextendo (confined by DNS.mitm),
  blanked identity under Nintendo on emuMMC, never touched on sysNAND; and the UI tells you
  plainly what that means for your console type.
- Your own `hosts` files are offered a one-time backup before Prelude writes over them.

## How it works

Prelude does not patch games and does not touch the network stack. It writes configuration that
Atmosphère already understands, then reboots so the changes take effect:

| What | Where |
| --- | --- |
| Host redirections | `/atmosphere/hosts/{sysmmc,emummc}.txt` (Atmosphère DNS.mitm) |
| DNS.mitm on/off | `/atmosphere/config/system_settings.ini` |
| PRODINFO per mode | `/exosphere.ini` (emuMMC only) |
| Certificate trust | `exefs_patches/`, `nro_patches/`, browser CA bundle |
| Game content (BCAT, mods, flags) | `/atmosphere/contents/` and `exefs_patches/` on the SD |

Because it only writes files Atmosphère reads at boot, everything it does is reversible by
switching modes, or by deleting those files by hand.

## Building

There is no local toolchain requirement beyond Docker:

```sh
docker run --rm -v "$PWD:/work" -w /work devkitpro/devkita64 \
  bash -c 'dkp-pacman -Syu --noconfirm switch-freetype switch-mpg123 && make -j$(nproc)'
```

The result is `nextendo.nro`. Copy it to `/switch/` on your SD card. Releases are also built
automatically by the GitHub Actions workflow, which attaches the `.nro` to every tagged release.

Version numbers are kept in lockstep: `APP_VERSION` in the `Makefile` is `X.Y.Z`, the update
checker compares full semver, and the GitHub tag is `vX.Y.Z`.

## Status

**Prelude is actively developed**: new releases land roughly weekly (see
[Releases](https://github.com/NextendoNetwork/Prelude-Nro/releases)), and the bundled game patches
are kept in sync with game and Atmosphère updates. Issues and pull requests are welcome; note that
the project started as an internal tool and release notes are sometimes written in French.

If you are running your own server, the addresses Prelude redirects to live in
`source/nextendo_hosts.h`: that file is the whole configuration surface.

## Licence

Copyright (C) 2026 Nextendo Network.

Prelude is licensed under the **PolyForm Shield License 1.0.0**. You may use, study, share and
modify it for any purpose, and distribute your changes, with one exception: you may not use it
to provide a product that competes with Nextendo Network, or with any product Nextendo Network
provides using it.

See [LICENSE.md](LICENSE.md) for the full text, or
<https://polyformproject.org/licenses/shield/1.0.0>.

Required Notice: Copyright 2026 Nextendo Network

This project is not affiliated with, endorsed by, or connected to Nintendo. "Nintendo" and
"Nintendo Switch" are trademarks of Nintendo. Use it on hardware you own.
