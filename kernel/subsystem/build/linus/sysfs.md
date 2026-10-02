# Sysfs and Kernfs

## Main structures

### Objects and how they relate

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

## Attributes and their callbacks

**Const callback alternatives**

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

**Sysfs on top of kernfs**

- `sysfs_file_kobj()`: reads `kn->__parent` with `rcu_dereference()` under
  `guard(rcu)()` and returns its `priv`; `struct kernfs_node` has no field
  named parent, and `kernfs_parent()` is not used here.
- Text table choice in `sysfs_add_file_mode_ns()`: looks only at
  `kobj->ktype->sysfs_ops` and `SYSFS_PREALLOC`; the attribute's own callbacks
  and its permission bits play no part.
- With a ktype whose `sysfs_ops` has both callbacks, for example
  `dev_sysfs_ops` or `kobj_sysfs_ops`, every text file gets
  `sysfs_file_kfops_rw` or `sysfs_prealloc_kfops_rw`.
- Binary attribute with no `mmap`, `read` or `write`: gets
  `sysfs_file_kfops_empty`.
- Open for a direction the table has no kernfs op for: `kernfs_fop_open()`
  returns `-EACCES`.
- The `-EINVAL` branches in `kernfs_file_read_iter()` and
  `kernfs_fop_write_iter()` are not reached with the sysfs tables, because
  that open has already failed.
- Text attribute with no callback of its own on a ktype that has the op: open
  succeeds when the mode has the bit; the read or write reaches the ktype
  dispatcher, which returns its own error, `-EIO` in `dev_attr_show()` and
  `kobj_attr_show()`.
- `sysfs_kf_write()` and `sysfs_kf_read()` call `ops->store` and `ops->show`
  with no NULL test; only the table choice keeps that safe.

**Binary attributes**

- The bound is `file_inode(of->file)->i_size`, not `battr->size`;
  `kernfs_init_inode()` sets it from the size given at creation, so a later
  change to `battr->size` does not move the bound. A size of 0 means no
  bound.
- `sysfs_kf_bin_write()` with a non-zero size and `pos >= size`: returns
  `-EFBIG`, including a write that starts exactly at the end; it does not
  return `-ENOSPC`.
- `sysfs_kf_bin_write()` order: bound test, then zero count returns 0, then
  NULL `write` returns `-EIO`.
- `sysfs_kf_bin_read()` order: zero count returns 0, then bound test, then
  NULL `read` returns `-EIO`.
- The `-EIO` for a missing callback is reachable only through
  `sysfs_bin_kfops_mmap`, which has both kernfs ops whatever the attribute
  sets; with the other tables open has already failed with `-EACCES`.
- One read(2) or write(2) makes one callback call of at most `PAGE_SIZE`
  bytes; kernfs does not loop, it returns the short count.

**Permission bits**

- `VERIFY_OCTAL_PERMISSIONS()` is defined in `include/linux/sysfs.h`.
- `VERIFY_OCTAL_PERMISSIONS()` accepts execute bits and group write; 0775
  passes. It rejects only values outside 0..0777, other-write, and a read or
  write bit that is weaker for user than for group (or group than other, for
  read).
- `__BIN_ATTR()` does not use `VERIFY_OCTAL_PERMISSIONS()`; nor does
  `__ATTR_IGNORE_LOCKDEP()` under `CONFIG_DEBUG_LOCK_ALLOC`.
- The WARN "Invalid permissions" and the mask to `SYSFS_PREALLOC | 0664` are
  in `create_files()` in `fs/sysfs/group.c`, not in
  `sysfs_add_file_mode_ns()`.
- `sysfs_add_file_mode_ns()` and `sysfs_add_bin_file_mode_ns()`: only
  `mode & 0777`, no WARN on the mode.
- `sysfs_create_file_ns()`, `sysfs_create_bin_file()`,
  `sysfs_add_file_to_group()` and `sysfs_merge_group()` pass `attr->mode`
  without the 0664 mask, so execute or other-write bits set at run time
  survive there.
