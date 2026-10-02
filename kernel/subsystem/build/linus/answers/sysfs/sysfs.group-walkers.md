| Function | Callbacks called | `SYSFS_GROUP_INVISIBLE` |
|---|---|---|
| `create_files()` | text, binary, `bin_size` | cleared; the rest is the mode, zero skips |
| `__first_visible()` | one, index 0 | returned as is to `internal_create_group()` |
| `sysfs_group_attrs_change_owner()` | text, binary | stops that array, tested before zero |
| `remove_files()` | none | not seen |
| `sysfs_merge_group()` | none | not seen |
| `sysfs_unmerge_group()` | none | not seen |

- Entries of the same array after one that returned the bit:
  `create_files()` goes on to them, `sysfs_group_attrs_change_owner()` never
  reaches them.
- Requirements for a by-name walker, as `sysfs_group_attrs_change_owner()`
  meets them:
  - Text callback: test `is_visible` and `is_visible_const`; under
    `CONFIG_CFI` they are separate members, so a test of `is_visible` alone
    misses a group that set only `is_visible_const`.
  - Index: restart at 0 for `bin_attrs`.
  - Result: treat zero, and a result of only `SYSFS_GROUP_INVISIBLE`, as not
    created.
  - Named group: look the directory up first, as `sysfs_group_change_owner()`
    does; a hidden group has none.
- Callback state: the walker sees the state now, not at creation.
  - Visible now and never created: `sysfs_group_attrs_change_owner()` returns
    `-ENOENT`.
  - Hidden now and present: the node is passed over.
  - Call `sysfs_update_group()` after each state change to keep the two in
    step.
- **Unsafe usage**: looking up every entry of a group by name with
  `kernfs_find_and_get()` and failing on NULL, without calling the callbacks.
  - Safe: remove by name and ignore absence, as `remove_files()` does;
    `kernfs_remove_by_name()` on a missing name removes nothing.
  - Safe: a group with no visibility callback, where `create_files()` creates
    every entry; `sysfs_group_attrs_change_owner()` does this for such a
    group.
