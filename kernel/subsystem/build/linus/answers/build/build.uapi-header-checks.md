- `cmd_hdrtest` checks beyond the C compile: include guard (the C pass
  includes the header twice), C++98 compatibility, and `headers_check.pl`.
- Failure of any step: `cmd` in `scripts/Kbuild.include` prefixes `set -e`, so
  `touch $@` is not reached and the target fails.
- `headers_check.pl`: calls three subs per line, `check_include()`,
  `check_asm_types()` and `check_declarations()`; each sets `$ret = 1`, so
  each is an error.
- Fixed-width types without `linux/types.h`: not checked; there is no
  check_sizetypes sub in this tree.
- Leftover `__user`, kernel-only types, an indented plain `int` struct
  member: not checked by the script.
- `check_declarations()`: rejects a line that starts with optional whitespace
  and `extern`, and also a line that starts in column 0 with `unsigned`,
  `char`, `short`, `int`, `long` or `void`.
- **Potentially unsafe usage**: a declaration in an exported header whose
  type begins with `unsigned`, `char`, `short`, `int`, `long` or `void`.
  - Unsafe: when the keyword is in column 0 of the installed copy under
    `usr/include`, for example a return type alone on its line or an
    unindented member; `check_declarations()` reports "userspace cannot
    reference function or variable defined in the kernel".
  - Safe: when the line is indented or another word comes first, as
    `static inline int vring_need_event()` in
    `include/uapi/linux/virtio_ring.h`; the regex in `check_declarations()`
    anchors the type keywords at column 0.
- `check_declarations()` exceptions: a line that starts with `extern "C"`, and
  a line that starts with `void seqbuf_dump(void);`.
- `check_asm_types()`: active; rejects `#include <asm/types.h>`, reported
  once per file.
- `check_asm_types()` skips: any file whose path matches
  `types.h|int-l64.h|int-ll64.h`, for example `linux/vhost_types.h`.
- `check_include()`: tests only `<...>` includes whose path begins with `asm`
  or `linux`; an include of another exported directory, such as `drm/`, is
  left to the compiler.
- `CONFIG_` leaks: the header comment of `headers_check.pl` lists the check,
  but no sub implements it; `scripts/headers_install.sh` does it.
