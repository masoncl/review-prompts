# Kernel Build System

## Main structures

### Objects and how they relate

- Stage makefiles: `scripts/Kbuild.include` includes none of them; the only
  makefile shorthands it defines are `build` and `clean`, for
  `scripts/Makefile.build` and `scripts/Makefile.clean`.
- Stage makefiles: the top-level `Makefile` runs each as its own
  `$(MAKE) -f`, and each includes `scripts/Kbuild.include` itself, for
  example `scripts/Makefile.modpost` and `scripts/Makefile.vmlinux`.
- `include/config/auto.conf`: the file the build makefiles and
  `scripts/link-vmlinux.sh` take option values from; none of them includes
  `.config`.
- `include/config/FOO`, the per-option file for `CONFIG_FOO`: an empty file;
  `conf_touch_dep()` in `scripts/kconfig/confdata.c` only creates or
  truncates it.
- `include/generated/rustc_cfg`: a third view of the configuration, written
  by `conf_write_autoconf()` together with `include/generated/autoconf.h` and
  `include/config/auto.conf`, and passed to `rustc` by `rust_flags` in
  `scripts/Makefile.lib`.
- Top-level `Kbuild`: holds the root `obj-y` directory list; the top-level
  `Makefile` only runs `$(build)=.` on it.
- `core-y`, `drivers-y`, `libs-y`: appended to by `arch/$(SRCARCH)/Makefile`
  (`libs-y` starts as `lib/` in the top-level `Makefile`), and reach the
  top-level `Kbuild` as `ARCH_CORE`, `ARCH_DRIVERS`, `ARCH_LIB`; `ARCH_LIB`
  holds only the directory entries of `libs-y`.
- `obj-y += dir/` in a parent that has `need-builtin`: the child's
  `built-in.a` is a member of the parent's `built-in.a`.
- `obj-y += dir/` or `obj-m += dir/` in a parent that has `need-modorder`:
  the child's `modules.order` is copied into the parent's `modules.order`
  (`cmd_gen_order` in `scripts/Makefile.build`).
- `scripts/link-vmlinux.sh` header comment: places `lib/lib.a` under
  `KBUILD_VMLINUX_LIBS`; the top-level `Makefile` does not.
- Order of the stages after the descent in a full kernel build; each of 1 to
  4 is a prerequisite of the next, 5 follows 3 (`modules: modpost`) and waits
  for 4 only under `CONFIG_DEBUG_INFO_BTF_MODULES`:
  1. `scripts/Makefile.vmlinux_a`: `KBUILD_VMLINUX_OBJS` → `built-in-fixup.a`
     (objects in `scripts/head-object-list.txt` moved first) → `vmlinux.a`.
  2. `scripts/Makefile.vmlinux_o`: `vmlinux.a` plus `KBUILD_VMLINUX_LIBS` →
     `vmlinux.o`.
  3. `scripts/Makefile.modpost`: modpost reads `vmlinux.o` and
     `modules.order`; writes `.vmlinux.export.c`, each `.mod.c`, and
     `Module.symvers`.
  4. `scripts/Makefile.vmlinux`: `scripts/link-vmlinux.sh` →
     `vmlinux.unstripped` → `objcopy` → `vmlinux`.
  5. `scripts/Makefile.modfinal`: each `.ko`.
- `vmlinux` depends on `modpost`: `.vmlinux.export.o`, compiled from the
  `.vmlinux.export.c` that modpost writes, is an input of the final link even
  with `CONFIG_MODULES` off.
- `vmlinux_link()` in `scripts/link-vmlinux.sh`: links `vmlinux.o` instead of
  `vmlinux.a` under `CONFIG_LTO_CLANG`, `CONFIG_X86_KERNEL_IBT` or
  `CONFIG_KLP_BUILD`.
- objtool on `vmlinux.o`: runs only when `delay-objtool` or
  `CONFIG_NOINSTR_VALIDATION` is set (`objtool-enabled` in
  `scripts/Makefile.vmlinux_o`); `delay-objtool` is defined only under
  `CONFIG_OBJTOOL`, in `scripts/Makefile.lib`.
- `modules.builtin.modinfo`: the `.modinfo` section of `vmlinux.unstripped`,
  copied out by objcopy (`-j .modinfo -O binary`) in
  `scripts/Makefile.vmlinux`.
- `.ko`: linked from `foo.o`, `foo.mod.o` and `.module-common.o` with
  `scripts/module.lds`; `.module-common.o` is built once from
  `scripts/module-common.c` and carries vermagic, so vermagic is not in
  `foo.mod.c`.
- `-DMODULE`: comes from `KBUILD_CFLAGS_MODULE` in the top-level `Makefile`;
  `modkern_cflags` in `scripts/Makefile.lib` applies it when the object is in
  `real-obj-m` (`part-of-module`).

## Where to look

**Core files**

| Job | File in this tree |
|---|---|
| Compile the objects of one directory | No single file. Pattern rules, `obj-y`/`obj-m` processing, `built-in.a`, `lib.a`: `scripts/Makefile.build`. `cmd_cc_o_c`, `rule_cc_o_c`, `cmd_as_o_S`, `rule_as_o_S`: defined in `scripts/Makefile.lib`, because other makefiles reuse them: `scripts/Makefile.vmlinux` both rules, `scripts/Makefile.modfinal` `rule_cc_o_c`. |
| Assemble each object's flags | `scripts/Makefile.lib` (`c_flags`, `a_flags`, `cpp_flags`, `ld_flags`, `rust_flags`). |
| Rerun a command when it changes | `scripts/Kbuild.include`: `if_changed`, `if_changed_dep`, `if_changed_rule`, `cmd-check`. It does not define `arg-check`; that name is only in `tools/build/Build.include`. Each makefile under `scripts/` that is run with `-f` and calls `if_changed` has its own `-include` of the `.cmd` files of its targets, for example `scripts/Makefile.vmlinux`; one that calls only `cmd`, such as `scripts/Makefile.modinst`, has none. An `if_changed` target missing from `targets` reruns every time. |
| Compiler and linker option probes | `scripts/Makefile.compiler` (`try-run`, `cc-option`, `ld-option`, `as-instr`, `rustc-option`). Outside `tools/`, included only by the top-level `Makefile` and `scripts/Makefile.build`; `scripts/Makefile.lib` does not include it, so for example `scripts/Makefile.vmlinux` and `scripts/Makefile.modfinal` have no `cc-option`. |
| Host programs | `scripts/Makefile.host`: C, C++ and Rust executables; no shared-library rules. |
| Default and extra warning options | `scripts/Makefile.warn`: kernel C defaults, `W=1`, `W=2`, `W=3`, `W=e` and `CONFIG_WERROR`. There is no Makefile.extrawarn. For kernel C the top-level `Makefile` keeps only the clang `-Wno-gnu` pair in `CC_FLAGS_DIALECT`; it also holds host and userprog warnings (`KBUILD_USERHOSTCFLAGS`) and the Rust lints. |
| Module stages after compilation | No single file. `scripts/Makefile.modpost`, then `scripts/Makefile.modfinal` (`.mod.o`, `.ko` link, BTF), then `scripts/Makefile.modinst` (install, strip, sign, compress). Signing is `cmd_sign` in `scripts/Makefile.modinst`, not in `scripts/Makefile.modfinal`. |
| `built-in.a` and `lib.a` to `vmlinux.a` | `scripts/Makefile.vmlinux_a`: `built-in-fixup.a` (reordered by `scripts/head-object-list.txt`), then `vmlinux.a`. Under `CONFIG_LTO_CLANG_THIN_DIST` it also runs `scripts/Makefile.thinlto`. The top-level `Makefile` only chains the phony `vmlinux_a`, `vmlinux_o`, `modpost`, `vmlinux`. |
| `vmlinux.a` to `vmlinux.o` | `scripts/Makefile.vmlinux_o`: link, objtool, `scripts/check-function-names.sh`. It does not run modpost. |
| modpost on `vmlinux.o` | `scripts/Makefile.modpost`, run by target `modpost` in the top-level `Makefile`; writes `.vmlinux.export.c`, which `scripts/Makefile.vmlinux` compiles. |
| `vmlinux.o` to `vmlinux.unstripped` | `scripts/Makefile.vmlinux` runs `scripts/link-vmlinux.sh` (`cmd_link_vmlinux`). |
| `vmlinux.unstripped` to `vmlinux` | `scripts/Makefile.vmlinux`: `cmd_strip_relocs`, an objcopy that removes `.modinfo`. `modules.builtin.modinfo` is also made here, from `vmlinux.unstripped`, and `modules.builtin` from `modules.builtin.modinfo`. |
| Install exported headers | No single file. `scripts/Makefile.headersinst` only fills `usr/include` in the object tree (target `headers`). The copy to `INSTALL_HDR_PATH` is `cmd_headers_install` in the top-level `Makefile`. |
| Minimal tool versions | No single file. Numbers: `scripts/min-tool-version.sh` (binutils, gcc, llvm, rustc, bindgen). `scripts/cc-version.sh`, `scripts/as-version.sh`, `scripts/ld-version.sh` compare; the build stops at the `$(error-if,...)` lines in `scripts/Kconfig.include`, not in `init/Kconfig`. `scripts/rustc-version.sh` only prints a version; `scripts/rust_is_available.sh` compares, and `prepare` in the top-level `Makefile` runs it at make time under `CONFIG_RUST`. GNU Make 4.0: `$(error ...)` at the head of the top-level `Makefile`. |

