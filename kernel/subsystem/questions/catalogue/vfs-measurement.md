# Questions: VFS (measurement set)

- guide: vfs.md
- title: VFS Subsystem

A wide set of questions about the VFS core: inodes, dentries, path lookup,
directory operations, permission, open files, superblocks and mounts. It is used
to measure what a model already knows before deciding what the built guide
should spend its words on. The hand-written guide it will replace is 1,559
words. The page cache, writeback and file locking have their own subjects and
are left out. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## vfs.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between files and headers
- words: 120

Which files hold path lookup, the dentry cache, the inode cache, superblocks,
mounts and namespaces, opening and the file table, the descriptor table,
attribute changes, directory reading, the pseudo-filesystem library and the
mount context API, and which headers declare the structures for each? A table.
Start from `fs/namei.c` and `include/linux/fs.h`.

## vfs.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

For each job (resolve a user path, open a file, create, unlink and rename by
name, look up one name under a directory from kernel code, find or create an
inode in the inode cache, drop the last reference to a file, to a dentry and to
an inode), which function do you start reading from? A table.

## vfs.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the locking tables are the contract
- words: 70

Which files under `Documentation/filesystems/` are the authority on the locking
each filesystem method is called with, on directory locking order, on path
lookup, on the meaning of each method, and on interface changes a filesystem
must follow?

## vfs.debug-asserts: Debug assertions

- section: Finding your way
- relevance: 3 - they compile out
- words: 60

Which assertion macros are specific to the VFS, which configuration option
turns them on, what do they compile to without it, and what does that mean for
a condition with side effects or a check that must hold in production? Start
from `include/linux/vfsdebug.h`.

## vfs.object-relations: Objects and references

- section: Finding your way
- relevance: 3 - the map everything else hangs on
- words: 100

What do a superblock, an inode, a dentry, a mount and an open file each
represent, which of them holds a counted reference on which, and which pointers
between them are not counted?

# Inodes

## vfs.inode-state-access: Inode state word

- section: Inode life cycle
- relevance: 4 - direct access no longer compiles or no longer asserts
- words: 80

What type is an inode's state word in this tree, how is it read and how is it
modified, which lock do the accessors expect, and which variants exist for a
lockless read or for an inode nobody else can see yet? Start from `struct inode`
in `include/linux/fs.h`.

## vfs.inode-state-flags: Lifecycle state flags

- section: Inode life cycle
- relevance: 4 - touching a dying inode is a use after free
- words: 100

What do the inode state flags for a new inode, an inode being created, and an
inode on its way to being freed each mean, who sets and clears each, and what
must code that finds an inode on a list or in the hash do when it sees them?
Start from the comment above the state flags in `include/linux/fs.h`.

## vfs.inode-refcount: Inode references

- section: Inode life cycle
- relevance: 4 - the wrong helper on an unreferenced inode resurrects it
- words: 90

Which functions take and drop a reference on an inode, which of them require
that the caller already holds one and which can be used on an inode found
without a reference, how is the count read, and may the final put sleep? Start
from `iput()` and `igrab()`.

## vfs.inode-last-put: Last reference

- section: Inode life cycle
- relevance: 3 - decides whether an inode is cached or evicted
- words: 80

What happens when the last reference to an inode is dropped: what does the
return value of the filesystem's drop method decide, what are the stock helpers
for it called in this tree, and when is the inode kept on the LRU instead of
evicted? Start from `iput_final()`.

## vfs.inode-cache-lookup: Finding or creating an inode

- section: Inode life cycle
- relevance: 4 - every filesystem's lookup does this
- words: 100

Which functions find an inode in the inode cache or insert a new one, in what
state is a newly created inode returned, what must the filesystem call once it
has filled the inode in or failed to, and what do other lookups of the same
inode do meanwhile? Start from `iget_locked()` and `iget5_locked()`.

## vfs.inode-eviction: Eviction

- section: Inode life cycle
- relevance: 4 - a missing step leaks pages or trips an assertion
- words: 100

List in order what happens when an inode is evicted, what a filesystem's
eviction method is required to do itself, and what is waited for before and
after it runs. Start from `evict()` in `fs/inode.c`.

## vfs.inode-free-rcu: Freeing an inode

