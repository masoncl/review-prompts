- `fscrypt_prepare_new_inode()` needs `i_blkbits` as well as `i_mode`: either
  one being 0 gives a warning and `-EINVAL`. Both tests run only after
  `fscrypt_policy_to_inherit()` returned a policy.
- Inode number: only `ci_hashed_ino` waits, and only for
  `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`. `fscrypt_set_context()` computes it
  with `fscrypt_hash_inode_number()`.
- `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64`: no part of key setup waits;
  `fscrypt_generate_iv()` in `fs/crypto/crypto.c` reads `i_ino` each time it
  builds an IV.
- `S_ENCRYPTED` on a new inode is set by the filesystem, at a point that
  differs:

  | Filesystem | Where |
  |---|---|
  | ext4 | `__ext4_new_inode()`, between the two calls |
  | f2fs | `f2fs_new_inode()`, between the two calls |
  | ubifs | inside `->set_context()`, in `create_xattr()` |
  | ceph | `ceph_fscrypt_prepare_context()` |

- `ext4_set_context()` with a handle: warns and returns `-EINVAL` if
  `IS_ENCRYPTED()` is false, so on ext4 the flag must precede
  `fscrypt_set_context()`.
- `fs_data`: passed through untouched to `->set_context()`; ext4 passes the
  journal handle, f2fs the inode folio, ubifs NULL.
- `fscrypt_context_for_new_inode()` in `fs/crypto/policy.c`: builds the
  context without calling `->set_context()` and without the delayed hash.
  `ceph_fscrypt_prepare_context()` uses it instead of `fscrypt_set_context()`;
  ceph sets neither `has_stable_inodes` nor `has_32bit_inodes`, so
  `fscrypt_supported_policy()` rejects `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`
  there.
- **Unsafe usage**: calling `fscrypt_set_context()` before `i_ino` is
  assigned.
  - Unsafe: with a `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` policy,
    `fscrypt_hash_inode_number()` warns on `i_ino == 0` and hashes it anyway.
  - Safe: after `i_ino` is assigned, as `__ext4_new_inode()` does;
    `fscrypt_set_context()` reads `i_ino` through
    `fscrypt_hash_inode_number()`.
