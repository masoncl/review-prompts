- `union fscrypt_policy`: defined in `fs/crypto/fscrypt_private.h`, not in
  `include/uapi/linux/fscrypt.h`; of the policy types, the uapi header
  defines only `struct fscrypt_policy_v1` and `struct fscrypt_policy_v2`.
- `fscrypt_policy` as a struct tag: a macro alias for `fscrypt_policy_v1`
  under `#ifndef __KERNEL__` in `include/uapi/linux/fscrypt.h`; kernel code
  cannot use it.
- `fscrypt_new_context()`: generates no nonce; it copies the nonce its caller
  passes in.
- Nonce for a directory given a policy by ioctl: `get_random_bytes()` in
  `set_encryption_policy()` in `fs/crypto/policy.c`.
- Nonce for a new inode: `get_random_bytes()` in `fscrypt_prepare_new_inode()`
  in `fs/crypto/keysetup.c`; held in `ci_nonce` of
  `struct fscrypt_inode_info` until written.
- `fscrypt_set_context()`: writes the `ci_nonce` generated earlier, through
  `fscrypt_context_for_new_inode()`; calling it without
  `fscrypt_prepare_new_inode()` first gives `-ENOKEY` after a warning.
- `fscrypt_ioctl_get_nonce()` (`FS_IOC_GET_ENCRYPTION_NONCE`): copies the
  on-disk nonce to userspace; `fscrypt_policy_from_context()` drops it.
