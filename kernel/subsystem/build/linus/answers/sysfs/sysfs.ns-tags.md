- Tag type: `const struct ns_common *`, not `const void *`, in every `_ns`
  argument of sysfs and kernfs, in `ns` of `struct kernfs_node` and
  `struct kernfs_super_info`, and as the return of `namespace()` in
  `struct kobj_type` and `struct class` and of `kobject_namespace()`.
- Non-const `struct ns_common *`: where a reference is owned, in
  `grab_current_ns()`, `drop_ns()`, `kobj_ns_grab_current()`, `kobj_ns_drop()`
  and `ns_tag` of `struct kernfs_fs_context`.
- Net tag: `&net->ns`, made with `to_ns_common()`; turned back with
  `to_net_ns()` or `container_of()`.
- Comparison in kernfs: by `ns_id`, through `kernfs_ns_id()` in
  `fs/kernfs/dir.c`, which maps a NULL tag to 0; `kernfs_name_hash()` seeds
  the hash with the same id.
- Pointer comparison remains in: `kernfs_test_super()`, which decides
  superblock sharing, and `kobj_usermode_filter()`.
- Tag present or absent: tested as `(bool)ns` in `kernfs_add_one()` and
  `kernfs_find_ns()`.
- Tag lifetime: `kernfs_ns_id()` dereferences the tag on every compare, so it
  must point to a live `struct ns_common` for as long as a node carries it.
- Mount tag: `sysfs_init_fs_context()` in `fs/sysfs/mount.c` stores
  `kobj_ns_grab_current()` in `ns_tag`; there is no sysfs_mount() or
  sysfs_get_tree() here.
- `KERNFS_NS`: set by `create_dir()` in `lib/kobject.c` through
  `sysfs_enable_ns()` on the new kobject's own directory, when that kobject's
  `child_ns_type()` returns operations.
- Filtering: switched on per directory, not per entry; `kernfs_iop_lookup()`
  and `kernfs_fop_readdir()` use the superblock's tag when the parent has
  `KERNFS_NS` and NULL otherwise.
