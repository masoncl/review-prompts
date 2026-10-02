# Questions: Sysfs and Kernfs

- guide: sysfs.md
- title: Sysfs and Kernfs

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/sysfs-measurement.md` is the
wider set the readers were measured on and `catalogue/sysfs-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## sysfs.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Attributes and their callbacks

## sysfs.const-alternatives: Const callback alternatives

- section: Attributes and their callbacks
- relevance: 5 - declared in every driver, and what a handler or a group may supply has changed

Where a reader expects one show, one store, one visibility callback and one attribute array,
what alternatives do a device attribute, a kobject attribute and an attribute group offer in
this tree, and how is it decided whether alternatives share storage? In what order do the
dispatch functions and the code that reads a group try them, and what is returned when none
is set? Start from `dev_attr_show()`, `kobj_attr_show()` and `struct attribute_group` in
`include/linux/sysfs.h`.

## sysfs.layering: Sysfs on top of kernfs

- section: Attributes and their callbacks
- relevance: 4 - every callback reaches the kobject through the node

How does a file's callback get from its kernfs node to the kobject and the attribute, what
decides which table of kernfs operations a text attribute's file gets and which a binary
attribute's, and what does that choice make open, read or write do for a file that has no
handler for it? Start from `sysfs_add_file_mode_ns()` and `sysfs_file_kobj()`.

## sysfs.bin-attribute: Binary attributes

- section: Attributes and their callbacks
- relevance: 4 - the callbacks take different arguments from text attributes

How does a binary attribute's size bound reads and writes, what does a read or write do when
the matching callback is missing, and what may differ per kobject when the attribute is
created through a group? Start from `sysfs_kf_bin_read()` and
`sysfs_add_bin_file_mode_ns()`.

## sysfs.mode-rules: Permission bits

- section: Attributes and their callbacks
- relevance: 4 - wrong bits are rejected in three different places

Which permission bits may a sysfs attribute have, and where is each rule enforced? What does
open(2) do for a file whose mode or callbacks do not allow the requested access even if the caller
is privileged? Start from `VERIFY_OCTAL_PERMISSIONS()` and `kernfs_fop_open()`.

## sysfs.show-buffer: The buffer given to show

- section: Attributes and their callbacks
- relevance: 5 - overruns here are memory corruption

What buffer does a text attribute's show callback receive: its size, whether it is zeroed and
its alignment? How many times is show called for one read(2), and for a read at a non-zero
offset? What does sysfs do when show returns a count of a page or more, on the normal path and
on the preallocated path? Start from `sysfs_kf_seq_show()` and `sysfs_kf_read()`.

## sysfs.store-semantics: The buffer given to store

- section: Attributes and their callbacks
- relevance: 4 - parsing code relies on termination and length

What does a text attribute's store callback receive: is the buffer NUL terminated, what is the
longest write passed through in one call and what happens to a longer one, does a zero-length
write reach the callback, and what happens when store returns less than the count it was
given? Start from `kernfs_fop_write_iter()` and `sysfs_kf_write()`.

## sysfs.abi-docs: Documenting a new attribute

- section: Attributes and their callbacks
- relevance: 4 - a new file without an ABI entry is sent back

Where must a new sysfs attribute be documented, and what do the directories under
`Documentation/ABI/` mean? What validates the entries? Start from `Documentation/ABI/README`.

## sysfs.abi-entry-fields: ABI entry fields

- section: Attributes and their callbacks
- relevance: 4 - a reviewer should ask only for the fields the tree requires

Which fields must an entry under `Documentation/ABI/` have, which may it leave out, and who
chooses the directory for a new entry? Start from `Documentation/ABI/README`.

# Groups

## sysfs.visibility-semantics: Visibility callback results

- section: Groups
- relevance: 5 - decides whether a file exists at all

What does the return value of a group's visibility callback do when the group is created:
what does zero mean, what does a non-zero value replace and which of its bits are kept? What
index is the callback passed, and when is it evaluated again after creation? Start from
`create_files()` in `fs/sysfs/group.c`.

## sysfs.group-invisible: Hiding a named group

- section: Groups
- relevance: 4 - an empty directory is user-visible ABI

Can a named group's directory be left out altogether, and if so which return value asks for
it, from which attribute's callback when the group has both text and binary attributes, and
which helper macros build such a callback and which member does each belong in? Start from
`__first_visible()` and `SYSFS_GROUP_VISIBLE()`.

## sysfs.update-group: Updating a group

- section: Groups
- relevance: 4 - the only way visibility changes after creation

What does `sysfs_update_group()` do to the files of a group whose visibility or mode has changed,
and to a named group's directory that did not exist before or should no longer exist? What is left
behind when it fails part of the way through?

## sysfs.update-group-early: Early group update

- section: Groups
- relevance: 4 - a caller that updates early has to handle the result

What does `sysfs_update_group()` do and return when it is called for a kobject that is not yet in
sysfs?

## sysfs.change-owner: Changing ownership

- section: Groups
- relevance: 5 - a lookup of a file that was never created fails the whole operation

When a device's owner has to change, for example when a network device moves to a namespace
owned by another user, which of the device's sets of groups does the walk cover and which not,
and how does it treat an attribute, and a named group's directory, that a visibility callback
left out? Which of the functions involved may a module call? Start from
`device_change_owner()` and `sysfs_group_change_owner()`.

## sysfs.group-walkers: Functions that walk a group

- section: Groups
- relevance: 4 - a new walker has to agree with the others about what exists