- Mode without a matching callback: `device_create_file()` WARNs, and it
  tests both members of each pair; no creation function in `fs/sysfs/`
  checks.
- `kernfs_fop_open()` refusal for a missing mode bit or a missing kernfs op:
  `-EACCES`, not `-EINVAL`; the test runs only under
  `KERNFS_ROOT_EXTRA_OPEN_PERM_CHECK`, which `sysfs_init()` sets.
- A 0644 device attribute with no `store` and no `store_const`: opens for
  write, because the callback half of the open check looks at the kernfs
  table, not at the attribute; the write returns `-EIO` from
  `dev_attr_store()`.

**The buffer given to show**

- Normal path zeroing: `sysfs_kf_seq_show()` does `memset(buf, 0, PAGE_SIZE)`
  before every call; the seq_file buffer itself comes from `kvmalloc()` in
  `seq_buf_alloc()`, with no `__GFP_ZERO`.
- Prealloc buffer: `kmalloc(PAGE_SIZE + 1)` in `kernfs_fop_open()`, never
  zeroed by kernfs or sysfs, reused by every read and write on that open
  file.
- `sysfs_emit()` and `sysfs_emit_at()`: WARN and return 0 when
  `offset_in_page(buf)` is non-zero, so they must be given the pointer show
  received, with any offset passed as `at`.
- Normal path, read at an offset that differs from `m->read_pos` (pread, or
  after lseek): `seq_read_iter()` calls `traverse()`, which runs show again
  from the start; nothing cached is used.
- Normal path, count of `PAGE_SIZE` or more: `sysfs_kf_seq_show()` does
  `WARN(1, "OOB write or bad count ...")` on every such call, then uses
  `PAGE_SIZE - 1`.
- Prealloc path, count of `PAGE_SIZE` or more: `sysfs_kf_read()` does a plain
  printk "fill_read_buffer: %pS returned bad count", no WARN, then uses
  `PAGE_SIZE - 1`.

**The buffer given to store**

- Longest write passed in one call: `PAGE_SIZE` bytes, with the NUL at
  `buf[PAGE_SIZE]`.
- No table in `fs/sysfs/file.c` sets `atomic_write_len`, so
  `kernfs_fop_write_iter()` clamps a longer write to `PAGE_SIZE`; it does not
  return `-E2BIG`.
- A longer write: store sees only the first `PAGE_SIZE` bytes, and write(2)
  returns what store returns.
- Zero-length write: reaches `sysfs_kf_write()`, which returns 0 without
  calling store.

**Documenting a new attribute**

- The validator is `tools/docs/get_abi.py`, with subcommands `rest`,
  `validate`, `search` and `undefined`; there is no get_abi script under
  `scripts/`.
- The parser is `AbiParser` in `tools/lib/python/abi/abi_parser.py`;
  `Documentation/sphinx/kernel_abi.py` runs the same parser and
  `check_issues()` during the docs build.
- `Documentation/Makefile` runs `get_abi.py validate` only when
  `CONFIG_WARN_ABI_ERRORS` is set; that option is inside `if COMPILE_TEST` in
  `Documentation/Kconfig`.
- `AbiParser` warns on, for example: a `Where:` tag, an unknown tag directly
  after a field other than `Description:`, an entry with no `Description:`,
  and one `What:` defined in more than one file.
- An unknown field name after `Description:` is taken as description text,
  with no warning.
- Nothing in the parser compares entries with kernel code; only `undefined`
  does a comparison, against a mounted sysfs.
- `scripts/checkpatch.pl` has no check for a missing ABI entry.
- `stable/` in `Documentation/ABI/README`: backward compatibility for at least
  2 years, not forever.
- `testing/` in `Documentation/ABI/README`: features may be added, but the
  current interface must not break except for grave errors or security
  problems.

**ABI entry fields**

- `Documentation/ABI/README` marks only `KernelVersion:` as "(Optional)";
  `What:`, `Date:`, `Contact:`, `Description:` and `Users:` are listed with no
  such mark.