## Language and toolchain

**C dialect and global options**

- `CC_FLAGS_DIALECT` in the top-level `Makefile`: holds the dialect; exported and
  appended to `KBUILD_CFLAGS`. There is no CSTD_FLAG in this tree.
- `CC_FLAGS_DIALECT` contents, in order: `-std=gnu11`; the value of
  `CONFIG_CC_MS_EXTENSIONS`; under `CONFIG_CC_IS_CLANG` also `-Wno-gnu` and
  `-Wno-microsoft-anon-tag`.
- `CONFIG_CC_MS_EXTENSIONS` (string, `init/Kconfig`): `-fms-anonymous-structs`
  when the compiler accepts it, `-fms-extensions` otherwise; `-fms-extensions`
  is therefore not on every command line.
- `-include $(srctree)/include/linux/compiler_types.h`: added by `c_flags` in
  `scripts/Makefile.lib`, not by `LINUXINCLUDE`.
- `USERINCLUDE` (part of `LINUXINCLUDE`): force-includes
  `include/linux/compiler-version.h` and `include/linux/kconfig.h`.

**Undefined behaviour options**

- `-fno-strict-overflow` and `-fno-delete-null-pointer-checks`: plain
  `KBUILD_CFLAGS +=`, no `cc-option`, no `ifdef`.
- `-fwrapv`: no makefile passes it.
- `--param=allow-store-data-races=0` and `-fno-allow-store-data-races`: each
  through `cc-option`, both inside `ifdef CONFIG_CC_IS_GCC`.
- Probe only (`cc-option`, any compiler): `-fzero-init-padding-bits=all`,
  `-fstrict-flex-arrays=3`, `-fno-stack-clash-protection`.

**Minimal tool versions**

- `scripts/cc-version.sh`, `scripts/ld-version.sh`, `scripts/as-version.sh`: on
  a too-old tool print "... is too old." to stderr and exit 1 with nothing on
  stdout.
- `scripts/Kconfig.include`: aborts on the empty `cc-info`, `as-info` or
  `ld-info` through `$(error-if,...)`; its message is "Sorry, this C compiler
  is not supported." (and the like), not the "too old" text.
- `scripts/as-version.sh`: makes no version check when its arguments contain
  `-fintegrated-as`; it prints `LLVM 0`.
- llvm minimum: applied to Clang in `scripts/cc-version.sh`, to LLD in
  `scripts/ld-version.sh`, and to the libclang that bindgen uses in
  `scripts/rust_is_available.sh`.
- `scripts/rust_is_available.sh` at Kconfig time: only sets
  `CONFIG_RUST_IS_AVAILABLE`; `success` in `scripts/Kconfig.include` discards
  its output, so configuration continues.
- `scripts/rust_is_available.sh` at build time: `prepare` in the top-level
  `Makefile` runs it under `CONFIG_RUST`; a too-old tool stops the build there.
- Minimums that depend on the architecture, in `scripts/min-tool-version.sh`:

| Tool | Test | Minimum |
|---|---|---|
| `gcc` | `$ARCH` is `parisc64` | 12.0.0 |
| `gcc` | otherwise | 8.1.0 |
| `llvm` | `$SRCARCH` is `loongarch` | 18.0.0 |
| `llvm` | otherwise | 17.0.1 |
| `rustc` | `$SRCARCH` is `s390` | 1.96.0 |
| `rustc` | `$ARCH` is `powerpc` | 1.95.0 |
| `rustc` | otherwise | 1.85.0 |

- `binutils` (2.30.0) and `bindgen` (0.71.1): one minimum for every
  architecture.
- `Documentation/process/changes.rst`: lists only the general values (GNU C
  8.1, Clang/LLVM 17.0.1, Rust 1.85.0); it does not give the per-architecture
  values of `scripts/min-tool-version.sh`.

**Code built with its own flags**

- Ways to replace the global flags:

| How | Applies to | Example |
|---|---|---|
| `KBUILD_CFLAGS :=` at makefile level | every object of the directory | `arch/x86/boot/compressed/Makefile` |
| target-specific `$(objs): KBUILD_CFLAGS :=` | the listed objects; other objects of the directory keep the global flags | `arch/loongarch/vdso/Makefile` |
| own `cmd_` rule with its own variable | objects built by that rule | `cmd_vdsocc` in `arch/arm64/kernel/vdso32/Makefile`, `cmd_bootcc` in `arch/powerpc/boot/Makefile` |

- `KBUILD_CFLAGS` is exported by the top-level `Makefile`: a makefile-level
  assignment also holds in directories that makefile descends into, unless
  they assign it again.
- First two ways: the object is still compiled with `c_flags` from
  `scripts/Makefile.lib`, which adds `KBUILD_CPPFLAGS`, `NOSTDINC_FLAGS`,
  `LINUXINCLUDE`, `-include` of `include/linux/compiler_types.h`, `ccflags-y`,
  the per-object `CFLAGS_` variable and `modkern_cflags`.
- Own `cmd_` rule with its own variable: bypasses `c_flags`; the object gets
  only what the variable holds.
- Sanitizer and coverage flags: `scripts/Makefile.lib` adds them only when
  `is-kernel-object` holds (object in `real-obj-y`, `lib-y` or `real-obj-m`) or
  the object or directory opts in; an object listed only in `targets` gets no
  instrumentation without any `KASAN_SANITIZE := n`.
- Options a replaced set repeats (search `arch/` and `drivers/` for the option
  name): `-funsigned-char` in none; `-fno-strict-overflow` only in
  `arch/arm64/kernel/vdso32/Makefile`; `-fno-delete-null-pointer-checks` only
  in `arch/parisc/boot/compressed/Makefile` and `KBUILD_CFLAGS_DECOMPRESSOR` in
  `arch/s390/Makefile`.
- `REALMODE_CFLAGS`, `arch/x86/boot/compressed/Makefile` and the x86 branch of
  `drivers/firmware/efi/libstub/Makefile`: do not pass `-funsigned-char`, so
  plain `char` there has the compiler's default signedness.
- Names that start with BOOT_COMPRESSED_: header include guards, for example
  `BOOT_COMPRESSED_MISC_H`; no flag set passes such a define.
  `__BOOT_COMPRESSED` is `#define`d in source files under
  `arch/x86/boot/compressed/`.
- **Unsafe usage**: a source file built both ways that depends on an option
  only the global set passes (signedness of plain `char`, wrapping signed or
  pointer arithmetic, kept NULL checks, zero-initialised locals).
  - Safe: the own set repeats the option, as `VDSO_CFLAGS` in
    `arch/arm64/kernel/vdso32/Makefile` repeats `-fno-strict-overflow` and
    `-fno-strict-aliasing`.
  - Safe: the set is derived from `$(KBUILD_CFLAGS)` with `filter-out`, as in
    `arch/x86/purgatory/Makefile`; every option not filtered stays.
- **Potentially unsafe usage**: a tagged struct or union used as an anonymous
  member in a header that own-flag code includes.
  - Unsafe: when the flag set carries only the `-std=` option, for example
    taken with `$(filter -std=%,$(KBUILD_CFLAGS))`; the
    `CONFIG_CC_MS_EXTENSIONS` option is then absent and the member is not
    accepted.
  - Safe: when the set includes `$(CC_FLAGS_DIALECT)`, as `REALMODE_CFLAGS` in
    `arch/x86/Makefile` does.

**The tools directory**

- Kbuild makefiles under `tools/` (those that set `obj-m`, for example
  `tools/testing/cxl/Kbuild` and `tools/testing/nvdimm/Kbuild`): their objects
  are compiled with `KBUILD_CFLAGS`.
