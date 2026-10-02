# Questions: VFS

- guide: vfs.md
- title: VFS Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/vfs-measurement.md` is the wider
set the readers were measured on and `catalogue/vfs-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## vfs.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## vfs.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between files and headers

A table and nothing else, job to file: path lookup; the dentry cache; the inode cache;
superblocks; mounts and namespaces; opening and the file table; the descriptor table; attribute
changes; directory reading; the pseudo-filesystem library; the mount context API; and the header
that declares each of the superblock, the inode, the dentry and the open file. Start from
`fs/namei.c` and `include/linux/fs.h`.

## vfs.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: resolve a user path; open a
file; create, unlink and rename by name; look up one name under a directory from kernel code; find
or create an inode in the inode cache; drop the last reference to a file, to a dentry and to an
inode. Give each function by the name it has in this tree. Do not describe what the functions do
inside.

# Inodes

## vfs.inode-state-access: Inode state word

- section: Inodes
- relevance: 4 - direct access no longer compiles or no longer asserts

How is an inode's state word read and changed in this tree, and which lock do the accessors
expect? Which accessors may be called without that lock, and what does each require in its place?
Start from `struct inode` in `include/linux/fs.h`.

## vfs.inode-state-flags: Lifecycle state flags

- section: Inodes
- relevance: 4 - touching a dying inode is a use after free

What do the inode state flags for a new inode, an inode being created, and an
inode on its way to being freed each mean, who sets and clears each, and what
must code that finds an inode on a list or in the hash do when it sees them?
Start from the comment above the state flags in `include/linux/fs.h`.

## vfs.inode-cache-lookup: Finding or creating an inode

- section: Inodes
- relevance: 4 - every filesystem's lookup does this

In what state does `iget_locked()` or `iget5_locked()` return an inode that it had to create, and
what must the filesystem call once it has filled the inode in or failed to? What do other lookups
of the same inode do meanwhile? Start from `iget_locked()` and `iget5_locked()`.

## vfs.inode-refcount: Inode references

- section: Inodes
- relevance: 4 - the wrong helper on an unreferenced inode resurrects it

Which of the functions that take a reference on an inode require that the caller already holds
one, and which may be used on an inode found on a list or in the hash without one? What does each
of the second kind require of the inode's state and of the locks held? May `iput()` sleep? Start
from `iput()` and `igrab()`.

## vfs.inode-last-put: Last reference

- section: Inodes
- relevance: 3 - decides whether an inode is cached or evicted

What happens when the last reference to an inode is dropped: what does the
return value of the filesystem's drop method decide, what are the stock helpers
for it called in this tree, and when is the inode kept on the LRU instead of
evicted? Start from `iput_final()`.

## vfs.inode-eviction: Inode eviction

- section: Inodes
- relevance: 4 - a missing step leaks pages or trips an assertion

In what order do things happen when an inode is evicted, what is a
filesystem's eviction method required to do itself, and what is waited for
before and after it runs? Start from `evict()` in `fs/inode.c`.

## vfs.inode-free-rcu: Freeing an inode

- section: Inodes
- relevance: 4 - path walk reads inodes without a reference

Which superblock methods free an inode's memory, which of them runs after an
RCU grace period, and what may a lockless path walk still touch in an inode
whose last reference has gone?

## vfs.sb-inode-walk: Walking a superblock's inodes

- section: Inodes
- relevance: 4 - a recurring source of use after free and sleeping under a spinlock

What are the requirements for a loop over all the inodes of a superblock under `s_inode_list_lock`
in order to assure safe usage? What must the loop hold before it drops the lock to work on an
inode? Name an in-tree loop that shows it. Start from `evict_inodes()` and `s_inode_list_lock`.

# Dentries

## vfs.dentry-fields: Dentry links and their locks

- section: Dentries
- relevance: 4 - several fields were renamed or moved into a union

Which lock or sequence count protects each of the fields of `struct dentry` that link a dentry to
its siblings, its children and its inode's alias list, and each of `d_flags`, `d_name`, `d_parent`
and `d_inode`? Give each field by the name it has in this tree. Start from `struct dentry`.

## vfs.dentry-states: Dentry states

- section: Dentries
- relevance: 4 - a negative dentry has no inode to dereference

