# Fscrypt

## Main structures

### Objects and how they relate

- Filesystems that set a `struct fscrypt_operations`: ext4, f2fs, ubifs and
  ceph only; search for `inode_info_offs` to list them.
- Contents encryption path is fixed per filesystem by flags in
  `struct fscrypt_operations`, not chosen per mount or per inode:

  | Filesystem flag | Regular-file key | Contents I/O |
  |---|---|---|
  | `is_block_based` (ext4, f2fs) | `blk_key` | blk-crypto, via `fscrypt_set_bio_crypt_ctx()` in `fs/crypto/block.c` |
  | `needs_bounce_pages` (ceph) | `tfm` | `fscrypt_encrypt_pagecache_blocks()` and the in-place helpers |
  | neither (ubifs) | `tfm` | `fscrypt_encrypt_block_inplace()`, `fscrypt_decrypt_block_inplace()` |

- Bounce page pool: one global pool; `fscrypt_initialize()` creates it only
  when `needs_bounce_pages` is set; `fscrypt_alloc_bounce_page()` warns and
  returns NULL while no pool exists.
- Directories and symlinks: always use `tfm`, on every filesystem.
- `struct fscrypt_inode_info` pointer: not a member of `struct inode`; it lives
  in the filesystem's own inode (`i_crypt_info` in `struct ext4_inode_info`,
  for example) and fscrypt finds it with `inode_info_offs` through
  `fscrypt_inode_info_addr()` in `include/linux/fscrypt.h`.
- `ci_master_key`: NULL when a v1 key came from the process-subscribed
  keyrings; such an inode holds no active ref, is not on
  `mk_decrypted_inodes`, and `fscrypt_drop_inode()` returns 0 for it.
- v2 inode info: `ci_master_key` is set by the time the
  `fscrypt_setup_encryption_info()` call that published it returns, since
  `setup_file_encryption_key()` returns `-ENOKEY` for v2 when the key is not
  in `s_master_keys`.
- v1 master keys: also live in `s_master_keys` when added with
  `FS_IOC_ADD_ENCRYPTION_KEY` and a descriptor (`CAP_SYS_ADMIN`);
  `setup_file_encryption_key()` searches there first and falls back to
  `fscrypt_setup_v1_file_key_via_subscribed_keyrings()`.
- `struct fscrypt_prepared_key`: `tfm` is a `struct crypto_sync_skcipher *`;
  `fscrypt_prepare_key()` sets exactly one of `tfm` and `blk_key`, never both.
- `ci_enc_key`: an embedded `struct fscrypt_prepared_key`; for a shared key it
  is a by-value copy of the owner's struct; `ci_owns_key` says whether the
  inode info frees it. Owners:

  | Policy | Owner of the key | Freed by |
  |---|---|---|
  | per-file key (v1 or v2, no key-sharing flag) | the inode info | `put_crypt_info()` |
  | v2 with `FSCRYPT_POLICY_FLAG_DIRECT_KEY`, `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` or `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` | a `struct fscrypt_mode_key` on `mk_mode_keys` | `fscrypt_put_master_key_activeref()`, on the last active ref |
  | v1 with `FSCRYPT_POLICY_FLAG_DIRECT_KEY` | a `struct fscrypt_direct_key` (`ci_direct_key`) | `fscrypt_put_direct_key()` |

- Shared mode keys: kept alive by the inode's active ref on the master key, not
  by a refcount of their own.
- `struct fscrypt_direct_key`: wraps a `struct fscrypt_prepared_key`
  (`dk_key`), so it may hold a `blk_key`; it sits in the global table
  `fscrypt_direct_keys` in `fs/crypto/keysetup_v1.c`, has its own
  `dk_refcount`, and is matched per superblock (`dk_sb`).
- `struct fscrypt_mode`: one entry per mode number in `fscrypt_modes[]`, not a
  contents/filenames pair; `select_encryption_mode()` in
  `fs/crypto/keysetup.c` picks the contents mode for regular files and the
  filenames mode for directories and symlinks.
- `struct fscrypt_dummy_policy`: inherited only by new regular files,
  directories and symlinks created under an unencrypted directory
  (`fscrypt_policy_to_inherit()`, `fscrypt_prepare_new_inode()`); existing
  inodes are untouched.

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| Contents encryption through the block layer | `fs/crypto/block.c` | There is no fs/crypto/inline_crypt.c and no fs/crypto/bio.c. Built by `fscrypto-$(CONFIG_BLOCK)` in `fs/crypto/Makefile`. `fscrypt_zeroout_range()` is here. |
| Choice between block layer and CPU | `fscrypt_using_inline_encryption()` in `fs/crypto/fscrypt_private.h` | There is no fscrypt_select_encryption_impl(). True for a regular file when `s_cop->is_block_based` is set, whatever the mount options. |
| Contents encryption by the CPU, filesystem not block-based | `fs/crypto/crypto.c` | Callers outside `fs/crypto/` are in `fs/ceph/` and `fs/ubifs/`. There is no fscrypt_decrypt_pagecache_blocks() and no fscrypt_decrypt_bio(). |
| Contents encryption by the CPU, block-based filesystem (ext4, f2fs) | `block/blk-crypto-fallback.c`, outside `fs/crypto/` | Reached from `__blk_crypto_submit_bio()`. Always used without `SB_INLINECRYPT`: `fscrypt_prepare_inline_crypt_key()` then omits `BLK_CRYPTO_CFG_ALLOW_HW`. |
| Key setup for blk-crypto keys | `fs/crypto/block.c` | `fscrypt_prepare_inline_crypt_key()` and `fscrypt_destroy_inline_crypt_key()` are defined here; `fs/crypto/keysetup.c` only calls them. |
| `CONFIG_FS_ENCRYPTION_INLINE_CRYPT` | `fs/crypto/Kconfig` | No prompt: `default y if FS_ENCRYPTION && BLOCK`. It guards the `fs/crypto/block.c` declarations and stubs in `fs/crypto/fscrypt_private.h` and `include/linux/fscrypt.h`, not the `fs/crypto/Makefile` line. |
| Hooks called from filesystem operations | `fs/crypto/hooks.c` holds the `__`-prefixed bodies, for example `__fscrypt_prepare_link()` | The unprefixed wrappers, for example `fscrypt_prepare_link()` and `fscrypt_encrypt_symlink()`, are inline in `include/linux/fscrypt.h` and test `IS_ENCRYPTED()` first. |