- `tools/testing/cxl/Kbuild`, `tools/testing/cxl/test/Kbuild`,
  `tools/testing/nvdimm/Kbuild`: filter two warnings out of `KBUILD_CFLAGS`.
  No other makefile under `tools/` refers to `KBUILD_CFLAGS`.
- `tools/scripts/Makefile.include`: defines `EXTRA_WARNINGS`, which a tool must
  add to `CFLAGS` itself; the only thing it appends to `CFLAGS` is
  `$(CLANG_CROSS_FLAGS)`. It sets no `-std=`, `-O` or `-g`.
- `-fno-strict-aliasing` in `tools/scripts/Makefile.include`: added to
  `EXTRA_WARNINGS` only when `MAKE_VERSION` is 3.x.
- Options that tools set themselves, for example:

| Makefile | Options |
|---|---|
| `tools/perf/Makefile.config` | `-std=gnu11`, `-funsigned-char`, `-fno-strict-aliasing` |
| `tools/objtool/Makefile` | `-std=gnu11` |
| `tools/lib/bpf/Makefile` | `-std=gnu89`, not the kernel's `-std=gnu11` |
| `tools/virtio/Makefile`, `tools/testing/vsock/Makefile` | `-fno-strict-overflow`, `-fno-strict-aliasing`, `-fno-common` |

- `-fno-delete-null-pointer-checks` and `-fshort-wchar`: in no makefile under
  `tools/`.
- `CFLAGS_$(obj)` and `CFLAGS_REMOVE_$(obj)` in `tools/build/Build.include`:
  keyed by the name given to `$(build)=` (for example `objtool`), not by
  directory.
- `KBUILD_HOSTCFLAGS`: `tools/build/Makefile` passes it as `HOSTCFLAGS` when it
  builds fixdep; `tools/objtool/Makefile` appends `$(HOSTCFLAGS)` to
  `OBJTOOL_CFLAGS`.
- `tools/objtool/sync-check.sh`: run by the `$(OBJTOOL_IN)` rule on every
  objtool build; `tools/perf/check-headers.sh` runs from the `check-headers`
  target in `tools/perf/Makefile`.
- Headers from the real tree: not every tool uses only the copies; for example
  `tools/virtio/Makefile` force-includes `../../include/linux/kconfig.h`, and
  `tools/platform/x86/amd/Makefile` adds `-I$(srctree)/include`.

**Interpreters for build scripts**

- `CONFIG_SHELL`: `sh`, set unconditionally in the top-level `Makefile`; it is
  never bash by choice of the build.
- `BASH`: `bash`, set and exported in the top-level `Makefile`;
  `Documentation/kbuild/makefiles.rst` does not list it.
- Interpreter in the rule decides: `$(CONFIG_SHELL) script` runs the script
  under `sh` whatever its `#!` line says.
- `SHELL`: the top-level `Makefile` and the makefiles under `scripts/` do not
  set it; `arch/um/Makefile`, which the top-level `Makefile` includes for that
  architecture, sets `SHELL := bash`.
- Python in `Documentation/process/changes.rst`: row `Python 3.9.x`, not marked
  "(optional)"; the Python section says several configuration options require
  it.
- GNU awk in `Documentation/process/changes.rst`: marked "(optional)", needed
  for `CONFIG_BUILTIN_MODULE_RANGES`; `AWK` is `awk`.
- **Unsafe usage**: a rule that runs a script by its path alone, relying on the
  execute bit.
  - Safe: name the interpreter before the path, as `$(PERL) -w
    $(srctree)/scripts/checkincludes.pl` in the `includecheck` target and
    `$(CONFIG_SHELL) $(srctree)/scripts/rust_is_available.sh` in `prepare`;
    `Documentation/kbuild/makefiles.rst`, "Script invocation", states the
    requirement.
- **Unsafe usage**: a script that uses bash syntax, run through
  `$(CONFIG_SHELL)`.
  - Safe: run it with `$(BASH)`, as `cmd_tags` in the top-level `Makefile` runs
    `scripts/tags.sh` and `cmd_genimage` in `arch/x86/boot/Makefile` runs
    `genimage.sh`.
  - Safe: a script that keeps to POSIX sh syntax, run through
    `$(CONFIG_SHELL)`, as `scripts/rust_is_available.sh` (`#!/bin/sh`).

## Exported headers

**Exported header processing**

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

**Compile test of exported headers**

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

**Checks beyond a plain compile**

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

## Probing the toolchain

**Option probes in makefiles**

| Probe | Runs | Existing flags in the test |
|---|---|---|
| `as-option` | `$(CC) -Werror ... -c -x assembler-with-cpp /dev/null` | `KBUILD_CPPFLAGS`, `KBUILD_AFLAGS` |
| `as-instr` | `printf "%b\n"` piped to `$(CC) -Werror ... -Wa,--fatal-warnings -c -x assembler-with-cpp -` | `CLANG_FLAGS`, `KBUILD_AFLAGS`; not `KBUILD_CPPFLAGS`, not `KBUILD_CFLAGS` |
| `ld-option` | `$(LD) $(KBUILD_LDFLAGS) $(1) -v`; no input file, nothing is linked | `KBUILD_LDFLAGS` |
| `__rustc-option` | a `no_core` crate on stdin, `--sysroot=/dev/null --crate-type=rlib --emit=obj=-` | `KBUILD_RUSTFLAGS_OPTION_CHKS`, then the caller's flags minus `--sysroot=/dev/null` and words matching `--target=%target.json` |

- `KBUILD_RUSTFLAGS_OPTION_CHKS`: where an arch that builds with
  `--target=$(objtree)/scripts/target.json` gives the probe a built-in
  `--target=`; see `arch/x86/Makefile`.
- `--target=<built-in triple>` in `KBUILD_RUSTFLAGS`: not filtered, it reaches
  the `rustc-option` test.
- There is no cc-ifversion here; the version probes are `gcc-min-version`,
  `clang-min-version` and `rustc-min-version`.
- Version probes: yield `y` or empty, never `n` (`test-ge` in
  `scripts/Kbuild.include`).
- `CONFIG_GCC_VERSION` under clang and `CONFIG_CLANG_VERSION` under GCC: 0
  (`init/Kconfig`), so the other compiler's probe yields empty.
- `TMPOUT`: `.tmp_$$$$`, relative to the directory make runs in; it has no
  `KBUILD_EXTMOD` case.
- Option that disables a warning: `__cc-option` compiles with every word
  `-Wno-<x>` of the option replaced by `-W<x>`, and yields the option as it
  was given.
- `cc-option`, `cc-option-yn` and `cc-disable-warning` all go through
  `__cc-option`, so all three test the positive form.
- `cc-disable-warning`: makes no test of its own; it is
  `$(call cc-option,-Wno-$(strip $1))`.
- `as-option`, `as-instr`, `ld-option`, `__rustc-option` and a bare
  `try-run`: no rewrite, the option is passed as given.

**Using option probes**

- `$(call cc-option,-Wno-foo)` and `$(call cc-disable-warning,foo)`: the same
  test; `scripts/Makefile.warn` uses the first form.
- **Unsafe usage**: testing a `-Wno-` option with a probe that does not go
  through `__cc-option`: a bare `try-run`, or `cc-option` in
  `scripts/Kconfig.include`.
  - Safe: `cc-option`, `cc-option-yn` or `cc-disable-warning` from
    `scripts/Makefile.compiler`; `__cc-option` tests the `-W` form, as
    `arch/x86/boot/compressed/Makefile` relies on.
- `:=` is not required: a per-object `+=` of a probe is routine, for example
  `CFLAGS_debug_info.o += $(call cc-option, ...)` in `lib/Makefile`.
- `CFLAGS_$(target-stem).o`: not initialised by `scripts/Makefile.build`, so
  `+=` leaves it recursive and the probe runs each time `c_flags` is expanded
  for that object; the cost is forks, the result is the same.
- `ccflags-y`, `asflags-y`, `ldflags-y`, `rustflags-y`: initialised with `:=`
  in `scripts/Makefile.build`, so `+=` onto them runs the probe once.
- Top `Makefile`: includes `scripts/Makefile.compiler` before
  `include/config/auto.conf`, and only under `need-compiler`.
- `need-compiler` empty (every goal is in `no-sync-config-targets`, such as
  `clean`): the arch `Makefile` is still included, and every probe call in it
  expands to empty; `cc-option-yn` is then neither `y` nor `n`, and no
  fallback is returned.
- Flags the object gets and the probe does not: see `c_flags` in
  `scripts/Makefile.lib`; for example `ccflags-y`, `CFLAGS_$(target-stem).o`,
  `KBUILD_CFLAGS_KERNEL`, and the removal by `CFLAGS_REMOVE_$(target-stem).o`.
