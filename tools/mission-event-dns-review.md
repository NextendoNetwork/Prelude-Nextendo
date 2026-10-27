# NSO mission-event DNS coverage

## Scope

In Nextendo mode the generated hosts contain `lp1.nso.nintendo.net`, but that exact name does not match `fw-api.lp1.nso.nintendo.net`. The latter also falls outside the existing `*.nintendo.com` and `*.srv.nintendo.net` rules. Without another user rule, mission uploads can therefore resolve to the official service.

Add an exact loopback entry for `fw-api.lp1.nso.nintendo.net`. This deliberately prevents official NSO mission-event uploads in Nextendo mode. It does not implement Nintendo missions, points or rewards. No new backend or certificate is installed, and no broad `*.nintendo.net` or `*.nso.nintendo.net` rule is introduced.

The registered Nextendo applet certificate alone is insufficient evidence of a mission-event backend. An unauthenticated GET of `/v1/events`, forced to the operator's Nextendo server with verified TLS, returned applet HTML. The safe change here is a local block rather than directing reports to an unverified API implementation.

The separate BAAS `invalid_token` report is not diagnosed by this patch. BAAS already matches `*.nintendo.com`. An explicit HTTP proxy can also choose its own upstream DNS; a console hosts entry does not control that proxy's resolver.

## Regression coverage

`python3 tools/test_mission_event_dns.py` compiles and executes the actual `nextendo_hosts_build` C function with two server addresses, and checks the generated rules using Atmosphere's documented wildcard and last-match precedence. It checks the following:

- The mission host resolves only to loopback, with one exact rule.
- BAAS, account login, the NSO applet, invitations, game services, Ubisoft/Just Dance, UCH, BCAT, connectivity and the distinct NAT-check destination retain their expected routes.
- Unrelated hosts and neighboring NSO domains receive no new match.
- The actual hosts-refresh policy replaces an older Prelude-owned file missing this rule, preserves an already-current file and leaves custom user files alone.

The new test fails against the old generator because the mission host has no matching rule. It is part of the PR's existing updater-test CI job before the full NRO build.

## Review and physical acceptance

This is a source PR, with no version bump or release. The generated hosts update takes effect after the existing mode-application/refresh flow and DNS reload or console restart. It does not add a migration that edits user-owned hosts or change the Nintendo-mode policy.

Before release, test on a Switch with Nextendo mode applied and no explicit upstream-resolving proxy: confirm the mission host resolves to loopback, the NSO applet opens, the friends list and invitation flow still work, and a representative game can connect. Check for persistent retry stalls caused by the intentionally unavailable mission uploader. These firmware behaviors are not proven by the host-generator tests. Integrating this with the separate mode-recovery PR should keep that PR's boot-specific hosts selection.

## References

- [Atmosphere DNS.mitm format and hosts selection](https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/features/dns_mitm.md)
- [Switchbrew's research on mnpp mission events](https://switchbrew.org/wiki/BCAT_services#SubmitEvent)
- [mitmproxy explicit proxy topology](https://docs.mitmproxy.org/stable/concepts/modes/#regular-proxy)