## Per-inode key state

**Per-inode key structure**

- `fscrypt_inode_info_addr()` in `include/linux/fscrypt.h`: the one helper
  that turns an inode into the address of the pointer;
  `fscrypt_get_inode_info()`, `fscrypt_get_inode_info_raw()`,
  `fscrypt_setup_encryption_info()` and `fscrypt_put_encryption_info()` go
  through it.
- `inode_info_offs` of 0: means "not set". In ext4, f2fs, ubifs and ceph the
  `i_crypt_info` field follows the embedded inode, so the offset is positive.
- `VFS_WARN_ON_ONCE()` on a zero offset: compiled out without
  `CONFIG_DEBUG_VFS`; the address is then the start of the `struct inode`.
- `s_cop`: `fscrypt_inode_info_addr()` dereferences `inode->i_sb->s_cop` with
  no NULL test, so no accessor may be used on a superblock that did not set
  `s_cop`.
- Initialising the field to NULL is the filesystem's job: ext4 does it in the
  slab constructor `init_once()`; f2fs has no slab constructor and calls its
  `init_once()` from `f2fs_alloc_inode()` at every allocation; ubifs does it
  by `memset()` in `ubifs_alloc_inode()`, ceph in `ceph_alloc_inode()`.

**Key setup and absent keys**

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

**Creating an encrypted inode**

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

**Inode teardown**

- `fscrypt_put_encryption_info()`: frees the whole
  `struct fscrypt_inode_info` through `put_crypt_info()` and sets the pointer
  to NULL.
- `fscrypt_free_inode()`: frees only `inode->i_link`, and only when
  `IS_ENCRYPTED(inode) && S_ISLNK(inode->i_mode)` holds at the time of the
  call.
- Which inodes: every inode the filesystem evicts; ext4, f2fs, ubifs and ceph
  call it with no test of the inode.
- `s_cop`: `fscrypt_put_encryption_info()` dereferences it with no NULL test,
  so `s_cop` must be set on every superblock whose inodes reach the call.
  Without `CONFIG_FS_ENCRYPTION` both functions are empty stubs.
- The reset to NULL is relied on: ext4 sets `i_crypt_info` to NULL only in
  the slab constructor `init_once()`, so a reused object is clean only
  because eviction cleared it.
- `make_bad_inode()` sets `i_mode` to `S_IFREG`; a later
  `fscrypt_free_inode()` then skips the `kfree()` of `i_link`.
- **Potentially unsafe usage**: calling `fscrypt_free_inode()` outside
  `->free_inode()`.
  - Unsafe: once the inode has been reachable by path walk; `fs/namei.c`
    reads `inode->i_link` in RCU mode, so the free needs the grace period that
    `->free_inode()` provides.
  - Safe: on a new symlink that was never hashed or instantiated, as the error
    path of `ubifs_symlink()` does; the function sets `i_link` to NULL, so
    the later call from `->free_inode()` does nothing.

**Reading the key pointer**

- `fscrypt_get_inode_info()` and `fscrypt_get_inode_info_raw()`: this tree has
  both, in `include/linux/fscrypt.h`.
- `fscrypt_get_inode_info_raw()` warning on NULL: `VFS_WARN_ON_ONCE()`,
  compiled out without `CONFIG_DEBUG_VFS`; the NULL is then returned
  silently, and callers that make no test of their own dereference it.
- Without `CONFIG_FS_ENCRYPTION`: `fscrypt_get_inode_info()` has a stub that
  returns NULL; `fscrypt_get_inode_info_raw()` and
  `fscrypt_inode_info_addr()` have no stub.
- Callers of `fscrypt_get_inode_info_raw()`: all are in `fs/crypto/`.
  Filesystems test for a key with `fscrypt_has_encryption_key()`.
- Exported helpers that use the raw accessor pass its requirement to the
  filesystem, for example `fscrypt_fname_encrypt()`,
  `fscrypt_fname_encrypted_size()`, `fscrypt_fname_siphash()` and
  `fscrypt_encrypt_block_inplace()`.
- Pointer lifetime: once non-NULL it stays set until
  `fscrypt_put_encryption_info()` at eviction, the only place in `fs/crypto/`
  that clears it.
