- Return value: computed from a lockless read of `mk_present`, so it can be
  stale at once; it does not guarantee that an inode is evicted once the
  key is removed.
- Dirty inode: `fscrypt_drop_inode()` returns 0 when any `I_DIRTY_ALL` bit
  is set, so an inode dirtied after the remover's sync stays cached and is
  counted busy.
- Reads: `fscrypt_get_inode_info()` loads the info pointer with
  `smp_load_acquire()`; `ci_master_key` is a plain read; only `mk_present`
  uses `READ_ONCE()`.
- `inode->i_lock`: must be held; `inode_state_read()` asserts it with
  `lockdep_assert_held()`.
- Generic helper: `inode_generic_drop()` in `include/linux/fs.h`; there is no
  generic_drop_inode() in this tree.
- Callers such as `ext4_drop_inode()`: call `fscrypt_drop_inode()` only when
  `inode_generic_drop()` returned 0.
- `fs/ceph`: sets `->drop_inode` to `inode_just_drop()` and never calls
  `fscrypt_drop_inode()`; its inodes are dropped at every final `iput()`.
- **Unsafe usage**: taking `mk_decrypted_inodes_lock` in
  `fscrypt_drop_inode()`.
  - Unsafe: `evict_dentries_for_decrypted_inodes()` takes `inode->i_lock`
    while holding `mk_decrypted_inodes_lock`, so the opposite order under
    `i_lock` can deadlock.
  - Safe: take `mk_decrypted_inodes_lock` at eviction, where `i_lock` is not
    held, as `put_crypt_info()` does.
