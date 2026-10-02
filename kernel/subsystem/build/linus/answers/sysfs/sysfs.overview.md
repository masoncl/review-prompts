- kernfs users in this tree: three callers of `kernfs_create_root()`: sysfs,
  cgroup, and resctrl (`fs/resctrl/rdtgroup.c`). A change in `fs/kernfs/`
  reaches all three.
- `struct kernfs_root`, `struct kernfs_super_info`, `struct kernfs_iattrs`:
  defined in `fs/kernfs/kernfs-internal.h`; `struct kernfs_open_node` in
  `fs/kernfs/file.c`. Code outside `fs/kernfs/` cannot dereference them; it
  gets the root node from `kernfs_root_to_node()`.
- `struct kernfs_open_node`: exists only while a file node has opens; holds
  the list of `struct kernfs_open_file` and the poll state that
  `kernfs_notify()` bumps.
- `struct kernfs_super_info`: one per superblock, pairing a root with one
  namespace tag; one root can have several.
- Inodes: `kernfs_get_inode()` makes one per (superblock, node), so one
  `struct kernfs_node` can back several inodes; each holds a `count`
  reference.
- `struct kernfs_node` parent and name: the members are `__parent` and
  `name`, both `__rcu`; there is no `parent` member. `kernfs_parent()` is
  internal to `fs/kernfs/`; outside, code uses `kernfs_get_parent()` or reads
  `__parent` with `rcu_dereference()`, as `sysfs_file_kobj()` does.
- `KERNFS_ROOT_INVARIANT_PARENT`: set only by cgroup's root. sysfs nodes can
  change parent (`sysfs_move_dir_ns()`); `sysfs_file_kobj()` reads `__parent`
  under RCU.
- `priv` of a sysfs directory: the kobject, for a kobject's directory and
  for a named group's directory alike (`internal_create_group()` passes
  `kobj`). It is NULL for the root node and for directories made by
  `sysfs_create_mount_point()`.
- `priv` of a sysfs file: the `struct attribute *`. For a binary file
  `sysfs_add_bin_file_mode_ns()` stores `&battr->attr` and the callbacks
  read it back as `struct bin_attribute *`, which relies on `attr` being
  the first member.
- `struct kernfs_ops`: has no `show` member; text reads go through
  `seq_show`, or through `read` for a `SYSFS_PREALLOC` file. `show` and
  `store` are members of `struct sysfs_ops`.
- sysfs `struct kernfs_ops` table for a binary attribute:
  `sysfs_add_bin_file_mode_ns()` picks it from the attribute's own `mmap`,
  `read` and `write`.
- `struct kernfs_open_file`: seen only by the `struct kernfs_ops` callbacks
  in `fs/sysfs/file.c`. `struct sysfs_ops` callbacks get the kobject and the
  attribute; `struct bin_attribute` callbacks get `of->file`.
- `struct attribute` wrappers: a convention of each `struct sysfs_ops`, not
  of sysfs. sysfs passes `kn->priv` untyped, and nothing checks that an
  attribute added to a kobject is the wrapper type its `struct sysfs_ops`
  casts to.
- Plain `struct attribute` with no wrapper: exists; for example
  `kfd_procfs_queue_show()` in `drivers/gpu/drm/amd/amdkfd/kfd_process.c`
  dispatches on `attr->name`.
- `release` in `struct kernfs_ops`: the one callback run without an active
  reference; `kernfs_release_file()` calls it from `kernfs_fop_release()`
  and, at removal, from `kernfs_drain_open_files()`. No sysfs table sets it.
- `struct kernfs_syscall_ops`: `sysfs_init()` passes NULL.
- `struct device`: the only one of the four driver-core structures that
  embeds a kobject (`kobj`).
- `struct device_driver`: its kobject is in `struct driver_private`, reached
  through `p`.
- `struct bus_type` and `struct class`: hold no kobject and no pointer to
  one. Theirs is the `subsys` kset of `struct subsys_private`
  (`drivers/base/base.h`), found by `bus_to_subsys()` and
  `class_to_subsys()`.
- `struct kset` as parent: `kobject_add_internal()` uses the kset's kobject
  as parent only when `kobj->parent` is NULL; kset members need not share a
  directory.
- Symlink: holds a `count` reference on the target node and no reference on
  the target kobject. Removing the target does not remove links to it.
- `struct attribute_group`: an unnamed group leaves no object of its own in
  the tree; its files sit directly in the kobject's directory, and
  `sysfs_remove_group()` removes by attribute name, whatever created the
  file.
- Namespace tag source: `create_dir()` in `lib/kobject.c` sets `KERNFS_NS`
  on a directory when the kobject's `child_ns_type` returns ops; a child's
  tag comes from its own `struct kobj_type` `namespace` callback. Group
  files are created with a NULL tag.
