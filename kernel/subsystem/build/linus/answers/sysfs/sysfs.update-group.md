- Each file: `create_files()` calls `kernfs_remove_by_name()` on every text
  and binary attribute, then adds again those the callback makes visible.
- `sysfs_update_group()` does not call `sysfs_chmod_file()`; a changed mode
  arrives on a new `struct kernfs_node`.
- Named directory that should no longer exist: `sysfs_remove_group()`, return
  0; `kernfs_remove()` takes everything under the directory, including files
  that `sysfs_merge_group()` added from another group.
- Failure while adding a file: `remove_files()` removes every text and binary
  file of the group by name, including those not yet reached.
- Named directory after a failure: it stays, without the group's files, if it
  existed before the call.
- Directory that this call created: `kernfs_remove()` removes it on failure,
  because `update` was cleared when the lookup failed.
- `sysfs_update_groups()` failing at one group: `internal_create_groups()`
  calls `sysfs_remove_group()` on every earlier group of the array.