Which functions in `fs/sysfs/group.c` that walk a group's attribute arrays call the group's
visibility callbacks, and which call none? How does each treat the return value
`SYSFS_GROUP_INVISIBLE`? What are the requirements for a function that looks up each attribute of
a group by name, so that it skips what `create_files()` did not create?

# Removal and lifetime

## sysfs.active-refs: Lifetime during show and store

- section: Removal and lifetime
- relevance: 5 - decides whether a callback can run after removal

What keeps a kobject and the data behind it valid while a show or store callback runs: does
opening a sysfs file take a reference on the kobject, and what does each read or write take
instead? What does removing the file or the directory wait for, and what does a file
descriptor opened before removal get on its next read or write? Start from
`kernfs_get_active()` and `kernfs_drain()`.

## sysfs.removal-scope: Extent of a removal

- section: Removal and lifetime
- relevance: 4 - decides what an error path still has to undo

What does removing a kobject's sysfs directory take with it: its default groups, files and
groups added later by other code, symlinks inside it, symlinks elsewhere that point at it,
child kobjects' directories? What do `sysfs_remove_group()` and `sysfs_remove_file()` do when
the thing to remove is not there? Start from `__kobject_del()`, `sysfs_remove_dir()` and
`kernfs_remove()`.

## sysfs.locks-in-callbacks: Locks in show and store

- section: Removal and lifetime
- relevance: 5 - a deadlock that no diff shows

What are the requirements for a lock that a show or store callback takes, with respect to the code
that removes the attribute or the device, in order to assure safe usage? How does lockdep model
it, and which attribute field or macro switches that modelling off? Name in-tree code that shows
each. Start from `kernfs_drain()` and `__ATTR_IGNORE_LOCKDEP()`.

## sysfs.self-removal: Removing from a callback

- section: Removal and lifetime
- relevance: 4 - "delete" and "remove" files exist on several buses

How can a store callback remove its own attribute, or the device the attribute belongs to,
without deadlocking: what does each helper for it do with the active reference and the kobject
reference, what may the callback still touch afterwards, and what happens when two writers
race? Start from `sysfs_remove_file_self()`, `sysfs_break_active_protection()` and
`device_remove_file_self()`.

## sysfs.kernfs-locks: Kernfs locks

- section: Removal and lifetime
- relevance: 4 - which lock covers what has changed more than once

One table, job to the kernfs lock that covers it in this tree, with the lock's scope (per
root, global, or hashed per node): the tree of nodes, inode attributes, the list of
superblocks, renames, the per-node list of open files, a single open file, the notification
list and the id allocator. Then the order in which removal takes them. Start from
`struct kernfs_root` and `kernfs_remove()`.

## sysfs.removal-sequence: Kernfs removal sequence

- section: Removal and lifetime
- relevance: 4 - the ordering is what makes removal safe

In what order does `__kernfs_remove()` shut a node to new users and unlink it? What does
`kernfs_drain()` wait for, and which locks does it drop while it waits? How are two concurrent
removers of the same node arbitrated? Start from `__kernfs_remove()`, `kernfs_drain()` and
`kernfs_drain_open_files()`.

## sysfs.removal-open-files: Open files at removal

- section: Removal and lifetime
- relevance: 4 - removal has to deal with files that are still open or mapped

What does removal of a kernfs node do to the memory mappings of its open files, and to open files
that have a release callback? Start from `kernfs_drain_open_files()`.

# Kobjects and the driver core

## sysfs.driver-core-groups: Groups the driver core creates

- section: Kobjects and the driver core
- relevance: 5 - choosing the right pointer removes the need for any create call

One table of the attribute group pointers a driver, bus, class, device type or plain kobject
can fill in so that the core creates and removes the files itself: for each, the function that
creates it, where that falls relative to the "add" uevent and to the driver's probe, and where
its removal falls relative to the driver's remove callback. Start from `device_add_attrs()`,
`bus_add_device()`, `really_probe()` and `create_dir()` in `lib/kobject.c`.

## sysfs.uevent-race: Attributes and the add uevent

- section: Kobjects and the driver core
- relevance: 5 - user space reads the file before it exists

What are the requirements for a call to `device_create_file()` or `sysfs_create_group()`, relative
to the "add" uevent for the device, in order to assure safe usage? Which in-tree patterns create
the same files with no such call, and which of them also remove the need for an explicit removal
call?

## sysfs.kobject-lifecycle: Kobject add and release

- section: Kobjects and the driver core
- relevance: 5 - the commonest leak in sysfs code

What must a caller do when `kobject_init_and_add()` or `kobject_add()` fails, so that everything
the failed call allocated is freed? What does the final `kobject_put()` do if the kobject is still
in sysfs, and who drops the reference a child holds on its parent, and when? Start from
`kobject_add_internal()` and `kobject_cleanup()`.

## sysfs.kobject-error-unwind: Unwinding partial setup

- section: Kobjects and the driver core
- relevance: 4 - init-time loops that return early

What are the requirements for the error path of code that creates several kobjects and then groups
on them, when one creation fails part of the way, in order to assure safe usage? What have
`kobject_create_and_add()` and `sysfs_create_group()` already undone themselves when they fail?
Does a group created on a kobject need an explicit removal before the final `kobject_put()`?

## sysfs.ns-tags: Namespace tags

- section: Kobjects and the driver core
- relevance: 3 - the type of the tag is in every _ns prototype

What type is the namespace tag that the sysfs and kernfs functions whose names end in _ns
take, in each place it appears, and how are two tags compared? How does a mounted sysfs decide
which tagged entries to show? Start from `sysfs_create_dir_ns()` and
`include/linux/kobject_ns.h`.

# Model gaps

## sysfs.model-gaps: Other mistakes models make

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