- `AbiParser` in `tools/lib/python/abi/abi_parser.py` enforces less: for a
  missing field it warns only when an entry has no `Description:`; a missing
  `Date:`, `Contact:` or `Users:` passes `validate`.
- Directory for a new entry: `Documentation/ABI/README` leaves it to the
  developer who adds the interface, not to the maintainer.

## Groups

**Visibility callback results**

- `is_visible_const`: a second text callback in `struct attribute_group`,
  taking `const struct attribute *`; `create_files()` calls it when
  `is_visible` is NULL, with the same index and the same treatment of the
  result.
- `SYSFS_GROUP_INVISIBLE` in a callback result: `create_files()` clears it
  before the zero test, so a result of only that bit skips the file.
- Bits outside `SYSFS_PREALLOC | 0664`: `WARN()` "Invalid permissions", then
  dropped; the test also runs on the static mode when there is no callback.
- Evaluated again by the ownership walk as well as by `sysfs_update_group()`
  and `sysfs_update_groups()`: `sysfs_group_attrs_change_owner()` calls the
  callbacks to decide which names to look up, and does not apply the mode.

**Hiding a named group**

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

**Updating a group**

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

**Early group update**

- `kobj->sd` NULL with `update` set: `internal_create_group()` returns
  `-EINVAL` with no warning, for a named and an unnamed group alike.
- NULL `kobj`: `WARN_ON()` and `-EINVAL` in update mode too.
- After removal: `sysfs_remove_dir()` in `fs/sysfs/dir.c` sets `kobj->sd` to
  NULL, so an update after it gets the same silent `-EINVAL`.
- Nothing is recorded for later; the group appears only if a later call
  creates it, and that call evaluates the callbacks with the state at that
  time.

**Changing ownership**

- Exported: only `sysfs_group_change_owner()` and
  `sysfs_groups_change_owner()`, both `EXPORT_SYMBOL_GPL()`.
- Not exported, so not callable from a module: `device_change_owner()`,
  `sysfs_change_owner()`, `sysfs_file_change_owner()`,
  `sysfs_link_change_owner()`.
- `struct class` has no `dev_attrs` member; `dev_groups` is its only set of
  device groups.
- Power groups: `dpm_sysfs_change_owner()` in `drivers/base/power/sysfs.c`
  leaves out `pm_qos_resume_latency_attr_group` and
  `pm_qos_flags_attr_group`.
- Files and the group from `device_add_attrs()` that
  `device_attrs_change_owner()` leaves out: `dev_attr_waiting_for_supplier`,
  `dev_attr_removable`, `dev_attr_physical_location_group`.
- Hidden attribute: `sysfs_group_attrs_change_owner()` calls `is_visible`,
  `is_visible_const` or `is_bin_visible` with the index `create_files()` uses;
  0 skips the entry.
- `SYSFS_GROUP_INVISIBLE` from a callback during the walk: stops the walk of
  that array, and the remaining entries keep the old owner.
- Node missing while the callback reports it visible, or the group has no
  callback: `-ENOENT`, and the whole walk fails.
- Hidden named directory: `sysfs_group_change_owner()` looks the directory up
  before any callback and returns `-ENOENT` when it is absent.
- **Unsafe usage**: a named group that can return `SYSFS_GROUP_INVISIBLE`, in
  a set the walk covers on a device whose owner can change; while hidden,
  `device_change_owner()` fails with `-ENOENT`.
  - Safe: an unnamed group whose callback returns 0 for the entries left out
    at creation, as `netdev_phys_group` in `net/core/net-sysfs.c`;
    `sysfs_group_attrs_change_owner()` skips those entries.

**Functions that walk a group**

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

## Removal and lifetime

**Lifetime during show and store**

- `kernfs_fop_open()` in `fs/kernfs/file.c`: takes no counted reference on the
  node; `of->kn` is a plain pointer.
- Node pin for an open file: the `kernfs_get()` in `kernfs_init_inode()`
  (`fs/kernfs/inode.c`), held by the inode until `kernfs_evict_inode()`.