- section: Inode life cycle
- relevance: 4 - path walk reads inodes without a reference
- words: 80

Which superblock methods free an inode's memory, which of them runs after an
RCU grace period, and what may a lockless path walk still touch in an inode
whose last reference has gone?

## vfs.nlink-helpers: Link count

- section: Inode life cycle
- relevance: 3 - direct writes are not allowed
- words: 70

How may a filesystem change an inode's link count, which helpers exist, what do
they check or account when the count reaches or leaves zero, and how is an
inode with no links that may still be linked in later marked?

## vfs.timestamps: Timestamp fields

- section: Inode life cycle
- relevance: 2 - the fields were renamed and have accessors
- words: 70

How are an inode's access, modification and change times stored in this tree,
which accessors read and set them, and what is different for a filesystem with
multigrain timestamps?

## vfs.i-rwsem-scope: Scope of the inode lock

- section: Inode locking
- relevance: 5 - what a method may assume about concurrency
- words: 110

Which operations does the VFS call with an inode's `i_rwsem` held exclusive,
which with it held shared, and which with it not held? A table by method. Start
from the inode_operations table in `Documentation/filesystems/locking.rst`.

## vfs.i-rwsem-classes: Lock subclasses

- section: Inode locking
- relevance: 4 - the wrong subclass blinds lockdep
- words: 90

Give a table of the lockdep subclasses of `i_rwsem`: name, value, and which
object in which operation is locked with each. Start from
`enum inode_i_mutex_lock_class`.

# Dentries

## vfs.dentry-fields: Dentry layout

- section: Dentry structure and state
- relevance: 4 - several fields were renamed or moved into a union
- words: 120

Which fields link a dentry to its parent, its siblings and children, its
inode's alias list and the hash, what are they called in this tree, which
fields share storage in a union, and which lock or sequence count protects each
of `d_flags`, `d_name`, `d_parent` and `d_inode`? Start from `struct dentry`.

## vfs.dentry-states: Dentry states

- section: Dentry structure and state
- relevance: 4 - a negative dentry has no inode to dereference
- words: 100

How are a negative, a positive, an unhashed, an in-lookup and a killed dentry
each represented, which helper tests each, and what is the difference between
the helpers that test the type bits and those that test the inode pointer?
Start from `d_is_negative()` and `d_really_is_negative()`.

## vfs.dentry-refcount: Dentry references

- section: Dentry structure and state
- relevance: 4 - a reference taken on a dead dentry is a use after free
- words: 100

How is a dentry's reference count stored, and what does dropping the last
reference do: when is the dentry kept and when killed? What usage of taking a
reference is unsafe (on which dentries may `dget()` not be called), and what is
used instead when the dentry was found without holding a reference? Start from
`dput()` and `dget_parent()`.

## vfs.d-instantiate: Attaching an inode

- section: Dentry structure and state
- relevance: 5 - the wrong one crashes or leaves the name unfindable
- words: 130

Compare the functions that attach an inode to a dentry (`d_instantiate()`,
`d_instantiate_new()`, `d_add()`, `d_splice_alias()`): what state must the
dentry and inode be in, which assertions fire otherwise, which of them hash the
dentry, and who owns the inode reference afterwards? A table.

## vfs.lookup-return: Result of a directory lookup

- section: Dentry structure and state
- relevance: 4 - callers must use the returned dentry, not the one passed in
- words: 100

What may a filesystem's lookup method return and what does each return mean to
the caller, why may the dentry that ends up holding the inode be a different one
from the dentry passed in, and which other directory methods can return a
replacement dentry in this tree? Start from `d_splice_alias()` and
`__lookup_slow()`.

## vfs.parallel-lookup: In-lookup dentries

- section: Dentry structure and state
- relevance: 3 - the calling convention changed
- words: 100

How do two lookups of the same name in one directory avoid both calling the
filesystem: which function allocates the in-lookup dentry and what are its
arguments in this tree, which flag marks it, how do waiters wait and get woken,
and who must end the in-lookup state? Start from `d_alloc_parallel()`.

## vfs.unhashing: Dropping, deleting and invalidating

- section: Dentry changes
- relevance: 3 - three calls that sound alike
- words: 90

