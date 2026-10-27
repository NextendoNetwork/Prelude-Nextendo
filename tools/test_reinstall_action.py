"""Compile the production manual-reinstall action with resource/UI service stubs."""
from pathlib import Path
import subprocess, sys, tempfile

root = Path(__file__).resolve().parents[1]
source = (root/'source/main.c').read_text(encoding='utf-8')
start = source.index('case RAIL_S3:')
end = source.index('case RAIL_S2:', start)
prefix = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
enum { CHOICE_NEXTENDO, CHOICE_NINTENDO, RAIL_S3, SCREEN_PICKER, SCREEN_PATCHES_REBOOT };
enum { STR_STATUS_SD_ERROR, STR_S3_DONE, STR_S3_CURRENT };
static bool success, changed, patchesUnchanged;
static int calls, current, screen, s3;
static char status[160];
static bool nextendo_provision_all_public(void) { ++calls; return success; }
static bool nextendo_provision_changed(void) { return changed; }
static void nextendo_s3_status(int *out) { (void)out; }
static const char *lang_str(int id) {
    return id==STR_STATUS_SD_ERROR ? "error" : id==STR_S3_DONE ? "installed" : "matching";
}
static void action(void) { switch (RAIL_S3) {
'''
main = r'''
} }
int main(void) {
    current=CHOICE_NEXTENDO;success=true;changed=false;screen=SCREEN_PICKER;
    action();assert(screen==SCREEN_PATCHES_REBOOT);assert(patchesUnchanged);
    assert(!strcmp(status,"matching"));assert(calls==1);
    changed=true;screen=SCREEN_PICKER;
    action();assert(screen==SCREEN_PATCHES_REBOOT);assert(!patchesUnchanged);
    assert(!strcmp(status,"installed"));
    success=false;screen=SCREEN_PICKER;
    action();assert(screen==SCREEN_PICKER);assert(!strcmp(status,"error"));
    current=CHOICE_NINTENDO;success=true;calls=0;screen=SCREEN_PICKER;
    action();assert(calls==0);assert(screen==SCREEN_PICKER);
    puts("PASS: actual manual action offers reboot for matching/changed patches, rejects failures and does nothing in Nintendo mode");
}
'''
with tempfile.TemporaryDirectory(prefix='prelude-reinstall-action-') as tmp:
    folder=Path(tmp);test=folder/'test.c'
    test.write_text(prefix+source[start:end]+main,encoding='utf-8')
    binary=folder/('test.exe' if sys.platform=='win32' else 'test')
    subprocess.run([sys.argv[1] if len(sys.argv)>1 else 'cc','-std=c11','-Wall','-Wextra','-Werror',
                    str(test),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