- `kernfs_get_active_of()`: what the file operations call; it fails on
  `of->released` before it tries `kernfs_get_active()` (see Open files at
  removal). Of the file operations in `fs/kernfs/file.c`, only
  `kernfs_fop_open()` calls `kernfs_get_active()` directly.
- `kobject_cleanup()` in `lib/kobject.c`: calls `__kobject_del()` when
  `state_in_sysfs` is set, before `t->release(kobj)`, so the ktype release
  runs after the drain even if the owner never called `kobject_del()`.
- Data other than the kobject: sysfs takes no reference on it;
  `sysfs_kf_seq_show()` and `sysfs_kf_write()` pass only the kobject and
  `of->kn->priv`. Sysfs orders its freeing against callbacks only through the
  drain: it can be freed once the removal of the file has returned, or from
  the ktype `release()`.

**Extent of a removal**

- `kernfs_remove_by_name_ns()` with a NULL parent: `WARN()` "kernfs: can not
  remove '%s', no directory", returns `-ENOENT`.
- `kobj->sd` is NULL after `sysfs_remove_dir()`, so `sysfs_remove_file()`,
  `sysfs_remove_bin_file()` and `sysfs_remove_link()` on that kobject hit that
  `WARN()`.
- Child kobject whose ancestor's directory was removed: its `kobj->sd` is
  stale, not NULL (pinned by `sysfs_get()` in `create_dir()`), so removals by
  name under it return `-ENOENT` silently, with no `WARN()`.

**Locks in show and store**

- **Unsafe usage**: a show or store, while it holds its active reference,
  blocks on a lock that some path holds while it removes that attribute, its
  group, its directory or its device. `kernfs_drain()` waits with a plain
  `wait_event()`, no timeout.
  - Safe: trylock, and `restart_syscall()` on failure, as
    `lock_device_hotplug_sysfs()` in `drivers/base/core.c` and
    `bond_opt_tryset_rtnl()` in `drivers/net/bonding/bond_options.c` (called
    from `bonding_sysfs_store_option()`).
  - Safe: drop the active reference before blocking, as `sysfs_rtnl_lock()` in
    `net/core/net-sysfs.c`: `dev_hold()`, `sysfs_break_active_protection()`,
    `rtnl_lock_interruptible()`, `dev_isalive()` check, then unbreak.
- `ignore_lockdep` (a field of `struct attribute` only under
  `CONFIG_DEBUG_LOCK_ALLOC`): only makes `sysfs_add_file_mode_ns()` and
  `sysfs_add_bin_file_mode_ns()` pass a NULL key, so the node lacks
  `KERNFS_LOCKDEP`; `kernfs_drain()` still waits, so a real cycle still hangs.
- Purpose of `ignore_lockdep`: every node built from one `struct attribute`
  shares one lock class, so a store that removes another object's node of the
  same attribute looks recursive to lockdep.
- Macros that set it: `__ATTR_IGNORE_LOCKDEP()`, `DEVICE_ATTR_IGNORE_LOCKDEP()`,
  `__DEVICE_ATTR_IGNORE_LOCKDEP()`, and a file-local
  `DRIVER_ATTR_IGNORE_LOCKDEP()` defined in `drivers/base/bus.c` and again in
  `drivers/dma/idxd/compat.c`.
- Users: search `IGNORE_LOCKDEP`; for example `unbind` and `bind` in
  `drivers/base/bus.c`, `remove` in `drivers/usb/core/sysfs.c`.
- `drivers/pci/pci-sysfs.c`: only `remove` uses it, together with
  `device_remove_file_self()`; `dev_attr_dev_rescan` is a plain `__ATTR()`.
- `sysfs_attr_init()`: needed for a dynamically allocated attribute; without
  it the key falls back to `&attr->skey` in non-static memory, and
  `lockdep_init_map_type()` prints "BUG: key ... has not been registered!" and
  turns lockdep off.

**Removing from a callback**

- `kernfs_remove_self()`: takes `kernfs_supers_rwsem` (read) and `kernfs_rwsem`
  (write) first, then drops the active reference; it restores the reference
  before unlocking.