What is the difference between `d_drop()`, `d_delete()` and `d_invalidate()`:
what each does to the hash, to the inode and to any mounts or children below,
and when each is the right call?

## vfs.d-move: Moving a dentry

- section: Dentry changes
- relevance: 4 - names and parents change under readers
- words: 110

What does moving or exchanging dentries on rename change, which locks and
sequence counts does it take, who calls it (the VFS or the filesystem), and what
must a reader that uses a dentry's name or parent without holding the parent's
lock do to get a stable value? Start from `d_move()`, `rename_lock` and
`take_dentry_name_snapshot()`.

## vfs.dentry-recheck-usage: Rechecking a dentry after locking

- section: Dentry changes
- relevance: 5 - a stale dentry makes a directory operation hit the wrong object
- words: 110

Code holds a reference to a dentry and later locks what it believes is the
parent directory. What usage of that dentry is unsafe without further checks,
exactly which conditions have to be rechecked under the lock, and which in-tree
helper does the locking and rechecking together? Name code that gets it right.

## vfs.d-revalidate: Revalidation

- section: Dentry changes
- relevance: 3 - the prototype changed
- words: 90

What are the arguments of a dentry's revalidate method in this tree, when is it
called, what do its return values mean, and how does the weak variant differ?
Start from `d_revalidate()` in `fs/namei.c`.

## vfs.persistent-dentries: Pinned dentries

- section: Dentry changes
- relevance: 3 - how pseudo filesystems keep their tree changed
- words: 100

How does a filesystem whose tree lives only in the dentry cache keep its
dentries from being pruned in this tree, which functions set and clear that,
how is a subtree removed, and which helper does unmount use now for such
filesystems? Start from `enum dentry_flags` and `simple_recursive_removal()`.

## vfs.default-d-op: Default dentry operations

- section: Dentry changes
- relevance: 2 - a mandatory conversion for new filesystems
- words: 60

How does a filesystem set the dentry operations used for all its dentries, how
can one dentry get different ones, and which older ways of doing either are no
longer available? Start from the default dentry operations field of
`struct super_block`.

# Path lookup

## vfs.walk-modes: Walk modes

- section: Walking a path
- relevance: 4 - what may be dereferenced depends on the mode
- words: 110

What are the two modes of path walking, what does each hold to keep dentries,
inodes and mounts alive, what does the lockless mode sample to detect a
concurrent change, and how does it report that it cannot continue? Start from
`path_init()` and `lookup_fast()`.

## vfs.walk-retry: Retry sequence

- section: Walking a path
- relevance: 3 - which errors are internal and which reach the caller
- words: 70

In what sequence does a path lookup retry, which error triggers each retry and
which flag is added, and can the last mode fail because of a concurrent change?
Start from `filename_lookup()`.

## vfs.unlazy: Leaving RCU mode

- section: Walking a path
- relevance: 4 - the references must be taken before RCU protection is dropped
- words: 100

How does a walk switch from the lockless mode to the reference-taking mode part
way, which functions do it and what does each legitimize, what happens when that
fails, and can a walk switch back? Start from `try_to_unlazy()`.

## vfs.rcu-walk-methods: Filesystem methods in RCU mode

- section: Walking a path
- relevance: 4 - a method that sleeps here is a bug lockdep may not see
- words: 100

Which filesystem methods can be called during a lockless walk, how is each told
so, what must it not do, and what does it return to ask for a retry in the
other mode?

## vfs.lookup-flags: Lookup flags

- section: Walking a path
- relevance: 3 - the intent flags changed meaning
- words: 130

Give a table of the `LOOKUP_` flags in this tree in three groups: those that
steer the walk, those that tell the filesystem the intent for the last
component, and those that scope the walk. Say what the exclusive-create flag
means here. Start from `include/linux/namei.h`.

## vfs.symlinks: Following symbolic links

- section: Walking a path
- relevance: 3 - the method is called in both modes
- words: 120

How is a symbolic link followed during a walk: which inode method supplies the
body and with what arguments in each mode, where is the state for nested links
kept, what are the limits, how does a filesystem that keeps the body in memory
avoid the method call, and how does a magic link jump? Start from `pick_link()`.

## vfs.filename-struct: Path name objects

