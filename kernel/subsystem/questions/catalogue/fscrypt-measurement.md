# Questions: Fscrypt (measurement set)

- guide: fscrypt.md
- title: Fscrypt

A wide set of questions about `fs/crypto` (fscrypt): policies and keys, how a
file's key is set up, filename encryption and no-key names, the hooks a
filesystem calls, the two data paths, and the documentation. It is used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 126 words, four
lists of general statements with no function or file named. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## fscrypt.core-files: Core files

- section: Finding your way
- relevance: 5 - a reviewer has to know which file a change belongs in
- words: 110

Which files hold fscrypt's policy handling, the filesystem-level keyring, key
setup for each policy version, the key derivation function, filename
encryption, the hooks called from filesystem operations, file contents
encryption done by the CPU, file contents encryption done through the block
layer, the private and public headers, the user API header and the
documentation? A table. Start from `fs/crypto/`.

## fscrypt.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - says where behaviour is specified and how a change is tested
- words: 70

Where is fscrypt documented for users and for filesystem implementers, and how
is it tested: which test suite, which test group, and which mount option lets
the ordinary tests run on encrypted files? Are there any fscrypt tests in the
kernel tree itself?

## fscrypt.config: Kconfig options

- section: Finding your way
- relevance: 3 - decides which code is built and which algorithms are present
- words: 80

What do the Kconfig symbols `FS_ENCRYPTION`, `FS_ENCRYPTION_ALGS` and
`FS_ENCRYPTION_INLINE_CRYPT` each select or depend on, which of them can a user
set, and what does a filesystem's own Kconfig entry have to do? Start from
`fs/crypto/Kconfig`.

## fscrypt.crypto-interfaces: Kernel crypto interfaces used

- section: Finding your way
- relevance: 3 - the interfaces have been moving from the crypto API to library calls
- words: 90

Which kernel crypto interfaces does fs/crypto use for contents and filename
encryption, for key derivation, for hashing long no-key names and for the v1
key derivation, and which kinds of crypto API driver does it refuse and why?
Start from `FSCRYPT_CRYPTOAPI_MASK`.

# Objects

## fscrypt.inode-info: Per-inode key state

- section: Structures
- relevance: 5 - every entry point starts by finding this
- words: 100

What structure holds an inode's set-up encryption key, where is the pointer to
it stored, and how does fs/crypto find that pointer for a given inode? Name
the accessors and say which memory ordering each uses. Start from
`fscrypt_get_inode_info()` and `struct fscrypt_operations`.

## fscrypt.operations-table: Filesystem operations table

- section: Structures
- relevance: 5 - what a filesystem declares decides which paths fs/crypto takes
- words: 120

List the fields and callbacks of `struct fscrypt_operations`, say what each
tells fs/crypto or does, and which a filesystem may leave unset. A table. How
is the table attached to a superblock?

## fscrypt.master-key: Master key object

- section: Structures
- relevance: 4 - key lifetime bugs come from misreading the states and counts
- words: 110

What does `struct fscrypt_master_key` represent, where do a filesystem's master
keys hang off the superblock, what states can a key be in, and how is its
lifetime counted: which references keep what alive? Start from
`fs/crypto/fscrypt_private.h` and `fs/crypto/keyring.c`.

## fscrypt.policy-and-context: Policy and context

- section: Structures
- relevance: 4 - the two are easy to confuse and one of them is on disk
- words: 90

What is the difference between an encryption policy and an encryption context,
which versions of each exist and how large are they, which value in the
version field denotes each policy version, and who generates the nonce? Start
from `union fscrypt_context` and `include/uapi/linux/fscrypt.h`.

## fscrypt.modes: Encryption modes

- section: Structures
- relevance: 3 - the accepted pairs differ by policy version
- words: 90

Which encryption modes does this tree define, which pairs of contents and
filenames modes does a policy of each version accept, and where are the mode
table and the pair checks? Start from `fscrypt_modes`.

# Keys

## fscrypt.key-setup-path: Key setup path

- section: Setting up and deriving keys
- relevance: 5 - the return convention is what callers get wrong
- words: 110

Trace how an existing encrypted inode gets its key set up: which function do
callers enter by, which reads the context, which validates the policy, which
finds the master key, which prepares the key, and how is the result published
when several tasks race? What does the entry function return when the master
key is absent, and how does a caller tell that case from success? Start from
`fscrypt_get_encryption_info()`.