- `sysfs_remove_file_self()` and `sysfs_break_active_protection()`: look the
  file up by `attr->name` directly under `kobj->sd`; an attribute inside a
  named group is not found.
- `sysfs_remove_file_self()`, file not found: `WARN_ON_ONCE()`, returns false.
- `sysfs_break_active_protection()`, file not found: returns NULL, has already
  dropped its kobject reference, and the active reference is still held.
- `sysfs_unbreak_active_protection()`: dereferences its argument, so it must
  not be given NULL; `sdev_store_delete()` in `drivers/scsi/scsi_sysfs.c`
  tests for NULL first.
- After `sysfs_break_active_protection()`: the callback removes its own file
  with plain `device_remove_file()`, not the self form; see
  `sdev_store_delete()`.
- `sysfs_break_active_protection()` with two writers: no arbitration, both
  run the removal. In `sdev_store_delete()` that is tolerated:
  `device_remove_file()` ignores a missing file while the directory exists,
  and `__scsi_remove_device()` returns early at `SDEV_DEL` under `scan_mutex`.
  `scsi_device_get()` there pins the device; it does not arbitrate.
- **Potentially unsafe usage**: touching the device or kobject after the
  callback's active reference was dropped.
  - Unsafe: when no reference on it was taken before the drop;
    `sysfs_remove_file_self()` and `device_remove_file_self()` take none.
    Once the node is unlinked no remover waits for this callback in
    `kernfs_drain()`, so the object can be freed under it. This covers a
    false return from `sysfs_remove_file_self()` too: by then the winner's
    whole operation has finished.
  - Safe: the callback takes the reference while the active reference is
    still held, as `sdev_store_delete()` does with `scsi_device_get()` before
    `sysfs_break_active_protection()`.
  - Safe: the kobject, between a non-NULL return of
    `sysfs_break_active_protection()` and `sysfs_unbreak_active_protection()`;
    the first does `kobject_get()` before it drops the active reference and
    the second puts it, as `interface_authorized_store()` in
    `drivers/usb/core/sysfs.c` relies on.

**Kernfs locks**

| Job | Lock | Scope | Easy to miss |
|---|---|---|---|
| tree of nodes | `kernfs_rwsem` | per root | field of `struct kernfs_root` in `fs/kernfs/kernfs-internal.h` |
| inode attributes | `kernfs_iattr_rwsem` | per root | also covers `dir.subdirs`, `dir.rev` and the `KERNFS_REMOVING` marking pass; xattr sets use the hashed mutex instead |
| list of superblocks | `kernfs_supers_rwsem` | per root | written in `kernfs_get_tree()` and `kernfs_kill_sb()`; the struct comment naming `kernfs_rwsem` does not match the code |
| renames | `kernfs_rename_lock`, an `rwlock_t` | per root | write-locked in `kernfs_rename_ns()` only when the parent changes; a same-parent rename swaps `name` under RCU |
| per-node list of open files | `node_mutex[]` in `struct kernfs_global_locks` | hashed per node, one global array | via `kernfs_node_lock_ptr()`; `kernfs_open_file_mutex_ptr()` and `kernfs_open_file_mutex_lock()` are wrappers in `fs/kernfs/file.c` |
| a single open file | `mutex` in `struct kernfs_open_file` | per open file | nests outside the active reference |
| notification list | `kernfs_notify_lock` | global | static spinlock in `fs/kernfs/file.c` |
| id allocator | `kernfs_idr_lock`, a spinlock | per root | lookup by id uses RCU only |

- Names absent from this tree: open_file_mutex[], kernfs_open_node_lock.
- Order in removal:
  1. `kernfs_remove()`: `kernfs_supers_rwsem` for read, then `kernfs_rwsem` for
     write; `__kernfs_remove()` asserts both.
  2. Marking pass: `kernfs_iattr_rwsem` for write, nested inside.
  3. `kernfs_drain()`: releases `kernfs_rwsem`, then `kernfs_supers_rwsem`.
  4. `kernfs_drain_open_files()`: hashed node mutex, taken alone.
  5. `kernfs_drain()` exit: `kernfs_supers_rwsem` for read, then `kernfs_rwsem`
     for write.
  6. `kernfs_unlink_sibling()` and the cleanup after it: `kernfs_iattr_rwsem`
     for write, nested inside.
  7. Last `kernfs_put()`: `kernfs_idr_lock`.