- `__cc-option`: no caller outside `scripts/Makefile.compiler` and `tools/`.
- **Potentially unsafe usage**: `cc-option` for objects that are not built
  with `KBUILD_CPPFLAGS` and `KBUILD_CFLAGS`.
  - Unsafe: when the probe expands before the makefile replaces
    `KBUILD_CFLAGS`, or the objects use another compiler; the answer is for
    flags the object is not built with.
  - Safe: assign `KBUILD_CFLAGS :=` first, then probe, as
    `arch/x86/boot/compressed/Makefile` does; `cc-option` reads
    `KBUILD_CFLAGS` at expansion.
  - Safe: a local probe on `try-run` with the other compiler, as `cc32-option`
    in `arch/arm64/kernel/vdso32/Makefile` does for `CC_COMPAT`.
- **Unsafe usage**: `cc-option` in the top `Makefile`, or a file it includes,
  after a `-fplugin=` flag is in `KBUILD_CFLAGS`.
  - Unsafe: on a clean tree the plugin is not built when the `Makefile` is
    parsed, so the compile fails and the probe yields the fallback.
  - Safe: probe before `scripts/Makefile.randstruct`,
    `scripts/Makefile.kstack_erase` and `scripts/Makefile.gcc-plugins` are
    included, as `scripts/Makefile.warn` does.
  - Safe: `ld-option` after them, as `Makefile` does; it passes only
    `KBUILD_LDFLAGS`.
- **Unsafe usage**: a literal comma inside a probe argument, in make or in
  Kconfig.
  - Unsafe: in Kconfig the text after the comma becomes `$(2)`, which
    `cc-option` in `scripts/Kconfig.include` never reads; the option tested is
    cut at the comma. In make `cc-option` takes it as the fallback.
  - Safe: write `$(comma)`, as `arch/mips/Makefile` and the `as-instr` calls
    in `arch/riscv/Kconfig` do; `scripts/kconfig/preprocess.c` splits
    arguments at every top-level comma.
- `scripts/Kconfig.include` has no `try-run`; its probes are built on
  `success` and `if-success`.
- `scripts/Kconfig.include` has no `as-option`, `cc-option-yn`,
  `cc-disable-warning` or `__cc-option`.
- Assembler option in Kconfig: tested with `$(cc-option,-Wa$(comma)...)`, as
  in `arch/arm64/Kconfig`.
- Kconfig `cc-option`: `$(CC) -Werror $(CLANG_FLAGS) $(1) -c -x c /dev/null`;
  no `-Wno-` rewrite.
- Kconfig `as-instr`: `$(CLANG_FLAGS)`, the optional second argument and
  `-Wa,--fatal-warnings`; no `-Werror`, which the makefile `as-instr` has.
- Kconfig `cc-option-bit`: not built on `cc-option`; runs `$(CC) -Werror $(1)
  -E`, without `CLANG_FLAGS`, and yields the flag or empty, not `y` or `n`.
- Kconfig `rustc-option`: `$(RUSTC) $(1) --crate-type=rlib /dev/null`; no
  `--target`, no `--sysroot=/dev/null`, no `no_core` crate, no
  `KBUILD_RUSTFLAGS_OPTION_CHKS`.
- External module build (`KBUILD_EXTMOD` set): `may-sync-config` is cleared,
  so Kconfig probes are not re-run and the values of probed symbols, for
  example `CONFIG_CC_HAS_ASM_INLINE`, are those of the compiler that
  configured the kernel; makefile probes run the current `$(CC)`.

## Saying what to build

**Goal variables**

- Where the lists are processed: all of it (`filter-out`, `subdir-ym`,
  `multi-search`, `real-search`, `hostprogs-always-y`) is in
  `scripts/Makefile.build`; `scripts/Makefile.lib` rewrites none of these
  lists.

| Variable | Correction | Built when |
|---|---|---|
| `obj-y` | archived in `$(obj)/built-in.a` | `need-builtin` and `KBUILD_BUILTIN` |
| `obj-m` | `scripts/Makefile.build` makes only `.o` and `.mod` | `KBUILD_MODULES` alone |
| `obj-m` | listed in `$(obj)/modules.order` | `KBUILD_MODULES` and `need-modorder` |
| `lib-y`, `lib-m` | `$(obj)/lib.a` | `KBUILD_BUILTIN` alone; `need-builtin` is not tested |
| `always-m` | appended to `always-y` unconditionally | whenever the directory is visited |
| `extra-y` | joins `targets-for-builtin` | `KBUILD_BUILTIN` |
| `dtb-y` | `scripts/Makefile.dtbs` appends it to `always-y` | whenever the directory is visited |

- `.ko` files: linked by `scripts/Makefile.modfinal` from the top-level
  `modules.order`, not by `scripts/Makefile.build`.
- `hostprogs-always-m` and `userprogs-always-m`: also appended to `always-y`
  unconditionally.
- `lib.a` of a directory entry in `libs-y`: put in `KBUILD_VMLINUX_OBJS` by the
  top `Makefile` and linked with `--whole-archive` in
  `scripts/Makefile.vmlinux_o`, so every `lib-y` object there is linked.
- Non-directory entries of `libs-y` (`KBUILD_VMLINUX_LIBS`): the only ones
  linked on demand, for example the EFI stub `lib.a` in `arch/arm64/Makefile`.
- Deprecated in `Documentation/kbuild/makefiles.rst`: `extra-y` only.
- Replacement the document gives: `always-$(KBUILD_BUILTIN) += vmlinux.lds`;
  `always-y` is named only for targets to build unconditionally.
- `always-$(KBUILD_BUILTIN)` with `KBUILD_BUILTIN` empty: expands to `always-`,
  which only `scripts/Makefile.clean` reads.
- `extra-y`: not in the initialised list at the top of
  `scripts/Makefile.build`, and no kbuild makefile in this tree assigns it; see
  `arch/x86/kernel/Makefile` for the replacement in use.
- hostprogs-y, hostprogs-m and a plain always variable: not named by the
  document and not read by anything under `scripts/`; a makefile that assigns
  them builds nothing, with no warning.

**Objects listed more than once**

- Duplicate in `obj-y` or `obj-m`: dropped by make's `$^` through
  `real-prereqs` in `scripts/Kbuild.include`, not by `$(sort)`; the first
  occurrence fixes the link order.
- `lib-y`: passed through `$(sort)` in `scripts/Makefile.build`, unlike
  `obj-y` and `obj-m`, so duplicates go and the order becomes alphabetical.
- Part listed twice in one composite module (`foo-y`, `foo-objs`): `cmd_mod`
  in `scripts/Makefile.build` filters the `.mod` file with awk, so it is
  linked once.
- `KBUILD_MODNAME` of a shared object: every owner joined with `:`, as in
  `"a:b"`; see `modname` in `scripts/Makefile.lib`.
- `__KBUILD_MODNAME` of a shared object: `a:b`, not an identifier;
  `name-fix-token` rewrites only `-` and `,`. `__initcall_id()` in
  `include/linux/init.h` and `__mod_device_table()` in
  `include/linux/module.h` paste it into a symbol name.
- `modname-multi`: walks `multi-obj-ym`, so built-in composites count as owners
  too, not only modules.
- Owners counted: only composites enabled in the current configuration, so the
  same makefile is flagged under one `.config` and not under another.
- Object in a built-in composite and in a module composite: compiled once with
  the module flags, because `modkern_cflags` tests `part-of-module` first, and
  that `.o` also goes into `built-in.a`.
- The warning "is added to multiple modules": `cmd_warn_shared_object` in
  `scripts/Makefile.build`, defined only when `KBUILD_EXTRA_WARN` contains 1
  (`W=1`).
- `cmd_warn_shared_object`: a `$(warning)`, so the build continues; it is
  printed only when the object is recompiled.
- Rust objects: `rule_rustc_o_rs` does not call `cmd_warn_shared_object`; only
  `rule_cc_o_c` and `rule_as_o_S` do.

**Host programs**

- Rust: `foo-rust := y`, a flag and not an object list; the crate root is
  `foo.rs`. See `samples/rust/hostprogs/Makefile`.
- `foo-y` for a host program: not read; `scripts/Makefile.host` reads only
  `$(foo-objs)`, `$(foo-cxxobjs)` and `$(foo-rust)`, so
  `foo-$(CONFIG_X) += x.o` adds nothing.
- `hostprogs-always-y += foo`: shorthand for `hostprogs` plus `always-y`,
  expanded in `scripts/Makefile.build`.
