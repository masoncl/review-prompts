# Questions: Sysfs and Kernfs (measurement set)

- guide: sysfs.md
- title: Sysfs and Kernfs

A wide set of questions about sysfs, the kernfs layer under it and the
attribute and group interfaces the driver core builds on them, used to measure
what a model already knows before deciding what the built guide should spend
its words on. The hand-written guide it will replace is 698 words. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## sysfs.core-files: Core files

- section: Finding your way
- relevance: 4 - the subject is spread over five directories
- words: 100

Which files hold the sysfs directory, file, group, symlink and mount code, the
kernfs layer under them, the public and internal headers of both, the kobject
core that creates and removes the directories, and the driver-core glue that
turns device attributes into sysfs files? A table. Start from `fs/sysfs/`,
`fs/kernfs/` and `lib/kobject.c`.

## sysfs.docs: Documentation and samples

- section: Finding your way
- relevance: 3 - several rules live only there
- words: 70

Which files under `Documentation/` are the authority on writing sysfs
attributes, on kobjects and their lifetime, on the rules user space must follow
when reading sysfs, and on documenting a new attribute, and which sample code
and selftests exercise kobjects, sysfs or kernfs?

## sysfs.layering: Sysfs on top of kernfs

- section: Finding your way
- relevance: 4 - every callback reaches the kobject through the node
- words: 90

How does sysfs represent a kobject's directory, an attribute, a binary
attribute and a symlink as kernfs nodes: what does each node's private pointer
hold, how does a file's callback find the kobject it belongs to, and which
tables of kernfs operations does sysfs choose between when it creates a file?
Start from `sysfs_add_file_mode_ns()` and `sysfs_file_kobj()`.

# What this tree calls things

## sysfs.attribute-group-fields: Attribute group fields

- section: Structures and macros
- relevance: 5 - the structure is declared in every driver and its members have changed
- words: 100

List the members of `struct attribute_group` in this tree, with the exact
type of each callback and array, and say which members are alternatives to one
another and how the structure decides whether alternatives share storage.
Start from `include/linux/sysfs.h`.

## sysfs.attr-handler-types: Show and store handler types

- section: Structures and macros
- relevance: 4 - a patch that changes a handler's signature has to match one of these
- words: 90

What are the members of `struct device_attribute` and `struct kobj_attribute`
in this tree, which show and store signatures does each accept, and how do the
dispatch functions in `struct sysfs_ops` for devices and for plain kobjects
choose among them and what do they return when no handler is set? Start from
`dev_attr_show()` and `kobj_attr_show()`.

## sysfs.definition-macros: Attribute definition macros

- section: Structures and macros
- relevance: 3 - reviewers ask for the macro instead of an open-coded initialiser
- words: 110

Which macros does this tree provide for defining a plain attribute, a device
attribute, a binary attribute and an array of groups, including the variants
for root-only permissions, for a file name that differs from the variable name
and for a binary attribute backed by a buffer in memory? A table of macro,
mode and what it expands to. Start from `__ATTR()`, `DEVICE_ATTR_RW()`,
`BIN_ATTR()` and `ATTRIBUTE_GROUPS()`.

## sysfs.bin-attribute: Binary attributes

- section: Structures and macros
- relevance: 4 - the callbacks take different arguments from text attributes
- words: 100

What are the members of `struct bin_attribute` and the signatures of its
callbacks in this tree, how does the file's size bound reads and writes, what
does a read or write return when the matching callback is missing, and what
may differ per kobject when the attribute is created through a group? Start
from `sysfs_kf_bin_read()` and `sysfs_add_bin_file_mode_ns()`.

## sysfs.ns-tags: Namespace tags

- section: Structures and macros
- relevance: 3 - the type of the tag is in every _ns prototype
- words: 70

What type is the namespace tag that the sysfs and kernfs functions whose names
end in _ns take in this tree, which `struct kobj_type` callbacks supply it for a
kobject and its children, which namespace types are defined, and how does a
mounted sysfs decide which tagged entries to show? Start from
`sysfs_create_dir_ns()` and `include/linux/kobject_ns.h`.

## sysfs.kernfs-node-fields: Kernfs node fields and flags

- section: Kernfs
- relevance: 3 - direct access to the parent or the name is no longer allowed
- words: 100

