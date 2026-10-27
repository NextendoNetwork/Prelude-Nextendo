"""Compile the actual hosts builder; verify closed Unity routing and managed refresh.
No console or external service is contacted.
"""
from pathlib import Path
import fnmatch
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "source/nextendo_apply.c").read_text(encoding="utf-8")
start = source.index("char *nextendo_hosts_build(")
builder = source[start:source.index("\nstatic bool commitConfig", start)]
prefix = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nextendo_hosts_refresh.h"
#define NEXTENDO_SERVER_IP_NNCSD2 "192.0.2.20"
'''
main = r'''
int main(int argc, char **argv) {
    assert(argc == 2);
    char *text = nextendo_hosts_build(argv[1]);
    assert(text);
    const char *mark = "NEXTENDO NETWORK - Atmosphere DNS-MITM";
    const char *old = "# NEXTENDO NETWORK - Atmosphere DNS-MITM\n192.0.2.1 api.braincloudservers.com\n";
    const char *custom = "192.0.2.2 user.example\n";
    assert(nextendo_hosts_refresh_action(old, strlen(old), text, mark) == HOSTS_REWRITE);
    assert(nextendo_hosts_refresh_action(text, strlen(text), text, mark) == HOSTS_KEEP_CURRENT);
    assert(nextendo_hosts_refresh_action(custom, strlen(custom), text, mark) == HOSTS_KEEP_NOT_OURS);
    fputs(text, stdout);
    free(text);
}
'''
hosts = ["player-auth.services.api.unity.com", "lobby.services.api.unity.com",
         "relay-allocations.services.api.unity.com", "qos-discovery.services.api.unity.com",
         "multiplay.services.api.unity.com", "matchmaker.services.api.unity.com",
         "wire.unity3d.com", "new-service.services.api.unity.com"]
with tempfile.TemporaryDirectory(prefix="prelude-gang-containment-") as directory:
    folder = Path(directory)
    src = folder / "test.c"
    binary = folder / ("test.exe" if sys.platform == "win32" else "test")
    src.write_text(prefix + builder + main, encoding="utf-8")
    subprocess.run([sys.argv[1] if len(sys.argv) > 1 else "cc", "-std=c11", "-Wall",
                    "-Wextra", "-Werror", "-I", str(root / "source"), str(src), "-o", str(binary)], check=True)
    for ip in ["192.0.2.1", "198.51.100.2"]:
        text = subprocess.check_output([str(binary), ip], text=True)
        rules = []
        for line in text.splitlines():
            parts = line.split("#", 1)[0].split()
            if len(parts) >= 2:
                rules.extend((pattern, parts[0]) for pattern in parts[1:])
        def destination(host):
            matches = [target for pattern, target in rules if fnmatch.fnmatchcase(host, pattern)]
            return matches[-1] if matches else None
        for host in hosts:
            assert destination(host) == "127.0.0.1", (host, destination(host))
        assert destination("api.braincloudservers.com") == ip
        assert destination("na.ultimatechickenhorseserver.com") == ip
        assert destination("unrelated.example") is None
        assert destination("other.unity3d.com") is None
print("PASS: seven observed Unity hosts + future service wildcard blocked; UCH selection and managed refresh preserved")