- Per-directory link flags: no such variable; HOST_EXTRALDFLAGS does not exist
  in this tree.
- Link variables: `KBUILD_HOSTLDFLAGS` and `KBUILD_HOSTLDLIBS` globally,
  `HOSTLDLIBS_foo` per program, nothing in between.
- Rust per-program flags: `HOSTRUSTFLAGS_foo`, without `.o`; the C and C++
  per-file variables keep the `.o`.
- Rust link: `cmd_host-rust` passes `KBUILD_HOSTLDFLAGS` through `-Clink-args`
  and uses neither `KBUILD_HOSTLDLIBS` nor `HOSTLDLIBS_foo`.

**Descending into subdirectories**

- `subdir-y` and `subdir-m`: identical; both are merged into `subdir-ym` and
  the child gets neither `need-builtin` nor `need-modorder`.
- `obj-y += dir/`: passes `need-builtin=1` only if the parent itself has
  `need-builtin`, and `need-modorder=1` only if the parent has `need-modorder`.
- `obj-m += dir/`: passes `need-modorder=1` only if the parent has
  `need-modorder`.
- `obj-y` object in a child without `need-builtin`: not compiled at all,
  because nothing but `$(obj)/built-in.a` depends on it; no warning is printed.
- `obj-m` object in a child without `need-modorder`: its `.o` and `.mod` are
  still built under `KBUILD_MODULES`, `scripts/Makefile.build` prints two
  `$(warning)` lines, and no `.ko` is made because the object is in no
  `modules.order`.
- `obj-m += dir/` in a makefile without `need-modorder`: no warning, since
  directory entries are filtered out before the test; `dir` is still visited,
  with neither flag.
- Child under the `obj-y` form with nothing in `obj-y`: valid;
  `cmd_ar_builtin` creates an empty `built-in.a`.
- **Potentially unsafe usage**: `obj-$(CONFIG_FOO) += foo/` where
  `foo/Makefile` lists objects in `obj-y`.
  - Unsafe: when `CONFIG_FOO` can be `m`; with `m` the child runs without
    `need-builtin`, `$(obj)/built-in.a` is not in `targets-for-builtin`, and
    the `obj-y` objects are silently left out of vmlinux.
  - Safe: when `CONFIG_FOO` is bool, as `obj-$(CONFIG_BLOCK) += block/` in
    the top-level `Kbuild`; the entry is then in `obj-y` or absent, and
    `scripts/Makefile.build` passes `need-builtin=1` for `obj-y` entries.

## Flags and paths

**Per-directory and per-file flags**

- `CFLAGS_REMOVE_$(target-stem).o`: the outermost filter in `_c_flags`; it
  also strips `CFLAGS_$(target-stem).o`, so the per-file add variable cannot
  put back what the per-file remove variable took out.
- `CFLAGS_$(target-stem).o`: outside the `ccflags-remove-y` filter, so it puts
  back a flag that `ccflags-remove-y` removed; `ccflags-y` and
  `subdir-ccflags-y` are inside both filters and put nothing back.
- `_a_flags` and `_rust_flags`: same nesting, with `asflags-remove-y` and
  `rustflags-remove-y`.
- `_cpp_flags` and `ld_flags`: no filter; there is no remove variable for
  `cppflags-y` or `ldflags-y`.
- `subdir-ccflags-y`, `subdir-asflags-y`, `subdir-rustflags-y`: the only
  subdir flag variables; `scripts/Makefile.build` appends them to
  `KBUILD_CFLAGS`, `KBUILD_AFLAGS`, `KBUILD_RUSTFLAGS`, not to `ccflags-y`.
- Removing a flag for a directory and below: no subdir remove variable
  exists; makefiles reassign `KBUILD_CFLAGS` itself, as
  `drivers/firmware/efi/libstub/Makefile` does with `filter-out`. This is the
  exported variable `subdir-ccflags-y` is appended to, so the change reaches
  subdirectories too.
- Flags no remove variable reaches: everything appended with `_c_flags +=`
  lower in `scripts/Makefile.lib` (sanitizer, coverage and profile flags,
  `-I$(src) -I$(obj)`), and what `c_flags` puts around `_c_flags`:
  `NOSTDINC_FLAGS`, `LINUXINCLUDE`, `modkern_cflags`, `basename_flags`,
  `modname_flags`.
- `KBUILD_CFLAGS_KERNEL` and `CFLAGS_KERNEL` (in `modkern_cflags`): to drop a
  flag from them the makefile rewrites the variable, as
  `drivers/firmware/efi/libstub/Makefile` does for `-fdata-sections`.
- Per-file key: `$(target-stem).o`, the target path relative to `$(obj)`, not
  `$@`; an object in a subdirectory keeps the directory, as
  `CFLAGS_arm/neon1.o` in `lib/raid/raid6/Makefile`.
- `ld_flags`: the per-target variable is `LDFLAGS_$(@F)`, keyed by file name
  without directory; it applies where a command uses `ld_flags`, for example
  `cmd_ld`, `cmd_ld_multi_m` and `cmd_ld_single`.
- `.ko` final link: `cmd_ld_ko_o` in `scripts/Makefile.modfinal` does not use
  `ld_flags`, so `ldflags-y` and a `.ko`-keyed variable never reach it; it
  takes `KBUILD_LDFLAGS`, `KBUILD_LDFLAGS_MODULE` and `LDFLAGS_MODULE`.
- Host programs: `HOST_EXTRACFLAGS` for the directory and
  `HOSTCFLAGS_$(target-stem).o` for one file, in `scripts/Makefile.host`;
  `hostc_flags` has no filter.

**Source and object paths**

| | in-tree | `O=` | external, built in its source dir | external, other output dir (`MO=`) |
|---|---|---|---|---|
| `$(objtree)` | `.` | `.` | kernel build dir, absolute | same |
| `$(srcroot)` | `.` | `..` or absolute | `.` | `..` or absolute |
| `$(obj)` | `drivers/foo` | `drivers/foo` | `.` at the top, `sub` below | same |
| `$(src)` | `./drivers/foo` | `$(srcroot)/drivers/foo` | `./.` at the top | `$(srcroot)/.` at the top |
| `building_out_of_srctree` | unset | `1` | unset | `1` |

- `$(srcroot)` is `..` when the working directory is a direct child of the
  source directory; `KBUILD_ABS_SRCTREE` keeps it absolute in every build.
- `$(srctree)`: equals `$(srcroot)` for kernel builds; for an external module
  it is the absolute kernel source and differs from `$(srcroot)`.
- `building_out_of_srctree` for an external module: compares the module
  source directory with the working directory, not the kernel tree; a module
  built in place gets no `VPATH` and no automatic `-I`.
- Automatic `-I$(src) -I$(obj)`: only under `building_out_of_srctree`; added
  to `_c_flags`, `_a_flags` and `_cpp_flags`, not to `_rust_flags`;
  `scripts/Makefile.host` adds only `-I $(obj)`.
- `-include` files in assembler and linker-script preprocessing: `a_flags`
  and `cpp_flags` in `scripts/Makefile.lib` carry `LINUXINCLUDE`, so both get
  `include/linux/compiler-version.h` and `include/linux/kconfig.h`; neither
  gets `include/linux/compiler_types.h`, which only `c_flags` adds.
- **Potentially unsafe usage**: `$(srctree)/$(obj)` or `$(objtree)/$(obj)`.
  - Unsafe: in a makefile that can be built as an external module; there
    `$(srctree)` and `$(objtree)` are the kernel trees while `$(obj)` is
    relative to the module.
  - Safe: in a makefile built only as part of the kernel, as
    `arch/powerpc/boot/Makefile`; the top `Makefile` sets `srctree` to
    `$(srcroot)` and `objtree` to `.` when `KBUILD_EXTMOD` is unset.
- **Potentially unsafe usage**: no explicit `-I$(src)` for a header in the
  makefile's own directory.
  - Unsafe: when the header is included from a file in another directory,
    such as `include/trace/define_trace.h` including `TRACE_INCLUDE_FILE`;
    it builds with `O=` and fails in-tree, where `scripts/Makefile.lib` adds
    no `-I`.
  - Safe: when the including file is in the same directory and uses quotes,
    as `kernel/trace/trace.c` including `trace.h`; with a separate output
    directory `scripts/Makefile.lib` adds `-I$(src) -I$(obj)`.
  - Safe: with `-I$(src)` given, as `CFLAGS_bpf_trace.o` in
    `kernel/trace/Makefile`.

**Instrumentation switches**

- `lib-y` objects: kernel objects; `part-of-builtin` in
  `scripts/Makefile.lib` matches `$(real-obj-y) $(lib-y)`.
