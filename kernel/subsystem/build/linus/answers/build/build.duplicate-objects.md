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