- `kernfs_remove_self()` and `kernfs_remove_by_name_ns()`: same first two locks
  in the same order.
- `kernfs_show()`: does not take `kernfs_supers_rwsem`; it takes `kernfs_rwsem`
  and calls `kernfs_drain()` with `drop_supers` false.
- Removal does not take `kernfs_rename_lock`, `kernfs_notify_lock` or the
  `mutex` of any `struct kernfs_open_file`.

**Kernfs removal sequence**

- `__kernfs_remove()` early return: tests `kernfs_parent(kn) &&
  RB_EMPTY_NODE(&kn->rb)`, that is, already unlinked; it does not test
  `KERNFS_REMOVING`.
- Deactivation: there is no kernfs_deactivate() here; `__kernfs_remove()` adds
  `KN_DEACTIVATED_BIAS` inline, in a post-order walk with
  `kernfs_next_descendant_post()`.
- `kernfs_drain()`: deactivates nothing; it does `WARN_ON_ONCE()` if the node
  is still active.
- `kernfs_drain()` early return: when the count is already at
  `KN_DEACTIVATED_BIAS` and `kernfs_should_drain_open_files()` is false, it
  returns without dropping any lock.
- Second remover of a node that is still linked: passes the early test,
  drains as well and returns only after the drain; only the cleanup is
  skipped for the caller that loses `kernfs_unlink_sibling()`.
- Unlink winner: also calls `kernfs_clear_inode_nlink()`, which walks
  `root->supers` and does `clear_nlink()` on each cached inode of the node;
  this is why `kernfs_supers_rwsem` is held.
- Root node (no parent): the cleanup branch runs without
  `kernfs_unlink_sibling()`.

**Open files at removal**

- `kernfs_drain_open_files()`: walks the list under the hashed node mutex
  only; it does not take `of->mutex`. `kernfs_release_file()` asserts the
  hashed mutex.
- Trigger: `kernfs_should_drain_open_files()` tests the counters `nr_mmapped`
  and `nr_to_release` of `struct kernfs_open_node`, not the node flags; an
  open file that never called mmap does not trigger the unmap.
- `of->vm_ops`: left as it is; the drain clears `of->mmapped` and decrements
  `nr_mmapped`.
- Unmap target: `file_inode(of->file)->i_mapping`. VMAs are linked to
  `vm_file->f_mapping` (`vma_link_file()` in `mm/vma.c`), and
  `sysfs_kf_bin_open()` replaces `f_mapping` when `struct bin_attribute` has
  `f_mapping` set (PCI resource files use `iomem_get_mapping()`), so this
  unmap does not reach mappings of those files.
- `of->released`: set by the drain's release, only on a node with
  `KERNFS_HAS_RELEASE`, and never cleared; `kernfs_get_active_of()` then fails
  for every later operation on that open file.
- `kernfs_show()` with show false: runs the same drain, so hiding a node also
  zaps its mappings and, on a node with `KERNFS_HAS_RELEASE`, releases its
  open files; the released open files stay dead after the node is shown
  again.

## Kobjects and the driver core

**Groups the driver core creates**

