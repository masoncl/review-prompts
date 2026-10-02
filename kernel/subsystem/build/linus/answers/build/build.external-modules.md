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
