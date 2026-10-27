# Issue #32: DNS preparation before identity changes

## Review scope

This candidate combines the exact mission-event block from PR #88 with the new
mode-transition guard. PR #88 has not been merged into main, so the combined
candidate includes its source change, regression and CI entry. This does not
remove or widen the mission rule. Review the combined PR instead of treating
these two changes as alternative fixes.

The mission rule prevents `fw-api.lp1.nso.nintendo.net` falling through to normal
DNS. The transition guard prevents `blank_prodinfo_emummc=0` being requested
after a failed DNS configuration write or preparation commit. Previously the
function attempted the identity change and returned failure only afterwards.

Existing successful Nextendo authentication, the explicit Nintendo-mode block,
game routes, custom settings and sysMMC identity policy are retained. There is
no version bump, production deployment or release in this PR.

## Tests already covered by the host harness

- Inject DNS settings failure: transition fails and no PRODINFO update is called.
- Inject preparation commit failure: the same condition holds.
- Normal repeated Nextendo/Nintendo cycles still succeed.
- Preserve unrelated INI settings, comments and sysMMC PRODINFO configuration.
- Keep NAND-specific hosts selection, emuMMC-ID precedence and shared default.
- Compile the actual hosts builder with two server IPs: exactly one loopback
  mission rule; existing account, invitations, applet, game and NAT routes remain.

The SD/resource-service stubs test control flow, not the physical durability of
every device write. The existing config I/O fault tests cover the file writer.

## Limits requiring maintainer review

The serial shown in Nextendo is expected with the current identity policy.
DNS.mitm redirects matching hostnames; it is not an egress firewall. Some names,
including d4c, are intentionally not overridden, and a manual upstream proxy or
IP-based connection can use another path. This patch does not establish complete
Nintendo isolation, make all writes transactional or prove that any reported ban
was caused by this issue. Do not close #32 as fully resolved on this patch alone.

Blanking PRODINFO is not a ban guarantee either: Atmosphere documents possible
cached identity data. A broader default-deny policy needs separate compatibility
review; do not silently add broad Nintendo wildcard changes to this candidate.

## Physical acceptance with Soul's Switch

Collecting should review the remaining network policy before an online trial.
Use the CI `nextendo` artifact for the exact reviewed commit, keep its SHA256,
and install it separately from the normal NRO (for example
`sd:/switch/prelude-issue32-test.nro`). Keep copies of the relevant SD configs
and their recovery siblings. Do not publish console serials, certificates, tokens
or unredacted network logs in the PR.

1. Start offline with Wi-Fi disconnected. Confirm boot type, installed CFW and
   selected hosts path; on firmware 23.x the relevant DNS support starts in
   Atmosphere 1.12.1. Prelude does not upgrade the CFW itself.
2. Apply Nextendo, inspect the written files while offline and reboot. Confirm
   DNS.mitm is enabled and the selected hosts contain exactly the loopback mission
   rule plus the expected Nextendo routes. Confirm the sysMMC identity setting and
   the other NAND's files were not changed. The successful emuMMC path still sets
   `blank_prodinfo_emummc=0`; a visible serial is not an acceptance failure here.
3. Use a controlled network with external blocking of Nintendo destinations for
   the console and no independent upstream-resolving proxy. Verify the active
   DNS interception and actual destinations before allowing the planned Nextendo
   tests. If this containment cannot be established, stop at the offline checks;
   a risk-of-ban test does not require exposing an unbanned console.
4. Verify NSO opening, friends, invitations and one supported game. Confirm the
   mission uploader does not cause persistent stalls; missions/rewards themselves
   are deliberately unavailable under the loopback rule.
5. Disconnect Wi-Fi before switching to Nintendo mode. Inspect its block policy
   and the chosen emuMMC identity setting offline, reboot offline and repeat the
   cycle. Nintendo mode inside CFW is not a test of stock firmware safety.
6. Failure injection remains in the host harness. Do not remove the SD during
   writes or damage configuration files on the physical console to simulate it.

Record firmware/CFW versions, boot type, candidate hash, pass/fail and sanitized
observations. A successful trial is compatibility evidence, not proof against
future bans or all network paths.

## Primary references

- [Issue #32](https://github.com/NextendoNetwork/Prelude-Nextendo/issues/32)
- [Existing mission block PR #88](https://github.com/NextendoNetwork/Prelude-Nextendo/pull/88)
- [Atmosphere DNS semantics and selection](https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/features/dns_mitm.md)
- [Atmosphere PRODINFO caveat](https://github.com/Atmosphere-NX/Atmosphere/blob/master/config_templates/exosphere.ini)
- [Firmware 23 DNS support](https://github.com/Atmosphere-NX/Atmosphere/releases/tag/1.12.1)