- **Potentially unsafe usage**: calling `fscrypt_get_inode_info_raw()`.
  - Unsafe: when nothing earlier on the calling path has seen the pointer
    non-NULL, or to test whether a key exists; callers such as
    `fscrypt_fname_encrypt()` dereference the result at once.
  - Safe: after the same task got success from `fscrypt_require_key()` on an
    `IS_ENCRYPTED()` inode, or true from `fscrypt_has_encryption_key()`, both
    of which do the acquire load; `fscrypt_policy_to_inherit()` and
    `fscrypt_setup_filename()` do this, the latter on a directory.
  - Safe: on a new inode after `fscrypt_prepare_new_inode()` returned 0 with
    `*encrypt_ret` true in the same task, as `fscrypt_set_context()` does
    when `__ext4_new_inode()` calls it.
  - Safe: in file contents I/O on an encrypted regular file, where
    `fscrypt_file_open()` required the key, as
    `fscrypt_encrypt_pagecache_blocks()` and `fscrypt_set_bio_crypt_ctx()`
    do.

## File contents data path

**Choosing the contents implementation**

- `fscrypt_using_inline_encryption()` in `fs/crypto/fscrypt_private.h`: the
  whole test is `S_ISREG(inode->i_mode) && inode->i_sb->s_cop->is_block_based`.
- There is no fscrypt_select_encryption_impl(), no ci_inlinecrypt field and no
  fs/crypto/inline_crypt.c here; the blk-crypto code is `fs/crypto/block.c`.
- Regular files on a block-based filesystem: always blk-crypto, with or without
  the inlinecrypt mount option; fs/crypto has no crypto API contents path for
  them.
- Regular file on ext4 or f2fs: always gets a `blk_key` and `tfm` stays NULL,
  whatever the mount options.
- `SB_INLINECRYPT` is not part of the test; `fscrypt_prepare_inline_crypt_key()`
  turns it into `BLK_CRYPTO_CFG_ALLOW_HW` for `blk_crypto_init_key()`.
- Without `BLK_CRYPTO_CFG_ALLOW_HW`: `blk_crypto_config_supported_natively()`
  returns false, so blk-crypto-fallback does every bio in software.
- Device capability never selects between blk-crypto and the crypto API in
  fs/crypto; with `BLK_CRYPTO_CFG_ALLOW_HW` and a raw key it only selects
  hardware or blk-crypto-fallback. There is no blk_crypto_config_supported()
  here.
- `blk_crypto_start_using_key()` failure: fails key setup; there is no fall
  back to `fscrypt_allocate_skcipher()`.
- `blk_crypto_mode` unset in a `struct fscrypt_mode`: not tested by fs/crypto;
  for a raw key `blk_crypto_init_key()` returns `-EINVAL` for the key size.
- `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` and `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`:
  no hardware requirement; see `supported_iv_ino_lblk_policy()` in
  `fs/crypto/policy.c`.
- Hardware-wrapped keys, regular file: `setup_per_mode_enc_key()` calls
  `fscrypt_prepare_inline_crypt_key()` directly, not `fscrypt_prepare_key()`;
  `-EINVAL` without `SB_INLINECRYPT`.
- `get_devices` unset: `fscrypt_get_devices()` uses `sb->s_bdev`; it is not a
  condition.
- There is no fscrypt_inode_uses_inline_crypto() or
  fscrypt_inode_uses_fs_layer_crypto() here; filesystem code does not test the
  path.
- `CONFIG_FS_ENCRYPTION_INLINE_CRYPT`: no prompt, `default y if FS_ENCRYPTION &&
  BLOCK`; `CONFIG_FS_ENCRYPTION` selects `BLK_INLINE_ENCRYPTION` and
  `BLK_INLINE_ENCRYPTION_FALLBACK` if `BLOCK` (`fs/crypto/Kconfig`).

**Filesystem operations table**

- `is_block_based`: bit field in `struct fscrypt_operations`
  (`include/linux/fscrypt.h`) that selects the data path; set by
  `ext4_cryptops` and `f2fs_cryptops`, not by ubifs or ceph.
- `needs_bounce_pages`: set only by `ceph_fscrypt_ops` in `fs/ceph/crypto.c`;
  `ext4_cryptops` and `f2fs_cryptops` do not set it.
- Attaching: ubifs and ceph call `fscrypt_set_ops()`; ext4 and f2fs assign
  `sb->s_cop` directly under `#ifdef CONFIG_FS_ENCRYPTION`, because the field
  exists only then.
- There is no fscrypt_set_test_dummy_encryption() here; see
  `fscrypt_parse_test_dummy_encryption()`.

**Block-based data path**

- Position unit: `fscrypt_set_bio_crypt_ctx()`, `fscrypt_mergeable_bio()` and
  `fscrypt_zeroout_range()` take `loff_t pos` in bytes; `fscrypt_zeroout_range()`
  also takes `len` in bytes. A block number passed as `pos` gives a wrong DUN
  silently: `fscrypt_generate_dun()` only shifts it by `ci_data_unit_bits`.
- `fscrypt_limit_io_blocks()`: still takes `lblk` and `nr_blocks` in filesystem
  blocks.
- There is no fscrypt_set_bio_crypt_ctx_bh() or fscrypt_mergeable_bio_bh() here;
  buffer-head code passes `folio_pos() + bh_offset()`, as
  `buffer_set_crypto_ctx()` in `fs/buffer.c` does.
- `fscrypt_set_bio_crypt_ctx()`: tests only
  `fscrypt_needs_contents_encryption()`, then reads `ci_enc_key.blk_key` through
  `fscrypt_get_inode_info_raw()`; the key must already be set up.
- Writes on ext4 and f2fs: no `fscrypt_encrypt_pagecache_blocks()` call; ext4
  puts the pagecache folio into the bio, in `io_submit_add_bh()`.
- Bios that move raw ciphertext carry no context: `f2fs_set_bio_crypt_ctx()`
  skips the call when `fio->encrypted_page` is set.
