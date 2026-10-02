- `struct fscrypt_keyring` (defined in `fs/crypto/keyring.c`): hashes
  `struct fscrypt_master_key` directly through `mk_node`; no `struct key`
  wraps a `struct fscrypt_master_key`, and `s_master_keys` is not a keyring
  of the key subsystem.
- Keys added by ioctl for v1 policies: stored in `s_master_keys` too, under
  `FSCRYPT_KEY_SPEC_TYPE_DESCRIPTOR`.
- Key setup takes a master key from outside `s_master_keys` only in
  `fscrypt_setup_v1_file_key_via_subscribed_keyrings()`, which finds a
  "logon" key; such inodes have `ci_master_key == NULL`.
- State: held as `mk_present` plus `mk_active_refs`; there is no state enum
  and no helper. `fscrypt_ioctl_get_key_status()` shows the mapping to
  `FSCRYPT_KEY_STATUS_PRESENT`, `FSCRYPT_KEY_STATUS_INCOMPLETELY_REMOVED`
  and `FSCRYPT_KEY_STATUS_ABSENT`.
- Inodes: each inode with `ci_master_key` set holds one `mk_active_refs`
  reference, taken in `fscrypt_setup_encryption_info()`, not a
  `mk_struct_refs` reference.
- `mk_struct_refs`: all active references together own one; each lookup
  holds one more for its duration.
- `fscrypt_put_master_key_activeref()`: does `refcount_dec_and_test()` and
  only afterwards takes the keyring `lock` to unlink.
- `fscrypt_find_master_key()`: of the two counts it tests only
  `mk_struct_refs`, so it can return a key whose `mk_active_refs` is
  already 0.
- Before using a looked-up key's secret or taking an active reference: test
  `mk_present` under `mk_sem`, as `setup_file_encryption_key()` does, or use
  `refcount_inc_not_zero()` on `mk_active_refs`, as
  `add_existing_master_key()` does (`KEY_DEAD` on failure).
- `mk_users`: `fscrypt_put_master_key()` empties it with `clear_mk_users()`
  at the last structural reference.
- `struct fscrypt_master_key_secret`: the key bytes are in `bytes`.
