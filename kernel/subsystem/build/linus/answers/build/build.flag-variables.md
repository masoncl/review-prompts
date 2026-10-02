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
