# Reinstall patches review — October 26, 2026

Reviewed main `54ff939` and the manual **Game Patches → Reinstall patches** path.
The button calls the same resource provisioner used on startup in Nextendo mode
and during mode application. It copies all `romfs:/sd` resources, including game
IPS files, firmware SSL/browser patches and browser certificate resources.
It does not itself rewrite DNS hosts, select a different server, or change PRODINFO.

## Reproduced defect

The previous `copyFile` opened the installed destination with `wb` before writing.
A host reproduction compiled that exact function from main with a failed-write
injection: the call returned failure but an existing working patch became empty
(`installedBytes=0`, `originalPreserved=false`). This is a demonstrated installer
failure path, not proof that every reported connection error has this cause.

Repeatedly pressing reinstall also rewrote identical resources. A successful
manual action only displayed a reboot toast; startup requested a reboot for
changed hosts/new news patches, but not for other changed resource bytes.
The displayed patch count checks presence rather than matching the installed
game/firmware build or validating its patches.

## Candidate

- Compare binary bytes first; identical resources require no write, rename or
  commit and the UI reports that nothing changed.
- Stage changed resources separately, commit and read them back before replacing
  the installed file. Preserve the old version as `.prelude-backup`; recover an
  interrupted old-to-backup rename on a subsequent attempt.
- Read, write, close, rename and commit failures return failure; rollback is
  attempted after promotion failures. If the storage also rejects rollback, the
  recovery sibling remains necessary. This is per-file recovery, not an atomic
  transaction across the whole resource tree or a guarantee against SD failure.
- Request reboot through an explicit result screen when provisioning changed
  resources, on startup or after the manual button. Preserve that pending screen
  through the initial hosts-backup questions.
- Keep mode, server selection, DNS policy, resource payloads and identity policy
  unchanged. The existing PR #92 remains a separate security change.

Atmosphère's official IPS loader requires filenames to end exactly in `.ips`,
so staging/recovery suffixes are not additional active IPS patches:
https://github.com/Atmosphere-NX/Atmosphere/blob/master/libraries/libstratosphere/source/patcher/patcher_api.cpp

## Automated checks

`tools/test_resource_copy.c` compiles the actual new installer with real temporary
binary files. It checks unchanged reinstall with zero writes, existing-file
preservation on injected read/write/close/rename/commit failures, staged readback
corruption, recovery after interrupted rename, missing sources, initial install,
empty boot flags and multi-chunk binary resources containing NUL bytes.

Existing mode/INI/DNS/GGST regressions are run separately. No failing-storage
injection is performed on a console. No payload, firmware patch or release
version is changed by this candidate.

## Hardware acceptance still required

1. Back up a known working SD configuration. Record firmware, Atmosphère,
   Prelude version, selected mode, game version and actual connection error.
2. With already matching resources, run the candidate's reinstall action:
   verify the unchanged message and matching resource hashes, then test the
   previously working game and NSO/friends.
3. Offline, remove one known managed game patch from the test copy only; reopen
   the candidate. Verify it restores that resource and requests a reboot.
   Reboot before checking online functionality.
4. Test the new manual-action reboot path with a controlled changed resource on
   a test setup, plus Nintendo/Nextendo mode cycles and unrelated SD files.
5. Obtain a report/log from an affected player to distinguish failed writes or
   missing reboot from unsupported game/CFW builds, DNS or server problems.

No Switch was modified as part of preparing this PR. Automated checks do not
establish physical acceptance or prove this resolves all user reports.