How are a negative, a positive, an unhashed, an in-lookup and a killed dentry
each represented, which helper tests each, and what is the difference between
the helpers that test the type bits and those that test the inode pointer?
Start from `d_is_negative()` and `d_really_is_negative()`.

## vfs.d-instantiate: Attaching an inode

- section: Dentries
- relevance: 5 - the wrong one crashes or leaves the name unfindable

A table comparing `d_instantiate()`, `d_instantiate_new()`, `d_add()` and `d_splice_alias()`: what
each requires of the dentry and of the inode, which of them hash the dentry, and who owns the
inode reference afterwards.

## vfs.lookup-return: Result of a directory lookup

- section: Dentries
- relevance: 4 - callers must use the returned dentry, not the one passed in

What may a filesystem's lookup method return, and what does each return require the caller to do
with the dentry it passed in? Which other directory methods return a dentry in this tree? Start
from `d_splice_alias()` and `__lookup_slow()`.

## vfs.d-move: Moving a dentry

- section: Dentries
- relevance: 4 - names and parents change under readers

Who calls the functions that move or exchange dentries on rename, the VFS or
the filesystem, which locks and sequence counts do they take, and what must a
reader that uses a dentry's name or parent without holding the parent's lock do
to get a stable value? Start from `d_move()`, `rename_lock` and
`take_dentry_name_snapshot()`.

## vfs.dentry-refcount: Dentry references

- section: Dentries
- relevance: 4 - a reference taken on a dead dentry is a use after free

What does dropping the last reference to a dentry do: when is the dentry kept and when killed?
What are the requirements for calling `dget()` on a dentry in order to assure safe usage, and what
takes a reference on a dentry that was found without holding one? Start from `dput()` and
`dget_parent()`.

# Path walking

## vfs.walk-modes: Walk modes

- section: Path walking
- relevance: 4 - what may be dereferenced depends on the mode

In each of the two modes of path walking, what keeps dentries, inodes and mounts alive, and so
what may be dereferenced? How does a walk in each mode detect a concurrent change, and how does it
report that it cannot continue in its mode? Start from `path_init()` and `lookup_fast()`.

## vfs.unlazy: Leaving RCU mode

- section: Path walking
- relevance: 4 - the references must be taken before RCU protection is dropped

Which functions switch a walk from the lockless mode to the reference-taking mode part way, and
what does each legitimize? What happens to the walk when that fails? Start from `try_to_unlazy()`.

## vfs.rcu-walk-methods: Filesystem methods in RCU mode

- section: Path walking
- relevance: 4 - a method that sleeps here is a bug lockdep may not see

How is a filesystem method told that it is being called during a lockless walk, what are the
requirements for what it does there, and what does it return to ask for a retry in the other mode?

# The inode lock and rename

## vfs.i-rwsem-scope: Inode lock by method

- section: The inode lock and rename
- relevance: 5 - what a method may assume about concurrency

A table by method of how the VFS holds an inode's `i_rwsem` when it calls the
method: exclusive, shared or not at all, and on which inode (the parent, the
child, both). Where the inode_operations table in
`Documentation/filesystems/locking.rst` and the code disagree, give the code.

## vfs.i-rwsem-classes: Lock subclasses

- section: The inode lock and rename
- relevance: 4 - the wrong subclass blinds lockdep

Which value of `enum inode_i_mutex_lock_class` is used for which object in which operation? What
are the requirements for the subclass passed to `inode_lock_nested()` in order to assure that
lockdep can check the lock order? Start from `enum inode_i_mutex_lock_class`.

## vfs.rename-locking: Rename locking

- section: The inode lock and rename
- relevance: 5 - the deadlock-avoidance scheme for the whole directory tree

Which locks does a rename take and in what order? Which functions implement it, and are they
available outside `fs/namei.c` in this tree? Start from `lock_rename()` and `vfs_rename()`.

## vfs.rename-helpers: Rename start helpers

- section: The inode lock and rename
- relevance: 4 - what stacking filesystems and file servers call

Which functions does code outside `fs/namei.c` call to take the locks and find the dentries for a
rename, and to release them? What do those functions check about the ancestry of the two dentries?
What does a caller fill in `struct renamedata` in this tree? Start from `vfs_rename()`.

