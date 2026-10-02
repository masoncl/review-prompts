- `select LIB` in a bool with `depends on PARENT`, PARENT=m: the term added to
  the reverse dependency of LIB is `BOOL && PARENT`, which is `y && m` = m; a
  tristate LIB is forced to at least m, not to y. See the `P_SELECT` branch of
  `_menu_finalize()` in `scripts/kconfig/menu.c`.
- Enclosing `if PARENT` or menu dependency: same result, because
  `_menu_finalize()` ANDs the parent's dependency into the term.
- Term that evaluates to y while PARENT=m: when the bool's dependencies
  evaluate to y, for example a comparison such as `PARENT != n` (comparisons
  give y or n in `__expr_calc_value()`), or no tristate dependency at all.
- **Potentially unsafe usage**: a bool that depends on a tristate PARENT and
  selects a tristate LIB whose functions the bool's code calls.
  - Unsafe: when the bool's objects are linked into vmlinux while PARENT=m;
    LIB may then be only m, and built-in code references symbols that exist
    only in a module.
  - Safe: when the bool's objects are part of PARENT's composite object, so
    they are modular whenever LIB is; `SQUASHFS_ZLIB` in `fs/squashfs/Kconfig`
    selects `ZLIB_INFLATE`, and `fs/squashfs/Makefile` adds its object with
    `squashfs-$(CONFIG_SQUASHFS_ZLIB)`. `SQUASHFS_LZ4`, `SQUASHFS_XZ` and
    `SQUASHFS_ZSTD` follow the same form.
- `FS_ENCRYPTION` in `fs/crypto/Kconfig` and `BLK_DEV_INTEGRITY` in
  `block/Kconfig`: bools with no tristate dependency, so their selects force
  y; they are not examples of a bool below a tristate.
