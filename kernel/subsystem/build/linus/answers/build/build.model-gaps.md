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