- Segment not aligned to the data unit size: `bio_split_io_at()` returns
  `-EINVAL`; blk-crypto-fallback ends the bio with `BLK_STS_INVAL`.
- **Unsafe usage**: submitting a bio that has a crypt context with
  `submit_bio()`.
  - Unsafe: `submit_bio_noacct()` ends it with `BLK_STS_NOTSUPP` unless
    `blk_crypto_supported()`, which is always false without `SB_INLINECRYPT`.
  - Safe: `blk_crypto_submit_bio()`, as `ext4_io_submit()` does;
    `__blk_crypto_submit_bio()` hands the bio to blk-crypto-fallback when the
    device has no native support.
  - Safe: a `submit_io` hook in `struct iomap_dio_ops` that calls
    `blk_crypto_submit_bio()`, as `f2fs_dio_read_submit_io()` does;
    `iomap_dio_submit_bio()` does not call it when the hook is set.
- **Unsafe usage**: passing `fscrypt_set_bio_crypt_ctx()` a `gfp_mask` without
  `__GFP_DIRECT_RECLAIM`.
  - Unsafe: `bio_crypt_set_ctx()` warns and dereferences the `mempool_alloc()`
    result unchecked.
  - Safe: `GFP_NOIO`, as `io_submit_init_bio()` in `fs/ext4/page-io.c` passes.

**Decryption after a read**

- Block-based filesystems make no fs/crypto call after a read completes; the
  bio's crypt context is the only fscrypt involvement.
- There is no fscrypt_decrypt_pagecache_blocks(), fscrypt_decrypt_bio(),
  fscrypt_enqueue_decrypt_work() or fscrypt_read_workqueue here; `fscrypt_init()`
  creates no workqueue.
- Software decryption: `blk_crypto_fallback_bio_prep()` in
  `block/blk-crypto-fallback.c` wraps `bi_end_io`; the work runs on
  `blk_crypto_wq`.
- Filesystem `bi_end_io` after fallback decryption: called from the
  `blk_crypto_wq` worker by `blk_crypto_fallback_decrypt_bio()`; on an I/O error
  it is called straight from `blk_crypto_fallback_decrypt_endio()`.
- Decryption failure: reaches the filesystem only as `bio->bi_status`.
- `fs/ext4/readpage.c`: has no `struct bio_post_read_ctx`; only
  `struct ext4_verity_work`, queued by `mpage_end_io()`.
- `fs/f2fs/data.c`: `enum bio_post_read_step` has `STEP_DECOMPRESS` and
  `STEP_VERITY` only.

**Direct I/O**

- There is no fscrypt_dio_supported() here, and nothing in fs/crypto decides;
  each filesystem tests alignment itself.
- inlinecrypt is not a condition: neither `ext4_dio_alignment()` nor
  `f2fs_force_buffered_io()` tests `SB_INLINECRYPT` or refuses a file for being
  encrypted.
- ext4: `ext4_dio_alignment()` returns `i_blocksize()` for `IS_ENCRYPTED()`;
  `ext4_should_use_dio()` falls back to buffered I/O when misaligned, with no
  error.
- f2fs: `f2fs_force_buffered_io()` has no encryption test;
  `f2fs_should_use_dio()` applies the block-size rule to every file.
- f2fs misaligned I/O: buffered fallback when aligned to the device logical
  block size; otherwise direct I/O is attempted, and `iomap_dio_bio_iter()`
  returns `-EINVAL` for a position or length not aligned to the logical block
  size.
- `iomap_dio_read_simple()` in `include/linux/iomap.h`: returns `-ENOTBLK` for
  `IS_ENCRYPTED()`; `__iomap_dio_read_simple()` sets no crypt context and uses
  `submit_bio()` or `submit_bio_wait()`.
- `fscrypt_set_bio_crypt_ctx()` callers in `fs/iomap/direct-io.c`:
  `iomap_dio_bio_iter_one()` and `iomap_dio_zero()`, with the byte `pos`.
- `fscrypt_limit_io_blocks()`: not called in `fs/iomap/`; `ext4_iomap_begin()`
  and `f2fs_iomap_begin()` call it.

**Filesystem-layer data path**

- Three functions in `fs/crypto/crypto.c`: `fscrypt_encrypt_pagecache_blocks()`,
  `fscrypt_encrypt_block_inplace()`, `fscrypt_decrypt_block_inplace()`.
- There is no fscrypt_decrypt_pagecache_blocks() here; ceph decrypts with
  `fscrypt_decrypt_block_inplace()`.
- On a block-based filesystem: `ci_enc_key.tfm` is NULL for regular files, so
  `fscrypt_crypt_data_unit()` warns and returns `-ENOKEY`.
- Key not set up: `fscrypt_crypt_data_unit()` has `WARN_ON_ONCE(ci == NULL)` and
  returns `-ENOKEY`.
- `fscrypt_encrypt_block_inplace()` and `fscrypt_decrypt_block_inplace()`: `len`
  and `offs` are bytes; `lblk_num` is used unchanged as the data unit index.
- `supports_subblock_data_units` set: both in-place functions warn and return
  `-EOPNOTSUPP`.
- `fscrypt_encrypt_pagecache_blocks()` alignment: `len` and `offs` must both be
  multiples of the data unit size and `len` nonzero; otherwise `WARN_ON_ONCE()`
  and `ERR_PTR(-EINVAL)`.
- Large folio: `fscrypt_encrypt_pagecache_blocks()` has
  `VM_BUG_ON_FOLIO(folio_test_large(folio), folio)`, which compiles out without
  `CONFIG_DEBUG_VM`.