- section: Names and single lookups
- relevance: 3 - ownership of the name changed
- words: 100

How does a path name from user space become a `struct filename`, how is that
object reference counted, which scope-based helpers release it, and do the
functions in `fs/namei.c` that take one for lookup, unlink, rename and the like
consume the caller's reference?

## vfs.single-name-lookup: Looking up one name

- section: Names and single lookups
- relevance: 5 - the family was renamed and the permission check moved
- words: 130

Which functions look up a single name under a directory dentry from kernel
code, what arguments do they take in this tree, which of them check permission
and which do not, which need the directory locked, and which family is for a
filesystem acting on itself as opposed to code reaching a filesystem through a
mount? Start from `lookup_one()` and `include/linux/namei.h`.

## vfs.kern-path-helpers: Kernel path helpers

- section: Names and single lookups
- relevance: 3 - renamed, and what they hold on return matters
- words: 100

Which helpers resolve a path given as a kernel string, and which of them return
the last component with its parent locked ready for creation or removal? What
do those return and hold, and what releases it? Start from `kern_path()` and
`include/linux/namei.h`.

# Directory operations

## vfs.dirop-helpers: Create and remove brackets

- section: Creating, removing and renaming
- relevance: 5 - the way in-kernel callers lock a directory and find a name
- words: 140

Which helpers lock a directory and look up a name in preparation for creating
or removing an entry, what variants exist (killable, without a permission
check, starting from a dentry already in hand), what does each return for an
existing and for a missing name, and what ends the bracket? Start from
`include/linux/namei.h`.

## vfs.parent-lock-usage: Locking a parent by hand

- section: Creating, removing and renaming
- relevance: 4 - the wrong subclass hides deadlocks from lockdep
- words: 100

When code outside `fs/namei.c` locks a directory in order to create, remove or
look up an entry in it, what usage of the inode lock helpers is unsafe or hides
bugs from lockdep, and what that looks similar is correct? Name in-tree code on
both sides if there is any.

## vfs.rename-locking: Rename locking

- section: Creating, removing and renaming
- relevance: 5 - the deadlock-avoidance scheme for the whole directory tree
- words: 140

Which locks does a rename take and in what order: the per-filesystem lock, the
two parents and their subclasses, and the children? Which functions implement
it, and are they available outside `fs/namei.c` in this tree? Start from
`lock_rename()` and `vfs_rename()`.

## vfs.rename-helpers: Rename brackets

- section: Creating, removing and renaming
- relevance: 4 - what stacking filesystems and file servers call
- words: 120

What does a caller fill in `struct renamedata`, which helpers take the locks
and find the dentries for a rename, what do they check about the two dentries'
ancestry and what error does each failure give, and what releases everything?
Start from `struct renamedata` and `vfs_rename()`.

## vfs.vfs-op-preconditions: Calling the vfs_ helpers

- section: Creating, removing and renaming
- relevance: 4 - the helpers check some things and trust the caller for others
- words: 130

For `vfs_create()`, `vfs_mkdir()`, `vfs_unlink()`, `vfs_rmdir()`, `vfs_link()`
and `vfs_rename()`: what must the caller hold and have done first (locks, write
access, references), and which checks does the helper make itself? Start from
`vfs_unlink()` and `vfs_rename()`.

## vfs.mkdir-return: Result of mkdir

- section: Creating, removing and renaming
- relevance: 4 - using the old dentry after the call is a bug
- words: 80

What do the directory-creation inode method and `vfs_mkdir()` return in this
tree, what happens to the dentry the caller passed in and to the parent's lock
on failure, and what must the caller pass to the function that ends the
creation bracket?

## vfs.delegation-break: Breaking delegations

- section: Creating, removing and renaming
- relevance: 3 - the retry loop must drop the directory lock
- words: 90

How do the helpers that unlink, rename, link or change attributes deal with a
delegation on an inode or directory: what type carries the inode back to the
caller, what error is returned, and what must the caller do with its locks
before waiting and retrying? Start from `try_break_deleg()`.

## vfs.dead-dir: Removed directories

- section: Creating, removing and renaming
- relevance: 3 - operations race with rmdir
- words: 80

