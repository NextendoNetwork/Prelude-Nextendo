// Copyright (C) 2026 Nextendo Network. See LICENSE.md.
#include "prelude_resource.h"
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

// -1: read/open error; 0: different/missing destination; 1: identical bytes.
static int resource_equal(const char *source, const char *destination) {
    FILE *a = fopen(source, "rb");
    if (!a) return -1;
    FILE *b = fopen(destination, "rb");
    if (!b) { int saved = errno; fclose(a); return saved == ENOENT ? 0 : -1; }
    unsigned char x[4096], y[4096];
    int same = 1;
    for (;;) {
        size_t nx = fread(x, 1, sizeof(x), a), ny = fread(y, 1, sizeof(y), b);
        if (ferror(a) || ferror(b)) { same = -1; break; }
        if (nx != ny || memcmp(x, y, nx)) { same = 0; break; }
        if (nx < sizeof(x)) break;
    }
    if (fclose(a)) same = -1;
    if (fclose(b)) same = -1;
    return same;
}

static int resource_exists(const char *path) {
    struct stat st;
    if (stat(path, &st) == 0) return S_ISREG(st.st_mode) ? 1 : -1;
    return errno == ENOENT ? 0 : -1;
}

bool prelude_remove_resource(const char *destination) {
    const char *suffixes[] = { "", ".prelude-new", ".prelude-backup" };
    bool ok = true;
    for (size_t i = 0; i < sizeof(suffixes) / sizeof(suffixes[0]); ++i) {
        char path[1024];
        if (snprintf(path, sizeof(path), "%s%s", destination, suffixes[i]) >= (int)sizeof(path)) {
            ok = false;
            continue;
        }
        int exists = resource_exists(path);
        if (exists < 0 || (exists && remove(path))) ok = false;
    }
    return ok;
}

int prelude_copy_resource(const char *source, const char *destination, bool (*commit)(void)) {
    char staged[1024], backup[1024];
    if (snprintf(staged, sizeof(staged), "%s.prelude-new", destination) >= (int)sizeof(staged) ||
        snprintf(backup, sizeof(backup), "%s.prelude-backup", destination) >= (int)sizeof(backup))
        return PRELUDE_COPY_FAILED;
    int had_old = resource_exists(destination), had_backup = resource_exists(backup);
    if (had_old < 0 || had_backup < 0 || resource_exists(staged) < 0) return PRELUDE_COPY_FAILED;
    // Recover an interrupted promotion before attempting another installation.
    if (!had_old && had_backup) {
        if (rename(backup, destination) || !commit()) return PRELUDE_COPY_FAILED;
        had_old = 1; had_backup = 0;
    }
    int equal = resource_equal(source, destination);
    if (equal < 0) return PRELUDE_COPY_FAILED;
    if (equal) return PRELUDE_COPY_CURRENT;
    FILE *in = fopen(source, "rb");
    if (!in) return PRELUDE_COPY_FAILED;
    FILE *out = fopen(staged, "wb");
    if (!out) { fclose(in); return PRELUDE_COPY_FAILED; }
    unsigned char buffer[4096];
    bool ok = true;
    size_t n;
    while ((n = fread(buffer, 1, sizeof(buffer), in)) != 0) {
        if (fwrite(buffer, 1, n, out) != n) { ok = false; break; }
    }
    if (ferror(in) || ferror(out)) ok = false;
    if (fclose(in)) ok = false;
    if (fclose(out)) ok = false;
    if (!ok || !commit() || resource_equal(source, staged) != 1) {
        remove(staged);
        return PRELUDE_COPY_FAILED;
    }
    if (had_backup && (remove(backup) || !commit())) return PRELUDE_COPY_FAILED;
    if (had_old && rename(destination, backup)) return PRELUDE_COPY_FAILED;
    if (!commit() || rename(staged, destination)) {
        if (had_old) rename(backup, destination);
        commit();
        return PRELUDE_COPY_FAILED;
    }
    if (!commit()) {
        if (rename(destination, staged) == 0 && had_old) rename(backup, destination);
        commit();
        return PRELUDE_COPY_FAILED;
    }
    return PRELUDE_COPY_UPDATED;
}
