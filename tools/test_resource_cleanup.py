"""Exercise the real managed-tree cleanup, including resource recovery siblings."""
from pathlib import Path
import subprocess, sys, tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'source/nextendo_apply.c').read_text(encoding='utf-8')
start = source.index('static bool removeTreeRomfs(')
end = source.index('\n}', start) + 2
prefix = r'''
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include "prelude_resource.h"
#define FS_MAX_PATH 4096
'''
main = r'''
int main(int argc,char **argv) {
    if (argc!=3) return 2;
    return removeTreeRomfs(argv[1],argv[2]) ? 0 : 1;
}
'''
with tempfile.TemporaryDirectory(prefix='prelude-resource-cleanup-') as tmp:
    folder = Path(tmp)
    test = folder / 'cleanup.c'
    test.write_text(prefix + source[start:end] + main, encoding='utf-8')
    binary = folder / ('cleanup.exe' if sys.platform == 'win32' else 'cleanup')
    subprocess.run([sys.argv[1] if len(sys.argv)>1 else 'cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-I', str(root/'source'), str(test), str(root/'source/prelude_resource.c'),
                    '-o', str(binary)], check=True)
    romfs, sd = folder/'romfs', folder/'sd'
    resources = ('exefs_patches/managed/a.ips', 'contents/managed/romfs/browser.pem')
    for resource in resources:
        src, dst = romfs/resource, sd/resource
        src.parent.mkdir(parents=True, exist_ok=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(b'expected\x00resource')
        for suffix in ('', '.prelude-new', '.prelude-backup'):
            Path(str(dst)+suffix).write_bytes(b'test resource')
    user_file = sd/'exefs_patches/user-patch.ips'
    user_file.write_bytes(b'unrelated user patch')
    user_backup = sd/'exefs_patches/user-patch.ips.prelude-backup'
    user_backup.write_bytes(b'unrelated recovery file')
    subprocess.run([str(binary), str(romfs), str(sd)], check=True)
    assert not (sd/'exefs_patches/managed').exists()
    assert not (sd/'contents').exists()
    assert user_file.read_bytes()==b'unrelated user patch'
    assert user_backup.read_bytes()==b'unrelated recovery file'
    # Idempotent cleanup of absent managed paths must still succeed.
    subprocess.run([str(binary), str(romfs), str(sd)], check=True)
    # Staging/recovery files alone must also be removed without an active file.
    dst = sd/resources[0]
    dst.parent.mkdir(parents=True)
    Path(str(dst)+'.prelude-backup').write_bytes(b'old resource')
    subprocess.run([str(binary), str(romfs), str(sd)], check=True)
    assert not dst.parent.exists()
    print('PASS: real resource-tree cleanup removes managed backups/staging and empty folders, preserving user files')
