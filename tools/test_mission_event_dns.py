"""Exercise the actual hosts generator and refresh policy, without libnx or network."""
from pathlib import Path
import fnmatch
import re
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "source/nextendo_apply.c").read_text(encoding="utf-8")
start = source.index("char *nextendo_hosts_build(")
brace = source.index("{", start)
depth, end = 1, brace + 1
while depth:
    depth += (source[end] == "{") - (source[end] == "}")
    end += 1

harness = r'''
#ifdef _WIN32
#define _CRT_SECURE_NO_WARNINGS
#endif
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nextendo_hosts.h"
#include "nextendo_hosts_refresh.h"
'''
main = r'''
int main(int argc, char **argv) {
    assert(argc == 3);
    char *text = nextendo_hosts_build(argv[1]);
    assert(text != NULL);
    const char *rule = "127.0.0.1 fw-api.lp1.nso.nintendo.net\n";
    char *found = strstr(text, rule);
    if (found) {
        char *old = malloc(strlen(text) + 1);
        assert(old != NULL);
        strcpy(old, text);
        size_t offset = (size_t)(found - text);
        memmove(old + offset, old + offset + strlen(rule), strlen(old + offset + strlen(rule)) + 1);
        assert(nextendo_hosts_refresh_action(old, strlen(old), text, NEXTENDO_HOSTS_HEADER_MARK) == HOSTS_REWRITE);
        assert(nextendo_hosts_refresh_action(text, strlen(text), text, NEXTENDO_HOSTS_HEADER_MARK) == HOSTS_KEEP_CURRENT);
        const char *custom = "127.0.0.1 localhost\n";
        assert(nextendo_hosts_refresh_action(custom, strlen(custom), text, NEXTENDO_HOSTS_HEADER_MARK) == HOSTS_KEEP_NOT_OURS);
        free(old);
    }
    FILE *out = fopen(argv[2], "wb");
    assert(out != NULL);
    assert(fwrite(text, 1, strlen(text), out) == strlen(text));
    assert(fclose(out) == 0);
    free(text);
    return 0;
}
'''
config = (root / "source/nextendo_config.h").read_text(encoding="utf-8")
nncs2 = re.search(r'#define NEXTENDO_SERVER_IP_NNCSD2\s+"([^"]+)"', config).group(1)

with tempfile.TemporaryDirectory(prefix="prelude-mission-dns-") as directory:
    folder = Path(directory)
    test = folder / "test.c"
    test.write_text(harness + source[start:end] + main, encoding="utf-8")
    binary = folder / ("test.exe" if sys.platform == "win32" else "test")
    subprocess.run([sys.argv[1] if len(sys.argv) > 1 else "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(root / "source"), str(test), "-o", str(binary)], check=True)
    for ip in ("192.0.2.10", "192.0.2.20"):
        generated = folder / "hosts.txt"
        subprocess.run([str(binary), ip, str(generated)], check=True)
        rules = []
        for line in generated.read_text(encoding="utf-8").splitlines():
            fields = line.split("#", 1)[0].split()
            if len(fields) > 1:
                rules.extend((pattern.replace("%", "lp1"), fields[0]) for pattern in fields[1:])

        def resolve(host):
            # Atmosphere: '*' spans any number of characters; last match wins.
            matches = [address for pattern, address in rules if fnmatch.fnmatchcase(host, pattern)]
            return matches[-1] if matches else None

        assert resolve("fw-api.lp1.nso.nintendo.net") == "127.0.0.1", "mission events still escape Nextendo DNS rules"
        assert sum(pattern == "fw-api.lp1.nso.nintendo.net" for pattern, _ in rules) == 1
        for host in (
            "lp1.nso.nintendo.net", "app.lp1.five.nintendo.net", "accounts.nintendo.com",
            "m-lp1.baas.nintendo.com", "example.baas.nintendo.com",
            "gamesync.npln.nintendo.net", "t-7b4e32ca-lp1.lp1.t.npln.srv.nintendo.net",
            "g23380901-lp1.s.n.srv.nintendo.net", "bcat-list-lp1.cdn.nintendo.net",
            "bvc-hac-lp1.cdn.nintendo.net", "receive-lp1.dg.srv.nintendo.net",
            "public-ubiservices.ubi.com", "jd.ubisoft.com", "api.braincloudservers.com",
            "conntest.nintendowifi.net",
        ):
            assert resolve(host) == ip, "existing routing changed: " + host
        assert resolve("nncs2-lp1.n.n.srv.nintendo.net") == nncs2
        assert resolve("g2b309e01-lp1.s.n.srv.nintendo.net") == nncs2
        for host in ("other.lp1.nso.nintendo.net", "fw-api.lp2.nso.nintendo.net",
                     "example.nintendo.net", "aqua.hac.lp1.d4c.nintendo.net", "example.org"):
            assert resolve(host) is None, "new rule is too broad: " + host

print("PASS: mission host blocked; account, invitations, NSO, games, NAT, unrelated DNS and refresh policy preserved")
