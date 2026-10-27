# Gang Beasts public-service containment in Nextendo mode

Gang Beasts 1.28.1 online requests observed in Citron use Unity Authentication,
Lobby, Relay, QoS, Matchmaker, Multiplay and Wire. They did not use the UCH
brainCloud redirect. Successful original-service matchmaking was not evidence
of a Nextendo-hosted Gang Beasts implementation.

Until a compatible Nextendo game backend exists, generated Nextendo hosts now
loop back the seven observed service hosts and `*.services.api.unity.com`.
The configured Nextendo server IP is deliberately not advertised as a functioning
Gang Beasts backend. Unsupported online requests should fail instead of reaching
the public service.

Atmosphere DNS rules apply to all titles: other games using these shared Unity
services also lose access while Nextendo mode is active. This does not change
Nintendo-mode behavior. DNS is not an IP firewall and cannot stop already cached
or literal IP destinations; close running games and reboot after applying hosts.
Do not claim this is complete egress isolation or playable Gang Beasts support.

The existing managed-host refresh mechanism detects the new generated content
on app launch in Nextendo mode and requests a restart. Mode reapplication also
includes the block. Unmarked user hosts retain the existing ownership rules.

## Verification

- `tools/test_gang_beasts_containment.py`: compiles the real production hosts
  builder, checks effective last-match routing for all seven hosts and a new
  Unity service, two configured IPs, preserved UCH routing, unrelated domains,
  and managed-host refresh behavior.
- `tools/test_ggst_hosts.py`: existing game routes remain valid.
- `tools/test_mode_isolation.py`: mode and NAND isolation regression checks pass.

No official game requests were replayed. No identity, PRODINFO, controller,
firmware, patch installation or game-save logic changed. Existing local console
DNS blocks were previously read back and confirmed in its DNS MITM startup log;
this source change has not yet been released/installed on other consoles.