How is a directory marked once it has been removed, where is that set, which
operations test for it and what error do they give, and what is done about
mounts on a removed or replaced dentry? Start from `IS_DEADDIR()` and
`dont_mount()`.

# Permission and attributes

## vfs.inode-permission-chain: Permission check chain

- section: Permission
- relevance: 4 - a new access path has to go through all of it
- words: 90

List in order the checks `inode_permission()` makes and the error each can
return. Start from `sb_permission()` and `do_inode_permission()`.

## vfs.may-open: Open-time checks

- section: Permission
- relevance: 4 - a check made after the side effect is too late
- words: 100

Which function makes the permission and file type checks for an open, at what
point in the open sequence does it run relative to creating the file, to
truncating it and to calling the filesystem's open method, and what does it
check for each file type? Start from `do_open()`.

## vfs.idmap: Idmapped mounts

- section: Permission
- relevance: 4 - the wrong idmap is a privilege bug
- words: 110

Which idmap argument do VFS helpers and inode methods take, where does a caller
get the right one from, what is passed when there is no mount, which typed
wrappers carry mapped ids, and what is refused when an id has no mapping? Start
from `struct mnt_idmap` and `i_uid_into_vfsuid()`.

## vfs.setattr: Attribute changes

- section: Permission
- relevance: 4 - the only sanctioned way to change mode, owner, size and times
- words: 110

Through which function do attribute changes reach a filesystem, what must its
caller hold, what does it check and adjust before calling the inode method, and
which helpers does a filesystem's method call to validate and copy the
attributes? Start from `notify_change()`.

# Open files

## vfs.file-refcount: File references

- section: File objects
- relevance: 4 - the count is not a plain atomic and files are recycled under RCU
- words: 110

What type is an open file's reference count in this tree, which functions take
a reference when the caller already has one and when the file was found under
RCU only, why can the latter see a different file than it looked up, and how is
the count read? Start from `get_file()` and `get_file_rcu()`.

## vfs.fput-deferral: Final fput

- section: File objects
- relevance: 4 - release does not run where fput was called
- words: 120

Where does the work of the last `fput()` run for a user task, for a kernel
thread and in interrupt context, in what order does it call into the filesystem
and drop what the file holds, and which variants run it synchronously? What
follows for code that needs a release to have finished? Start from `__fput()`.

## vfs.f-op-setup: File operations pointer

- section: File objects
- relevance: 4 - a raw assignment skips the module reference
- words: 120

What is a file's operations pointer set to when the file is allocated, when it
is opened normally, and when it is opened as a path-only descriptor? What
happens if the inode has no operations or the module cannot be pinned, and what
are the rules for replacing the pointer in an open method? Start from
`do_dentry_open()` and `replace_fops()`.

## vfs.open-sequence: Open sequence

- section: File objects
- relevance: 3 - where a filesystem hooks in
- words: 110

List the functions an open passes through from the path walk to the
filesystem's open method, where a filesystem's atomic open method fits, and what
the mode bits that record that the file was opened and that it was created are
used for. Start from `path_openat()` and `finish_open()`.

## vfs.private-data: Private data

- section: File objects
- relevance: 3 - leaks and double frees live here
- words: 80

What is the lifetime of a file's `private_data`, who frees what it points to and
from which method, how many times and when is that method called compared with
the flush method, and is either called for a file whose open failed?

## vfs.fd-lookup: Descriptor lookup

- section: Descriptors and write access
- relevance: 4 - the structure and its accessors changed
- words: 120

How does kernel code turn a descriptor number into a file: what is `struct fd`
in this tree, how are the file and the emptiness test read from it, which
scope-based forms exist, when is a reference actually taken, and what may the
caller not do while holding a borrowed one? Start from `fdget()` and
`include/linux/file.h`.

## vfs.fd-install: Installing a descriptor

- section: Descriptors and write access
- relevance: 4 - an installed descriptor cannot be taken back
- words: 110

What is the order of operations for giving user space a new descriptor for a
new file, what may not happen after the file is installed, how are failures
before that unwound, and which helpers combine the steps in this tree? Start
from `fd_install()` and `include/linux/file.h`.

## vfs.write-access: Write access and freezing