Which fields does `struct kernfs_node` have for its parent, its name, its
reference counts and its flags in this tree, how must code outside kernfs and
inside it read the parent and the name, and what does each flag in
`enum kernfs_node_flag` mean? Start from `include/linux/kernfs.h` and
`fs/kernfs/kernfs-internal.h`.

## sysfs.kernfs-locks: Kernfs locks

- section: Kernfs
- relevance: 4 - which lock covers what has changed more than once
- words: 120

List the locks kernfs uses in this tree and what each protects: the tree of
nodes, inode attributes, the list of superblocks, renames, the per-node list of
open files, a single open file, the notification list and the id allocator.
Say which are per root, which are global or hashed, and the order in which
removal takes them. Start from `struct kernfs_root` and `kernfs_remove()`.

## sysfs.kernfs-users: Other kernfs users

- section: Kernfs
- relevance: 3 - a kernfs change has to keep all of them working
- words: 60

Besides sysfs, which subsystems in this tree create a kernfs root, and which
root flags does each pass compared with sysfs? Start from the callers of
`kernfs_create_root()`.

# Facts that are easy to get wrong

## sysfs.visibility-semantics: Visibility callback results

- section: Groups
- relevance: 5 - decides whether a file exists at all
- words: 100

What does the return value of a group's visibility callback do when the group
is created: what does zero mean, what does a non-zero value replace, which
bits are accepted and what happens to the others, what index is passed, and
when is the callback evaluated again after creation? Start from
`create_files()` in `fs/sysfs/group.c`.

## sysfs.group-invisible: Hiding a named group

- section: Groups
- relevance: 4 - an empty directory is user-visible ABI
- words: 90

Can a named group's directory be left out altogether, and if so which return
value asks for it, which attribute's callback is consulted when the group has
both text and binary attributes, and which helper macros build such a
callback? Start from `__first_visible()` and `SYSFS_GROUP_VISIBLE()`.

## sysfs.update-group: Updating a group

- section: Groups
- relevance: 4 - the only way visibility changes after creation
- words: 100

What does `sysfs_update_group()` do to the files of a group whose visibility
or mode has changed, what does it do when a named group's directory did not
exist before or should no longer exist, may it be called before the kobject is
in sysfs, and what is left behind when it fails part of the way through?

## sysfs.change-owner: Changing ownership

- section: Groups
- relevance: 5 - a lookup of a file that was never created fails the whole operation
- words: 120

When a device's owner has to change, for example when a network device moves
to a namespace owned by another user, which sysfs functions change the owner
of its directory, groups, attributes and symlinks, which group sets of a device
are covered and which are not, and how do they treat an attribute or a named
group directory that a visibility callback left out? Are these functions
available to modules? Start from `device_change_owner()` and
`sysfs_group_change_owner()`.

## sysfs.merge-group: Merging into a group

- section: Groups
- relevance: 2 - a handful of callers, mainly power management
- words: 60

What do `sysfs_merge_group()` and `sysfs_add_file_to_group()` require of the
target group, which members of the group structure do they look at and which
do they ignore, and what do they return when the group's directory does not
exist?

## sysfs.show-buffer: The buffer given to show

- section: Reading and writing
- relevance: 5 - overruns here are memory corruption
- words: 110

What buffer does a text attribute's show callback receive: its size, whether
it is zeroed and its alignment? How many times is show called for one read(2),
and for a read at a non-zero offset? What does sysfs do when show returns a
count of a page or more, on the normal path and on the preallocated path?
Start from `sysfs_kf_seq_show()` and `sysfs_kf_read()`.

## sysfs.emit-helpers: Formatting helpers

- section: Reading and writing
- relevance: 4 - the helpers reject buffers that look valid
- words: 90

What do `sysfs_emit()` and `sysfs_emit_at()` require of the buffer and offset
they are given, and what do they do and return when the requirement is not
met? What usage of them is incorrect, for example with a pointer into the
middle of the buffer or in a binary attribute's read callback, and what that
looks similar is correct?

## sysfs.store-semantics: The buffer given to store

- section: Reading and writing
- relevance: 4 - parsing code relies on termination and length
- words: 100

What does a text attribute's store callback receive: is the buffer NUL
terminated, what is the longest write passed through in one call and what
happens to a longer one, does a zero-length write reach the callback, and what
happens when store returns less than the count it was given? Start from
`kernfs_fop_write_iter()` and `sysfs_kf_write()`.

