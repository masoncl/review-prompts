- `mk_users`: a list of `struct fscrypt_master_key_user`, not a keyring; an
  empty list for v1 keys.
- A user's claim: found by `find_master_key_user()`, which compares `uid`
  with `current_fsuid()` under `mk_sem`.
- `quota_key` in each claim: a `struct key` of type `key_type_fscrypt_user`,
  whose registered name is ".fscrypt". It holds no secret.
- `quota_key` allocation: `add_master_key_user()` calls `key_alloc()` with
  flags 0, so it is in quota, owned by the caller's fsuid.
- `quota_key` linkage: `key_instantiate_and_link()` gets a `NULL` keyring,
  so the key is in no keyring; `fs/crypto` reaches it only through the
  claim.
- Payload charge per claim: `FSCRYPT_MAX_RAW_KEY_SIZE` bytes, reserved in
  `fscrypt_user_key_instantiate()`, whatever the key size.
- Size check: `fscrypt_valid_key_size()` allows `FSCRYPT_MIN_KEY_SIZE` up to
  `FSCRYPT_MAX_RAW_KEY_SIZE`, or up to `FSCRYPT_MAX_HW_WRAPPED_KEY_SIZE` with
  `FSCRYPT_ADD_KEY_FLAG_HW_WRAPPED`.
- "fscrypt-provisioning" key: `get_keyring_key()` requires both
  `payload->type` equal to the specifier type and `payload->flags` equal to
  the ioctl `flags`; a mismatch or another key type gives `-EKEYREJECTED`.
- `FSCRYPT_ADD_KEY_FLAG_HW_WRAPPED`: the only flag accepted, and only with
  `FSCRYPT_KEY_SPEC_TYPE_IDENTIFIER`; otherwise `-EINVAL`.
- Hardware-wrapped add: `fscrypt_derive_sw_secret()` returns `-EOPNOTSUPP`
  unless the superblock has `SB_INLINECRYPT`.
- Hardware-wrapped identifier: derived with
  `HKDF_CONTEXT_KEY_IDENTIFIER_FOR_HW_WRAPPED_KEY`, so a hardware-wrapped key
  and its software secret added as a raw key get different identifiers.
