# What the vfs measurement found

Three models were asked the 67 questions in `vfs-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C. Reader C
is the most current, reader A is a few releases behind it, and reader B is
several releases behind that; which models they were does not matter here. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted below.

## What all three readers got wrong

Almost all of it is names and layouts that have moved. The mechanisms were
described correctly by readers A and C nearly everywhere.

- **The by-name entry points in `fs/namei.c` were renamed and no longer consume
  the name.** All three offered do_filp_open(), do_unlinkat(), do_mkdirat(),
  do_rmdir() and do_renameat2(). The tree has `do_file_open()`,
  `filename_unlinkat()`, `filename_mkdirat()`, `filename_rmdir()` and
  `filename_renameat2()`. None of them calls `putname()`; the system call owns
  the name through `CLASS(filename, ...)`.
- **The permission helpers for create and delete** are `may_create_dentry()` and
  `may_delete_dentry()`. All three used the old names without the suffix.
- **`struct super_block` is in `include/linux/fs/super_types.h`**, not
  `include/linux/fs.h`, and its passive count is `s_passive`, a `refcount_t`.
  All three described an s_count integer kept under `sb_lock`; two also
  offered __put_super(), which does not exist.
- **The old mount interface is gone.** All three said the mount method of
  `struct file_system_type`, mount_bdev(), mount_nodev(), mount_single() and
  the remount_fs superblock method still exist. None does. A filesystem
  supplies `init_fs_context()`, and remount arrives through `->reconfigure()`.
- **`struct dentry` has no d_u union.** The union is anonymous and holds
  `d_alias`, `d_in_lookup_hash`, `d_rcu` and `waiters`. Readers A and C gave the
  assertion in `d_instantiate()` as a test of d_u.d_alias being unhashed, and
  reader B had it require an unhashed dentry; it is
  `BUG_ON(d_really_is_positive(entry))`.
- **`d_alloc_parallel()` takes two arguments.** All three passed it a wait
  queue, and two had waiters sleep on a d_wait field. There is no such field;
  waiters set `DCACHE_LOOKUP_WAITERS` and wait on `d_flags`.
- **Helpers that do not exist for rechecking a dentry after locking its
  parent.** All three offered lock_parent(), ovl_parent_lock() or the static
  `lock_rename_child()`. The exported helpers are `start_creating_dentry()`,
  `start_removing_dentry()` and `start_renaming_two_dentries()`, which check the
  parent pointer, the hash and `IS_DEADDIR()` under the lock. Only reader C
  named them, and only reader C listed the dead-directory check.
- **`I_MUTEX_XATTR`** was described as the class for xattr directories or as
  unused. Its only users are the ext4 EA inodes.
- **A failed open can still reach the release method.** `do_dentry_open()` sets
  `FMODE_OPENED` and can then fail the `O_DIRECT` check, and `do_open()` can fail
  in truncation; `__fput()` then calls `->release()`.
- **Timestamps**: all three were weak on the multigrain details. Left out of
  the guide as too narrow.
- **Selftests**: the openat2 tests are under
  `tools/testing/selftests/filesystems/openat2/`.

## What readers A and B got wrong as well

- `lock_rename()`, `lock_rename_child()` and `unlock_rename()` are static in
  `fs/namei.c`. Both said they are exported for stacking filesystems. Outside
  callers use `start_renaming()`, `start_renaming_dentry()`,
  `start_renaming_two_dentries()` and `end_renaming()`.
- kern_path_create(), done_path_create() and kern_path_locked() do not exist.
  The tree has `start_creating_path()`, `end_creating_path()`,
  `start_removing_path()`, `end_removing_path()` and `kern_path_parent()`.
- When `vfs_mkdir()` fails it has already unlocked the parent and dropped the
  dentry, through `end_creating()`. Both said the parent stays locked.
- `vfs_rename()` has no check that gives `-EXDEV`. That error comes from
  `lock_two_directories()` when the parents have no common ancestor. Both also
  invented a lock_two_inodes() for the children; `vfs_rename()` uses
  `I_MUTEX_CHILD`, plain `inode_lock()` and `lock_two_nondirectories()`.
- `mnt_want_write()` is `sb_start_write()` followed by
  `mnt_get_write_access()`, not the mount count alone.
- wait_on_inode() is `wait_on_new_inode()`; inode_add_lru() does not exist.
- The default dentry operations field is `__s_d_op`, set only through
  `set_default_d_op()`.

Reader A also gave `try_break_deleg()` two arguments, and said
`flush_delayed_fput()` is a general way to wait for a release (reader C said the
same; its comment reserves it for boot).

## What only reader B got wrong

Reader B is out of date on whole mechanisms, not just names:

- The inode state word is a plain integer changed with open-coded bit
  operations. It is `struct inode_state_flags`, read and changed only through
  `inode_state_read()`, `inode_state_set()` and their siblings, which assert
  `i_lock`; `inode_state_read_once()` is the lockless read.
- generic_drop_inode() and generic_delete_inode(): the tree has
  `inode_generic_drop()` and `inode_just_drop()`.
- Dentry children on d_child and d_subdirs lists. They are `d_sib` and
  `d_children`, hlists.
- An open file counted by an atomic f_count. It is `f_ref`, a `file_ref_t`,
  and files are recycled under `SLAB_TYPESAFE_BY_RCU`.
- `struct fd` as a pointer and a flags word. It is one word with the flags in
  the low bits, read with `fd_file()` and `fd_empty()`.
- The directory-creation method and `vfs_mkdir()` returning an int. Both return
  a dentry.
- lookup_one_len() and its family. They are `lookup_noperm()` and friends, take
  a `struct qstr *` first, and no longer check permission.
- `struct renamedata` with two idmaps and directory inodes. It has one
  `mnt_idmap` and `old_parent`/`new_parent` dentries.
- The order of `evict()`, what `clear_inode()` does to `I_FREEING`, which flag
  `inode_insert5()` sets, that `->free_inode()` exists, that `I_LINKABLE`
  exists.
- Lookup flags for the root that are really `ND_ROOT_PRESET` and
  `ND_ROOT_GRABBED` in `nd->state`; an unlazy_walk() that does not exist; an
  exclusive directory iteration method that does not exist.
- It did not recognise the VFS debug assertions or `DCACHE_PERSISTENT` at all.

## What only reader C got wrong

- `start_creating()` on an existing name returns the positive dentry, not
  `-EEXIST`. Only the path forms built on `filename_create()` pass
  `LOOKUP_EXCL`.
- Callers of all six `vfs_` directory helpers must check for the same mount.
  That applies only to link and rename.
- `s_roots` holds dentries through `d_sib`, not `d_hash`.

## What the readers already knew

The documentation map (no corrections for any reader). The file layout apart
from the superblock header. For readers A and C: the permission chain in
`inode_permission()`, what filesystem methods may do in RCU-walk mode, what a
lookup method returns, what a change to a VFS method must update, the inode
walk pattern, the debug assertions, how `fdget()` borrows a reference. Reader C
also had path walking, eviction, RCU freeing, revalidation, `d_move()` and write
access essentially right.

## Where the hand-written guide is stale

`vfs.md` was partly refreshed at some point (it knows `__start_dirop()` and
`inode_state_read()`), but:

- It quotes `BUG_ON(!hlist_unhashed(&entry->d_u.d_alias))` from
  `d_instantiate()`. The assertion is `BUG_ON(d_really_is_positive(entry))` and
  there is no d_u.
- It presents `lock_rename()` as the way to lock for a rename. It is static;
  the interface is `start_renaming()` and its variants.
- Its wrong-and-right example hand-locks a directory around `vfs_create()`. In
  this tree in-kernel callers use `start_creating()` and `end_creating()`, and
  hand-locking with `I_MUTEX_PARENT` survives only in a few pseudo filesystems
  and fuse.
- Its two-condition recheck (parent pointer and hash) leaves out
  `IS_DEADDIR()` on the parent, and does not mention that
  `start_removing_dentry()` and `start_creating_dentry()` do all three.
- Its `s_umount` quick check lists remount_fs, which does not exist.
- "REF-walk does not fail due to concurrency" is too strong: a scoped lookup
  returns `-EAGAIN` from `handle_dots()` in either mode when the mount or rename
  sequence changed.
- Its `REPORT as bugs` line is an instruction to the reviewer, not a fact about
  the code; the built guide states the unsafe usage and the correct one.
- It was never onboarded to the drift checker.

## What was left out of the build set

The hand-written guide is 1,559 words, so the build set is 29 of the 67
questions. It keeps the hand-written guide's subjects (inode lock classes and
scope, rename locking, attaching an inode to a dentry, walk modes, open-time
checks, the file operations pointer, rechecking a dentry) and the helper
families every reader had under old names. Left out, by reason:

- Readers A and C answer them and the hand-written guide did not cover them:
  the inode life cycle (state flags, references, cache lookup, eviction, RCU
  freeing, link count), `d_move()`, revalidation, RCU-walk method rules, lookup
  flags, the permission chain, idmapped mounts, the inode walk pattern, the
  debug assertions, the documentation map.
- Caught by the compiler, so a name is enough and the entry points table or a
  neighbouring answer carries it: `d_alloc_parallel()`'s arguments, the mount
  context API, the default dentry operations, `struct fd`, descriptor
  installation.
- Too narrow for a guide loaded on every filesystem patch: timestamps,
  symbolic links, `struct filename`, delegation breaks, removed directories,
  attribute changes, the open sequence, directory reading, superblock setup
  and teardown, mounts, the library helpers, tests.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 159 corrections, 34% rewritten on average
reader B: 198 corrections, 75% rewritten on average
reader C: 151 corrections, 17% rewritten on average

question                         reader A       reader B       reader C
vfs.core-files                    3% ( 1)        4% ( 1)        4% ( 3)
vfs.entry-points                 10% ( 2)       16% ( 4)        9% ( 4)
vfs.docs                          0% ( 0)        0% ( 0)        0% ( 0)
vfs.debug-asserts                 8% ( 1)       94% ( 1)        0% ( 0)
vfs.object-relations             17% ( 1)       46% ( 3)       18% ( 2)
vfs.inode-state-access           41% ( 1)       92% ( 3)       29% ( 1)
vfs.inode-state-flags            18% ( 3)       75% ( 4)       12% ( 1)
vfs.inode-refcount               24% ( 1)       74% ( 1)       18% ( 1)
vfs.inode-last-put               34% ( 1)       69% ( 2)       28% ( 1)
vfs.inode-cache-lookup           28% ( 2)       79% ( 1)       11% ( 1)
vfs.inode-eviction               19% ( 3)       89% ( 4)        0% ( 0)
vfs.inode-free-rcu               21% ( 3)       79% ( 2)        3% ( 1)
vfs.nlink-helpers                39% ( 2)       93% ( 1)       15% ( 1)
vfs.timestamps                   60% ( 2)       83% ( 2)       42% ( 4)
vfs.i-rwsem-scope                31% ( 6)       53% ( 4)        6% ( 2)
vfs.i-rwsem-classes              21% ( 4)       86% ( 4)       14% ( 3)
vfs.dentry-fields                17% ( 3)       72% ( 4)       40% ( 5)
vfs.dentry-states                16% ( 1)       75% ( 3)        8% ( 1)
vfs.dentry-refcount              53% ( 1)       83% ( 2)       39% ( 4)
vfs.d-instantiate                17% ( 5)       55% ( 4)        1% ( 1)
vfs.lookup-return                 0% ( 0)       79% ( 3)        0% ( 0)
vfs.parallel-lookup              45% ( 3)       79% ( 2)       40% ( 4)
vfs.unhashing                    42% ( 1)       83% ( 3)       24% ( 1)
vfs.d-move                       29% ( 1)       86% ( 3)        3% ( 1)
vfs.dentry-recheck-usage         55% ( 3)       77% ( 1)       30% ( 4)
vfs.d-revalidate                 24% ( 1)       63% ( 2)        0% ( 0)
vfs.persistent-dentries          56% ( 1)       83% ( 3)        8% ( 1)
vfs.default-d-op                 62% ( 1)       82% ( 2)       19% ( 1)
vfs.walk-modes                   44% ( 3)       81% ( 6)        0% ( 0)
vfs.walk-retry                   50% ( 2)       83% ( 1)        1% ( 2)
vfs.unlazy                       43% ( 2)       89% ( 4)       15% ( 2)
vfs.rcu-walk-methods              7% ( 1)       73% ( 5)        9% ( 2)
vfs.lookup-flags                 26% ( 3)       91% ( 4)       12% ( 2)
vfs.symlinks                     48% ( 4)       67% ( 2)       30% ( 4)
vfs.filename-struct              50% ( 7)       73% ( 7)       23% ( 4)
vfs.single-name-lookup           42% ( 1)       82% ( 2)       17% ( 3)
vfs.kern-path-helpers            51% ( 3)       82% ( 2)        7% ( 2)
vfs.dirop-helpers                51% ( 8)       88% ( 6)       28% ( 4)
vfs.parent-lock-usage            59% ( 2)       93% ( 1)       38% ( 1)
vfs.rename-locking               73% ( 5)       81% ( 3)       23% ( 5)
vfs.rename-helpers               71% ( 3)       93% ( 3)       14% ( 3)
vfs.vfs-op-preconditions         31% ( 4)       85% ( 7)       24% ( 5)
vfs.mkdir-return                 55% ( 2)       83% ( 3)       19% ( 1)
vfs.delegation-break             49% ( 3)       81% ( 3)       34% ( 3)
vfs.dead-dir                     35% ( 3)       84% ( 3)       38% ( 3)
vfs.inode-permission-chain       18% ( 2)       72% ( 1)        0% ( 0)
vfs.may-open                     42% ( 3)       91% ( 1)       10% ( 3)
vfs.idmap                        36% ( 1)       71% ( 1)        6% ( 1)
vfs.setattr                      54% ( 1)       67% ( 2)       16% ( 4)
vfs.file-refcount                52% ( 4)       75% ( 5)       37% ( 4)
vfs.fput-deferral                52% ( 5)       80% ( 4)       32% ( 3)
vfs.f-op-setup                   16% ( 1)       60% ( 3)       38% ( 2)
vfs.open-sequence                26% ( 2)       78% ( 5)       16% ( 3)
vfs.private-data                 33% ( 3)       88% ( 3)       29% ( 1)
vfs.fd-lookup                    17% ( 1)       93% ( 6)        8% ( 1)
vfs.fd-install                   52% ( 1)       75% ( 2)       13% ( 2)
vfs.write-access                 31% ( 3)       88% ( 3)        0% ( 0)
vfs.readdir                      38% ( 2)       78% ( 2)       11% ( 1)
vfs.sb-refcounts                 31% ( 3)       83% ( 4)       28% ( 3)
vfs.s-umount                     38% ( 3)       77% ( 2)       29% ( 7)
vfs.sb-lifecycle                 43% ( 2)       77% ( 3)       16% ( 3)
vfs.fs-context                   50% ( 2)       72% ( 2)       36% ( 5)
vfs.sb-inode-walk                33% ( 2)       77% ( 5)        8% ( 2)
vfs.mount-struct                 25% ( 2)       76% ( 3)       18% ( 3)
vfs.libfs-helpers                31% ( 2)       49% ( 4)       21% ( 5)
vfs.api-change-checklist          9% ( 1)       72% ( 3)        7% ( 2)
vfs.tests                        39% ( 3)       81% ( 3)       13% ( 2)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `vfs.setattr`, `vfs.fd-install`, `vfs.fs-context`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `vfs.inode-state-flags`, `vfs.inode-refcount`, `vfs.inode-cache-lookup`, `vfs.inode-eviction`, `vfs.inode-free-rcu`, `vfs.dentry-states`, `vfs.lookup-return`, `vfs.d-move`, `vfs.rcu-walk-methods`, `vfs.inode-permission-chain`, `vfs.idmap`, `vfs.fd-lookup`, `vfs.sb-inode-walk`.

## Questions reorganised

47 questions before and 47 after, every id kept, by subject after the two tables: inodes (8),
dentries (6), path walking (3), the inode lock and rename (5), looking up and changing directory
entries (6), files and descriptors (7), superblocks and write access (4), permission and
attributes (3), changing the VFS (1). Nothing merged or dropped; the parts named for a kind of
statement are gone, so each inode, dentry and directory question sits with its neighbours. The
two tables are job-to-name tables that say where a reader would look in vain. "Which functions"
and "which fields" questions (`vfs.inode-refcount`, `vfs.dentry-fields`, `vfs.i-rwsem-classes`,
`vfs.sb-inode-walk`, `vfs.rename-helpers`) ask for the rule or the unsafe usage; longer ones cut.