## sysfs.mode-rules: Permission bits

- section: Reading and writing
- relevance: 4 - wrong bits are rejected in three different places
- words: 110

Which permission bits may a sysfs attribute have, and where is each rule
enforced: at compile time in the definition macros, when a group's files are
created, when `device_create_file()` is called, and at open(2)? What does
open(2) do for a file whose mode or callbacks do not allow the requested
access even if the caller is privileged? Start from
`VERIFY_OCTAL_PERMISSIONS()` and `kernfs_fop_open()`.

## sysfs.active-refs: Lifetime during show and store

- section: Removal and lifetime
- relevance: 5 - decides whether a callback can run after removal
- words: 120

What keeps a kobject and the data behind it valid while a show or store
callback runs: does opening a sysfs file take a reference on the kobject, what
does each read or write take instead, what does removing the file or the
directory wait for, and what does a file descriptor opened before removal get
on its next read or write? Start from `kernfs_get_active()` and
`kernfs_drain()`.

## sysfs.locks-in-callbacks: Locks in show and store

- section: Removal and lifetime
- relevance: 5 - a deadlock that no diff shows
- words: 100

What usage of a lock inside a show or store callback can deadlock against
removal of the attribute or of the device, and what that looks similar is
safe? How does lockdep model it, and which attribute field or macro switches
that modelling off? Name in-tree code that shows each. Start from
`kernfs_drain()` and `__ATTR_IGNORE_LOCKDEP()`.

## sysfs.self-removal: Removing from a callback

- section: Removal and lifetime
- relevance: 4 - "delete" and "remove" files exist on several buses
- words: 110

How can a store callback remove its own attribute, or the device the
attribute belongs to, without deadlocking: which helpers exist for it, what
does each do with the active reference and the kobject reference, what may the
callback still touch afterwards, and what happens when two writers race?
Start from `sysfs_remove_file_self()`, `sysfs_break_active_protection()` and
`device_remove_file_self()`.

## sysfs.removal-scope: Extent of a removal

- section: Removal and lifetime
- relevance: 4 - decides what an error path still has to undo
- words: 100

What does removing a kobject's sysfs directory take with it: its default
groups, files and groups added later by other code, symlinks inside it,
symlinks elsewhere that point at it, child kobjects' directories? What do
`sysfs_remove_group()` and `sysfs_remove_file()` do when the thing to remove
is not there? Start from `__kobject_del()`, `sysfs_remove_dir()` and
`kernfs_remove()`.

## sysfs.dynamic-attrs: Dynamically allocated attributes

- section: Removal and lifetime
- relevance: 3 - only lockdep builds notice
- words: 60

What must code do to a `struct attribute` or `struct bin_attribute` that is
not statically allocated before registering it, why, and what happens on a
kernel with lock debugging when it does not? Start from `sysfs_attr_init()`.

## sysfs.symlinks: Symlinks

- section: Links and notification
- relevance: 3 - the target is usually owned by someone else
- words: 90

What does `sysfs_create_link()` require of the two kobjects, what does it
return when the target has no sysfs directory or the name exists, how is a
target that is being removed at the same time handled, and how do
`sysfs_remove_link()` and `sysfs_delete_link()` differ? Start from
`sysfs_do_create_link_sd()` and `sysfs_symlink_target_lock`.

## sysfs.duplicate-names: Duplicate names

- section: Links and notification
- relevance: 3 - the stack dump is a common bug report
- words: 60

What happens when a directory, file, group or symlink is created with a name
that already exists under the same parent: the return value, what is logged,
and which creation functions skip the log? Start from `sysfs_warn_dup()`.

## sysfs.notify-poll: Notification and poll

- section: Links and notification
- relevance: 3 - context rules differ between the two entry points
- words: 90

How does the kernel tell user space that an attribute's value changed, what
does a poller see and have to do next, and from which contexts may
`sysfs_notify()`, `sysfs_notify_dirent()` and `kernfs_notify()` each be
called? Start from `kernfs_notify()` and `kernfs_generic_poll()`.

# Using it safely

## sysfs.driver-core-groups: Groups the driver core creates

- section: Driver core
- relevance: 5 - choosing the right pointer removes the need for any create call
- words: 130

