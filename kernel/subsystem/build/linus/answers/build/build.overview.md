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