- `needs_bounce_pages` unset: `fscrypt_alloc_bounce_page()` warns and the caller
  gets `ERR_PTR(-ENOMEM)`, while the global `fscrypt_bounce_page_pool` is NULL.
- **Potentially unsafe usage**: `fscrypt_encrypt_pagecache_blocks()` with a
  blocking `gfp_flags` for every page of one request.
  - Unsafe: for the second and later pages; `mempool_alloc()` in
    `fscrypt_alloc_bounce_page()` waits for a page that the same request holds,
    so the mempool can deadlock.
  - Safe: `GFP_NOFS` for the first page and `GFP_NOWAIT` after, as
    `move_dirty_folio_in_page_array()` in `fs/ceph/addr.c` does.

## Filenames and no-key dentries

**Filename encryption**

- `fname->is_nokey_name`: set to true for every no-key lookup, before the name
  is decoded, so it is also true when `fscrypt_setup_filename()` returns
  `-ENOENT`; `__fscrypt_prepare_lookup()` reads it after `-ENOENT`.
- `fname->hash` and `fname->minor_hash`: filled from `dirhash[]` for every
  decoded no-key name, short or long.
- `fname->disk_name` in a no-key lookup: points at `bytes` inside `crypto_buf`
  for the short form; stays NULL with length 0 when the decoded length equals
  `FSCRYPT_NOKEY_NAME_MAX`.
- `-ENAMETOOLONG`: returned only when the plaintext length exceeds `NAME_MAX`.
- Padded length above the maximum: `__fscrypt_fname_encrypted_size()` clamps it
  to the maximum, so a ciphertext name can have a length that is not a
  multiple of the policy's padding.
- Maximum length: `fscrypt_setup_filename()` passes the constant `NAME_MAX`, not
  a per-filesystem limit; a filesystem tests its own limit itself, as
  `ubifs_lookup()` does with `UBIFS_MAX_NLEN`.
- IV: `fscrypt_generate_iv()` in `fs/crypto/crypto.c` is called with index 0 and
  the directory's `struct fscrypt_inode_info`; the `union fscrypt_iv` is all
  zero when the policy has none of the three flags below.

| Policy flag, tested in this order | IV for a filename |
|---|---|
| `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` | index holds the directory's `i_ino` in its upper 32 bits |
| `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` | index is `ci_hashed_ino` |
| `FSCRYPT_POLICY_FLAG_DIRECT_KEY` | index 0, and `ci_nonce` copied into the IV |

- Filename modes: the accepted set is in `fscrypt_valid_enc_modes_v1()` and
  `fscrypt_valid_enc_modes_v2()` in `fs/crypto/policy.c`; it includes
  `FSCRYPT_MODE_AES_128_CTS` and `FSCRYPT_MODE_SM4_CTS`.

**No-key names**

- `struct fscrypt_nokey_name`: defined in `fs/crypto/fname.c`, not in a header.
- There is no FSCRYPT_FNAME_MAX_UNDIGESTED_SIZE here; the 149-byte limit is the
  array size of `bytes`, written as `sizeof(nokey_name.bytes)`.
- There is no fscrypt_base64url_encode() here; `fscrypt_fname_disk_to_usr()`
  calls `base64_encode()` and `fscrypt_setup_filename()` calls
  `base64_decode()`, both in `lib/base64.c`, with `BASE64_URLSAFE` and `padding`
  false.
- `dirhash[]`: always the first 8 bytes of what `fscrypt_fname_disk_to_usr()`
  encodes, for every caller and for short names too, so a no-key name from it
  is never the encoding of the bare ciphertext.
- `dirhash[]` is zero when the caller passes 0 for `hash` and `minor_hash`, as
  `fscrypt_get_symlink()` does.
- `fscrypt_match_name()`: chooses its branch on `fname->disk_name.name` being
  non-NULL, not on `is_nokey_name`; a short no-key name takes the plain
  compare.
- `fscrypt_match_name()` reads only `disk_name` and `crypto_buf`;
  `ext4_match()` and `f2fs_match_name()` pass it a `struct fscrypt_name` on the
  stack with only `usr_fname`, `disk_name` and `crypto_buf` filled in.
- ubifs does not call `fscrypt_match_name()`: when `disk_name.name` is NULL,
  `ubifs_lookup()` finds the entry with `nm.hash` and `nm.minor_hash` through
  `ubifs_tnc_lookup_dh()`.
- ubifs `minor_hash`: the entry's `cookie`, which `ubifs_readdir()` passes to
  `fscrypt_fname_disk_to_usr()`.

**No-key dentries**

- `fscrypt_d_revalidate()` on a no-key dentry with `LOOKUP_RCU`: returns
  `-ECHILD` before it looks at the key, whether or not the key was added.
- `fscrypt_d_revalidate()` on a no-key dentry in ref-walk: calls
  `fscrypt_get_encryption_info(dir, true)` before it tests the key, so it sets
  up the directory's key itself; a negative result is returned as is.
- `fscrypt_d_revalidate()` uses its `dir` argument; it does not take the parent
  from the dentry.
- `__fscrypt_prepare_lookup()`: calls `fscrypt_prepare_dentry()` with
  `fname->is_nokey_name` when `fscrypt_setup_filename()` returns 0 or `-ENOENT`;
  on any other error it returns without calling `fscrypt_prepare_dentry()`.
- `fscrypt_prepare_dentry()`: changes only `d_flags`; it never installs dentry
  operations.