| Pointer | Created in | Relative to uevent and probe | Removed in, relative to the remove callback |
|---|---|---|---|
| `dev_groups` in `struct class`, `groups` in `struct device_type`, `groups` in `struct device` | `device_add_attrs()` | before `KOBJ_ADD` and probe | `device_remove_attrs()` in `device_del()`, before `bus_remove_device()` unbinds, so before the callback |
| `dev_groups` in `struct bus_type` | `bus_add_device()` | before `KOBJ_ADD` and probe | `bus_remove_device()`, before its `device_release_driver()`, so before the callback |
| `dev_groups` in `struct device_driver` | `really_probe()` | after `KOBJ_ADD`, after `call_driver_probe()` returned 0, before `KOBJ_BIND` | `device_remove()` in `drivers/base/dd.c`, before it calls the callback |
| `groups` in `struct device_driver` | `driver_register()` | driver directory; after `bus_add_driver()` returned, so after `driver_attach()`; before the driver's `KOBJ_ADD` | `driver_unregister()`, before `bus_remove_driver()`, so before `driver_detach()` |
| `drv_groups` in `struct bus_type` | `bus_add_driver()` | driver directory; after `driver_attach()`; before the driver's `KOBJ_ADD` | `bus_remove_driver()`, before `driver_detach()` |
| `bus_groups`, `class_groups` | `bus_register()`, `class_register()` | after `kset_register()` has sent `KOBJ_ADD` for the directory | `bus_unregister()`, `class_unregister()` |
| `default_groups` in `struct kobj_type` | `create_dir()` in `lib/kobject.c`, from `kobject_add_internal()` | with the directory; `kobject_add()` sends no uevent; no probe | `__kobject_del()`, before `sysfs_remove_dir()`; no remove callback |

- Probe before the `kobject_uevent()` call for `KOBJ_ADD` in `device_add()`:
  cannot happen; `__driver_probe_device()` returns `-EPROBE_DEFER` until
  `device_add()` has called `dev_set_ready_to_probe()`, which comes after
  `kobject_uevent()`.
- `dev_groups` of the driver, creation fails: `really_probe()` calls
  `device_remove()`, so the remove callback runs, and the bind fails.
- `drv_groups` creation fails: `bus_add_driver()` prints an error and still
  returns 0.
- `driver_override` in `struct bus_type`: a `bool`, not a group pointer; when
  set, `bus_add_device()` creates `driver_override_dev_group` right after the
  bus `dev_groups`, and `bus_remove_device()` removes it.

**Attributes and the add uevent**

- Earliest point for a create call: after `kobject_add()` or `device_add()`
  made the directory; before that `kobj->sd` is NULL and
  `sysfs_create_file_ns()` and `internal_create_group()` hit `WARN_ON()` and
  return `-EINVAL`.
- **Potentially unsafe usage**: `device_create_file()` or
  `sysfs_create_group()` on a device after `device_add()` returned.
  - Unsafe: when user space is to find the file on the "add" event and uevents
    were not suppressed; `device_add()` has already sent `KOBJ_ADD`.
  - Safe: `dev_set_uevent_suppress()` set before `device_add()`, cleared after
    the create calls, then `KOBJ_ADD` sent by hand, as
    `workqueue_sysfs_register()` does; `kobject_uevent_env()` drops events
    while `uevent_suppress` is set.
  - Safe: from a `BUS_NOTIFY_ADD_DEVICE` notifier, which `device_add()` calls
    before `kobject_uevent()`, as `usb_bus_notify()` does; removal is then
    explicit, on `BUS_NOTIFY_DEL_DEVICE`.
  - Safe: inside probe, as `max197_probe()` in `drivers/hwmon/max197.c`, for
    a file user space looks for on the "bind" event; `driver_bound()` sends
    `KOBJ_BIND` after `call_driver_probe()` returned. The driver removes the
    file itself.
- Plain kobject: `kobject_add()`, `kobject_init_and_add()` and
  `kobject_create_and_add()` send no uevent, so a create call after them
  races with nothing unless the caller sends `KOBJ_ADD` first;
  `driver_register()` sends it after the groups.
- `kset_register()` and `kset_create_and_add()`: call `kobject_uevent()` for
  `KOBJ_ADD` themselves, so files added to a kset directory always come after
  it.
- `devm_device_add_group()`: is itself a create call, and the only devm
  attribute helper declared in `include/linux/device.h`; there is no
  devm_device_add_groups.
- `devm_device_add_group()` removal: `devm_attr_group_remove()` runs from
  `devres_release_all()` in `device_unbind_cleanup()`, after the remove
  callback returned; driver `dev_groups` are removed before the callback is
  called.
