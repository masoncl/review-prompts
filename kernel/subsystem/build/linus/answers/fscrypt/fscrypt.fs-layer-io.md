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
