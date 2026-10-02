- Rewrites: all are in the one `sed -E` block of `scripts/headers_install.sh`,
  seven substitutions:

| Input | Output |
|---|---|
| `__user`, `__force`, `__iomem`, after whitespace or `(` and before whitespace | removed |
| `__attribute_const__` before whitespace or end of line | removed |
| `#include <linux/compiler.h>` at line start | removed |
| `__packed` | `__attribute__((packed))` |
| `inline`, `asm`, `volatile`, after line start, whitespace or `(` and before whitespace, `(` or line end | `__inline__`, `__asm__`, `__volatile__` |
| `_UAPI` after `#ifndef`, `#define`, `#endif /*` | removed |
| `__ASSEMBLY__` | `__ASSEMBLER__` |

- `#include <linux/compiler_types.h>`: not stripped by the script;
  `include/uapi/linux/stddef.h` hides it under `#ifdef __KERNEL__` instead.
- `scripts/unifdef -U__KERNEL__ -D__EXPORTED_HEADERS__`: runs after `sed`; an
  exit status above 1 fails the install.
- SPDX check: runs first, on the input; any line with
  `SPDX-License-Identifier:` followed by `GPL-` and without
  `WITH Linux-syscall-note` on the same line fails.
- SPDX check and LGPL: the pattern `GPL-` also matches `LGPL-`, so an LGPL
  header needs the note too.
- `CONFIG_` check: nothing is rewritten; the first identifier that begins with
  `CONFIG_` fails with "leak ... to user-space".
- `CONFIG_` check, what is scanned: the unifdef output with `/* */` comments
  removed; `//` comments and string literals are scanned as code.
- `CONFIG_` check, what passes: an identifier that only contains `CONFIG_`, for
  example `VIRTIO_CONFIG_S_DRIVER`.
- `CONFIG_` in a condition that unifdef can decide from `__KERNEL__` alone:
  passes, because the line is gone before the scan; see
  `#if !defined(CONFIG_M68K) || !defined(__KERNEL__)` in
  `include/uapi/linux/acct.h`.
- Exemption list: there is no config_leak_ignores list in this tree, and no
  other allowlist for the `CONFIG_` check or the SPDX check.
- On any failure: the `trap` in the script deletes the output file and the
  `.tmp` file.
- `no-export-headers`: `scripts/Makefile.headersinst` reads it from
  `$(src)/Kbuild`, the top of the uapi directory, with paths relative to that
  directory.
- `no-export-headers` users: only `include/uapi/Kbuild` sets it; no
  `arch/*/include/uapi/Kbuild` file exists.