- `faux_device_create_with_groups()`: no create call and no removal call, but
  `faux_probe()` creates the groups, so they appear after `KOBJ_ADD`.

**Kobject add and release**

- After a failed `kobject_add_internal()`: the kset is left, the parent put and
  `kobj->parent` cleared; the name is all that remains allocated.
- Name: freed by `kobject_cleanup()` itself, after `release()` returned, from a
  pointer saved at entry; `release()` does not free it.
- `kset_register()` failure: frees the name and sets it to NULL itself;
  callers such as `kset_create_and_add()` and `bus_register()` then free the
  container with `kfree()`.
- `KOBJ_REMOVE` on the final put: sent inside `__kobject_del()`, only if
  `KOBJ_ADD` was sent and `KOBJ_REMOVE` was not, after `default_groups` are
  removed and before `sysfs_remove_dir()`; never sent for a kobject that is
  not in sysfs.
- `CONFIG_DEBUG_KOBJECT_RELEASE`: `kobject_release()` defers the whole of
  `kobject_cleanup()` by 1 to 4 seconds, so the directory and its files stay
  in sysfs after the final `kobject_put()` returned.
- Code that needs the directory gone at a known point: calls `kobject_del()`
  before the put.
- `__kobject_del()`: clears `kobj->parent` but does not put the parent.
- Parent reference: `kobject_del()` puts it right after `__kobject_del()`;
  without an explicit delete, `kobject_cleanup()` puts it last, after
  `release()` and after the name is freed.
- `struct kobj_type` with no `release()`: `kobject_cleanup()` only prints with
  `pr_debug()`; `device_release()` in `drivers/base/core.c` is what uses
  `WARN()`, for a `struct device`.

**Unwinding partial setup**

- Failed `sysfs_create_group()`, unnamed group: `remove_files()` removes every
  attribute name of the group from the directory, including a same-named file
  that was there before the call.
- `sysfs_remove_group()` on a group that is not there: no warning; a named
  group gets `pr_debug()` and return, an unnamed one a silent `-ENOENT` from
  `kernfs_remove_by_name_ns()`.
- **Unsafe usage**: `sysfs_remove_group()` or `sysfs_remove_file()` on a
  kobject whose directory is gone, so `kobj->sd` is NULL: after
  `kobject_del()` or after a failed add. A named group dereferences NULL in
  `kernfs_root()`; an unnamed group or a file hits `WARN()` for each name in
  `kernfs_remove_by_name_ns()`.
  - Safe: remove the group before `kobject_del()`, as `device_del()` does with
    `device_remove_attrs()`.
  - Safe: no removal at all when the next step is the delete or the final put,
    as `example_exit()` in `samples/kobject/kobject-example.c`;
    `sysfs_remove_dir()` removes the subtree.
- Order of puts between a parent and its child: not what keeps the parent
  alive; the child holds a reference on the parent from
  `kobject_add_internal()` until its own `kobject_del()` or the end of its
  `kobject_cleanup()`.
- Child directory after an ancestor's directory was removed: `create_dir()`
  took an extra reference with `sysfs_get()`, so the child's `kobj->sd` stays
  valid until its own `__kobject_del()`.

**Namespace tags**

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

## Model gaps

### Other mistakes models make

- Models take `device_change_owner()` to work for any device in sysfs. For a
  device without a class it returns `-EINVAL` from the `class_to_subsys()`
  test, after ownership of the directory and groups has already changed.
- `struct kobj_type` without `release()`: at the final put nothing in
  `kobject_cleanup()` frees the object.
- Models take a file operation to fail with `-ENODEV` only when the node is
  deactivated. `kernfs_get_active_of()` in `fs/kernfs/file.c` also fails once
  `of->released` is set; only `kernfs_release_file()` sets it, and its callers
  call it only for a node with `KERNFS_HAS_RELEASE`. No sysfs table has a
  `release` op, so it is never set on a sysfs file.
- Models name kernfs_create_file_ns() and kernfs_create_file() as the file
  constructors. Neither exists here; callers use `__kernfs_create_file()` and
  pass the lockdep key, or NULL, themselves.
