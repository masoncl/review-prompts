- Owner check: `inode_owner_or_capable()` failing gives `-EACCES`.
- Order in `fscrypt_ioctl_set_policy()`, which decides the error when several
  conditions fail: `get_user()` of the version byte, version,
  `copy_from_user()` of the rest, owner, `mnt_want_write_file()`, then under
  `inode_lock()` the existing policy, `-ENOTDIR`, `-ENOENT`, `-ENOTEMPTY`,
  then `set_encryption_policy()`.
- Order in `set_encryption_policy()`: `fscrypt_supported_policy()`, then the
  v2 key check, then `->set_context()`.
- `-ENOTDIR`, `-ENOENT` (`IS_DEADDIR()`), `-ENOTEMPTY`: tested only when
  `fscrypt_get_policy()` returns `-ENODATA`, that is, the inode has no policy.
- Inode that already has a policy, regular file included: 0 if the policy is
  equal, `-EEXIST` if not; the `-ENOTDIR` test is not reached.
- Equal-policy path: never reaches `set_encryption_policy()`, so it succeeds
  without `fscrypt_supported_policy()` and without the v2 key being present.
- Stored context of unrecognized version or size: `fscrypt_get_policy()`
  returns `-EINVAL` and the ioctl turns it into `-EEXIST`.
- Any other error from `fscrypt_get_policy()`: returned unchanged.
- Empty-directory test: `fscrypt_ioctl_set_policy()` calls
  `s_cop->empty_dir()` itself; it is not left to `->set_context()`.
- `s_cop->set_context` and `s_cop->empty_dir`: called with no NULL test.
- `-EOPNOTSUPP`: no test in `fscrypt_ioctl_set_policy()` or
  `set_encryption_policy()` gives it; it comes from the filesystem handler
  before the call, for example `ext4_has_feature_encrypt()` or
  `f2fs_sb_has_encrypt()` failing, from `->set_context()`, or from the stub
  in `include/linux/fscrypt.h` without `CONFIG_FS_ENCRYPTION`.
- `fscrypt_verify_key_added()` in `fs/crypto/keyring.c`: returns `-ENOKEY`
  both when the key is absent and when the current user did not add it,
  unless `capable(CAP_FOWNER)`, which gives 0 in both cases; it does not
  return `-EACCES`.
- Errors from `->set_context()`: returned to userspace unchanged; for
  example `ext4_set_context()` gives `-EPERM` for the root directory and
  `-EOPNOTSUPP` when `EXT4_INODE_DAX` is set.
- `fscrypt_supported_policy()` conditions, all `-EINVAL`: see
  `fscrypt_supported_v1_policy()`, `fscrypt_supported_v2_policy()` and
  `supported_iv_ino_lblk_policy()` in `fs/crypto/policy.c`.
- Easy to miss in `fscrypt_supported_v1_policy()`: a v1 policy is rejected on
  an `IS_CASEFOLDED()` directory.
- Easy to miss in `fscrypt_supported_v2_policy()`:
  `FSCRYPT_POLICY_FLAG_DIRECT_KEY`, `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` and
  `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` are mutually exclusive; a nonzero
  `log2_data_unit_size` needs `supports_subblock_data_units`.
- Easy to miss in `supported_iv_ino_lblk_policy()`: contents mode must be
  `FSCRYPT_MODE_AES_256_XTS`; `has_32bit_inodes` is a bit in
  `struct fscrypt_operations`, not a callback;
  `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` needs `s_blocksize == PAGE_SIZE`.
