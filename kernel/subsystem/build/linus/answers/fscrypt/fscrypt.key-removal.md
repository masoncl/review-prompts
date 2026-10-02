- `do_remove_key()`: touches no `struct key` for the master key and does not
  call `key_invalidate()`; `fscrypt_initiate_key_removal()` does the removal.
- Deferred to the last active reference, in
  `fscrypt_put_master_key_activeref()`: every `struct fscrypt_mode_key` on
  `mk_mode_keys`, and `mk_ino_hash_key`.
- v1 file with `FSCRYPT_POLICY_FLAG_DIRECT_KEY`: `dk_raw` in
  `struct fscrypt_direct_key` is a copy of the raw master key that outlives
  the wipe of `mk_secret`; `fscrypt_put_direct_key()` frees it when the last
  inode using it is evicted.
- `try_to_lock_encrypted_files()` order: one `sync_filesystem()`, then
  `evict_dentries_for_decrypted_inodes()`, then `check_for_busy_inodes()`.
- `try_to_lock_encrypted_files()`: does not call `shrink_dcache_sb()` and
  does not invalidate pages itself.
- `shrink_dcache_inode()`: for a directory it calls `shrink_dcache_parent()`
  first, since child dentries pin the directory's dentry; then
  `d_prune_aliases()`.
- `do_remove_key()` calls no eviction function: the final `iput()` in
  `evict_dentries_for_decrypted_inodes()` calls the filesystem's
  `->drop_inode`, which decides; ext4, f2fs and ubifs call
  `fscrypt_drop_inode()` from it.
- `check_for_busy_inodes()`: the warning gives the count of busy inodes and
  one example inode number.
- `sync_filesystem()` failure: `try_to_lock_encrypted_files()` returns
  `err1 ?: err2`, so the ioctl returns the sync error and writes no
  `removal_status_flags`, although eviction was still attempted.
