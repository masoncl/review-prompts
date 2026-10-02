# Questions: Fscrypt

- guide: fscrypt.md
- title: Fscrypt

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/fscrypt-measurement.md` is the
wider set the readers were measured on and `catalogue/fscrypt-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## fscrypt.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## fscrypt.core-files: Core files

- section: Finding your way
- relevance: 5 - the block-layer code is not in the files readers remember

A table and nothing else, job to file: policy handling; the filesystem-level
keyring; key setup for each policy version; the key derivation function;
filename encryption; the hooks called from filesystem operations; file contents
encryption done by the CPU; file contents encryption done through the block
layer; the private header, the public header and the user API header. Where a
reader is likely to look for a file that does not exist in this tree, say so in
the row. Start from `fs/crypto/`.

# Per-inode key state

## fscrypt.inode-info: Per-inode key structure

- section: Per-inode key state
- relevance: 5 - every entry point starts by finding this, and it has moved

What is the structure that holds an inode's set-up encryption key called, where is the pointer to
it stored, and how does fs/crypto find that pointer for a given inode? Start from
`fscrypt_get_inode_info()` and `struct fscrypt_operations`.

## fscrypt.key-setup-path: Key setup and absent keys

- section: Per-inode key state
- relevance: 4 - success is returned when the key is absent

What does `fscrypt_get_encryption_info()` return when the inode's master key is absent, and what
must a caller test to learn whether the key was set up? How is the result published when several
tasks set up the same inode at once? Start from `fscrypt_get_encryption_info()`.

## fscrypt.new-inode: Creating an encrypted inode

- section: Per-inode key state
- relevance: 5 - the split around the transaction is easy to break

When must `fscrypt_prepare_new_inode()` and `fscrypt_set_context()` each be called relative to the
filesystem's transaction, and what must the filesystem have set on the inode before each call?
Which part of key setup, if any, waits until the inode number is known? Start from
`fscrypt_prepare_new_inode()` and `fscrypt_set_context()`.

## fscrypt.inode-teardown: Inode teardown

- section: Per-inode key state
- relevance: 4 - two frees with different RCU requirements

What does `fscrypt_put_encryption_info()` free and what does `fscrypt_free_inode()` free, and from
which filesystem method must each be called? For which inodes must a filesystem call
`fscrypt_put_encryption_info()`? Start from `fscrypt_put_encryption_info()` and
`fscrypt_free_inode()`.

## fscrypt.info-access-usage: Reading the key pointer

- section: Per-inode key state
- relevance: 4 - the two accessors differ only in a barrier and an assertion

What do `fscrypt_get_inode_info()` and `fscrypt_get_inode_info_raw()` each guarantee about
ordering against the publication of the key? What are the requirements for calling
`fscrypt_get_inode_info_raw()` in order to assure safe usage? If this tree has only one accessor,
say so and stop. Start from `fscrypt_get_inode_info_raw()`.

# File contents data path

## fscrypt.contents-impl-choice: Choosing the contents implementation

- section: File contents data path
- relevance: 5 - no reader knows what makes the choice in this tree

What decides whether a regular file's contents are encrypted and decrypted by the block layer or
by fs/crypto calling the crypto API, and which function makes the test? What does the inlinecrypt
mount option change? Start from `fscrypt_prepare_key()`.

## fscrypt.operations-table: Filesystem operations table

- section: File contents data path
- relevance: 5 - what a filesystem declares decides which paths fs/crypto takes

Which members of `struct fscrypt_operations` select the file contents data path, permit bounce
pages and say where the per-inode pointer lives? How does a filesystem attach its `struct
fscrypt_operations` to a superblock?

## fscrypt.block-io-hooks: Block-based data path

- section: File contents data path
- relevance: 5 - the arguments and the submit call have changed

What must a block-based filesystem call for each bio that carries an encrypted file's contents,
from allocating the bio to submitting it, and in what unit do the fscrypt calls take the position
in the file? What are the requirements for submitting such a bio in order to assure safe usage?
Start from `fscrypt_set_bio_crypt_ctx()`.

