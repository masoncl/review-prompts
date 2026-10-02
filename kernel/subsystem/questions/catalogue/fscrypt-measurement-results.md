# What the fscrypt measurement found

Three models were asked the 42 questions in `fscrypt-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Readers A and C said they assumed
kernels 6.10 to 6.19, know how fscrypt works and get nine names in ten right;
reader C needed the fewest corrections. Reader B said 6.10 to 6.12 and was
three-quarters rewritten: it carried the per-inode structure, the operations
table and the key setup return convention of a much older kernel, and was wrong
about a number of fundamentals. The hand-written guide was never checked
against current sources, so differences between it and the built guide are
expected and are noted near the end.

What fscrypt is for is well known to readers A and C: the two policy versions,
the context and its nonce, the HKDF contexts, the IV layouts, no-key names, the
hooks a filesystem calls and the errors user space sees. What every reader got
wrong is the file contents data path, which this tree has reworked: a
block-based filesystem now always goes through blk-crypto, the helpers that
decrypted a completed read are gone, and the two files all three readers named
for that code do not exist. After that come names and layouts inside the
keyring, the move of key derivation from crypto API transforms to library
calls, and a handful of facts that would change a verdict.

One word was dropped from `fscrypt.block-io-hooks` after the measurement: it
asked which "fscrypt functions" a filesystem calls when submitting, and the
call it needs there is a block layer one. Three more were reworded when the
build set was resized. `fscrypt.dio` now asks whether direct I/O works on an
encrypted file before it asks under what conditions, and
`fscrypt.info-access-usage` says what to do on a tree that has only one
accessor: each took something for granted. `fscrypt.key-setup-path` asked what
"that function" returns without having named one, and one builder's answer
never said whose return value it was giving; it now asks for the function
callers enter by and what that returns. The numbers are for the earlier
wordings.

## What all three readers got wrong

- **Where the block-layer code is.** All three named fs/crypto/inline_crypt.c,
  and readers A and C also fs/crypto/bio.c. Neither exists. `fs/crypto/block.c`
  holds the whole blk-crypto path and is built only with `CONFIG_BLOCK`;
  `fs/crypto/crypto.c` is the CPU path, used only by filesystems that are not
  block-based.
- **What decides the contents implementation.** All three described a
  per-inode choice made by fscrypt_select_encryption_impl() from the
  inlinecrypt mount option, the policy and what the device supports, recorded
  in a ci_inlinecrypt flag or tested with fscrypt_inode_uses_inline_crypto().
  None of those exists. `fscrypt_using_inline_encryption()` in
  `fs/crypto/fscrypt_private.h` tests only `S_ISREG()` and
  `s_cop->is_block_based`, so every regular file on ext4 or f2fs gets a
  `blk_crypto_key` and never a crypto API transform. `SB_INLINECRYPT` only
  makes `fscrypt_prepare_inline_crypt_key()` pass `BLK_CRYPTO_CFG_ALLOW_HW`;
  without it the block layer's fallback does the work on the CPU.
- **Decryption after a read.** All three described a post-read step in the
  filesystem: fscrypt_enqueue_decrypt_work(), fscrypt_decrypt_bio(), a
  bio_post_read_ctx with a decrypt step, an fscrypt read workqueue. None is in
  the tree. `mpage_end_io()` in `fs/ext4/readpage.c` handles only fs-verity,
  `fscrypt_init()` creates no workqueue, and decryption happens in the inline
  hardware or in `block/blk-crypto-fallback.c`. There is no
  fscrypt_decrypt_pagecache_blocks() either; the filesystem-layer functions
  are `fscrypt_encrypt_pagecache_blocks()` (only CephFS, which sets
  `needs_bounce_pages`) and the two in-place functions (UBIFS and CephFS).
- **The bio interface.** `fscrypt_set_bio_crypt_ctx()` and
  `fscrypt_mergeable_bio()` take a byte position (`loff_t pos`), not a logical
  block number, and the buffer-head variants all three named are gone:
  `fs/buffer.c` sets the context itself. `fscrypt_zeroout_range()` takes
  (inode, pos, sector, len). A bio with a crypt context has to be submitted
  with `blk_crypto_submit_bio()`; `submit_bio_noacct()` fails one the device
  cannot handle natively. Readers A and B said plain submit_bio(); reader C
  named the right call and marked it unsure.
- **Direct I/O.** All three required inlinecrypt and named
  fscrypt_dio_supported(), which does not exist. The documentation asks only
  for a block-based filesystem and alignment to the filesystem block size;
  `ext4_dio_alignment()` tests `IS_ENCRYPTED()` itself, and
  `fs/iomap/direct-io.c` sets the context from a byte position.
- **The operations table.** Readers A and C left out `is_block_based` (and
  so the field that picks the data path); reader B listed
  get_ino_and_lblk_bits(), get_num_devices() and key_prefix, none of which
  exists, and missed `inode_info_offs`, `needs_bounce_pages`,
  `has_32bit_inodes`, `supports_subblock_data_units`, `legacy_key_prefix` and
  `get_devices()`. ext4 and f2fs assign `sb->s_cop` directly; only ubifs and
  ceph use `fscrypt_set_ops()`.
- **Kconfig.** `FS_ENCRYPTION_INLINE_CRYPT` is a hidden bool, `default y if
  FS_ENCRYPTION && BLOCK`, not a user option depending on
  `BLK_INLINE_ENCRYPTION`. `FS_ENCRYPTION` itself selects
  `BLK_INLINE_ENCRYPTION` and `BLK_INLINE_ENCRYPTION_FALLBACK` if `BLOCK`,
  plus `CRYPTO_LIB_AES`, `CRYPTO_LIB_SHA256` and `CRYPTO_LIB_SHA512`.
  `FS_ENCRYPTION_ALGS` selects only AES, CBC, CTS and XTS, and exists so that
  the algorithms can be modules when the filesystems are.
- **Crypto interfaces.** The v1 key derivation calls the AES library
  (`aes_prepareenckey()`, `aes_encrypt()`) in `setup_v1_file_key_derived()`;
  all three said an ecb(aes) transform in a derive_key_aes() that is gone.
  HKDF is the library `hmac_sha512_init()`, `hmac_sha512_update()` and
  `hmac_sha512_final()` keyed by a `struct hmac_sha512_key` (reader B said
  crypto_shash, reader A was unsure and named a struct fscrypt_hkdf that does
  not exist), and `fscrypt_hkdf_expand()` returns void. Transforms are
  `struct crypto_sync_skcipher`, and `FSCRYPT_CRYPTOAPI_MASK` has three flags;
  readers A and B each left one out.
- **User claims on a master key.** `mk_users` is a list of
  `struct fscrypt_master_key_user`, each holding a quota key of type
  ".fscrypt"; all three called it a keyring, and reader C had
  `do_remove_key()` call keyring_clear(). A user already on the list is not
  charged again.
- **Who sets the encrypted flag.** Readers A and C said `->set_context` sets
  `S_ENCRYPTED` on a new inode. The filesystem does, before that:
  `__ext4_new_inode()`, `f2fs_set_encrypted_inode()`; `ext4_set_context()`
  warns if it is not already set.

## What only some readers got wrong

- **Reader B on fundamentals.** It called the per-inode structure struct
  fscrypt_info, reached through inode->i_crypt_info in `struct inode` with a
  fscrypt_get_info() accessor; the tree has `struct fscrypt_inode_info`, a
  pointer in the filesystem's own inode at `s_cop->inode_info_offs`, and
  `fscrypt_get_inode_info()`. It said `fscrypt_get_encryption_info()` returns
  -ENOKEY when the master key is absent (it returns 0, and
  `fscrypt_require_key()` is what gives -ENOKEY); that a v2 DIRECT_KEY policy
  encrypts with the master key (a per-mode key is derived); that
  IV_INO_LBLK_64 wraps; that filenames get an all-zero IV; that the v1
  descriptor is 16 bytes and the v1 context version 0; that there is a
  "revoked" key state and an mk_secret_sem; that the no-key name carries only
  a prefix and a dirhash, and that `fscrypt_match_name()` compares hashes;
  that `fscrypt_prepare_lookup()` installs dentry operations; that
  `fscrypt_d_revalidate()` checks the policy; that readdir, getattr on a
  symlink and drop_inode need no fscrypt call; that the symlink length prefix
  is encrypted and the reported size is the ciphertext's; that the test dummy
  key is fixed and added at mount; and that the add-key ioctl takes a "logon"
  key (it takes an "fscrypt-provisioning" key).
- **Per-mode keys** (readers A and C). Both named mk_direct_keys,
  mk_iv_ino_lblk_64_keys and mk_iv_ino_lblk_32_keys arrays. The tree has one
  list, `mk_mode_keys`, of `struct fscrypt_mode_key` nodes searched by
  `fscrypt_find_mode_key()` under RCU with `mk_sem` read-held and appended to
  under `fscrypt_mode_key_setup_mutex`. They are destroyed when the last
  active reference goes, not when removal starts; only `mk_secret` is wiped
  at once, in `fscrypt_initiate_key_removal()`.
- **Which accessor the I/O paths use** (readers A and B). Both said I/O paths
  must use the acquire accessor. The contents, bio and filename functions all
  use `fscrypt_get_inode_info_raw()`, because `fscrypt_file_open()` or
  `fscrypt_require_key()` already set the key up; the raw accessor's NULL
  check is a `VFS_WARN_ON_ONCE()` that compiles away without
  `CONFIG_DEBUG_VFS`, so it cannot be used to test for a key.
- **Filename IVs** (readers A and B). `fscrypt_fname_encrypt()` calls
  `fscrypt_generate_iv()` with index 0, so the nonce or the (hashed) inode
  number is still mixed in under the policy flags. Padding is computed in
  `__fscrypt_fname_encrypted_size()`, not in the encrypt function.
- **The same-policy check at lookup** (reader A). It said the check is
  deliberately not made at lookup. ext4, f2fs and ubifs call
  `fscrypt_has_permitted_context()` in `->lookup` for directories and
  symlinks and return -EPERM; regular files are checked in
  `fscrypt_file_open()`. The case allowed for deletion is a parent and child
  that both have an unrecognised policy.
- **The test dummy key** (readers A and B). It is random per boot
  (`get_random_once()`) and added on demand in `setup_file_encryption_key()`
  when the inode's policy equals the dummy policy.
- **No-key name sizes** (reader A). The decoded maximum is 189 bytes and
  encodes to 252 characters; the encoder is the library `base64_encode()`
  with `BASE64_URLSAFE`.
- **Changing inode flags** (readers A and C). `fscrypt_prepare_setflags()` is
  called by the VFS, from `fileattr_set_prepare()` in `fs/file_attr.c`, not by
  the filesystem's ioctl.
- **Adding a mode** (readers A and C). There is no FSCRYPT_MODE_MAX to bump.
  Because regular files on block-based filesystems always use blk-crypto, a
  contents mode without a `blk_crypto_mode` cannot be used there.
- **Set policy** (reader A on the first point, reader B on all three). An
  unrecognised existing context gives -EEXIST, an identical policy succeeds,
  and `fscrypt_ioctl_set_policy()` does not test `s_cop`; the filesystem's
  ioctl does.

## What the readers already knew

Readers A and C: the file map apart from the two missing files, the per-inode
structure and its offset in the operations table, the key setup path and its
return convention, policies against contexts and their sizes, the mode pairs,
the HKDF contexts and info strings, the IV layouts for contents, where v1 keys
come from, hardware-wrapped keys in outline, the set-policy checks, the hook
table (one correction each), the error codes, and what must never change on
disk. Reader C also had the no-key create rule, the dirhash key, the v1 key
sources and the set-policy checks right without a correction. The error codes
and the hook table were reader B's best answers, a quarter rewritten each.

## Where the hand-written guide is stale

`fscrypt.md` names no function, file or structure, so it has nothing that
drifts by name; what it says is general, and several lines are wrong or
misleading as stated.

- "Master keys in keyring": v2 keys are in a per-superblock hash table,
  `s_master_keys`, not a kernel keyring; only the legacy v1 path searches
  process keyrings.
- "Per-file keys derived" and "Per-file key derivation prevents IV
  collisions" hold only for the default setting. With DIRECT_KEY,
  IV_INO_LBLK_64 or IV_INO_LBLK_32 one per-mode key is shared by many files
  and the nonce or inode number in the IV keeps them apart.
- "Key removal makes files unreadable": removal wipes the secret and tries to
  evict the inodes; files still open keep working and the key stays
  "incompletely removed" until they go.
- "Key identifiers are cryptographic hashes": for v2. A v1 descriptor is
  whatever user space chose.
- "Stored in xattr or superblock": the context is per inode and where it goes
  is the filesystem's business; nothing in `fs/crypto` stores one in a
  superblock.
- "Must be unique per file and logical block": the unit is the crypto data
  unit, which can be smaller than a block, and every filename in a directory
  shares one IV by design.
- "Proper padding to block size (usually 16 bytes)" mixes two things: contents
  lengths must be multiples of `FSCRYPT_CONTENTS_ALIGNMENT`, and filenames are
  padded to at least 16 bytes and then to 4, 8, 16 or 32 as the policy says.
- "Key availability before decrypt operations": on a block-based filesystem
  the filesystem never calls a decrypt function.
- It has nothing on the hooks a filesystem must call, no-key names and
  dentries, the two data paths, or where anything is.

## What was left out of the build set and why

The build set has 11 of the 42 questions and asks for 505 words, which with
titles and headings comes to the 600 words a guide this short is sized to; no
answer has fewer than 40. It first had 9 questions at 20 to 35 words each,
sized to 300 words, and many of the bullets came out as fragments that meant
nothing without the question. The same 9 are kept with room to say what each
fact is about, and two came back: `fscrypt.dio`, where every reader required a
mount option the tree does not ask for and named a helper it does not have, and
`fscrypt.info-access-usage`, where two readers had the rule backwards and the
answer changes a verdict on any patch inside `fs/crypto`. The set is still
weighted towards the data path, which every reader has wrong and which decides
what a filesystem may call, then the two facts a reader two releases behind
gets backwards (where the per-inode pointer is and what key setup returns), the
rules a patch most often breaks, and what must never change. Left out, and kept
in the measurement set:

- What readers A and C answer and only reader B does not: policies and
  contexts, modes, key derivation and the KDF, IV generation, v1 key sources,
  hardware-wrapped keys, filename encryption, no-key names and dentries, the
  dirhash key, symlinks, set-policy, unsupported policies, the dummy mount
  option, error codes, inode teardown, adding a mode. For reader B this guide
  will not be enough; the documentation file is current and is the better
  remedy.
- `fscrypt.hook-list`: every reader has the table nearly right, and at 140
  words it is a quarter of the guide.
- `fscrypt.operations-table`: all weak, but the two fields that matter most
  (`inode_info_offs`, `is_block_based`) come out in the questions that are
  kept, `needs_bounce_pages` concerns one filesystem, and a table of every
  field needs 100 words.
- `fscrypt.fs-layer-io`, `fscrypt.config` and `fscrypt.crypto-interfaces`: all
  three readers wrong in part, but each matters to few patches (two
  filesystems, the Kconfig file, the key derivation internals), and the code
  or Kconfig text is in front of whoever changes it. They are the next to
  bring back if the guide is allowed to grow.
- The keyring internals (`fscrypt.master-key`, `fscrypt.add-key`,
  `fscrypt.key-removal`, `fscrypt.locks`, `fscrypt.secret-handling-usage`):
  the structure comment in `fs/crypto/fscrypt_private.h` is accurate and
  longer than this guide.
- `fscrypt.policy-enforcement`: one reader wrong about lookup and one about
  most of it, but it asks for the call sites, their error codes and the
  exception, which needs 70 words or more; no room.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           88        27%     14     10   6.10 to 6.18
reader B          105        74%      1     39   6.10 to 6.12
reader C           81        21%     22      7   6.12 to 6.19

question                           reader A      reader B      reader C   verdict
fscrypt.core-files                  4% ( 4)      12% ( 1)       8% ( 2)   all fair: drop, or shrink to a pointer
fscrypt.docs-and-tests              8% ( 1)      67% ( 1)      40% ( 1)   weak: reader B, reader C
fscrypt.config                     46% ( 4)      90% ( 1)      47% ( 1)   all weak
fscrypt.crypto-interfaces          61% ( 2)      78% ( 2)      43% ( 2)   all weak
fscrypt.inode-info                  0% ( 4)      84% ( 7)      11% ( 6)   weak: reader B
fscrypt.operations-table           42% ( 4)      63% ( 2)      40% ( 3)   all weak
fscrypt.master-key                 18% ( 1)      79% ( 3)      16% ( 4)   weak: reader B
fscrypt.policy-and-context         10% ( 1)      83% ( 2)       9% ( 1)   weak: reader B
fscrypt.modes                       8% ( 0)      73% ( 2)      11% ( 0)   weak: reader B
fscrypt.key-setup-path              5% ( 2)      83% ( 4)      13% ( 3)   weak: reader B
fscrypt.key-derivation             23% ( 4)      84% ( 3)      14% ( 3)   weak: reader B
fscrypt.kdf                         9% ( 3)      79% ( 2)       4% ( 1)   weak: reader B
fscrypt.iv-generation              26% ( 3)      69% ( 2)       1% ( 2)   weak: reader B
fscrypt.v1-key-sources              7% ( 1)      81% ( 2)       0% ( 0)   weak: reader B
fscrypt.hw-wrapped-keys            11% ( 1)      68% ( 2)      37% ( 1)   weak: reader B
fscrypt.add-key                    41% ( 5)      77% ( 3)      24% ( 6)   weak: reader A, reader B
fscrypt.key-removal                45% ( 3)      87% ( 4)      24% ( 3)   weak: reader A, reader B
fscrypt.locks                      25% ( 3)      79% ( 4)      10% ( 2)   weak: reader B
fscrypt.secret-handling-usage      25% ( 1)      68% ( 1)      11% ( 1)   weak: reader B
fscrypt.contents-impl-choice       63% ( 4)      88% ( 3)      66% ( 6)   all weak
fscrypt.block-io-hooks             32% ( 1)      77% ( 1)      35% ( 1)   weak: reader B
fscrypt.read-decryption            84% ( 1)      82% ( 1)      81% ( 1)   all weak
fscrypt.fs-layer-io                26% ( 1)      78% ( 1)      23% ( 1)   weak: reader B
fscrypt.data-unit-size             30% ( 1)      85% ( 1)       2% ( 1)   weak: reader B
fscrypt.dio                        63% ( 1)      78% ( 1)      65% ( 1)   all weak
fscrypt.filename-encryption        38% ( 4)      66% ( 8)       3% ( 2)   weak: reader B
fscrypt.nokey-names                31% ( 2)      85% ( 3)      10% ( 2)   weak: reader B
fscrypt.nokey-dentries             50% ( 1)      90% ( 2)      18% ( 2)   weak: reader A, reader B
fscrypt.nokey-create-usage         31% ( 1)      82% ( 2)       0% ( 0)   weak: reader B
fscrypt.dirhash                    28% ( 1)      72% ( 1)       0% ( 0)   weak: reader B
fscrypt.symlinks                   30% ( 1)      84% ( 3)      10% ( 1)   weak: reader B
fscrypt.set-policy                 13% ( 1)      92% ( 3)       0% ( 0)   weak: reader B
fscrypt.policy-enforcement         33% ( 1)      87% ( 3)      12% ( 2)   weak: reader B
fscrypt.unsupported-policy         27% ( 1)      91% ( 1)      12% ( 1)   weak: reader B
fscrypt.test-dummy                 22% ( 1)      79% ( 2)      31% ( 1)   weak: reader B
fscrypt.error-codes                13% ( 0)      26% ( 3)      12% ( 0)   middling
fscrypt.hook-list                   1% ( 1)      23% ( 5)       4% ( 2)   middling
fscrypt.new-inode                  28% ( 5)      79% ( 2)      35% ( 1)   weak: reader B
fscrypt.info-access-usage          61% ( 3)      81% ( 1)      33% ( 4)   weak: reader A, reader B
fscrypt.inode-teardown              9% ( 0)      75% ( 2)      32% ( 2)   weak: reader B
fscrypt.format-stability            6% ( 5)      67% ( 3)      18% ( 5)   weak: reader B
fscrypt.new-mode                   35% ( 4)      69% ( 5)      25% ( 3)   weak: reader B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `fscrypt.operations-table`, `fscrypt.nokey-dentries`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `fscrypt.master-key`, `fscrypt.policy-and-context`, `fscrypt.key-derivation`, `fscrypt.iv-generation`, `fscrypt.add-key`, `fscrypt.key-removal`, `fscrypt.locks`, `fscrypt.secret-handling-usage`, `fscrypt.fs-layer-io`, `fscrypt.filename-encryption`, `fscrypt.nokey-names`, `fscrypt.set-policy`, `fscrypt.policy-enforcement`, `fscrypt.inode-teardown`.

## Questions reorganised

29 questions before and 29 after, every id kept, now by subject after the file table: per-inode
key state (5), the file contents data path (6), filenames and no-key dentries (4), master keys and
the keyring (5), policies (3), key derivation and IVs (3). Nothing merged or dropped. Inventories
reworded: `fscrypt.core-files` is a job-to-file table naming the files a reader expects that are
absent; `fscrypt.operations-table` asks which members pick the data path and which remembered
ones are gone; `fscrypt.locks` asks what covers the secret, the users and shared keys.
`fscrypt.key-setup-path` no longer asks for a trace; accessor ordering moved from
`fscrypt.inode-info` to `fscrypt.info-access-usage`. Four-part questions were cut to three.
