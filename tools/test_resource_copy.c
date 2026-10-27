// Exercise the production binary-resource installer with real temporary files.
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int fail_write, fail_close, fail_rename, fail_commit, fail_read, corrupt_write;
static int writes, closes, renames, commits, reads;
static FILE *read_fault;
static size_t injected_read(void *p,size_t s,size_t n,FILE *f) {
    if (++reads == fail_read) { read_fault=f; return 0; }
    return fread(p,s,n,f);
}
static int injected_error(FILE *f) { return f==read_fault || ferror(f); }
static size_t injected_write(const void *p,size_t s,size_t n,FILE *f) {
    if (++writes == fail_write) return fwrite(p,s,n ? n-1 : 0,f);
    if (corrupt_write && s==1 && n>0) {
        unsigned char first=((const unsigned char *)p)[0]^1;
        return fwrite(&first,1,1,f)+fwrite((const unsigned char *)p+1,1,n-1,f);
    }
    return fwrite(p,s,n,f);
}
static int injected_close(FILE *f) { int rc=fclose(f);return ++closes==fail_close ? EOF : rc; }
static int injected_rename(const char *a,const char *b) { return ++renames==fail_rename ? -1 : rename(a,b); }
#define fwrite injected_write
#define fclose injected_close
#define rename injected_rename
#define fread injected_read
#define ferror injected_error
#include "../source/prelude_resource.c"
#undef fwrite
#undef fclose
#undef rename
#undef fread
#undef ferror
static const unsigned char previous[]={ 'P','A','T','C','H',0,0xff,'E','O','F' };
static const unsigned char expected[]={ 'P','A','T','C','H',0,0xfe,0,1,'E','O','F' };
static bool commit(void) { return ++commits != fail_commit; }
static void write_bytes(const char *path,const void *bytes,size_t n) {
    FILE *f=fopen(path,"wb");assert(f);assert(fwrite(bytes,1,n,f)==n);assert(!fclose(f));
}
static void matches(const char *path,const void *bytes,size_t n) {
    unsigned char buffer[64];FILE *f=fopen(path,"rb");assert(f);
    assert(fread(buffer,1,sizeof(buffer),f)==n);assert(!memcmp(buffer,bytes,n));assert(!fclose(f));
}
static void reset(void) {
    fail_write=fail_close=fail_rename=fail_commit=writes=closes=renames=commits=0;
    fail_read=corrupt_write=reads=0;read_fault=NULL;
    remove("installed.ips");remove("installed.ips.prelude-new");remove("installed.ips.prelude-backup");
    write_bytes("source.ips",expected,sizeof(expected));write_bytes("installed.ips",previous,sizeof(previous));
}
int main(void) {
    reset();fail_write=1;
    assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_FAILED);
    matches("installed.ips",previous,sizeof(previous));
    for (int i=1;i<=6;i++) {
        reset();fail_read=i;
        assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_FAILED);
        matches("installed.ips",previous,sizeof(previous));
    }
    reset();corrupt_write=1;
    assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_FAILED);
    matches("installed.ips",previous,sizeof(previous));
    // Both comparison closes and both staging-copy closes must fail safely.
    for (int i=1;i<=4;i++) {
        reset();fail_close=i;
        assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_FAILED);
        matches("installed.ips",previous,sizeof(previous));
    }
    for (int i=1;i<=2;i++) {
        reset();fail_rename=i;
        assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_FAILED);
        matches("installed.ips",previous,sizeof(previous));
    }
    for (int i=1;i<=3;i++) {
        reset();fail_commit=i;
        assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_FAILED);
        matches("installed.ips",previous,sizeof(previous));
    }
    reset();assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_UPDATED);
    matches("installed.ips",expected,sizeof(expected));matches("installed.ips.prelude-backup",previous,sizeof(previous));
    writes=renames=commits=0;
    assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_CURRENT);
    assert(!writes&&!renames&&!commits);matches("installed.ips",expected,sizeof(expected));
    reset();assert(remove("installed.ips")==0);
    assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_UPDATED);
    matches("installed.ips",expected,sizeof(expected));
    // Recover a previously interrupted rename instead of discarding its old file.
    reset();assert(rename("installed.ips","installed.ips.prelude-backup")==0);fail_write=1;
    assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_FAILED);
    matches("installed.ips",previous,sizeof(previous));
    reset();assert(prelude_copy_resource("missing-source","installed.ips",commit)==PRELUDE_COPY_FAILED);
    matches("installed.ips",previous,sizeof(previous));
    // Zero-byte boot flags and binary NUL bytes are legitimate resources.
    reset();write_bytes("source.ips","",0);
    assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_UPDATED);
    matches("installed.ips","",0);
    reset();unsigned char large[9001];memset(large,0xa5,sizeof(large));large[5000]=0;
    write_bytes("source.ips",large,sizeof(large));
    assert(prelude_copy_resource("source.ips","installed.ips",commit)==PRELUDE_COPY_UPDATED);
    assert(resource_equal("source.ips","installed.ips")==1);
    puts("PASS: binary patches, no-op reinstall, read/write/close/rename/commit failures, readback verification and interrupted-copy recovery");
    remove("source.ips");remove("installed.ips");remove("installed.ips.prelude-new");remove("installed.ips.prelude-backup");
}
