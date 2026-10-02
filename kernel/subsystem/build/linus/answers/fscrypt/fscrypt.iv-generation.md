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
