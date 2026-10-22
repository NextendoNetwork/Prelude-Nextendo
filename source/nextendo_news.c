// Prelude, Nintendo Switch homebrew for the Nextendo Network.
// See LICENSE.md for the full terms, or <https://polyformproject.org/licenses/shield/1.0.0>.

// ============================================================
//  Actualites du menu HOME (News) a chaque bascule de mode.
//
//  Les actualites telechargees vivent dans deux sauvegardes systeme du module bcat
//  (010000000000000C), relevees sur une sysNAND 22.5.0 le 04/10/2026 :
//    0x8000000000000090 « news »     : data/*.msgpack, un fichier par article telecharge.
//    0x8000000000000091 « news-sys » : news.v3.db (l'index), history.bin (les articles deja
//                                      vus, jamais retelecharges), passphrase.bin, id.bin, task.bin.
//
//  Purger = vider data/ et retirer news.v3.db + history.bin. passphrase.bin n'est JAMAIS
//  touche : la cle de dechiffrement des actualites en derive.
//
//  Mode Nextendo : purge seulement si le patch nextendo_bcat_signature couvre le module bcat
//  de CETTE console (sinon nos actualites ne s'affichent pas : on garde celles de Nintendo).
//  Mode Nintendo : purge toujours, les actualites de Nintendo se retelechargent au demarrage.
//  Chaque etape est tracee dans sdmc:/prelude_trace.txt.
// ============================================================
#include <switch.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>

#include "nextendo_apply.h"
#include "nextendo_news.h"

#define BCAT_PROGRAM_ID   0x010000000000000CULL
#define NEWS_SAVE_DATA    0x8000000000000090ULL
#define NEWS_SAVE_SYS     0x8000000000000091ULL
#define NEWS_PATCH_DIR    "romfs:/sd/atmosphere/exefs_patches/nextendo_bcat_signature"

static void tracef(const char *fmt, ...) {
    char ligne[256];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(ligne, sizeof(ligne), fmt, ap);
    va_end(ap);
    nextendo_trace(ligne);
}

// Build-id du module bcat en cours d'execution, en 40 hex majuscules.
static bool bcatBuildId(char out[41]) {
    bool ok = false;
    if (R_FAILED(pmdmntInitialize())) return false;
    if (R_SUCCEEDED(ldrDmntInitialize())) {
        u64 pid = 0;
        if (R_SUCCEEDED(pmdmntGetProcessId(&pid, BCAT_PROGRAM_ID))) {
            LoaderModuleInfo mods[8];
            s32 n = 0;
            if (R_SUCCEEDED(ldrDmntGetProcessModuleInfo(pid, mods, 8, &n)) && n > 0) {
                for (int i = 0; i < 20; i++) sprintf(out + i * 2, "%02X", mods[0].build_id[i]);
                out[40] = 0;
                ok = true;
            }
        }
        ldrDmntExit();
    }
    pmdmntExit();
    return ok;
}

bool nextendo_news_patch_for_console(void) {
    char id[41];
    if (!bcatBuildId(id)) {
        nextendo_trace("news: build-id bcat illisible");
        return false;
    }
    char p1[160], p2[160];
    struct stat st;
    snprintf(p1, sizeof(p1), "%s/%s.ips", NEWS_PATCH_DIR, id);
    snprintf(p2, sizeof(p2), "%s/%s000000000000000000000000.ips", NEWS_PATCH_DIR, id);
    bool ok = stat(p1, &st) == 0 || stat(p2, &st) == 0;
    tracef("news: bcat %s, patch %s", id, ok ? "present" : "absent pour ce firmware");
    return ok;
}

// Vide le dossier d'une sauvegarde montee (fichiers seulement).
static int viderDossier(const char *dossier) {
    DIR *d = opendir(dossier);
    if (!d) return 0;
    int n = 0;
    struct dirent *e;
    char chemin[512];
    while ((e = readdir(d)) != NULL) {
        if (e->d_name[0] == '.') continue;
        snprintf(chemin, sizeof(chemin), "%s/%s", dossier, e->d_name);
        if (remove(chemin) == 0) n++;
    }
    closedir(d);
    return n;
}