- There is no generic_set_encrypted_ci_d_ops() here; `generic_set_sb_d_ops()`
  in `fs/libfs.c` calls `set_default_d_op()`, which sets `__s_d_op` and
  `s_d_flags` in `struct super_block`.
- `generic_set_sb_d_ops()`: tests `sb->s_encoding` and then `sb->s_cop` at the
  time of the call, and installs nothing if both are unset.
- Order at mount in ext4, f2fs and ubifs: `sb->s_cop` is set first (directly or
  with `fscrypt_set_ops()`), then `generic_set_sb_d_ops()`, then the root dentry
  is allocated; `__d_alloc()` copies `__s_d_op` and `s_d_flags` into each new
  dentry.
- `DCACHE_NOKEY_NAME` is also set outside `fscrypt_prepare_dentry()`:
  `ceph_fill_trace()` and `ceph_readdir_prepopulate()` in `fs/ceph/inode.c` set
  it directly, under `d_lock`, on dentries they allocate.

**Disabling revalidation**

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

**Creating under a no-key dentry**

- `fscrypt_setup_filename()` with `lookup` 0: returns `-ENOKEY` only while the
  directory has no key; once the key was added after the lookup it succeeds and
  encrypts the no-key string as if it were a plaintext name.
- `ext4_add_entry()`: tests `fscrypt_is_nokey_name()` and returns `-ENOKEY`
  before it calls `__ext4_add_entry()`.
- ubifs: the test is in `ubifs_prepare_create()` in `fs/ubifs/dir.c`, which its
  create methods call, for example `ubifs_create()`.
- The two tests can differ: flag set and key present, when the key was added
  after the lookup.
- `fscrypt_has_encryption_key()`: tests only that the inode's
  `struct fscrypt_inode_info` pointer is non-NULL; fs/crypto clears that
  pointer only in `fscrypt_put_encryption_info()`.
- `__fscrypt_prepare_link()` and `__fscrypt_prepare_rename()`: after the flag
  test they make no key test of the directory.
- **Potentially unsafe usage**: a method that adds a name for a dentry that
  came from lookup, and calls `fscrypt_setup_filename()` with `lookup` 0 or
  tests `fscrypt_has_encryption_key()` on the directory.
  - Unsafe: when the directory can be encrypted and nothing earlier on the path
    tested `fscrypt_is_nokey_name()` on that dentry; if the key was added after
    the lookup, `fscrypt_setup_filename()` encrypts the no-key string as a
    plaintext name.
  - Safe: test `fscrypt_is_nokey_name()` first and return `-ENOKEY`, as
    `ext4_add_entry()`, `f2fs_add_link()` and `ubifs_prepare_create()` do; the
    flag is the one `fscrypt_prepare_dentry()` set at lookup.
  - Safe: after `fscrypt_prepare_link()` or `fscrypt_prepare_rename()` returned
    0 for an encrypted directory, as in `ubifs_link()` and `ubifs_rename()`;
    `__fscrypt_prepare_link()` and `__fscrypt_prepare_rename()` test the flag.
  - Safe: on a filesystem that never sets `S_ENCRYPTED`, as
    `btrfs_new_inode_prepare()` in `fs/btrfs/inode.c`;
    `fscrypt_setup_filename()` returns at its `IS_ENCRYPTED()` test.

## Master keys and the keyring

**Master key object**

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

**Adding a key**

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

**Removing a key**

- `do_remove_key()`: touches no `struct key` for the master key and does not
  call `key_invalidate()`; `fscrypt_initiate_key_removal()` does the removal.
- Deferred to the last active reference, in
  `fscrypt_put_master_key_activeref()`: every `struct fscrypt_mode_key` on
  `mk_mode_keys`, and `mk_ino_hash_key`.
- v1 file with `FSCRYPT_POLICY_FLAG_DIRECT_KEY`: `dk_raw` in
  `struct fscrypt_direct_key` is a copy of the raw master key that outlives
  the wipe of `mk_secret`; `fscrypt_put_direct_key()` frees it when the last
  inode using it is evicted.
- `try_to_lock_encrypted_files()` order: one `sync_filesystem()`, then
  `evict_dentries_for_decrypted_inodes()`, then `check_for_busy_inodes()`.
- `try_to_lock_encrypted_files()`: does not call `shrink_dcache_sb()` and
  does not invalidate pages itself.
- `shrink_dcache_inode()`: for a directory it calls `shrink_dcache_parent()`
  first, since child dentries pin the directory's dentry; then
  `d_prune_aliases()`.
- `do_remove_key()` calls no eviction function: the final `iput()` in
  `evict_dentries_for_decrypted_inodes()` calls the filesystem's
  `->drop_inode`, which decides; ext4, f2fs and ubifs call
  `fscrypt_drop_inode()` from it.
- `check_for_busy_inodes()`: the warning gives the count of busy inodes and
  one example inode number.
- `sync_filesystem()` failure: `try_to_lock_encrypted_files()` returns
  `err1 ?: err2`, so the ioctl returns the sync error and writes no
  `removal_status_flags`, although eviction was still attempted.

**Locks in fs/crypto**

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

**Eviction check context**

- Return value: computed from a lockless read of `mk_present`, so it can be
  stale at once; it does not guarantee that an inode is evicted once the
  key is removed.
- Dirty inode: `fscrypt_drop_inode()` returns 0 when any `I_DIRTY_ALL` bit
  is set, so an inode dirtied after the remover's sync stays cached and is
  counted busy.
- Reads: `fscrypt_get_inode_info()` loads the info pointer with
  `smp_load_acquire()`; `ci_master_key` is a plain read; only `mk_present`
  uses `READ_ONCE()`.
