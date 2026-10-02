- Output that may change: `Documentation/filesystems/fscrypt.rst` names only
  the way filenames are presented without the key (the no-key name
  encoding); it says nothing of the kind about `/proc/keys` or log messages.
- No-key names, still guaranteed by the document: at most `NAME_MAX` bytes,
  no `/` or `\0`, and unique per directory entry.
- Key identifier contexts: `HKDF_CONTEXT_KEY_IDENTIFIER_FOR_RAW_KEY` (1) and
  `HKDF_CONTEXT_KEY_IDENTIFIER_FOR_HW_WRAPPED_KEY` (8); there is no
  HKDF_CONTEXT_KEY_IDENTIFIER.
- SipHash key byte order is part of the derivation:
  `fscrypt_derive_siphash_key()` converts the HKDF output with
  `le64_to_cpus()`, for both `ci_dirhash_key` and `mk_ino_hash_key`.
- Size assertions: search `fs/crypto/` for `BUILD_BUG_ON` and
  `static_assert`; they sit inside the functions that use the structure,
  not in `fscrypt_init()`.
- `fscrypt_new_context()` in `fs/crypto/policy.c`: has no assertion; the
  context sizes are asserted in `fscrypt_context_size()`, and
  `fscrypt_context_for_new_inode()` asserts `sizeof(union fscrypt_context)`
  equals `FSCRYPT_SET_CONTEXT_MAX_SIZE`.
- `fscrypt_fname_disk_to_usr()` in `fs/crypto/fname.c`: asserts that
  `struct fscrypt_nokey_name` has no padding between fields and that
  `FSCRYPT_NOKEY_NAME_MAX_ENCODED` fits `NAME_MAX`; it does not assert the
  struct's size.
- Derivation inputs are guarded too: `setup_per_mode_enc_key()` asserts the
  HKDF info buffer is 17 bytes, `fscrypt_derive_siphash_key()` asserts a
  16-byte two-word key, `setup_v1_file_key_derived()` asserts
  `FSCRYPT_FILE_NONCE_SIZE == AES_KEYSIZE_128`.
- No size assertion: `struct fscrypt_policy_v1`, `struct fscrypt_policy_v2`
  and `struct fscrypt_symlink_data`.
- Run-time check: `fscrypt_context_is_valid()` rejects a stored context
  whose length differs from `fscrypt_context_size()` for its version, so
  `fscrypt_policy_from_context()` returns `-EINVAL`.
