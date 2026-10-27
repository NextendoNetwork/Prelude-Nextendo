// Prelude — Nintendo Switch homebrew for the Nextendo Network.
// Copyright (C) 2026 Nextendo Network
//
// Licensed under the PolyForm Shield License 1.0.0.
//
// You may use, modify and distribute this software for any purpose EXCEPT providing a product
// that competes with Nextendo Network, or with any product Nextendo Network provides using it.
//
// See LICENSE.md for the full terms, or <https://polyformproject.org/licenses/shield/1.0.0>.
//
// Required Notice: Copyright 2026 Nextendo Network

// ============================================================
//  Nextendo .nro — logique systeme (ecrire hosts / editer l'ini / reboot)
// ============================================================
#ifndef NEXTENDO_APPLY_H
#define NEXTENDO_APPLY_H
#include <switch.h>

typedef enum { BOOT_UNKNOWN = -1, BOOT_SYSMMC = 0, BOOT_EMUMMC = 1 } BootType;

// Ecrit une etape dans sdmc:/prelude_trace.txt et COMMIT immediatement. Le commit par ligne coute
// cher, mais c'est tout l'interet : sans lui les ecritures SD restent en cache et une coupure au
// POWER les perd — c'est precisement ce qui rendait un blocage invisible sur la carte. Ainsi la
// derniere ligne presente = la derniere etape franchie, meme apres un arret force.
void nextendo_trace(const char *step);
#define NEXTENDO_TRACE_PATH "sdmc:/prelude_trace.txt"

// Detecte le storage de boot; les hosts sont modifies seulement pour cette NAND.
BootType nextendo_detect_boot(void);

// Mode ACTUELLEMENT charge : 0 = NEXTENDO, 1 = NINTENDO, 2 = CAPTURE (memes valeurs que
// CHOICE_*). Lu depuis les fichiers hosts (redirection VPS presente ou non), puis le marqueur
// du mode CAPTURE (qui exige aussi les patches disable_ca_verification sur la carte).
int nextendo_current_mode(void);

// Mode NEXTENDO : ecrit les hosts de la NAND courante + enable_dns_mitm=1.
// ip : IP du serveur à utiliser (NEXTENDO_SERVER_IP_DEFAULT ou NEXTENDO_SERVER_IP_ALT).
bool nextendo_apply_nextendo_ip(const char *ip);

// Mode NEXTENDO avec l'IP par défaut.
bool nextendo_apply_nextendo(void);

// Mode NINTENDO : renomme les hosts Nextendo en .bak + enable_dns_mitm=0 -> tout redevient normal.
bool nextendo_apply_nintendo(void);

// Nintendo mode: both PRODINFO choices keep Nintendo DNS blocked. The identity
// setting takes effect only after reboot and never grants a ban-free guarantee.
bool nextendo_apply_nintendo_ex(bool blankProdinfo);

// exosphere.ini contient blank_prodinfo_emummc=1.
bool nextendo_prodinfo_emummc_blanked(void);
// Saved setting for the next boot: -1 unreadable/invalid, 0 disabled, 1 enabled.
int nextendo_prodinfo_emummc_state(void);

// Mode CAPTURE (cache) : mode NINTENDO + patches disable_ca_verification du ssl + PRODINFO reel
// en emuMMC + marqueur. Pour capturer avec mitmproxy uniquement ; voir l'avertissement dans l'UI.
bool nextendo_apply_capture(void);

// Teste la connectivite reseau de base et loggue les resultats dans la trace
// (diagnostic pour 2123-0011 et 2810-1224). Necessite socketInitializeDefault().
void nextendo_diag_network(void);

// Redemarre la console (ne revient pas si succes ; bpcRebootSystem).
Result nextendo_reboot(void);

// SSBU Online Deluxe mod — install / remove / detect.
// Install copie romfs:/ssbu_quickplay/ vers sdmc:. Remove fait l'inverse.
bool nextendo_ssbu_is_installed(void);
bool nextendo_ssbu_install(void);
// true si le mod est installe mais differe de celui embarque dans CE Prelude.
bool nextendo_ssbu_needs_update(void);
void nextendo_ssbu_remove(void);

