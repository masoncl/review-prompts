- At lookup: `fscrypt_prepare_dentry()` with `is_nokey_name` false clears
  `DCACHE_OP_REVALIDATE`, if both of its tests below pass.
- Callers that reach it with false: `fscrypt_prepare_lookup()` for an
  unencrypted directory, `__fscrypt_prepare_lookup()` when the key is present,
  and `fscrypt_prepare_lookup_partial()` when the key is present or key setup
  failed.
- `fscrypt_prepare_dentry()` tests two things: `DCACHE_OP_REVALIDATE` is set,
  and `dentry->d_op->d_revalidate == fscrypt_d_revalidate`.
- `fscrypt_handle_d_move()` tests `DCACHE_NOKEY_NAME`, clears it, then tests
  only `dentry->d_op->d_revalidate == fscrypt_d_revalidate`.
- `fscrypt_handle_d_move()` has no NULL test of `dentry->d_op` and no test of
  `DCACHE_OP_REVALIDATE`, so a dentry that carries `DCACHE_NOKEY_NAME` must
  have dentry operations.
- `fscrypt_handle_d_move()` takes no lock; `__d_move()` in `fs/dcache.c` calls
  it while it holds `dentry->d_lock`.
- `__d_move()` calls `fscrypt_handle_d_move()` on `dentry`, the one being
  moved, and not on `target`.