## fscrypt.read-decryption: Decryption after a read

- section: File contents data path
- relevance: 5 - readers remember helpers this tree may not have

After a read bio for an encrypted file completes on a block-based filesystem,
does the filesystem call into fs/crypto to decrypt the pages, and is there an
fscrypt workqueue for that? If so name the functions; if not, say where
decryption happens. Start from `fs/ext4/readpage.c`.

## fscrypt.dio: Direct I/O

- section: File contents data path
- relevance: 4 - every reader measured names a helper and a requirement this tree may not have

Does direct I/O work on an encrypted file in this tree, and under what
conditions? What happens when they are not met, and is there an fscrypt helper
that a filesystem calls to decide? Start from the direct I/O section of
`Documentation/filesystems/fscrypt.rst` and `fs/iomap/direct-io.c`.

## fscrypt.fs-layer-io: Filesystem-layer data path

- section: File contents data path
- relevance: 4 - the restrictions are asserted at run time, not compile time

Which functions does fs/crypto provide to a filesystem that is not block-based for encrypting and
decrypting file contents? What do they require of the filesystem and of the lengths passed to
them, and where is each requirement enforced? Start from `fs/crypto/crypto.c`.

# Filenames and no-key dentries

## fscrypt.filename-encryption: Filename encryption

- section: Filenames and no-key dentries
- relevance: 4 - the lookup argument changes what comes back

What does `fscrypt_setup_filename()` produce when the directory's key is available, when it is not
and the caller is a lookup, and when it is not and the caller wants to create a name? What padding
and what IV does filename encryption use?

## fscrypt.nokey-names: No-key names

- section: Filenames and no-key dentries
- relevance: 4 - the format has to round-trip through lookup

How is a filename presented to user space when the directory's key is absent:
what is encoded and with which encoding, how are long names kept within
NAME_MAX, and how is such a name matched back to a directory entry? Start from
`struct fscrypt_nokey_name` and `fscrypt_match_name()`.

## fscrypt.nokey-dentries: No-key dentries

- section: Filenames and no-key dentries
- relevance: 5 - a stale no-key dentry after the key is added is a recurring bug

How is a dentry that was looked up by no-key name marked, and what does `fscrypt_d_revalidate()`
return for it once the key is added? What must a filesystem do so that `fscrypt_d_revalidate()` is
called for its dentries? Start from `fscrypt_prepare_lookup()` and `fscrypt_d_revalidate()`.

## fscrypt.revalidation-off: Disabling revalidation

- section: Filenames and no-key dentries
- relevance: 5 - a change to a filesystem's dentry operations decides whether a no-key dentry is ever checked again

When does fs/crypto stop `fscrypt_d_revalidate()` from being called for a dentry, and what does it
test about the dentry's operations before it does? Start from `fscrypt_prepare_dentry()` and
`fscrypt_handle_d_move()`.

## fscrypt.nokey-create-usage: Creating under a no-key dentry

- section: Filenames and no-key dentries
- relevance: 5 - checking the directory's key is the fix that looks right and is not

What are the requirements for a filesystem method that creates a new filename in an encrypted
directory, when it is passed a no-key dentry, in order to assure safe usage? What does
`fscrypt_is_nokey_name()` test, and can its result differ from a test of whether the directory
inode has its key? Start from `fscrypt_is_nokey_name()`.

# Master keys and the keyring

## fscrypt.master-key: Master key object

- section: Master keys and the keyring
- relevance: 4 - key lifetime bugs come from misreading the states and counts