## vfs.parent-lock-usage: Locking a parent by hand

- section: The inode lock and rename
- relevance: 4 - the wrong subclass hides deadlocks from lockdep

When code outside `fs/namei.c` locks a directory in order to create, remove or look up an entry in
it, what are the requirements for calling `inode_lock()` or `inode_lock_nested()` on the directory
in order to assure safe usage and a lock order that lockdep can check? Name in-tree code that
shows it.

# Looking up and changing directory entries

## vfs.single-name-lookup: Looking up one name

- section: Looking up and changing directory entries
- relevance: 5 - the family was renamed and the permission check moved

What does this tree call the functions that look up a single name under a directory from kernel
code? Which of them check permission, and which require the directory to be locked? Start from
`lookup_one()` and `include/linux/namei.h`.

## vfs.lookup-noperm-callers: Lookup without permission check

- section: Looking up and changing directory entries
- relevance: 5 - the wrong family skips the permission check or uses the wrong idmap

Which callers may use `lookup_noperm()` and its variants, and which must use `lookup_one()` and
its variants? What does `lookup_one()` take that lets it check permission? Start from
`lookup_one()` in `fs/namei.c`.

## vfs.kern-path-helpers: Kernel path helpers

- section: Looking up and changing directory entries
- relevance: 3 - renamed, and what they hold on return matters

Which helpers that resolve a path given as a kernel string return the last component with its
parent locked, ready for creation or removal? What does each return and hold, and what releases
it? Start from `kern_path()` and `include/linux/namei.h`.

## vfs.dirop-helpers: Create and remove start helpers

- section: Looking up and changing directory entries
- relevance: 5 - the way in-kernel callers lock a directory and find a name

How do `start_creating()`, `start_removing()` and their variants differ in what they require of
the caller? What does each return for a name that exists and for one that does not, and what ends
the bracket? Start from `include/linux/namei.h`.

## vfs.mkdir-return: Result of mkdir

- section: Looking up and changing directory entries
- relevance: 4 - using the old dentry after the call is a bug

What do the directory-creation inode method and `vfs_mkdir()` return in this
tree, what happens to the dentry the caller passed in and to the parent's lock
on failure, and what must the caller pass to the function that ends the
creation bracket?

## vfs.vfs-op-preconditions: Calling the vfs_ helpers

- section: Looking up and changing directory entries
- relevance: 4 - the helpers check some things and trust the caller for others

For `vfs_create()`, `vfs_mkdir()`, `vfs_unlink()`, `vfs_rmdir()`, `vfs_link()` and `vfs_rename()`:
what must the caller hold and have done before the call, and which checks does the helper make
itself? Start from `vfs_unlink()` and `vfs_rename()`.

## vfs.dentry-recheck-usage: Rechecking a dentry after locking

- section: Looking up and changing directory entries
- relevance: 5 - a stale dentry makes a directory operation hit the wrong object

Code holds a reference to a dentry and later locks the directory it believes is the dentry's
parent. What are the requirements for using the dentry under that lock in order to assure safe
usage, and which in-tree helper meets them for its caller? Name in-tree code that shows it.

# Files and descriptors

## vfs.file-refcount: File references

- section: Files and descriptors
- relevance: 4 - the count is not a plain atomic and files are recycled under RCU

How is an open file counted in this tree? Which function takes a reference when the caller already
has one and which when the file was found under RCU only, and what does the second guarantee about
the file it returns? Start from `get_file()` and `get_file_rcu()`.

## vfs.fd-lookup: Descriptor lookup

- section: Files and descriptors
- relevance: 4 - the structure and its accessors changed

What is a `struct fd` in this tree and how are the file and the emptiness test
read from it, when does `fdget()`, or its scope-based form, take a reference
and when does it only borrow one, and what may the caller not do while it holds
a borrowed one? Start from `include/linux/file.h`.

## vfs.fd-install: Installing a descriptor

- section: Files and descriptors
- relevance: 4 - an installed descriptor cannot be taken back

What are the requirements for code that runs after `fd_install()` has joined a file to a reserved
descriptor, and how is a failure before that call unwound? Which helpers in this tree combine
reserving the descriptor, creating the file and joining the two? Start from `fd_install()` and
`include/linux/file.h`.

## vfs.may-open: Open-time checks