- Kernel object or not: decided by the list the object is in, not by the
  image it ends up in.
- gcov and KCOV: on for a kernel object only with `CONFIG_GCOV_PROFILE_ALL`
  or `CONFIG_KCOV_INSTRUMENT_ALL`; otherwise only where a switch says `y`.
- Other switches of the same form: `CONTEXT_ANALYSIS` (opt-in unless
  `CONFIG_WARN_CONTEXT_ANALYSIS_ALL`), `UBSAN_INTEGER_WRAP` (falls back to
  `UBSAN_SANITIZE`), `AUTOFDO_PROFILE`; search `scripts/Makefile.lib` for
  `$(target-stem).o)` to list them.
- Propeller: `scripts/Makefile.lib` reads `PROPELLER_PROFILE` for the
  directory but no per-file variable with that prefix.
- Directory switches: exported nowhere in the tree, so each subdirectory
  makefile sets its own.
- Assembler objects: `_a_flags` gets no sanitizer or coverage flags.
- Rust objects: `_rust_flags` gets only the KASAN, KCOV and AutoFDO flags.
- objtool: runs from `cmd_cc_o_c`, `cmd_as_o_S` and `cmd_rustc_o_rs` on every
  `$(obj)/%.o` for which `is-standard-object` in `scripts/Makefile.build` is
  set, under `CONFIG_OBJTOOL` and with `delay-objtool` empty.
- `OBJECT_FILES_NON_STANDARD_$(target-stem).o := n`: overrides a directory
  `OBJECT_FILES_NON_STANDARD := y`.
- `delay-objtool` (`CONFIG_LTO_CLANG`, `CONFIG_X86_KERNEL_IBT` or
  `CONFIG_KLP_BUILD`): per-object objtool runs only for single-object
  modules; multi-part modules get it at `cmd_ld_multi_m`, built-in code in
  `scripts/Makefile.vmlinux_o`.
- `scripts/Makefile.vmlinux_o`: does not read `OBJECT_FILES_NON_STANDARD`; it
  also runs objtool on `vmlinux.o` under `CONFIG_NOINSTR_VALIDATION` without
  `delay-objtool`, so the switch does not exempt built-in code from noinstr
  validation.
- Set of kinds to turn off: not fixed by the build; `kernel/entry/Makefile`
  and `mm/kasan/Makefile` set only `KASAN_SANITIZE`, `UBSAN_SANITIZE` and
  `KCOV_INSTRUMENT` to `n`.
- `__noinstr_section()` in `include/linux/compiler_types.h`: carries the
  per-function attributes for KCSAN, KASAN, KMSAN, coverage and profiling;
  some expand to nothing, for example `__no_sanitize_coverage` when the
  compiler lacks the attribute; it has no UBSAN attribute.
- `drivers/firmware/efi/libstub/Makefile` and the x86 vDSO
  (`arch/x86/entry/vdso/common/Makefile.include`): set no switch at all;
  the objects compiled from the stub sources and the vDSO objects
  (`vobjs-y`) are in `targets` only.
- **Potentially unsafe usage**: listing an object of code that must not be
  instrumented in `obj-y`, `obj-m` or `lib-y`.
  - Unsafe: when the makefile sets no switch for a kind that must be off and
    that the configuration enables; `is-kernel-object` is `y`, so
    `scripts/Makefile.lib` adds that kind's flags and objtool runs.
  - Safe: the compiled object is only in `targets` and a renamed copy goes in
    the list, as `drivers/firmware/efi/libstub/Makefile` does with
    `targets := $(lib-y)` and the `.stub.o` copies; `is-kernel-object` is
    empty for the compiled object.
  - Safe: a switch set to `n` for each kind that must be off, as
    `kernel/entry/Makefile` does for KASAN, UBSAN and KCOV on its `obj-y`
    objects; the `patsubst n%` tests in `scripts/Makefile.lib` read the
    switch before `is-kernel-object`.

## Custom rules

**Command change detection**

- `if_changed`, `if_changed_dep`, `if_changed_rule`: read only `$?`, `$^` and
  `$@` themselves; `$<` and `real-prereqs` matter only where `cmd_<name>`
  uses them.
- `if_changed_rule`: the comparison is against `cmd_<name>` with the same
  `<name>` as `rule_<name>`, so where `cmd_<name>` is defined `rule_<name>`
  must save that command, through `cmd_and_fixdep` or `cmd_and_savecmd`; see
  `rule_cc_o_c` in `scripts/Makefile.lib`.
- `echo-cmd`: not defined for Kbuild; it is defined only in
  `tools/build/Build.include`. `cmd` in `scripts/Kbuild.include` prints the
  log line.
- `if_changed_dep`: the command must write `$(depfile)`; `read_file()` in
  `scripts/basic/fixdep.c` exits with status 2 when the depfile, or a file
  listed in it, cannot be opened, and the recipe fails.
- `check-FORCE`: the warning is part of the recipe, so it prints only on a
  build where make already runs the recipe; a rule without `FORCE` whose
  prerequisites are older than the target prints nothing.
- Phony prerequisites: must be in the `PHONY` variable (`PHONY += name`), not
  only under `.PHONY:`; `newer-prereqs` filters `$?` by `$(PHONY)`, and a
  name left in it reruns the command on every build.
- `targets`: selects which `.cmd` files are read (and what
  `scripts/Makefile.clean` removes); it does not cause the target to be
  built. See the `$(obj)/:` rule in `scripts/Makefile.build`.
- Automatic `targets` entries beyond the `obj-y` family: for example
  `userprogs`, the `dtb-y` primitives, `MAKECMDGOALS`, and files derived by
  `intermediate_targets` such as `.asn1.c`, `.lex.c`, `.tab.c`.
- Makefiles not run through `scripts/Makefile.build`: must read the `.cmd`
  files themselves; search for `existing-targets` to see the block most of
  them repeat, for example in `scripts/Makefile.modpost`.
- **Potentially unsafe usage**: a `targets` entry that carries `$(obj)/`.
  - Unsafe: in a kbuild file read by `scripts/Makefile.build` with `$(obj)`
    other than `.`; `targets := $(addprefix $(obj)/, $(targets))` prefixes it
    again, no file matches, the `.cmd` file is never read and the target is
    rebuilt on every build.
  - Safe: stripping the prefix first, as
    `targets += $(patsubst $(obj)/%,%,$(vmlinux-objs-y))` does in
    `arch/x86/boot/compressed/Makefile`.
  - Safe: in a fragment included after that line, such as
    `scripts/Makefile.host`, where `targets += $(host-csingle)` appends names
    that already carry the prefix.
  - Safe: in a standalone makefile such as `scripts/Makefile.asm-headers`,
    where `targets := $(syscall-y)` holds prefixed names; it does no
    prefixing and uses the names as written.
- Several targets in one rule: a static pattern rule over a list, such as
  `$(host-cobjs): $(obj)/%.o: $(obj)/%.c FORCE` in `scripts/Makefile.host`,
  runs once per target with its own `$@` and `.cmd` file; each member must be
  in `targets`.
- Two `if_changed` calls in one recipe: both write `savedcmd_$@` to the same
  file, so on the next run the call that did not write last sees a changed
  command and reruns without the other.

**Header and configuration dependencies**

- Per-option file: `include/config/FOO` for `CONFIG_FOO`; the name is copied
  as written, same case, flat, no `.h` suffix. See `use_config()` in
  `scripts/basic/fixdep.c` and `conf_touch_dep()` in
  `scripts/kconfig/confdata.c`.
- `is_ignored_file()`: drops only `include/generated/autoconf.h`;
  `include/linux/kconfig.h` stays in `deps_<target>` and is scanned.
- `_MODULE` suffix: stripped by `parse_config_file()`, so `CONFIG_FOO_MODULE`
  records `include/config/FOO`.
- Token pasting: `CONFIG_##name` records nothing, because the name after
  `CONFIG_` is empty; an object that reaches an option only that way is not
  rebuilt when the option changes.
- `conf_touch_deps()`: touches the file when the value differs from the old
  `include/config/auto.conf`, when an option with no old value is now set,
  and when an option with an old value has no new one.
- Header rule without `FORCE`: `$(call cmd,...)` with real prerequisites only
  is also valid, as the `.asn1.h` rule in `scripts/Makefile.build`; it reruns
  on timestamps only, and a header that `make clean` must remove then goes in
  `clean-files`, as `crc32table.h` in `lib/crc/Makefile`.