- `inode->i_lock`: must be held; `inode_state_read()` asserts it with
  `lockdep_assert_held()`.
- Generic helper: `inode_generic_drop()` in `include/linux/fs.h`; there is no
  generic_drop_inode() in this tree.
- Callers such as `ext4_drop_inode()`: call `fscrypt_drop_inode()` only when
  `inode_generic_drop()` returned 0.
- `fs/ceph`: sets `->drop_inode` to `inode_just_drop()` and never calls
  `fscrypt_drop_inode()`; its inodes are dropped at every final `iput()`.
- **Unsafe usage**: taking `mk_decrypted_inodes_lock` in
  `fscrypt_drop_inode()`.
  - Unsafe: `evict_dentries_for_decrypted_inodes()` takes `inode->i_lock`
    while holding `mk_decrypted_inodes_lock`, so the opposite order under
    `i_lock` can deadlock.
  - Safe: take `mk_decrypted_inodes_lock` at eviction, where `i_lock` is not
    held, as `put_crypt_info()` does.

**Handling key material**

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

## Policies

**Policy and context**

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

**Setting a policy**

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

**Same-policy rule**

- Returns 1 without comparing, besides an unencrypted parent and a child that
  is not a regular file, directory or symlink: when parent and child are both
  encrypted and `fscrypt_get_policy()` returns `-EINVAL` for both
  (unrecognized context version or size); this lets such files be deleted.
- Any error from `fscrypt_get_encryption_info()`, any other error from
  `fscrypt_get_policy()`, or `-EINVAL` for only one of the two: returns 0.
- Recognized version with unsupported modes or flags: not the `-EINVAL` case;
  the two policies are compared with `fscrypt_policies_equal()`.
- Without `CONFIG_FS_ENCRYPTION`: the stub in `include/linux/fscrypt.h`
  returns 0 for every pair.
- Link: `__fscrypt_prepare_link()` returns `-EXDEV`, not `-EPERM`.
- Link and rename: the filesystem calls `fscrypt_prepare_link()` and
  `fscrypt_prepare_rename()`, never `fscrypt_has_permitted_context()`
  directly.
- Rename within one directory: not checked; `__fscrypt_prepare_rename()`
  compares only when `old_dir != new_dir`.
- Lookup: `__fscrypt_prepare_lookup()` in `fs/crypto/hooks.c` does not call
  it; the filesystem's lookup method does, as in `ext4_lookup()`,
  `f2fs_lookup()` and `ubifs_lookup()`.
- Lookup check in `ext4_lookup()`, `f2fs_lookup()` and `ubifs_lookup()`: made
  only when `IS_ENCRYPTED(dir)` and the child is a directory or symlink;
  failure gives `-EPERM`.
- Regular files: not checked by those lookup methods; `fscrypt_file_open()`,
  which the filesystem calls from its open method or, in ubifs, installs as
  `->open`, checks them against the parent of the dentry used to open.

## Key derivation and IVs

**Contents key derivation**

- Shared keys: kept as `struct fscrypt_mode_key` nodes on the list
  `mk_mode_keys` in `struct fscrypt_master_key`
  (`fs/crypto/fscrypt_private.h`), one list for all three flags.
- There are no per-flag arrays here: mk_direct_keys, mk_iv_ino_lblk_64_keys,
  mk_iv_ino_lblk_32_keys and FSCRYPT_MODE_MAX are not defined in this tree.
- Node identity: `fscrypt_find_mode_key()` matches `hkdf_context`,
  `mode_num`, `data_unit_bits` and the prepared form (`blk_key` or `tfm`,
  via `fscrypt_is_key_prepared()`).
- One master key under one flag can therefore own several nodes with the
  same raw key bytes; for example `FSCRYPT_POLICY_FLAG_DIRECT_KEY` on ext4
  gets one `blk_key` node for regular files and one `tfm` node for
  directories and symlinks.
- `setup_per_mode_enc_key()` in `fs/crypto/keysetup.c`: derives and appends
  the node under `fscrypt_mode_key_setup_mutex`; there is no
  fscrypt_setup_per_mode_enc_key(), fscrypt_get_derived_key(),
  setup_mode_prepared_key() or mk_prepared_keys_lock.
- `fscrypt_find_mode_key()`: returns a pointer into the node with no
  reference taken; safe only because the caller holds `mk_sem` for read with
  `mk_present` true, as `setup_file_encryption_key()` does, which keeps the
  list append-only.
- Hardware-wrapped master key, regular file: `setup_per_mode_enc_key()`
  skips HKDF and passes `mk_secret.bytes` to
  `fscrypt_prepare_inline_crypt_key()` with `is_hw_wrapped` true.
- Hardware-wrapped master key, directory or symlink: the per-mode key is
  still HKDF-derived, with HKDF keyed by the software secret from
  `fscrypt_derive_sw_secret()`.
- `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`: the HKDF info includes `sb->s_uuid`,
  the same as `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64`; only
  `FSCRYPT_POLICY_FLAG_DIRECT_KEY` passes `include_fs_uuid` false.
- `FSCRYPT_POLICY_FLAG_DIRECT_KEY`: `supported_direct_key_modes()` requires
  equal contents and filenames modes, and the only such pair that
  `fscrypt_valid_enc_modes_v1()` or `fscrypt_valid_enc_modes_v2()` accepts
  is `FSCRYPT_MODE_ADIANTUM`; `FSCRYPT_MODE_AES_256_HCTR2` never qualifies.
