"""Exercise production mode switching with an in-memory SD and resource-service stubs."""
from pathlib import Path
import subprocess,sys,tempfile
root=Path(__file__).resolve().parents[1]
source=(root/'source/nextendo_apply.c').read_text(encoding='utf-8')
def function(name,decl):
 start=source.index(decl+name+'(');p=source.index('{',start)+1;depth=1
 while depth:
  depth+=(source[p]=='{')-(source[p]=='}');p+=1
 return source[start:p]
prefix=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "prelude_dns_block.h"
#include "prelude_prodinfo.h"
#define FS_MAX_PATH 1024
#define NEXTENDO_HOSTS_SYSMMC "sdmc:/atmosphere/hosts/sysmmc.txt"
#define NEXTENDO_HOSTS_EMUMMC "sdmc:/atmosphere/hosts/emummc.txt"
#define NEXTENDO_HOSTS_DEFAULT "sdmc:/atmosphere/hosts/default.txt"
#define NEXTENDO_HOSTS_DIR "sdmc:/atmosphere/hosts"
#define NEXTENDO_BACKUP_DIR "sdmc:/switch/prelude_hosts_backup"
#define NEXTENDO_HOSTS_HEADER_MARK "NEXTENDO NETWORK - Atmosphere DNS-MITM"
#define NEXTENDO_SERVER_IP_DEFAULT "51.178.29.194"
#define NEXTENDO_SERVER_IP_ALT "3.135.232.168"
#define NEXTENDO_CAPTURE_FLAG "capture"
#define NEXTENDO_SETTINGS_INI "settings.ini"
#define NEXTENDO_EXOSPHERE_INI "sdmc:/exosphere.ini"
#define SETTINGS_DIR "."
#define ACCOUNT_LINK_DIR "account-link"
#define ACCOUNT_LINK_FLAGS "account-link/flags"
#define ACCOUNT_LINK_BOOTFLAG "account-link/flags/boot2.flag"
#define R_FAILED(x) ((x)!=0)
typedef enum {BOOT_UNKNOWN=-1,BOOT_SYSMMC,BOOT_EMUMMC} BootType;
static BootType boot=BOOT_EMUMMC;
static BootType nextendo_detect_boot(void){return boot;}
struct entry{char path[1024];char text[4096];};
static struct entry files[32];static int count;
static const char *get(const char*p){for(int i=0;i<count;i++)if(!strcmp(files[i].path,p))return files[i].text;return NULL;}
static void put(const char*p,const char*t){int i=0;while(i<count&&strcmp(files[i].path,p))i++;assert(i<32);if(i==count)count++;snprintf(files[i].path,1024,"%s",p);snprintf(files[i].text,4096,"%s",t);}
static bool fileExists(const char*p){return get(p)!=NULL;}
static bool fileHas(const char*p,const char*n){return get(p)&&strstr(get(p),n);}
static bool prelude_read_config(const char*p,char**t,size_t*n){const char*s=get(p);*t=s?strdup(s):NULL;*n=s?strlen(s):0;return true;}
static bool writeTextFile(const char*p,const char*t){put(p,t);return true;}
static bool configCommitFail, dnsSettingsFail;
static bool commitConfig(void){return !configCommitFail;}
static bool modeConfigReadable(void){return true;}
static int ensureDir(const char*p){(void)p;return 0;}
static void nextendo_trace(const char*p){(void)p;}
static bool nextendo_provision_all(void){return true;}
static bool nextendo_news_patch_for_console(void){return false;}
static int nextendo_news_purge(const char*p){(void)p;return 0;}
static void nextendo_purge_leaks(void){}
static int nextendo_purge_stale(void){return 0;}
static bool cleanupFails;
static const char *const NEXTENDO_STALE_FILES[]={"old-cert-resource"};
static bool removeTreeRomfs(const char*a,const char*b){(void)a;(void)b;return !cleanupFails;}
static int fakeRemove(const char *path){
 if(cleanupFails && strstr(path,ACCOUNT_LINK_DIR)){errno=EIO;return -1;}
 for(int i=0;i<count;i++)if(!strcmp(files[i].path,path)){files[i]=files[--count];return 0;}
 errno=ENOENT;return -1;
}
static int fakeRmdir(const char *path){(void)path;return 0;}
#define remove fakeRemove
#define rmdir fakeRmdir
static bool prelude_remove_resource(const char *path){
 const char *suffixes[]={"",".prelude-new",".prelude-backup"};bool ok=true;
 for(unsigned i=0;i<3;i++){
  char item[1024];snprintf(item,sizeof(item),"%s%s",path,suffixes[i]);
  if(fakeRemove(item)!=0&&errno!=ENOENT)ok=false;
 }
 return ok;
}
bool nextendo_account_link_remove(void);
static int prodinfoWrites;
static bool iniSetBlankProdinfoEmummc(bool b){(void)b;prodinfoWrites++;return true;}
static bool iniSetDnsMitm(bool a,bool b){(void)a;(void)b;return !dnsSettingsFail;}
static bool nextendo_backup_use_for_nintendo(void){return true;}
static bool captureFlagPresent(void){return false;}
static bool capturePatchesPresent(void){return false;}
static char*nextendo_hosts_build(const char*ip){char text[256];snprintf(text,sizeof(text),"%s\n%s accounts.nintendo.com\n",NEXTENDO_HOSTS_HEADER_MARK,ip);return strdup(text);}
'''
names=[('activeHostsPath','static bool '),('activeHostsBackupPath','static const char *'),('copyFileRaw','static bool '),('backupCandidateOk','static bool '),('nextendo_current_mode','int '),('iniSetNetworkMitm','static bool '),('nextendo_account_link_remove','bool '),('prodinfoFlag','static int '),('nextendo_prodinfo_emummc_state','int '),('nextendo_account_link_is_recommended','bool '),('nextendo_apply_nextendo_ip','bool '),('applyNintendoPolicy','static bool '),('nextendo_apply_nintendo_ex','bool ')]
# Skip forward declarations and locate the body definition, not the prototype.
def definition(name,decl):
 global source
 needle=decl+name+'(';start=0
 while True:
  start=source.index(needle,start);semi=source.find(';',start);brace=source.find('{',start)
  if brace<semi:break
  start=semi+1
 p=brace+1;depth=1
 while depth:
  depth+=(source[p]=='{')-(source[p]=='}');p+=1
 return source[start:p]
main=r'''
int main(void){
 // An unsuccessful transition must not attempt to disable identity blanking.
 // In particular, returning false only after writing exosphere is too late.
 boot=BOOT_EMUMMC;prodinfoWrites=0;dnsSettingsFail=true;
 assert(!nextendo_apply_nextendo_ip(NEXTENDO_SERVER_IP_DEFAULT));assert(prodinfoWrites==0);
 dnsSettingsFail=false;configCommitFail=true;
 assert(!nextendo_apply_nextendo_ip(NEXTENDO_SERVER_IP_DEFAULT));assert(prodinfoWrites==0);
 configCommitFail=false;
 put(NEXTENDO_EXOSPHERE_INI,"[exosphere]\nblank_prodinfo_sysmmc=1\nblank_prodinfo_emummc=0\n");
 boot=BOOT_EMUMMC;assert(!nextendo_account_link_is_recommended());
 boot=BOOT_SYSMMC;assert(nextendo_account_link_is_recommended());
 put(NEXTENDO_EXOSPHERE_INI,"[exosphere]\nblank_prodinfo_sysmmc=0\nblank_prodinfo_emummc=1\n");
 boot=BOOT_EMUMMC;assert(nextendo_account_link_is_recommended());
 boot=BOOT_SYSMMC;assert(!nextendo_account_link_is_recommended());
 boot=BOOT_UNKNOWN;assert(!nextendo_account_link_is_recommended());
 boot=BOOT_EMUMMC;
 put(NEXTENDO_EXOSPHERE_INI,"[exosphere]\n# blank_prodinfo_emummc=1\nblank_prodinfo_emummc = 0\n");
 assert(nextendo_prodinfo_emummc_state()==0);
 put(NEXTENDO_EXOSPHERE_INI,"[exosphere]\nblank_prodinfo_emummc = 1 ; saved\n");
 assert(nextendo_prodinfo_emummc_state()==1);
 put(NEXTENDO_EXOSPHERE_INI,"[exosphere]\nblank_prodinfo_emummc=invalid\n");
 assert(nextendo_prodinfo_emummc_state()==-1);
 const char *emu=NEXTENDO_HOSTS_EMUMMC,*sys=NEXTENDO_HOSTS_SYSMMC,*def=NEXTENDO_HOSTS_DEFAULT;
 put(sys,"# Nintendo sysMMC user file\n");put(def,"# shared user defaults\n");
 put("sdmc:/emuMMC/emummc.ini","[emummc]\nenabled=1\nid=0x0001\n");
 for(int i=0;i<4;i++){
  assert(nextendo_apply_nextendo_ip(NEXTENDO_SERVER_IP_DEFAULT));assert(nextendo_current_mode()==0);
  assert(!strcmp(get(sys),"# Nintendo sysMMC user file\n"));assert(!strcmp(get(def),"# shared user defaults\n"));
  assert(nextendo_apply_nintendo_ex(true));assert(nextendo_current_mode()==1);
  assert(!strstr(get(emu),NEXTENDO_SERVER_IP_DEFAULT));
  assert(strstr(get(emu),"127.0.0.1 nintendo.*"));
  assert(nextendo_apply_nintendo_ex(false));assert(strstr(get(emu),"127.0.0.1 nintendo.*"));
 }
 // Removing account linking must preserve both identity configuration values.
 const char *identity="[exosphere]\nblank_prodinfo_sysmmc=1\nblank_prodinfo_emummc=1\n";
 put("sdmc:/exosphere.ini",identity);
 put(ACCOUNT_LINK_BOOTFLAG,"flag");put(ACCOUNT_LINK_DIR "/mitm.lst","ssl");put(ACCOUNT_LINK_DIR "/exefs.nsp","synthetic");
 put(ACCOUNT_LINK_DIR "/exefs.nsp.prelude-backup","old synthetic");
 put(ACCOUNT_LINK_DIR "/mitm.lst.prelude-new","staged synthetic");
 assert(nextendo_account_link_remove());assert(!fileExists(ACCOUNT_LINK_BOOTFLAG));
 assert(!fileExists(ACCOUNT_LINK_DIR "/exefs.nsp.prelude-backup"));
 assert(!fileExists(ACCOUNT_LINK_DIR "/mitm.lst.prelude-new"));
 assert(!strcmp(get("sdmc:/exosphere.ini"),identity));
 put(ACCOUNT_LINK_BOOTFLAG,"flag");cleanupFails=true;
 assert(!nextendo_account_link_remove());assert(!strcmp(get("sdmc:/exosphere.ini"),identity));
 cleanupFails=false;assert(nextendo_account_link_remove());
 // The other NAND's Nextendo mode must not change this NAND's indicator.
 put(sys,NEXTENDO_SERVER_IP_DEFAULT);assert(nextendo_current_mode()==1);
 // A legacy Nextendo default cannot take over Nintendo after a switch.
 put(def,NEXTENDO_SERVER_IP_DEFAULT);assert(nextendo_apply_nintendo_ex(true));assert(nextendo_current_mode()==1);
 // Atmosphere's emuMMC-ID-specific file takes precedence over the generic file.
 const char *specific="sdmc:/atmosphere/hosts/emummc_0001.txt";
 put(specific,"# custom per-emummc file\n");
 assert(nextendo_apply_nextendo_ip(NEXTENDO_SERVER_IP_DEFAULT));assert(fileHas(specific,NEXTENDO_SERVER_IP_DEFAULT));
 assert(!fileHas(emu,NEXTENDO_SERVER_IP_DEFAULT));
 assert(nextendo_apply_nintendo_ex(true));assert(strstr(get(specific),"# custom per-emummc file\n"));assert(strstr(get(specific),"127.0.0.1 nintendo.*"));
 assert(!strcmp(get(def),NEXTENDO_SERVER_IP_DEFAULT));assert(!strcmp(get(sys),NEXTENDO_SERVER_IP_DEFAULT));
 boot=BOOT_SYSMMC;prodinfoWrites=0;
 assert(nextendo_apply_nextendo_ip(NEXTENDO_SERVER_IP_DEFAULT));assert(prodinfoWrites==0);
 assert(nextendo_apply_nintendo_ex(true));assert(prodinfoWrites==0);assert(nextendo_current_mode()==1);
 assert(nextendo_apply_nextendo_ip(NEXTENDO_SERVER_IP_DEFAULT));cleanupFails=true;
 assert(!nextendo_apply_nintendo_ex(true));assert(nextendo_current_mode()==0);
 cleanupFails=false;assert(nextendo_apply_nintendo_ex(true));
 assert(applyNintendoPolicy(true,false));assert(!strstr(get(sys),"PRELUDE NINTENDO DNS BLOCK"));
 assert(nextendo_apply_nintendo_ex(false));assert(strstr(get(sys),"PRELUDE NINTENDO DNS BLOCK"));
 boot=BOOT_UNKNOWN;int before=count;
 assert(!nextendo_apply_nextendo_ip(NEXTENDO_SERVER_IP_DEFAULT));assert(!nextendo_apply_nintendo_ex(true));assert(before==count);
 puts("PASS: repeated mode switches; NAND isolation; shared default preserved; emuMMC ID precedence; unknown boot refused; sysMMC does not alter emuMMC PRODINFO");
}
'''
with tempfile.TemporaryDirectory(prefix='prelude-mode-') as directory:
 folder=Path(directory);test=folder/'test.c';binary=folder/('test.exe' if sys.platform=='win32' else 'test')
 test.write_text(prefix+'\n'.join(definition(n,d) for n,d in names)+main,encoding='utf-8')
 subprocess.run([sys.argv[1] if len(sys.argv)>1 else 'cc','-std=gnu11','-Wall','-Wextra','-Werror','-I',str(root/'source'),str(test),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],cwd=folder,check=True)