- Header name in the depfile: `parse_dep_file()` copies it verbatim into
  `deps_<target>` and emits `$(deps_<target>):` with no recipe; fixdep puts
  no requirement on how the explicit dependency is spelled.

## Modules and modpost

**Modpost diagnostics**

- Severity is fixed by the macro: `mod_error()`, `error()` and `fatal()` are
  errors, `mod_warn()` and `warn()` are warnings. Only two calls pick it at run
  time, both `modpost_log()` in `check_exports()`.
- Switches that soften an error, in `scripts/Makefile.modpost`:

| Switch | modpost flag | What becomes a warning |
|---|---|---|
| `KBUILD_MODPOST_WARN`, any non-empty value | `-w` | undefined symbol, nothing else |
| `CONFIG_MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS`, or `KBUILD_NSDEPS` (set by `make nsdeps`) | `-N` | namespace used but not imported |
| `CONFIG_SECTION_MISMATCH_WARN_ONLY=y` (`default y`) | omits `-E` | the "Section mismatches detected." summary is not printed |

- `W=1` (`-W`): sets `extra_warn`, which nothing in `scripts/mod/` reads; it
  enables no check.
- `make -i`: adds `-n`; `parse_elf()` then prints "(ignored)" for a module object
  it cannot open instead of exiting.
- Message format: `ERROR: modpost: <mod>.ko: symbol '<sym>' undefined!`; there is
  no `"sym" [mod.ko]` form to grep for.

| Problem | Where | Severity |
|---|---|---|
| section mismatch, each reference | `default_mismatch_handler()` | warning, always |
| "Section mismatches detected." | `main()` | error, only with `-E` |
| `__ex_table` reference to a section outside the text list | `default_mismatch_handler()` | `fatal()` if the section is black-listed, warning if it is executable, error otherwise |
| missing `MODULE_DESCRIPTION()` | `read_symbols()` | warning on every build |
| `MODULE_IMPORT_NS()` of a `module:` namespace | `read_symbols()` | error; `-N` does not soften it |
| undefined symbol | `check_exports()` | error; weak ones are never reported |
| symbol exported twice | `sym_add_exported()` | error; with `-e` silent unless the earlier export is in vmlinux or the same module |
| symbol exported without definition | `check_exports()` | error |
| local symbol exported, unknown export license | `check_export_symbol()` | error |
| `EXPORT_SYMBOL` on an init or exit section symbol | `check_export_symbol()` | warning |
| module name too long | `check_modname_len()` | error |
| too long symbol | `add_versions()` | error, only with `CONFIG_BASIC_MODVERSIONS` and without `CONFIG_EXTENDED_MODVERSIONS` |
| symbol has no CRC, version generation failed | `add_versions()`, `add_exported_symbols()` | warning |
| device table size mismatch or no terminator | `do_table()` in `scripts/mod/file2alias.c` | error, not `fatal()` |
| COMMON symbol, non-allocatable section | `handle_symbol()`, `check_section()` | warning |
| `$(objtree)/Module.symvers` or `vmlinux.o` missing | `cmd_modpost` in `scripts/Makefile.modpost` | message only; `-w` is not added, undefined symbols stay errors |
| a `-i` dump file cannot be opened | `read_text_file()` | `exit(1)`; the `!buf` test in `read_dump()` never fires |

- vmlinux: `read_symbols()` skips the `.modinfo` checks (license, description,
  import) and `main()` skips `check_exports()` and `check_modname_len()`; the
  section and device-table checks run on `vmlinux.o` too, and the export checks
  do under `CONFIG_MODULES` (`-M`).

**Namespaces in makefiles and modpost**

- Quoting: `___EXPORT_SYMBOL()` in `include/linux/export.h` pastes the value
  after `.ascii`, so `-DDEFAULT_SYMBOL_NAMESPACE=NS` without quotes is not a valid
  form; write `ccflags-y += -DDEFAULT_SYMBOL_NAMESPACE='"NS"'`.
- Macros affected: only `EXPORT_SYMBOL()`, `EXPORT_SYMBOL_GPL()` and macros
  built on them, for example `EXPORT_PER_CPU_SYMBOL()`;
  `EXPORT_SYMBOL_NS()`, `EXPORT_SYMBOL_NS_GPL()` and
  `EXPORT_SYMBOL_FOR_MODULES()` name their own namespace.
- `ccflags-y` scope: C files of that one makefile; `scripts/Makefile.build`
  resets it per directory and `scripts/Makefile.lib` does not put it in
  `_a_flags`, so subdirectories and `.S` files are not covered.
- Softening the missing-import error: there is no
  KBUILD_ALLOW_MISSING_NS_IMPORTS; `-N` comes from
  `CONFIG_MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS` or from `KBUILD_NSDEPS`.
- `make nsdeps`: modpost gets `-d modules.nsdeps`; `scripts/nsdeps` reads that
  file. There is no per-module ".nsdeps" file.
- Built-in users: `main()` in `scripts/mod/modpost.c` skips `check_exports()` for
  vmlinux, so code linked into vmlinux is never checked for imports.
- Not importable: only namespaces that start with `module:`
  (`MODULE_NS_PREFIX`); no other name is refused.
- `module:` namespaces are created by `EXPORT_SYMBOL_FOR_MODULES()`, which is a
  GPL-only export; there is no EXPORT_SYMBOL_GPL_FOR_MODULES() in this tree.

**External modules**

- Output without `MO=`: the module source directory only when make runs in the
  kernel source or build directory (the `-C` form); with `make -f
  <kernel>/Makefile M=...` from elsewhere, output goes to the current directory.
- `M=`: exactly one directory, with no `%` or `:` in the path; the top-level
  `Makefile` stops with `$(error ...)` otherwise.
- Kernel built with `O=`: `objtree` is `$(KBUILD_OUTPUT)` and generated files
  are read from there; pointing `-C` at the build directory works because its
  generated `Makefile` exports `KBUILD_OUTPUT`.
- Checked up front: `include/config/auto.conf`,
  `include/generated/autoconf.h` and `include/generated/rustc_cfg` under
  `$(objtree)` (`checked-configs`); no other file of the kernel tree is tested
  up front.
- Not checked, and with no rule in an external build:
  `$(objtree)/scripts/mod/modpost` and `$(objtree)/scripts/module.lds`;
  `modules_prepare` builds the second on top of `prepare`.
- `Module.symvers` in the kernel tree: written only by a modpost run that has
  both `vmlinux.o` and `KBUILD_MODULES`; `make vmlinux` writes
  `vmlinux.symvers`, and `make modules` without `vmlinux.o` writes
  `modules-only.symvers`. Of the three, an external build reads only
  `$(objtree)/Module.symvers`.
- `KBUILD_EXTRA_SYMBOLS`: may be assigned in the module's own top `Kbuild` or
  `Makefile`, since `scripts/Makefile.modpost` includes `$(kbuild-file)` to pick
  it up.
- Alternative to `KBUILD_EXTRA_SYMBOLS`: one top-level `Kbuild` that lists both
  modules, giving one `modules.order` and one modpost run; see
  `Documentation/kbuild/modules.rst`.

**Build steps for external modules**

- Tree check: only `checked-configs` is tested; the error text says to run `make
  oldconfig && make prepare`, not `modules_prepare`.
- `prepare`: replaced by a rule that only prints warnings when
  `CC_VERSION_TEXT` or `PAHOLE_VERSION` differ from the kernel's; its recipe
  never fails.
- `outputmakefile`: still a prerequisite of `prepare`; with a separate output
  directory it fails if `$(srcroot)/modules.order` exists, and writes `Makefile`,
  a `source` symlink and `.gitignore` there.
- `KBUILD_MODULES`: set to `y`, not 1; `KBUILD_BUILTIN` is empty.
- modpost `-i` dumps: only `$(objtree)/Module.symvers` plus
  `KBUILD_EXTRA_SYMBOLS`; `vmlinux.symvers` is not read.
- modpost `-e`: `add_header()` leaves out `MODULE_INFO(intree, "Y")`.
- BTF: `%.ko` in `scripts/Makefile.modfinal` has no `$(objtree)/vmlinux`
  prerequisite because `KBUILD_BUILTIN` is empty; `cmd_btf_ko` prints a skip
  message when `vmlinux` is absent.
- `modules_install`: installs under `$(MODLIB)/$(INSTALL_MOD_DIR)`, default
  `updates`; the `depmod` target still runs.
- `modules_install` leaves out: removing `$(MODLIB)/kernel`, the `build` symlink,
  and installing `modules.order` and `modules.builtin`.
- Signing in `modules_install`: under `KBUILD_EXTMOD` `cmd_sign` ends in
  `|| true`, so a signing failure does not stop the install.
