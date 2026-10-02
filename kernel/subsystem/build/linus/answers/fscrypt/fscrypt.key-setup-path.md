- `fscrypt_get_encryption_info()`: declared in `fs/crypto/fscrypt_private.h`
  and not exported; a filesystem reaches it only through hooks such as
  `fscrypt_file_open()`, `fscrypt_prepare_readdir()` and
  `fscrypt_setup_filename()`.
- `fscrypt_prepare_readdir()`: returns 0 when the key is absent; it does not
  produce `-ENOKEY`. `fscrypt_require_key()` does, and `fscrypt_file_open()`
  in `fs/crypto/hooks.c` calls it.
- There is no __fscrypt_file_open() here; the function is
  `fscrypt_file_open()`.
- `allow_unsupported` true: 0 with no key is also returned for `-ERANGE` from
  `->get_context()`, an unrecognised context, an unsupported policy, and
  `-ENOPKG` from key setup.
- `mk_sem`: held for read from `setup_file_encryption_key()` until after the
  `cmpxchg_release()` in `fscrypt_setup_encryption_info()`, when the master
  key came from `s_master_keys`. Nothing is held when a v1 key came
  from a process-subscribed keyring (`mk` is NULL).
- Fields written after publication: the winner sets `ci_master_key` and adds
  `ci_master_key_link` to `mk_decrypted_inodes` after the
  `cmpxchg_release()`, so the acquire load in `fscrypt_get_inode_info()` does
  not order them. `fscrypt_drop_inode()` tests `ci_master_key` for NULL.