static bool monter(u64 id, const char *dev) {
    FsFileSystem fs;
    Result rc = fsOpen_SystemSaveData(&fs, FsSaveDataSpaceId_System, id, (AccountUid){0});
    if (R_FAILED(rc)) {
        tracef("news: ouverture %016lX refusee rc=0x%x", id, rc);
        return false;
    }
    if (fsdevMountDevice(dev, fs) < 0) {
        fsFsClose(&fs);
        tracef("news: montage %016lX impossible", id);
        return false;
    }
    return true;
}

// Vide le stockage par le service des actualites lui-meme : ses sauvegardes sont montees en
// permanence par le module bcat, les ouvrir depuis Prelude rend 2002-0007 (cible verrouillee,
// mesure le 04/10 sur sysNAND 22.5.0). news:a (tous droits) -> IServiceCreator::CreateNewsService
// (0) -> INewsService::ClearStorage (40200), d'apres switchbrew.
static Result viderParService(void) {
    Service createur, news;
    Result rc = smGetService(&createur, "news:a");
    if (R_FAILED(rc)) return rc;
    rc = serviceDispatch(&createur, 0, .out_num_objects = 1, .out_objects = &news);
    if (R_SUCCEEDED(rc)) {
        rc = serviceDispatch(&news, 40200);
        serviceClose(&news);
    }
    serviceClose(&createur);
    return rc;
}

// Reabonne la console aux chaines suivies d'office par le menu HOME : INewsService (40101)
// RequestAutoSubscription(u64 title id), lu dans le module bcat 22.5.0 (un seul argument de 8
// octets). ClearStorage efface ces abonnements et la console ne les recree pas d'elle-meme :
// sans ca, plus aucun telechargement des actualites Nextendo (constate le 04/10).
Result nextendo_news_resubscribe(void) {
    Service createur, news;
    Result rc = smGetService(&createur, "news:a");
    if (R_SUCCEEDED(rc)) {
        rc = serviceDispatch(&createur, 0, .out_num_objects = 1, .out_objects = &news);
        if (R_SUCCEEDED(rc)) {
            const u64 home = 0x0100000000001000ULL;
            rc = serviceDispatchIn(&news, 40101, home);
            serviceClose(&news);
        }
        serviceClose(&createur);
    }
    tracef("news: RequestAutoSubscription(0100000000001000) rc=0x%x", rc);
    return rc;
}

bool nextendo_news_purge(const char *mode) {
    tracef("news: purge (%s)", mode);
    Result rcSrv = viderParService();
    tracef("news: ClearStorage rc=0x%x", rcSrv);
    if (R_SUCCEEDED(rcSrv)) {
        nextendo_news_resubscribe();
        return true;
    }
    bool ok = true;
    if (monter(NEWS_SAVE_DATA, "nxnews")) {
        int n = viderDossier("nxnews:/data");
        Result rc = fsdevCommitDevice("nxnews");
        fsdevUnmountDevice("nxnews");
        tracef("news: %d article(s) retire(s), commit rc=0x%x", n, rc);
        ok = ok && R_SUCCEEDED(rc);
    } else {
        ok = false;
    }
    if (monter(NEWS_SAVE_SYS, "nxnewss")) {
        int a = remove("nxnewss:/news.v3.db") == 0;
        int b = remove("nxnewss:/history.bin") == 0;
        Result rc = fsdevCommitDevice("nxnewss");
        fsdevUnmountDevice("nxnewss");
        tracef("news: index %s, historique %s, commit rc=0x%x", a ? "retire" : "absent", b ? "retire" : "absent", rc);
        ok = ok && R_SUCCEEDED(rc);
    } else {
        ok = false;
    }
    return ok;
}
