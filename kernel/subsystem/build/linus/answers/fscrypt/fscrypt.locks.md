- `mk_users`: a plain list protected by `mk_sem` alone; the key subsystem
  locks nothing here. `add_new_master_key()` and `fscrypt_put_master_key()`
  touch it unlocked, before the key is published and after the last
  structural reference.
- `mk_mode_keys`: appended with `list_add_tail_rcu()` under
  `fscrypt_mode_key_setup_mutex`; searched by `fscrypt_find_mode_key()`
  under `guard(rcu)`, the first time without the mutex.
- `fscrypt_is_key_prepared()`: plain reads of `tfm` and `blk_key`; it does
  not use `smp_load_acquire()`.
- `fscrypt_prepare_key()`: plain store of `tfm`; it does not use
  `smp_store_release()`. Publication of a shared key on `mk_mode_keys` is
  the RCU list insertion.
- `mk_ino_hash_key`: read with no lock by `fscrypt_hash_inode_number()` when
  called from `fscrypt_set_context()`; the inode's active reference keeps it
  from being zeroed, and key setup initialised it earlier.