## fscrypt.key-derivation: Contents key derivation

- section: Setting up and deriving keys
- relevance: 4 - which key a file uses depends on the policy flags
- words: 110

How is the key that encrypts a file's contents derived from the master key
under a v2 policy: by default, and under each of the three policy flags that
change it? What does the v1 derivation do instead? Name the function for each
case and what goes into the derivation. Start from
`fscrypt_setup_v2_file_key()`.

## fscrypt.kdf: Key derivation function

- section: Setting up and deriving keys
- relevance: 3 - the inputs are persistent and the implementation has changed
- words: 90

Which key derivation function does fscrypt use for v2 policies, how is its
application-specific info string built, in which contexts is it used, and
which kernel crypto interface implements it? Can an expansion fail? Start from
`fs/crypto/hkdf.c`.

## fscrypt.iv-generation: IV generation

- section: Setting up and deriving keys
- relevance: 4 - IV reuse is the failure this code exists to prevent
- words: 100

How is the IV for a data unit of file contents built under the default setting
and under each policy flag that changes it, what IV do filenames use, and
under which setting can the IV's low bits wrap around within one file? Which
function must be kept in step with the IV generator? Start from
`fscrypt_generate_iv()`.

## fscrypt.v1-key-sources: Keys for v1 policies

- section: Setting up and deriving keys
- relevance: 2 - legacy, but still in the key setup path
- words: 70

Where can the master key for a v1 policy come from, in which order are the
sources searched, and what can fscrypt not do for an inode whose key came from
the legacy source? Start from
`fscrypt_setup_v1_file_key_via_subscribed_keyrings()`.

## fscrypt.hw-wrapped-keys: Hardware-wrapped keys

- section: Setting up and deriving keys
- relevance: 3 - a newer feature with its own restrictions
- words: 90

How does fscrypt support hardware-wrapped master keys: how is one added, which
policies and mount options does it require, what is derived from it for uses
other than file contents, and how are its key identifiers kept distinct from
those of raw keys? Start from `fscrypt_derive_sw_secret()`.

## fscrypt.add-key: Adding a key

- section: The keyring ioctls
- relevance: 4 - the privilege and quota rules are security relevant
- words: 110

What does `FS_IOC_ADD_ENCRYPTION_KEY` check and do: who may add a key for each
policy version, how is a v2 key's identifier obtained, how are several users
adding the same key tracked and charged, and how can the key come from a
keyring key instead of the ioctl argument? Start from
`fscrypt_ioctl_add_key()`.

## fscrypt.key-removal: Removing a key

- section: The keyring ioctls
- relevance: 4 - removal races with inodes still in use
- words: 110

What happens when a master key is removed: what is wiped at once, what is done
to the inodes that were unlocked with it, what does user space learn if some
stay busy, and how does `fscrypt_drop_inode()` take part? Start from
`do_remove_key()`.

## fscrypt.locks: Locks in fs/crypto

- section: The keyring ioctls
- relevance: 4 - several fields are read without their lock on purpose
- words: 110

List the locks in fs/crypto and what each protects: those in the master key,
the one in the keyring, and the file-scope mutexes and spinlocks. Which fields
are read without their lock and how, and which exported function cannot take
the master key's semaphore because of the context it is called in?

## fscrypt.secret-handling-usage: Handling key material

- section: The keyring ioctls
- relevance: 4 - a missed wipe is invisible in testing
- words: 90

What handling of key material in fs/crypto leaves secrets in memory, and what
does correct code do for stack buffers, for heap objects and for the master key
secret once it is no longer needed? When is a raw master key not kept at all?
Start from `fs/crypto/keyring.c` and `fscrypt_destroy_prepared_key()`.

# File contents

## fscrypt.contents-impl-choice: Choosing the contents implementation

- section: Data path
- relevance: 5 - decides which set of functions a filesystem may call
- words: 100

What decides whether a regular file's contents are encrypted and decrypted by
the block layer or by fs/crypto calling the crypto API: a mount option, a
property of the filesystem, the hardware, or the policy? Which function makes
the test, and what does the inlinecrypt mount option change? Start from
`fscrypt_prepare_key()`.

## fscrypt.block-io-hooks: Block-based data path

- section: Data path
- relevance: 5 - the signatures and the submit call are what a patch touches
- words: 110

