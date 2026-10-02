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