- section: Descriptors and write access
- relevance: 4 - a modification outside the brackets races with remount and freeze
- words: 130

Which calls must bracket a modification of a filesystem: the one that takes
write access on the mount, the one that holds off a freeze at each level, and
the per-inode write count? Which helper combines the first two, and in what
order do they nest with `i_rwsem` and with `mmap_lock`? Start from
`mnt_want_write()` and `sb_start_write()`.

## vfs.readdir: Reading a directory

- section: Descriptors and write access
- relevance: 3 - the exclusive variant of the method is gone
- words: 90

Which function calls a filesystem's directory iteration method, which method is
that in this tree, what lock is held and in what mode, what is checked about
the directory first, and how does the method hand entries back and keep its
position? Start from `iterate_dir()`.

# Superblocks and mounts

## vfs.sb-refcounts: Superblock references

- section: Superblocks
- relevance: 4 - two counts with different meanings, one renamed
- words: 100

Which two counts does a superblock have in this tree, what is each field called
and what does each keep alive, which functions drop each, and what happens when
the active count reaches zero? Start from `deactivate_super()` and
`put_super()`.

## vfs.s-umount: The superblock lock

- section: Superblocks
- relevance: 4 - a superblock found on a list may be half built or dying
- words: 120

What does a superblock's `s_umount` protect, which superblock methods are called
with it held exclusive, shared or not at all, and how does code that finds a
superblock on a list take it safely while the superblock may be still being set
up or already dying? Start from `super_lock()`.

## vfs.sb-lifecycle: Superblock setup and teardown

- section: Superblocks
- relevance: 3 - the order of teardown is what filesystems rely on
- words: 140

List the steps from a mount request to a live superblock and from the last
unmount to the superblock being freed: which function allocates or finds it,
which flags mark it born, active and dying, and what does the generic shutdown
do in order? Start from `vfs_get_tree()`, `sget_fc()` and
`generic_shutdown_super()`.

## vfs.fs-context: Mount context API

- section: Superblocks
- relevance: 4 - the older interface may be gone
- words: 120

What does a filesystem type supply in order to be mounted in this tree, which
helpers build the superblock for block-device, device-less, single-instance and
keyed filesystems, how are options parsed and how is a remount delivered, and
do the older mount method and its helpers still exist? Start from
`struct file_system_type` and `struct fs_context_operations`.

## vfs.sb-inode-walk: Walking a superblock's inodes

- section: Superblocks
- relevance: 4 - a recurring source of use after free and sleeping under a spinlock
- words: 110

What is the safe pattern for walking all inodes of a superblock: which list and
lock, which inodes must be skipped, how is the current inode pinned while the
lock is dropped, and where must the previous inode's reference be dropped? Name
an in-tree loop that does it. Start from `evict_inodes()` and
`s_inode_list_lock`.

## vfs.mount-struct: Mounts

- section: Superblocks
- relevance: 3 - needed to read anything in the namespace code
- words: 120

How do `struct vfsmount` and `struct mount` relate, how is a mount reference
counted and how does a lockless walk take one safely, and which two locks
protect the mount tree and the mount hash, with which scope-based guards? Start
from `fs/mount.h` and `mntput()`.

## vfs.libfs-helpers: Library helpers

- section: Superblocks
- relevance: 3 - most new pseudo filesystems are built from these
- words: 120

Which helpers in `fs/libfs.c` does a simple in-memory filesystem use for lookup,
directory reading, create and remove brackets, filling a superblock from a
table, and for a filesystem that only exists to give inodes to anonymous files?
A table.

# Changing the implementation

## vfs.api-change-checklist: Changing a method or helper

- section: What a change must preserve
- relevance: 4 - the VFS has users all over the tree
- words: 110

What must a patch that changes the prototype, locking or semantics of a VFS
method or exported helper update besides the function itself: which documents,
which in-tree instances, and which in-kernel callers outside the filesystems
(stacking filesystems, file servers, caches)?

## vfs.tests: Tests

- section: What a change must preserve
- relevance: 2 - where to add a test
- words: 80

Where in the tree are tests that exercise VFS behaviour (path resolution flags,
the mount API, idmapped mounts, file descriptors), and which test suite outside
the tree do filesystem maintainers expect a change to have been run against?
