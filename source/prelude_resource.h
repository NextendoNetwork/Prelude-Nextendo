// Copyright (C) 2026 Nextendo Network. See LICENSE.md.
#ifndef PRELUDE_RESOURCE_H
#define PRELUDE_RESOURCE_H
#include <stdbool.h>
enum { PRELUDE_COPY_FAILED = -1, PRELUDE_COPY_CURRENT = 0, PRELUDE_COPY_UPDATED = 1 };
// Binary resource installation. Identical files are not rewritten. Failed writes
// preserve the installed file; replacement keeps a recovery sibling.
int prelude_copy_resource(const char *source, const char *destination, bool (*commit)(void));
#endif
