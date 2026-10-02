# What the sysfs measurement found

Three models were asked the 39 questions in `sysfs-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader A said it assumed kernels 6.10 to
6.16, reader C 6.13 to 6.19, and both describe sysfs, kernfs and the kobject
core correctly in outline; reader C needed the fewest corrections. Reader B
said 6.10 to 6.12 and was wrong about fundamentals: what a visibility callback
returning zero does, what an open file pins, and what a store callback is
handed. The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

Sysfs is old and its outline is well known. What the readers got wrong is
what has changed in the last few releases (the const variants of every
callback, the namespace tag type, the kernfs lock layout), the error and
failure paths that few people read (ownership change, a failed group update,
which message a bad show count produces), and what is and is not exported.

## What all three readers got wrong

- **Const handler variants.** None knew that `struct device_attribute` and
  `struct kobj_attribute` carry `show_const` and `store_const` beside `show`
  and `store`, wrapped in `__SYSFS_FUNCTION_ALTERNATIVE()` (a union, or a
  struct when `CONFIG_CFI` is set). Reader A said in so many words that no
  const signatures exist. `dev_attr_show()` and `kobj_attr_show()` try the
  plain pointer, then the const one, then return `-EIO`. The same pairing
  exists in `struct attribute_group` as `is_visible_const` and `attrs_const`:
  reader A named bin_attrs_new, which is gone, reader B said no union is used,
  and reader C listed the structure correctly and then doubted the const
  callback in two other answers.
- **Namespace tags** are `const struct ns_common *`, not `const void *`, in
  every sysfs and kernfs prototype and in `struct kobj_type`'s `namespace()`.
  Kernfs compares them by namespace id, not by address.
- **Who may call the ownership functions.** All three said every function is
  exported. Only `sysfs_group_change_owner()` and `sysfs_groups_change_owner()`
  are; `device_change_owner()`, `sysfs_change_owner()`,
  `sysfs_file_change_owner()` and `sysfs_link_change_owner()` are not.
- **What the ownership walk does with a file that was never created.** Each
  was wrong a different way. Reader A said an attribute a callback left out
  gives `-ENOENT`; reader B said every missing entry is skipped silently;
  reader C said binary attributes are looked up unconditionally.
  `sysfs_group_attrs_change_owner()` calls `is_visible()`, else
  `is_visible_const()`, and `is_bin_visible()`, skips mode 0, and stops the
  array on `SYSFS_GROUP_INVISIBLE`. A named group whose directory was hidden
  still fails the whole operation with `-ENOENT`, because the directory lookup
  in `sysfs_group_change_owner()` comes before any callback. None covers
  `bus->dev_groups` or a driver's `dev_groups`.
- **The walkers disagree with each other.** No reader saw that
  `create_files()` strips `SYSFS_GROUP_INVISIBLE` from every result while
  the ownership walker breaks out of the array on it at any index, or that
  `remove_files()`, `sysfs_merge_group()` and `sysfs_unmerge_group()` call no
  callback. Reader A said the ownership walker uses names only; reader B
  offered a helper that does not exist.
- **Hiding a named group.** Readers B and C said the directory is left out
  when every callback returns zero. Only `SYSFS_GROUP_INVISIBLE` from
  `__first_visible()` does it, only index 0 is asked, and the text callback
  wins over the binary one. Reader A put the binary helper macros in
  `.is_visible`; they define a binary callback and go in `.is_bin_visible`.
- **A failed group update.** Readers A and C said the named directory is
  removed; reader B said a mix of old and new files is left. The directory is
  removed only if this call created it; an existing one survives, emptied of
  the group's files.
- **Removing a group that is not there.** All three said `sysfs_remove_group()`
  warns. It calls `pr_debug()` and returns.
- **A bad count from show.** Each reader swapped or lost a message.
  `sysfs_kf_seq_show()` does a `WARN` ("OOB write or bad count") and
  `sysfs_kf_read()`, the preallocated path, prints "fill_read_buffer ...
  returned bad count"; both clamp to a page less one. `dev_attr_show()` only
  prints and does not clamp. Only the seq_file buffer is zeroed.
- **Kernfs locks.** Every reader gave the hashed per-node mutexes a name that
  does not exist; they are `kernfs_locks->node_mutex[]` and also cover xattr
  updates. All left `kernfs_supers_rwsem` out of the removal order, and
  readers A and B called locks global (the rename and id locks, the main
  rwsem) that are fields of `struct kernfs_root`.
- **Which operations table a text file gets** depends on the ktype's
  `struct sysfs_ops`, not on the attribute's own handlers; the attribute's
  mode only matters for `SYSFS_PREALLOC`. A binary attribute with no read or
  write callback gets a table without that operation, so open(2) fails with
  `-EACCES` under `KERNFS_ROOT_EXTRA_OPEN_PERM_CHECK`; `-EIO` is reached only
  through the mmap table.
- **Documentation and tests.** All said there is no kernfs selftest;
  `tools/testing/selftests/filesystems/kernfs_test.c` exists. Two named the
  ABI checker as a script under scripts/; it is `tools/docs/get_abi.py`. Two
  made `Users:` optional; `Documentation/ABI/README` marks only
  `KernelVersion:` so. Two said new entries normally go in `testing/`; the
  README leaves the level to the developer.
- **Builds without sysfs.** All said `sysfs_get_dirent()` returns NULL. It is
  not a stub; the stubs a caller must not rely on are
  `sysfs_break_active_protection()` (NULL) and `sysfs_remove_file_self()`
  (false).

## What only some readers got wrong

- **Reader B on fundamentals.** A visibility callback returning zero creates
  the file with its default mode (it skips the file); an update changes the
  mode in place with `kernfs_setattr()` (it removes and re-adds); open(2)
  takes a kobject reference for the life of the descriptor (it takes none,
  and removal drains active references instead); a write longer than a page
  is rejected (truncated), a zero-length write reaches store (it does not),
  and a zero return means failure (only a negative one does);
  `sysfs_emit(buf + n)` miscounts (it warns and writes nothing);
  `VERIFY_OCTAL_PERMISSIONS()` forbids execute bits (it does not check them);
  a missing `sysfs_ops` does not block creation (`-EINVAL` and a `WARN`);
  `really_probe()` creates no groups (it adds the driver's `dev_groups`);
  groups may be added before `device_add()` (`-EINVAL` without `kobj->sd`);
  an explicit `sysfs_remove_group()` is needed before the last
  `kobject_put()` (removal of the directory is recursive); managed helpers
  that are gone are still exported (only `devm_device_add_group()` is left).
- **Reader B on kernfs.** The parent field is `parent` (it is `__parent`,
  RCU-protected, read through `kernfs_get_parent()`); removal unlinks before
  it deactivates (the reverse); `kernfs_notify()` defers the wakeup (only
  fsnotify is deferred); resctrl is not a kernfs user.
- **Probe and the add event** (readers A and B). Probe runs after the "add"
  uevent, so files created from probe race too; the driver's `dev_groups`
  appear after "add" and before "bind". The class, type, device and bus
  groups are removed before the driver's remove callback, not after.
- **The parent reference** (readers A and C). `kobject_cleanup()` puts the
  parent only when the kobject was still in sysfs; after `kobject_del()` the
  put has already happened there.
- **Lockdep and removal** (readers A and C). Reader A knew of no in-tree user
  of `ignore_lockdep`; there are several (`DEVICE_ATTR_IGNORE_LOCKDEP()` on
  the PCI `remove` file, `bind` and `unbind` in `drivers/base/bus.c`). Reader
  C described `sysfs_rtnl_lock()` as a trylock and restart; it pins the
  device, breaks active protection and takes the lock interruptibly.
- **What an open file holds** (reader A). Not a node reference from
  `kernfs_fop_open()`; the inode holds it. Reads and writes go through
  `kernfs_get_active_of()`, which also fails once the file was released by a
  drain (reader C).
- **Reader A alone.** A second `kobject_put()` after a failed
  `kobject_create_and_add()` as a double free (the function returns NULL and
  the put is a no-op); the lockdep message for a dynamic attribute without
  `sysfs_attr_init()`.
- **What the sysfs document asks** (readers A and B). Neither a trailing
  newline nor tolerance of one is in `Documentation/filesystems/sysfs.rst`;
  only its example has one.

## What the readers already knew

Readers A and C: where the files are, how a directory, file and symlink map
onto kernfs nodes, the formatting helpers and their alignment rule, the store
buffer, the permission checks, that removal waits for running callbacks and
later reads get `-ENODEV`, self-removal and its helpers, that removing a
directory is recursive, merging into a group, symlinks and
`sysfs_symlink_target_lock`, notification and poll, the operations table a
ktype must supply, what to do when `kobject_init_and_add()` fails, and (reader
C) the table of groups the driver core creates.

## Where the hand-written guide is stale

- Its first paragraph describes `sysfs_group_attrs_change_owner()` failing with
  `-ENOENT` on an attribute whose callback returned zero as what happens, and
  a later line says the function already checks. In this tree it checks. What
  still fails is a named group whose directory was hidden, which the guide
  does not mention.
- Its "correct" loop calls `is_visible()` only. A walker in this tree also has
  to call `is_visible_const()` when `is_visible` is unset, and the arrays may
  be `attrs_const`.
- It says either callback may return `SYSFS_GROUP_INVISIBLE` to hide a named
  group. Only the first attribute's result is looked at, and a text callback,
  if there is one, decides even when the group also has binary attributes.
- Its call chain sends the device's groups through `sysfs_change_owner()`.
  That function covers the ktype's default groups; the class, type and device
  groups go through `device_attrs_change_owner()`.
- It says a child's release drops the parent. That is so only while the child
  is still in sysfs; `kobject_del()` drops it earlier.
- It says nothing of the show buffer, of locks taken in callbacks against
  removal, of the group pointers the driver core creates on its own, or of
  the const callback variants, all of which load under the same trigger.
- Its "review trigger" tells a reviewer what to go and check. The build set
  asks for the unsafe usage and the correct usage that looks like it.

## What was left out of the build set and why

The build set has 14 of the 39 questions, sized to the 698 words of the
hand-written guide. Left out:

- What readers A and C answer and only the oldest reader does not: the
  formatting helpers, the store buffer, permission bits, self-removal, the
  extent of a removal, dynamic attributes, symlinks, duplicate names,
  notification, merging into a group, the operations table requirement,
  managed helpers, the definition macros, attribute content conventions.
- What all got partly wrong but few patches under this guide's trigger touch:
  kernfs locks, kernfs node fields, the removal sequence, other kernfs users,
  builds without sysfs, the ABI documentation rules, the documentation and
  tests. They stay in the measurement set; a kernfs guide would want them.
- Binary attributes: the const callback signatures are caught by the compiler
  and the missing-callback error is rare.
- Folded into a kept question: attributes created after the add event (the
  table of groups the driver core creates gives the order against the uevent
  and probe); kobject add and release (unwinding partial setup asks what the
  failed calls have already undone); sysfs on top of kernfs (the active
  reference question says what a callback can rely on).

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           80        29%      7     11   6.10 to 6.16
reader B          104        76%      1     38   6.10 to 6.12
reader C           68        21%     13      5   6.13 to 6.19

question                          reader A      reader B      reader C   verdict
sysfs.core-files                   4% ( 0)       0% ( 2)       0% ( 0)   all fair: drop, or shrink to a pointer
sysfs.docs                        17% ( 1)      61% ( 2)      25% ( 1)   weak: reader B
sysfs.layering                    34% ( 4)      80% ( 4)      31% ( 4)   weak: reader B
sysfs.attribute-group-fields      38% ( 1)      73% ( 1)       0% ( 0)   weak: reader B
sysfs.attr-handler-types          70% ( 1)      68% ( 1)      54% ( 2)   all weak
sysfs.definition-macros           24% ( 1)      70% ( 1)      34% ( 2)   weak: reader B
sysfs.bin-attribute               26% ( 1)      64% ( 2)      16% ( 2)   weak: reader B
sysfs.ns-tags                     58% ( 1)      76% ( 2)      27% ( 1)   weak: reader A, reader B
sysfs.kernfs-node-fields          15% ( 2)      89% ( 4)      22% ( 5)   weak: reader B
sysfs.kernfs-locks                36% ( 3)      82% ( 6)      22% ( 3)   weak: reader B
sysfs.kernfs-users                17% ( 1)      92% ( 1)      28% ( 1)   weak: reader B
sysfs.visibility-semantics        24% ( 5)      84% ( 4)      21% ( 2)   weak: reader B
sysfs.group-invisible             40% ( 2)      89% ( 3)      48% ( 1)   all weak
sysfs.update-group                24% ( 2)      89% ( 4)      45% ( 1)   weak: reader B, reader C
sysfs.change-owner                40% ( 4)      88% ( 5)      31% ( 3)   weak: reader A, reader B
sysfs.merge-group                 16% ( 1)      83% ( 1)      15% ( 1)   weak: reader B
sysfs.show-buffer                 49% ( 4)      78% ( 4)      16% ( 1)   weak: reader A, reader B
sysfs.emit-helpers                25% ( 1)      79% ( 3)       3% ( 1)   weak: reader B
sysfs.store-semantics             18% ( 2)      77% ( 3)       3% ( 1)   weak: reader B
sysfs.mode-rules                  21% ( 2)      70% ( 4)      19% ( 1)   weak: reader B
sysfs.active-refs                 27% ( 4)      81% ( 2)       6% ( 4)   weak: reader B
sysfs.locks-in-callbacks          37% ( 1)      86% ( 1)      30% ( 3)   weak: reader B
sysfs.self-removal                36% ( 3)      83% ( 2)       9% ( 1)   weak: reader B
sysfs.removal-scope                8% ( 1)      70% ( 1)      11% ( 1)   weak: reader B
sysfs.dynamic-attrs               47% ( 2)      90% ( 2)      12% ( 0)   weak: reader A, reader B
sysfs.symlinks                    28% ( 1)      64% ( 4)      13% ( 1)   weak: reader B
sysfs.duplicate-names             51% ( 2)      80% ( 3)      17% ( 1)   weak: reader A, reader B
sysfs.notify-poll                  6% ( 0)      81% ( 3)      26% ( 1)   weak: reader B
sysfs.driver-core-groups          16% ( 4)      57% ( 6)       1% ( 1)   weak: reader B
sysfs.uevent-race                 13% ( 2)      75% ( 1)      19% ( 1)   weak: reader B
sysfs.devm-groups                  0% ( 0)      82% ( 1)      16% ( 1)   weak: reader B
sysfs.attr-needs-ktype             9% ( 0)      80% ( 2)      14% ( 0)   weak: reader B
sysfs.kobject-lifecycle           21% ( 2)      68% ( 3)       4% ( 2)   weak: reader B
sysfs.kobject-error-unwind        30% ( 3)      66% ( 2)      36% ( 5)   weak: reader B
sysfs.one-value-rule              41% ( 1)      87% ( 1)      23% ( 1)   weak: reader A, reader B
sysfs.abi-docs                    48% ( 3)      79% ( 3)      29% ( 3)   weak: reader A, reader B
sysfs.group-walkers               50% ( 4)      92% ( 6)      44% ( 2)   all weak
sysfs.removal-sequence            29% ( 5)      89% ( 3)      22% ( 5)   weak: reader B
sysfs.config-off                  61% ( 3)      83% ( 1)      57% ( 2)   all weak
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `sysfs.layering`, `sysfs.bin-attribute`, `sysfs.kernfs-locks`, `sysfs.emit-helpers`, `sysfs.store-semantics`, `sysfs.mode-rules`, `sysfs.self-removal`, `sysfs.removal-scope`, `sysfs.uevent-race`, `sysfs.kobject-lifecycle`, `sysfs.abi-docs`, `sysfs.removal-sequence`.

## Questions reorganised

Grouped by subject: attributes and their callbacks, groups, removal and lifetime, kobjects and the
driver core. 28 questions became 26.
Merged: `sysfs.attribute-group-fields` and `sysfs.attr-handler-types` into `sysfs.const-alternatives`;
both asked for the members of a structure, and what readers lacked in both was the const alternative.
Dropped: `sysfs.core-files`, an inventory every reader answered (marked "drop" in the table above),
so the file has no "Where to look" part. `sysfs.layering`, `sysfs.bin-attribute`, `sysfs.kernfs-locks`,
`sysfs.removal-sequence`, `sysfs.change-owner` and `sysfs.group-walkers` were reworded from "list" and
"which functions" into contracts.