What must a block-based filesystem do to each bio that carries an encrypted
file's contents: which functions does it call when allocating the bio, when
adding more data, when sizing the I/O and when submitting, and which arguments
identify the position in the file? Start from `fscrypt_set_bio_crypt_ctx()`.

## fscrypt.read-decryption: Decryption after a read

- section: Data path
- relevance: 5 - readers may remember helpers this tree may not have
- words: 80

After a read bio for an encrypted file completes on a block-based filesystem,
does the filesystem call into fs/crypto to decrypt the pages, and is there an
fscrypt workqueue for that? If so name the functions; if not, say where
decryption happens. Start from `fs/ext4/readpage.c`.

## fscrypt.fs-layer-io: Filesystem-layer data path

- section: Data path
- relevance: 4 - the restrictions are asserted at run time, not compile time
- words: 110

Which functions does fs/crypto offer to a filesystem that is not block-based
for encrypting and decrypting file contents, what must the filesystem declare
to use the ones that need bounce pages, what alignment must lengths have, and
which in-tree filesystems use which? Start from `fs/crypto/crypto.c`.

## fscrypt.data-unit-size: Crypto data units

- section: Data path
- relevance: 3 - the data unit is not always the filesystem block
- words: 90

What is a crypto data unit, how is its size chosen for a file, what limits
apply to a user-selected size, and which filesystem capability permits one?
Which functions refuse to work with sub-block data units? Start from
`fscrypt_policy_du_bits()`.

## fscrypt.dio: Direct I/O

- section: Data path
- relevance: 3 - the conditions have changed with the data path
- words: 70

Does direct I/O work on an encrypted file in this tree, and under what
conditions? What happens when they are not met, and is there an fscrypt helper
that a filesystem calls to decide? Start from the direct I/O section of
`Documentation/filesystems/fscrypt.rst` and `fs/iomap/direct-io.c`.

# Filenames

## fscrypt.filename-encryption: Filename encryption

- section: Names
- relevance: 4 - the lookup argument changes what comes back
- words: 100

How is a filename encrypted: what padding and minimum length apply, what IV is
used, and what does `fscrypt_setup_filename()` produce when the directory's key
is available, when it is not and the caller is a lookup, and when it is not
and the caller wants to create a name?

## fscrypt.nokey-names: No-key names

- section: Names
- relevance: 4 - the format has to round-trip through lookup
- words: 100

How is a filename presented to user space when the directory's key is absent:
what is encoded, with which encoding and which helper, how are long names kept
within NAME_MAX, and how is such a name matched back to a directory entry?
Start from `struct fscrypt_nokey_name` and `fscrypt_match_name()`.

## fscrypt.nokey-dentries: No-key dentries

- section: Names
- relevance: 5 - a stale no-key dentry after the key is added is a recurring bug
- words: 110

How is a dentry that was looked up by no-key name marked, how does it become
invalid once the key is added, which dentry operation must a filesystem
install for that and which VFS helper installs it, and when is revalidation
switched off again? Start from `fscrypt_prepare_lookup()` and
`fscrypt_d_revalidate()`.

## fscrypt.nokey-create-usage: Creating under a no-key dentry

- section: Names
- relevance: 5 - checking the directory's key is the fix that looks right and is not
- words: 90

What usage of a no-key dentry in a filesystem's create, mkdir, mknod, symlink,
link or rename method is unsafe, and what does correct in-tree code do? Why
is checking that the directory inode has its key not enough? Start from
`fscrypt_is_nokey_name()`.

## fscrypt.dirhash: Directory hash key

- section: Names
- relevance: 3 - only casefolded directories, but it ties into key setup
- words: 80

Which directories get a secret hash key for filenames, from what is it
derived, when is it derived for a directory that already exists, and which
policy version cannot have one? Start from `fscrypt_derive_dirhash_key()` and
`fscrypt_prepare_setflags()`.

## fscrypt.symlinks: Encrypted symlinks

- section: Names
- relevance: 3 - a two-step interface with a cache that outlives the key info
- words: 100

How is an encrypted symlink target stored on disk, which functions does a
filesystem call to create one and to read one, where is the decrypted target
cached and when is that cache freed, and what is reported as the size? Start
from `fscrypt_prepare_symlink()` and `fscrypt_get_symlink()`.

# Policies

## fscrypt.set-policy: Setting a policy