Which attribute group pointers does the driver core create and remove on its
own for a device, a driver, a bus, a class and a plain kobject, from which
function is each created, and where does each fall relative to the "add"
uevent and to the driver's probe and remove callbacks? A table. Start from
`device_add_attrs()`, `bus_add_device()`, `really_probe()` and `create_dir()`
in `lib/kobject.c`.

## sysfs.uevent-race: Attributes created after the add event

- section: Driver core
- relevance: 5 - user space reads the file before it exists
- words: 90

What usage of `device_create_file()` or `sysfs_create_group()` races with user
space handling the "add" uevent, and what in-tree patterns create the same
files without the race? Which of them also remove the need for an explicit
removal call?

## sysfs.devm-groups: Managed group helpers

- section: Driver core
- relevance: 3 - one of the pair was removed and patches still use it
- words: 60

Which device-managed helpers for attribute groups does this tree export, which
commonly remembered ones are absent, and when does the managed removal run
relative to the driver's remove callback? Start from
`devm_device_add_group()`.

## sysfs.attr-needs-ktype: Operations table requirement

- section: Driver core
- relevance: 3 - a kobject without it cannot have files
- words: 60

What must a kobject's type provide before an attribute file can be created on
it, what happens when it is missing, and which ready-made operations tables
exist for `struct kobj_attribute` and `struct device_attribute`? Start from
`sysfs_add_file_mode_ns()` and `kobj_sysfs_ops`.

## sysfs.kobject-lifecycle: Kobject add and release

- section: Kobjects
- relevance: 5 - the commonest leak in sysfs code
- words: 120

What must a caller do when `kobject_init_and_add()` or `kobject_add()` fails,
and why is freeing the structure directly wrong? What is the difference
between `kobject_del()` and `kobject_put()`, what does the final put do if the
kobject is still in sysfs, and who drops the reference a child holds on its
parent? Start from `kobject_add_internal()` and `kobject_cleanup()`.

## sysfs.kobject-error-unwind: Unwinding partial setup

- section: Kobjects
- relevance: 4 - init-time loops that return early
- words: 110

In code that creates several kobjects and then groups on them, what is unsafe
on a failure half way, and what does a correct unwind look like? Say what
`kobject_create_and_add()` and `sysfs_create_group()` have already undone
themselves when they fail, and whether a group created on a kobject needs an
explicit removal before the final `kobject_put()`.

## sysfs.one-value-rule: Attribute content conventions

- section: Conventions
- relevance: 2 - widely known, but reviewers enforce it
- words: 60

What conventions does the sysfs documentation set for the content of an
attribute: how many values, which format, line termination, and what a store
callback should accept? Start from `Documentation/filesystems/sysfs.rst`.

## sysfs.abi-docs: Documenting a new attribute

- section: Conventions
- relevance: 4 - a new file without an ABI entry is sent back
- words: 100

Where must a new sysfs attribute be documented, what do the directories under
`Documentation/ABI/` mean, which fields does an entry have and which of them
are optional in this tree, and which script validates the entries? Start from
`Documentation/ABI/README`.

# Changing the implementation

## sysfs.group-walkers: Functions that walk a group

- section: What a change must preserve
- relevance: 4 - a new walker has to agree with the others about what exists
- words: 110

Which functions in `fs/sysfs/group.c` iterate over a group's attribute arrays,
and for each, does it consult the visibility callbacks, both variants of them,
with the right index, and handle the value that hides the whole group? What
would a new function that looks up each attribute of a group by name have to
do to agree with them?

## sysfs.removal-sequence: Kernfs removal sequence

- section: What a change must preserve
- relevance: 4 - the ordering is what makes removal safe
- words: 120

List in order what kernfs does to remove a node and its subtree: how new users
are shut out, what is waited for, what is done to memory mappings and to open
files with a release callback, which locks are dropped while waiting, and how
two concurrent removers of the same node are arbitrated. Start from
`__kernfs_remove()`, `kernfs_drain()` and `kernfs_drain_open_files()`.

## sysfs.config-off: Builds without sysfs

- section: What a change must preserve
- relevance: 2 - the stubs return success
- words: 60

What do the sysfs functions do when the kernel is built without
`CONFIG_SYSFS`, which of them return something a caller must not dereference
or rely on, and what does that mean for code that treats creating an attribute
as proof that it exists?