- section: Files and descriptors
- relevance: 4 - a check made after the side effect is too late

Which function makes the permission and file type checks for an open, at what
point in the open sequence does it run relative to creating the file, to
truncating it and to calling the filesystem's open method, and what does it
check for each file type? Start from `do_open()`.

## vfs.f-op-setup: File operations pointer

- section: Files and descriptors
- relevance: 4 - a raw assignment skips the module reference

What is a file's operations pointer set to when the file is allocated, when it
is opened normally, and when it is opened as a path-only descriptor? What
happens if the inode has no operations or the module cannot be pinned, and what
are the rules for replacing the pointer in an open method? Start from
`do_dentry_open()` and `replace_fops()`.

## vfs.private-data: Private data

- section: Files and descriptors
- relevance: 3 - leaks and double frees live here

Who frees what a file's `private_data` points to and from which method, how
many times and when is that method called compared with the flush method, and
can either be called for a file whose open failed?

## vfs.fput-deferral: Final fput

- section: Files and descriptors
- relevance: 4 - release does not run where fput was called

Where does the work of the last `fput()` run for a user task, for a kernel thread and in interrupt
context? Which variants run it synchronously, and what does each require of its caller? What must
code that needs a file's release method to have finished do? Start from `__fput()`.

# Superblocks and write access

## vfs.sb-refcounts: Superblock references

- section: Superblocks and write access
- relevance: 4 - two counts with different meanings, one renamed

What are a superblock's two reference counts called in this tree, and what does each keep alive?
What happens when the active count reaches zero? Start from `deactivate_super()` and
`put_super()`.

## vfs.s-umount: The superblock lock

- section: Superblocks and write access
- relevance: 4 - a superblock found on a list may be half built or dying

What does a superblock's `s_umount` protect, which superblock methods are called
with it held exclusive, shared or not at all, and how does code that finds a
superblock on a list take it safely while the superblock may be still being set
up or already dying? Start from `super_lock()`.

## vfs.fs-context: Mount context API

- section: Superblocks and write access
- relevance: 4 - the older interface may be gone

What does a filesystem type supply in order to be mounted in this tree, and does `struct
file_system_type` have a mount method of its own? How is a remount delivered? Start from `struct
file_system_type` and `struct fs_context_operations`.

## vfs.write-access: Write access and freezing

- section: Superblocks and write access
- relevance: 4 - a modification outside the brackets races with remount and freeze

Which calls must bracket a modification of a filesystem, and which helper combines the ones for
the mount and for a freeze? In what order do they nest with `i_rwsem` and with `mmap_lock`? Start
from `mnt_want_write()` and `sb_start_write()`.

# Permission and attributes

## vfs.inode-permission-chain: Permission check chain

- section: Permission and attributes
- relevance: 4 - a new access path has to go through all of it

In what order does `inode_permission()` make its checks and which error can
each return, so what has a new access path skipped if it calls only the last of
them? Start from `sb_permission()` and `do_inode_permission()`.

## vfs.idmap: Idmapped mounts

- section: Permission and attributes
- relevance: 4 - the wrong idmap is a privilege bug

Which `struct mnt_idmap` does a caller pass to VFS helpers and inode methods, when there is a
mount and when there is none? What are the requirements for comparing or storing an inode's owner
as `vfsuid_t` and `vfsgid_t` in order to assure safe usage, and what do the VFS helpers refuse
when an id has no mapping? Start from `struct mnt_idmap` and `i_uid_into_vfsuid()`.

## vfs.setattr: Attribute changes

- section: Permission and attributes
- relevance: 4 - the only sanctioned way to change mode, owner, size and times

What must the caller of `notify_change()` hold, what does it check and adjust
before it calls the inode method, and which helpers must a filesystem's method
call to validate and to copy the attributes, and in which order?

# Changing the VFS

## vfs.api-change-checklist: Changing a method or helper

- section: Changing the VFS
- relevance: 4 - the VFS has users all over the tree

Which documents does the tree ask a patch to update when it changes the prototype, locking or
semantics of a VFS method or exported helper? Which kinds of in-kernel code outside the
filesystems call the VFS methods and helpers, so that the patch has to convert them too?

# Model gaps

## vfs.model-gaps: Other mistakes models make

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