Where does a superblock keep the filesystem's master keys, what states can a `struct
fscrypt_master_key` be in, and which of its reference counts keeps what alive? Start from
`fs/crypto/fscrypt_private.h` and `fs/crypto/keyring.c`.

## fscrypt.add-key: Adding a key

- section: Master keys and the keyring
- relevance: 4 - the privilege and quota rules are security relevant

Who may add a key for each policy version with `FS_IOC_ADD_ENCRYPTION_KEY`, how
are several users who add the same key tracked and charged, and what kind of
keyring key can supply the key in place of the ioctl argument? Start from
`fscrypt_ioctl_add_key()`.

## fscrypt.key-removal: Removing a key

- section: Master keys and the keyring
- relevance: 4 - removal races with inodes still in use

When `do_remove_key()` removes a master key, what is wiped at once and what only when the last
file that uses the key goes? What do `do_remove_key()` and `fscrypt_drop_inode()` each do to the
inodes that were unlocked with the key, and what does user space learn when some of them stay
busy? Start from `do_remove_key()`.

## fscrypt.locks: Locks in fs/crypto

- section: Master keys and the keyring
- relevance: 4 - several fields are read without their lock on purpose

Which lock protects a master key's secret and state, which its list of users, and which the
setting up of a key shared by many files? Which members of `struct fscrypt_master_key` does the
code read without the lock that protects them, and by what means?

## fscrypt.drop-inode-context: Eviction check context

- section: Master keys and the keyring
- relevance: 4 - a lock added to this function sleeps in a context that cannot sleep

In what context does `fscrypt_drop_inode()` run, and which locks may it take there? What does its
return value guarantee when the master key is removed at the same time? Start from
`fscrypt_drop_inode()`.

## fscrypt.secret-handling-usage: Handling key material

- section: Master keys and the keyring
- relevance: 4 - a missed wipe is invisible in testing

What are the requirements for code in fs/crypto that holds key material, in order to assure that
no secret is left in memory once the key material is no longer needed? Under what condition does
fs/crypto not keep a raw master key at all? Start from `fs/crypto/keyring.c` and
`fscrypt_destroy_prepared_key()`.

# Policies

## fscrypt.policy-and-context: Policy and context

- section: Policies
- relevance: 4 - the two are easy to confuse and one of them is on disk

What is the difference between an encryption policy and an encryption context
and which of them is on disk, what value in the version field denotes each
version of each, and who generates the nonce? Start from
`union fscrypt_context` and `include/uapi/linux/fscrypt.h`.

## fscrypt.set-policy: Setting a policy

- section: Policies
- relevance: 4 - each failed condition has its own error code

What must hold for `FS_IOC_SET_ENCRYPTION_POLICY` to succeed on an inode, what
error does each failed condition give, and what extra check applies to a v2
policy? Start from `fscrypt_ioctl_set_policy()`.

## fscrypt.policy-enforcement: Same-policy rule

- section: Policies
- relevance: 5 - a filesystem that skips a call site loses the protection

What does `fscrypt_has_permitted_context()` enforce, and for which parent and child does it return
success without comparing policies? In which operations must a filesystem call it itself?

# Key derivation and IVs

## fscrypt.key-derivation: Contents key derivation

- section: Key derivation and IVs
- relevance: 4 - which key a file uses depends on the policy flags

Under a v2 policy, which key encrypts a file's contents by default and under each policy flag that
changes it? Where are the keys that many files share kept, and when are they destroyed? Start from
`fscrypt_setup_v2_file_key()`.

## fscrypt.v1-key-derivation: Version 1 file keys

- section: Key derivation and IVs
- relevance: 4 - a change to the v1 derivation makes existing v1 files unreadable

How is a file's key derived under a v1 policy, and which crypto interface does the derivation
call? Start from `fs/crypto/keysetup_v1.c`.

## fscrypt.iv-generation: IV generation

- section: Key derivation and IVs
- relevance: 4 - IV reuse is the failure this code exists to prevent

How does `fscrypt_generate_iv()` build the IV for a data unit of file contents by default and
under each policy flag that changes it? What do `fscrypt_mergeable_bio()` and
`fscrypt_limit_io_blocks()` require of I/O code because of that layout? Start from
`fscrypt_generate_iv()`.

## fscrypt.format-stability: Persistent formats

- section: Key derivation and IVs
- relevance: 5 - a change here makes existing files unreadable

Which of fscrypt's formats and derivations are persistent and must never change, and which
user-visible output does `Documentation/filesystems/fscrypt.rst` say may change? What does the
code do to catch an accidental change in a structure's size?

# Model gaps

## fscrypt.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
