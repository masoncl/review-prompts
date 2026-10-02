- Raw master key not kept: for a v2 (`FSCRYPT_KEY_SPEC_TYPE_IDENTIFIER`) key
  with `is_hw_wrapped` false; `add_master_key()` zeroes `bytes` right after
  `fscrypt_init_hkdf()`.
- Hardware-wrapped key: the wrapped blob stays in `mk_secret.bytes` until
  removal, because `setup_per_mode_enc_key()` passes it to
  `fscrypt_prepare_inline_crypt_key()`; only the on-stack `sw_secret` is
  zeroed.
- `dk_raw` in `struct fscrypt_direct_key`: a second copy of a v1 raw master
  key; `free_direct_key()` frees it with `kfree_sensitive()`.
- HKDF state: there is no struct fscrypt_hkdf; `hkdf` is a
  `struct hmac_sha512_key` embedded in `struct fscrypt_master_key_secret`;
  `wipe_master_key_secret()` zeroes it with the rest. There is no HKDF
  destroy function and no transform to free.
- `fscrypt_init_hkdf()` and `fscrypt_hkdf_expand()`: return `void`, so a
  derivation has no error path that could skip a wipe.
- `fscrypt_destroy_prepared_key()`: `tfm` is a
  `struct crypto_sync_skcipher *`, freed with `crypto_free_sync_skcipher()`.
- `fscrypt_derive_dirhash_key()`: derives straight into `ci_dirhash_key`;
  `put_crypt_info()` zeroes it with the whole `struct fscrypt_inode_info`.
- `fscrypt_get_test_dummy_secret()`: keeps the per-boot test key in a static
  buffer that is never wiped; only the stack copies are.
- **Potentially unsafe usage**: returning without wiping an on-stack
  `struct fscrypt_master_key_secret` or derived-key buffer.
  - Unsafe: on any return after key bytes were written to the buffer.
  - Safe: before the first copy of key bytes, as the `-EINVAL` returns in
    `fscrypt_ioctl_add_key()` that precede `get_keyring_key()` and the
    `copy_from_user()` into `bytes`; every later exit goes through
    `out_wipe_secret`.
- **Potentially unsafe usage**: freeing an object that held key material
  with `kfree()` or `kmem_cache_free()`.
  - Unsafe: while the object still holds key bytes or a prepared key that
    was not destroyed.
  - Safe: after `fscrypt_destroy_prepared_key()` zeroed the embedded
    `struct fscrypt_prepared_key`, as `fscrypt_put_master_key_activeref()`
    does before `kfree()` of each `struct fscrypt_mode_key`.
  - Safe: after `memzero_explicit()` of the whole object, as
    `put_crypt_info()` does before `kmem_cache_free()`.
  - Safe: with `kfree_sensitive()`, as `fscrypt_free_master_key()` does.
