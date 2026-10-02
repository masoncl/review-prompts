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
