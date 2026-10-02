- There is no SYSFS_BIN_GROUP_VISIBLE macro; `SYSFS_GROUP_VISIBLE()` is
  assigned to `.is_visible` or to `.is_bin_visible`.

| Macro | Needs | Member |
|---|---|---|
| `DEFINE_SYSFS_GROUP_VISIBLE()` | `name##_group_visible()`, `name##_attr_visible()` | `.is_visible` |
| `DEFINE_SIMPLE_SYSFS_GROUP_VISIBLE()` | `name##_group_visible()` | `.is_visible` |
| `DEFINE_SYSFS_BIN_GROUP_VISIBLE()` | `name##_group_visible()`, `name##_attr_visible()` | `.is_bin_visible` |
| `DEFINE_SIMPLE_SYSFS_BIN_GROUP_VISIBLE()` | `name##_group_visible()` | `.is_bin_visible` |

- `DEFINE_SIMPLE_SYSFS_BIN_GROUP_VISIBLE()`: no user in this tree; its body
  returns `a->mode`, and `struct bin_attribute` has no `mode` member, only
  `attr.mode`.
- All four macros define a function with the same name,
  `sysfs_group_visible_##name`, so one `name` can use only one of them.
- The two text macros take a non-const `struct attribute *`; the result has
  the type of `.is_visible`, not of `.is_visible_const`.
- `__first_visible()` order: `is_visible`, then `is_visible_const`, then
  `is_bin_visible`; the text ones need `grp->attrs[0]`, the binary one needs
  `grp->bin_attrs[0]`.
- Text and binary attributes with no text callback: `__first_visible()` asks
  `is_bin_visible` about `bin_attrs[0]`.
- Any index-0 result with the `SYSFS_GROUP_INVISIBLE` bit set hides the
  directory; `internal_create_group()` ignores the other bits.
- Zero for every attribute of a named group: the directory is still created,
  empty.
- A visible directory's mode: `S_IRWXU | S_IRUGO | S_IXUGO`, 0755.
- **Potentially unsafe usage**: one of the four macros on an unnamed group
  with more than one attribute.
  - Unsafe: when `name##_group_visible()` can return false and is meant to
    hide every file; only index 0 returns the bit, and `create_files()` goes
    on to the others, for which the two simple macros return `a->mode`.
  - Safe: a named group, as `nvme_ns_mpath_attr_group` in
    `drivers/nvme/host/sysfs.c`; `internal_create_group()` returns before
    `create_files()`.
  - Safe: an unnamed group with one attribute, as `pci_tsm_auth_attr_group`
    in `drivers/pci/tsm.c`; `create_files()` skips index 0.
  - Safe: `name##_group_visible()` always returns true and
    `name##_attr_visible()` decides each index, as `fan_boost_group` in
    `drivers/platform/x86/dell/alienware-wmi-wmax.c`.
