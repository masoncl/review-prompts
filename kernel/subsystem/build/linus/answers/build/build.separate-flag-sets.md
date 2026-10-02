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