- `fscrypt_put_master_key()`: drops only a structural reference and frees
  the struct through `call_rcu()`; it destroys no mode key.

**Version 1 file keys**

- `setup_v1_file_key_derived()` in `fs/crypto/keysetup_v1.c`: does the
  derivation inline; there is no derive_key_aes() in this tree.
- Crypto interface: the AES library, not the skcipher API;
  `aes_prepareenckey()` keys a stack `struct aes_enckey`, then
  `aes_encrypt()` runs once per 16-byte block.
- No transform is allocated, so the derivation itself has no allocation or
  `-ENOPKG` failure; errors come only from the size check and from
  `fscrypt_set_per_file_enc_key()`.
- Roles: the file nonce `ci_nonce` is the AES-128 key; the first
  `ci_mode->keysize` bytes of the master key are the plaintext.
- `keysize` not a multiple of `AES_BLOCK_SIZE`, or above
  `FSCRYPT_MAX_RAW_KEY_SIZE`: `WARN_ON_ONCE()` and `-EINVAL`.
- Derived key buffer: on the stack, wiped with `memzero_explicit()`; the
  `struct aes_enckey` is not wiped because the nonce is not secret.
- Master key lookup order: `setup_file_encryption_key()` in
  `fs/crypto/keysetup.c` searches `s_master_keys` first and calls
  `fscrypt_setup_v1_file_key()` with `mk_secret.bytes`.
- `fscrypt_setup_v1_file_key_via_subscribed_keyrings()`: runs only when that
  search finds nothing; it, not `fscrypt_setup_v1_file_key()`, calls
  `find_and_lock_process_key()`.
- `find_or_insert_direct_key()`: reuses a `struct fscrypt_direct_key` only
  if descriptor, `dk_sb`, `dk_mode`, the prepared form and the raw key
  (`crypto_memneq()`) all match.

**IV generation**

- `fscrypt_generate_iv()` in `fs/crypto/crypto.c`: zeroes the whole
  `union fscrypt_iv` (`sizeof(*iv)`), not `ci_mode->ivsize` bytes.
- `index` argument: already a data unit index; `fscrypt_generate_dun()` in
  `fs/crypto/block.c` computes it as `pos >> ci_data_unit_bits`. There is no
  ci_data_units_per_block_bits field.
- `fscrypt_mergeable_bio()` and `fscrypt_limit_io_blocks()`: both are in
  `fs/crypto/block.c`; neither tests the mount option or whether hardware is
  used; they act on every encrypted regular file.
- `fscrypt_crypt_data_unit()`: the other caller of `fscrypt_generate_iv()`
  for contents; it serves non-block-based filesystems and returns `-ENOKEY`
  with a WARN when `ci_enc_key.tfm` is NULL.
- `fscrypt_limit_io_blocks()` adds `lblk` to `ci_hashed_ino` as if a block
  were a data unit; that holds because `fscrypt_supported_v2_policy()`
  rejects sub-block data units with `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`;
  `supported_iv_ino_lblk_policy()` also rejects that flag when
  `s_blocksize != PAGE_SIZE`.
- `ci_hashed_ino`: set for any inode type, not only regular files;
  `fscrypt_setup_iv_ino_lblk_32_key()` skips it while `i_ino` is 0 and
  `fscrypt_set_context()` computes it later.
- Key must be set up: `fscrypt_set_bio_crypt_ctx()`,
  `fscrypt_mergeable_bio()` and `fscrypt_limit_io_blocks()` read the info
  through `fscrypt_get_inode_info_raw()` and dereference it with no NULL
  test.
- **Potentially unsafe usage**: adding data to a bio without calling
  `fscrypt_mergeable_bio()` for the added position.
  - Unsafe: when the added data can belong to another inode, is not
    logically consecutive, or under `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`
    lies in a range not bounded by `fscrypt_limit_io_blocks()`; blk-crypto
    derives later DUNs by `bio_crypt_dun_increment()`, so the data gets the
    wrong IV. The bio need not have a crypt context for this:
    `fscrypt_mergeable_bio()` returns false when the bio has none and the
    inode needs contents encryption, and the reverse.
  - Safe: one bio per logically contiguous range of one inode, inside a
    mapping whose length `fscrypt_limit_io_blocks()` bounded, as
    `iomap_dio_bio_iter_one()` does on mappings from `ext4_iomap_begin()`
    and `f2fs_iomap_begin()`.
  - Safe: check every added buffer and start a new bio on false, as
    `io_submit_add_bh()` in `fs/ext4/page-io.c` does through
    `io_submit_need_new_bio()`.

**Persistent formats**

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

## Model gaps

### Other mistakes models make

- Models allocate transforms with a zero mask. `fscrypt_allocate_skcipher()`
  passes `FSCRYPT_CRYPTOAPI_MASK`, which excludes async, memory-allocating
  and driver-only implementations.
- Models take the secret bytes to be sized by `FSCRYPT_MAX_KEY_SIZE`.
  `fs/crypto/fscrypt_private.h` undefines `FSCRYPT_MAX_KEY_SIZE`, so use
  `FSCRYPT_MAX_RAW_KEY_SIZE` or `FSCRYPT_MAX_ANY_KEY_SIZE`.
- Models take `i_ino` to be `unsigned long`. It is `u64` in `struct inode`,
  so `fs/crypto/` prints it with `%llu`; the 32-bit inode number limit for
  `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` and
  `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` policies comes from
  `has_32bit_inodes`, tested in `supported_iv_ino_lblk_policy()`, not from
  the type.