// --- Batailles Speciales de Super Mario Bros. 35 — mod OPTIONNEL. ---
// Vit dans romfs:/smb35_spbattle/ et se copie dans sdmc:, comme le mod SSBU.
//
// ⚠️ POURQUOI C'EST OPTIONNEL ET NON POSE PAR DEFAUT : le correctif exefs ne s'ajoute
// pas au jeu, il le REMPLACE. Une seule instruction est modifiee, a l'adresse plate
// 0x320, sur la branche qui prepare la bataille NORMALE (game_mode := 1 devient 4).
// Mesure le 2026-09-08 : cette fonction n'a qu'UN appelant, 0x9EA9C, et il est sur la
// branche « type d'entree == 0 ». Le joueur qui pose ce correctif ne gagne donc pas un
// mode de plus : il perd la bataille a 35 ordinaire, qui devient une bataille speciale.
// C'est pour ca que ffsaga publie « 1a » (sans) et « 1c » (avec) comme deux mods qu'on
// n'installe jamais ensemble, et c'est pour ca que ceci a un bouton.
bool nextendo_smb35sp_is_installed(void);
bool nextendo_smb35sp_install(void);
// true si le mod est pose mais differe de celui qu'embarque CE Prelude.
bool nextendo_smb35sp_needs_update(void);
void nextendo_smb35sp_remove(void);

// Overclock EMBARQUE du mod (plugin libnx_over.nro + sysmodule 00FF0000A11CE0FF).
// A desactiver quand le joueur utilise deja Horizon OC / sys-clk : les deux pilotent
// les memes rails PCV et la console gele au lancement de Smash. Reversible : la
// reactivation recopie depuis le romfs du .nro. Prend effet au redemarrage.
bool nextendo_ssbu_oc_is_disabled(void);
bool nextendo_ssbu_oc_set(bool enabled);

// --- Fallback de vinculacion de cuenta (network_mitm v2 / sysmodule 4200000000000666) ---
// Para consolas con PRODINFO en blanco (emuMMC) que reciben error 0x0000167B en ssl:s.
bool nextendo_account_link_is_installed(void);
bool nextendo_account_link_is_recommended(void);
// Vrai si le firmware rend le fallback inutilisable (HOS >= 23.0.0, issue #42).
bool nextendo_account_link_fw_blocked(void);
bool nextendo_account_link_install(void);
bool nextendo_account_link_remove(void);

// --- Etat des correctifs de jeux (Game Patches) poses sur la carte SD ---
#define NEXTENDO_MAX_GAME_FOLDERS 8
#define NEXTENDO_MAX_FOLDER_NAME  48
#define NEXTENDO_MAX_GAMES        16

typedef struct {
    char gameName[64];
    char folders[NEXTENDO_MAX_GAME_FOLDERS][NEXTENDO_MAX_FOLDER_NAME];
    int  folderCount;
    int  patchCount;
} NextendoGamePatchStatus;

typedef struct {
    int  onSd;        // correctifs presents sur la carte
    int  inRomfs;     // correctifs livres par ce .nro
    bool dnsMitmOn;   // enable_dns_mitm = 1 dans system_settings.ini
    bool hostsOk;     // les hosts portent bien notre IP
    int  installedGameCount;
    NextendoGamePatchStatus installedGames[NEXTENDO_MAX_GAMES];
} NextendoS3Status;

typedef struct {
    const char *gameName;
    const char *prefix;
} GamePatchDef;

void nextendo_s3_status(NextendoS3Status *out);
bool nextendo_provision_all_public(void);
// Whether the last provision actually changed resource bytes on SD.
bool nextendo_provision_changed(void);

// Au demarrage, quand le mode Nextendo est deja actif : remet les hosts de la carte au contenu de CETTE version
// de Prelude s'ils sont a nous (signature Nextendo) et different. Renvoie le nombre de fichiers reecrits (0 =
// rien a faire) ; les hosts ne sont lus qu'au demarrage de la console, donc > 0 impose un redemarrage.
int nextendo_hosts_refresh(void);
void nextendo_purge_legacy_n64_patch(void);

// --- Sauvegarde des hosts dns.mitm que l'utilisateur avait AVANT Prelude. ---
// create/restore renvoient le NOMBRE de fichiers traites (0 = rien a faire, pas une erreur).
bool nextendo_hosts_backup_exists(void);
int  nextendo_hosts_backup_create(void);
int  nextendo_hosts_backup_restore(void);
// La question ne se pose qu'au premier lancement et apres chaque mise a jour.
bool nextendo_backup_prompt_needed(void);
void nextendo_backup_prompt_done(void);
bool nextendo_backup_use_for_nintendo(void);
void nextendo_backup_set_use_for_nintendo(bool on);

#endif // NEXTENDO_APPLY_H
