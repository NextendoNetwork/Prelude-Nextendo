// Prelude, Nintendo Switch homebrew for the Nextendo Network.
// See LICENSE.md for the full terms, or <https://polyformproject.org/licenses/shield/1.0.0>.
#pragma once
#include <stdbool.h>
#include <switch.h>

// Le patch nextendo_bcat_signature du romfs couvre-t-il le module bcat de cette console ?
bool nextendo_news_patch_for_console(void);

// Efface les actualites telechargees (articles, index, historique). Garde passphrase.bin.
bool nextendo_news_purge(const char *mode);

// Reabonne aux chaines suivies d'office par le menu HOME (INewsService 40101).
Result nextendo_news_resubscribe(void);
