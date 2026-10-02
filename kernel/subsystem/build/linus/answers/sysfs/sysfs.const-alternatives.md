- `struct device_attribute` (`include/linux/device.h`) and
  `struct kobj_attribute` (`include/linux/kobject.h`): `show` pairs with
  `show_const`, `store` with `store_const`; the const form takes a const
  attribute pointer.
- `struct attribute_group`: `is_visible` pairs with `is_visible_const`,
  `attrs` with `attrs_const`; `is_bin_visible`, `bin_size` and `bin_attrs`
  have no alternative.
- `__SYSFS_FUNCTION_ALTERNATIVE()` in `include/linux/sysfs.h`: wraps each
  function-pointer pair; a `struct` (separate members) under `CONFIG_CFI`, a
  `union` (shared storage) otherwise.
- The symbol tested is `CONFIG_CFI`; `CFI_CLANG` in `arch/Kconfig` is only a
  transitional symbol.
- `attrs` and `attrs_const`: a plain `union` in every configuration.
- `__DEVICE_ATTR_SHOW_STORE()` and `__KOBJ_ATTR_SHOW_STORE()`: under
  `CONFIG_CFI` they set the member matching the handler's type and NULL the
  other; otherwise they set only `.show` and `.store`, casting a const handler
  with `(void *)`.
- `__ATTR()` in `include/linux/sysfs.h`: assigns `.show` and `.store`
  directly, with no `_Generic` selection.
- Under `CONFIG_CFI` a const handler leaves `show`/`store` NULL, so a test for
  "has a handler" has to look at both members, as `device_create_file()` does.
- `ATTRIBUTE_GROUPS()`: always initialises `.attrs`; its `_Generic` only casts
  a const array with `(void *)`. `__ATTRIBUTE_GROUPS()` has no `_Generic`.
- `fs/sysfs/group.c` reads only `grp->attrs`, never `attrs_const`; it relies
  on the union.
- `__first_visible()` in `fs/sysfs/group.c`: tries `is_visible`, then
  `is_visible_const`, then `is_bin_visible`; returns 0 when none applies, and
  `internal_create_group()` then creates the named directory.
