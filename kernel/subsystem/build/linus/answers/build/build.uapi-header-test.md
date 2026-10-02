- `CONFIG_UAPI_HEADER_TEST` in `init/Kconfig`: depends on `HEADERS_INSTALL`
  only; it does not depend on `CC_CAN_LINK`.
- Two passes per header in `cmd_hdrtest`: C with `-x c` and the header
  included twice, then C++ with `-x c++` and the header included once.
- C flags: `$(KBUILD_USERCFLAGS) $(UAPI_CFLAGS) -Wp,-MMD,$(depfile)` from
  `c_flags`, then `$(hdrtest-flags)`.
- `UAPI_CFLAGS`: `-std=c90 -Werror=implicit-function-declaration`.
- `KBUILD_USERCFLAGS` in the top-level `Makefile`: starts as `-Wall
  -Wmissing-prototypes -Wstrict-prototypes -O2 -fomit-frame-pointer
  -std=gnu11 $(USERCFLAGS)`.
- `-std=gnu11` from `KBUILD_USERCFLAGS`: overridden, because `-std=c90`
  comes later on the command line.
- `KBUILD_USERCFLAGS` additions: `$(CONFIG_ARCH_USERFLAGS)` if set, else
  `-m32`/`-m64` taken from the kernel flags; `--target=%` in both cases;
  `-Werror` from `scripts/Makefile.warn` under `W=e` or `CONFIG_WERROR`.
- `hdrtest-flags`: `-fsyntax-only -Werror -nostdinc -I $(obj)`; there is no
  `-isystem`.
- `-nostdinc`: unconditional, so neither libc headers nor the compiler's own
  headers, such as its `stddef.h`, are found.
- `cxx_flags`: `KBUILD_USERCFLAGS` without `-Wmissing-prototypes`,
  `-Wstrict-prototypes` and `-std=%`, plus `-std=c++98`.
- C++ pass: skipped without a message when `cc-can-compile-cxx` is empty, that
  is when `$(CC)` cannot compile `-x c++`.
- Three excuse lists in `usr/include/Makefile`:

| List | Effect on a listed header |
|---|---|
| `no-header-test` | the C pass compiles only `/dev/null`; the C++ pass is skipped |
| `no-header-test-cxx` | only the C++ pass is skipped |
| `uses-libc` | both passes add `-I $(srctree)/usr/dummy-include` |

- `usr/dummy-include`: 13 stub headers, for example `stdint.h` (typedefs
  from `linux/types.h`) and `sys/socket.h`; seven of the 13 are empty files;
  a libc header not stubbed there is not found.
- `CONFIG_CC_CAN_LINK`: not tested anywhere in `usr/include/Makefile`.
- Per-arch blocks: keyed on `UAPI_ARCH`, which is `HEADER_ARCH` if set, else
  `SRCARCH`.
- `linux/bpf_perf_event.h`: excused on arc, openrisc, xtensa and nios2.
- `asm/shmbuf.h` and `linux/android/binder.h`: not on `no-header-test`.
- A header on `no-header-test`: still goes through `headers_check.pl`.