- `CONFIG_MODULES` unset: `modules` and `modules_install` fail through
  `__external_modules_error`.
- Targets: everything inside the `ifeq ($(KBUILD_EXTMOD),)` block of the
  top-level `Makefile` is absent; targets after it still work, for example
  `nsdeps`, `compile_commands.json` and single targets, though `help` lists only
  `modules`, `modules_install`, `clean` and `rust-analyzer`.

## Shared makefiles

**Changing Kbuild itself**

- Path variables per setup, all set in the top `Makefile`; make always runs
  in the output directory:

  | Setup | `srctree` | `srcroot` | `objtree` | `building_out_of_srctree` | `VPATH` |
  |---|---|---|---|---|---|
  | in-tree | `.` | `.` | `.` | unset | empty |
  | `O=` | `..` or absolute | same as `srctree` | `.` | 1 | `$(srcroot)` |
  | `M=`, built in the module directory | absolute | `.` | absolute | unset | empty |
  | `M=` with `MO=` | absolute | `..` or absolute, module source | absolute | 1 | `$(srcroot)` |

- `KBUILD_ABS_SRCTREE`: keeps `srcroot` absolute in every row, so `$(src)` is
  absolute even in an in-tree build.
- `src`: `src := $(srcroot)/$(obj)` in `scripts/Makefile.build` and
  `scripts/Makefile.clean`; `obj` is relative to the current directory, except
  that `rust-analyzer` under `KBUILD_EXTMOD` passes `$(objtree)/rust` with
  `src=` on the command line.
- There is no extmod_prefix or kbuild-dir here, and Kbuild does not define
  `abs_objtree`; `kbuild-file` in `scripts/Kbuild.include` finds the makefile
  through `$(src)`, and the top `Makefile` uses `abs_output`.
- `KBUILD_OUTPUT` (`O=`) under `KBUILD_EXTMOD`: names the kernel build
  directory and becomes `objtree`; it must exist.
- `KBUILD_EXTMOD_OUTPUT`: the variable that `MO=` on the command line sets;
  when it is set it is the module output directory, ahead of the other cases.
  See `output` in the top `Makefile`.
- `Module.symvers`, `modules.order` and `.module-common.o` of an external
  module: written to the current directory, which is the module output
  directory.
- `KBUILD_EXTMOD` in the makefiles under `scripts/`: tested only for being
  set, never used as a path; `scripts/Makefile.lib` and
  `scripts/Makefile.modfinal` do not name it at all.
- `scripts/Makefile.modpost` under `KBUILD_EXTMOD`: sets `obj := .` and
  `src := $(srcroot)` and includes the module's `$(kbuild-file)` again, to
  read `KBUILD_EXTRA_SYMBOLS`.
- `INSTALL_MOD_DIR`: read only under `KBUILD_EXTMOD` in
  `scripts/Makefile.modinst`; in-tree modules go to `$(MODLIB)/kernel`.
- Compile pattern rules in `scripts/Makefile.build`: the prerequisite is
  `$(obj)/%.c`, not `$(src)/%.c`; `VPATH` finds a checked-in source, so one
  rule serves generated and checked-in files.
- Rules whose input is always checked in name `$(src)/%`, for example
  `$(obj)/%.lds` in `scripts/Makefile.build` and `$(obj)/%.lex.c` in
  `scripts/Makefile.host`.
- Include paths added under `building_out_of_srctree`: `scripts/Makefile.lib`
  adds `-I` for `$(src)` and `$(obj)` to `_c_flags`, `_a_flags` and
  `_cpp_flags`; `scripts/Makefile.host` adds only `$(obj)`;
  `scripts/Makefile.userprogs` adds none.
- `-fmacro-prefix-map=$(srcroot)/=`: added by the top `Makefile` only under
  `building_out_of_srctree`; no makefile in this tree passes
  -ffile-prefix-map.
- Read-only source tree: `cmd_copy` in `scripts/Makefile.lib` uses `cat`,
  because `cp` would carry the read-only mode to the copy and the next run of
  the rule would fail.
- `KBUILD_BUILTIN` and `KBUILD_MODULES`: the `$(obj)/` rule in
  `scripts/Makefile.build` builds `targets-for-builtin` only with the first,
  `targets-for-modules` only with the second, and `always-y` regardless of
  both.
- `KBUILD_BUILTIN` under `KBUILD_EXTMOD`: empty, so the `$(obj)/` rule builds
  no `extra-y`, `lib.a` or `built-in.a` for an external module.
- Single targets: `scripts/Makefile.build` has no `ifdef` on `single-build`
  and there is no KBUILD_SINGLE_TARGETS; the top `Makefile` passes
  `single-goals` as make goals, and `single-subdirs` and
  `single-subdir-goals` in `scripts/Makefile.build` hand each to its
  directory.
- Single-target suffixes: listed in `single-targets` in the top `Makefile`;
  `%.symtypes` is not among them.
- Single-target `.cmd` files: `scripts/Makefile.build` adds the goals to
  `targets`, so the goal's `.cmd` file is read even if nothing else lists it.
- `scripts/package/install-extmod-build`: fills the module build tree that
  the deb, rpm and pacman packages ship; it copies `scripts/` minus what
  `find_in_scripts()` prunes (for example `dtc` and `kconfig`), and tools
  outside `scripts/` only by name.
- A shared rule that runs a new tool for modules needs that tool copied by
  `scripts/package/install-extmod-build`.
- `vmlinux`: not copied by `scripts/package/install-extmod-build`;
  `cmd_btf_ko` in `scripts/Makefile.modfinal` tests for `$(objtree)/vmlinux`
  and skips BTF without it.
- `CC` differs from `HOSTCC` when packaging:
  `scripts/package/install-extmod-build` rebuilds the copied `scripts/`
  through `$(build)` with `HOSTCC` set to the target compiler, `VPATH` empty
  and `srcroot=.`.
- Source packages: `check-git` in `scripts/Makefile.package` fails them
  outside a git repository.
- `quiet_cmd_`: optional; `quiet_log_print` in `scripts/Kbuild.include`
  prints nothing for a `cmd_` without one, as for `cmd_mod` and
  `cmd_gen_order` in `scripts/Makefile.build`.
- `make -s`: `silent_log_print` runs `exec >/dev/null` before the command, so
  anything a `cmd_` prints on stdout is dropped; messages go to stderr.
- **Unsafe usage**: writing `$(srctree)/$(src)`.
  - Unsafe: `$(src)` already starts with `$(srcroot)`, so the path is wrong
    whenever `srcroot` is not `.`.
  - Safe: `$(src)/file`, as `$(obj)/%: $(src)/%_shipped` in
    `scripts/Makefile.lib`; `src` is defined in `scripts/Makefile.build`.
- **Potentially unsafe usage**: a bare relative path in a recipe or
  prerequisite of a shared makefile.
  - Unsafe: the path names a kernel file (a tool under `scripts/`, a
    generated header, a kernel source) and the rule can run under
    `KBUILD_EXTMOD`; the current directory is the module output directory and
    `VPATH` is empty or the module source.
  - Safe: the path names an output of the tree being built, as
    `modules.order` and `Module.symvers` in `scripts/Makefile.modpost`.
  - Safe: a kernel file with its root spelled out, as
    `$(srctree)/scripts/module-common.c` and `$(objtree)/scripts/module.lds`
    in `scripts/Makefile.modfinal`; the top `Makefile` makes both roots
    absolute under `KBUILD_EXTMOD`.
  - Safe: a makefile run only for the kernel, as `scripts/Makefile.vmlinux`,
    which the top `Makefile` invokes inside `ifeq ($(KBUILD_EXTMOD),)`; the
    current directory is `objtree`, and a checked-in file is named bare only
    as a prerequisite, where `VPATH` finds it, as `scripts/link-vmlinux.sh`,
    which the recipe runs as `$<`.

## Model gaps

### Other mistakes models make

- Models take `src` to start with `$(srcroot)` in every makefile under
  `scripts/`. `scripts/Makefile.headersinst` sets `src := $(srctree)/$(obj)`,
  and `scripts/Makefile.asm-headers` also builds `src` from `$(srctree)`.
- Models take `KBUILD_MODULES` and `KBUILD_BUILTIN` to be `1`. They are `y`
  or empty, which is what lets a makefile write
  `always-$(KBUILD_BUILTIN) += vmlinux.lds`, as `arch/x86/kernel/Makefile`
  does.
- Models take `W=e` and `CONFIG_WERROR` to cover kernel C only. In
  `scripts/Makefile.warn` they also cover host programs, userprogs and the
  linker.