- section: Policy rules
- relevance: 4 - each failed condition has its own error code
- words: 100

What must hold for `FS_IOC_SET_ENCRYPTION_POLICY` to succeed on an inode, what
error does each failed condition give, and what extra check applies to a v2
policy? Start from `fscrypt_ioctl_set_policy()`.

## fscrypt.policy-enforcement: Same-policy rule

- section: Policy rules
- relevance: 5 - a filesystem that skips a call site loses the protection
- words: 110

What does `fscrypt_has_permitted_context()` enforce, at which points must a
filesystem or fs/crypto call it, which error code does each caller turn a
failure into, and which case does it allow so that undecipherable files can
still be deleted?

## fscrypt.unsupported-policy: Unsupported policies

- section: Policy rules
- relevance: 3 - deletion has to keep working on files this kernel cannot read
- words: 80

How does fs/crypto treat an inode whose context or policy this kernel does not
recognise or support: which operations still work, which parameter selects
that behaviour, and which callers pass it? Start from
`fscrypt_get_encryption_info()`.

## fscrypt.test-dummy: Dummy encryption mount option

- section: Policy rules
- relevance: 2 - test-only, but every filesystem has to wire it up
- words: 80

How does the test_dummy_encryption mount option work: which helpers parse and
show it, which policies can it select, where does its key come from and when
is that key added?

## fscrypt.error-codes: Error codes

- section: Policy rules
- relevance: 3 - user space and the tests match on them
- words: 100

Which error does user space see for each of: opening a file without its key,
creating in a directory without its key, linking or renaming across policies,
a mode the kernel lacks an algorithm for, an unsupported policy on open, and a
corrupt encrypted name? Name the function that returns each.

# Using fscrypt from a filesystem

## fscrypt.hook-list: Filesystem hooks

- section: Filesystem integration
- relevance: 5 - the checklist for adding or reviewing fscrypt support
- words: 140

For each filesystem operation (open, lookup, readdir, create, link, rename,
setattr, symlink creation and reading, getattr on a symlink, changing inode
flags, inode eviction, inode freeing, drop_inode, unmount), which fscrypt
function must be called, and by whom: the filesystem or the VFS? A table.
Start from `fs/crypto/hooks.c` and `include/linux/fscrypt.h`.

## fscrypt.new-inode: Creating an encrypted inode

- section: Filesystem integration
- relevance: 5 - the split around the transaction is easy to break
- words: 110

In what order does a filesystem call fscrypt when creating a file in an
encrypted directory, which call must come before the transaction starts and
which runs inside it and why, which inode fields must already be set, and what
is deferred until the inode number is known? Start from
`fscrypt_prepare_new_inode()` and `fscrypt_set_context()`.

## fscrypt.info-access-usage: Reading the key pointer

- section: Filesystem integration
- relevance: 4 - the two accessors differ only in a barrier and an assertion
- words: 90

What usage of the raw, barrier-free accessor for an inode's fscrypt info is
unsafe, and what that looks similar is correct? Name in-tree callers of each
accessor that show the difference. If this tree has only one accessor, say so
and stop. Start from `fscrypt_get_inode_info_raw()`.

## fscrypt.inode-teardown: Inode teardown

- section: Filesystem integration
- relevance: 4 - two frees with different RCU requirements
- words: 80

Which fscrypt function frees an inode's key state and which frees what needs
an RCU delay, from which filesystem methods is each called, and why can the
first not skip inodes that do not have the encrypted flag set? Start from
`fscrypt_put_encryption_info()` and `fscrypt_free_inode()`.

# Changing the implementation

## fscrypt.format-stability: Persistent formats

- section: What a change must preserve
- relevance: 5 - a change here makes existing files unreadable
- words: 100

Which of fscrypt's formats and derivations are persistent and must never
change (on-disk structures, derivation inputs, IV layouts, padding), and which
user-visible output does the documentation say may change? What does the code
do to catch an accidental change in a structure's size?

## fscrypt.new-mode: Adding an encryption mode

- section: What a change must preserve
- relevance: 3 - touches the UAPI, the mode table, the block layer and the docs
- words: 90

What has to be added or updated to support a new encryption mode: the UAPI
number, the mode table fields, the pair checks, the block layer mode, Kconfig
and the documentation? Where may a new mode pair not be added? Start from
`fscrypt_valid_enc_modes_v2()`.
