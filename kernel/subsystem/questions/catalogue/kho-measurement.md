# Questions: KHO (Kexec Handover) (measurement set)

- guide: kho.md
- title: KHO (Kexec Handover) Subsystem

A wide set of questions about `kernel/liveupdate/`: the Kexec HandOver core
(tracking preserved memory, the root FDT and its subtrees, scratch regions, the
boot of the next kernel, loading the kexec image), the serialization blocks,
the Live Update Orchestrator built on top (the device node, sessions, file
handlers, file-lifecycle-bound objects, the reboot hook) and the memfd handler
that is its first user. It is used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written guide
it will replace is 727 words. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## kho.files: Source files

- section: Finding your way
- relevance: 4 - the code moved and gained an orchestrator no older reader has seen
- words: 120

Which files hold the Kexec HandOver core, its debugfs interface, the
serialization blocks, the parts of the Live Update Orchestrator, the public
headers, the headers that define what is passed between kernels, the
memfd handler, the in-kernel tests and the selftests? A table. Start from
`kernel/liveupdate/Makefile` and `include/linux/kho/abi/`.

## kho.docs: Documentation

- section: Finding your way
- relevance: 2 - most of it is kernel-doc pulled from the sources
- words: 60

Which files under `Documentation/` cover the Kexec HandOver concepts, its use
by an administrator, what is passed between kernels, the orchestrator, its
ioctl interface and memfd preservation, and which of them are mostly
kernel-doc pulled from source files?

## kho.config: Config options and boot parameters

- section: Finding your way
- relevance: 3 - decides whether any of the code runs
- words: 90

Which Kconfig symbols and which kernel command line parameters turn Kexec
HandOver and the Live Update Orchestrator on, and what is the default of each?
Which further Kconfig symbols add debug checks, debugfs and tests? Start from
`kernel/liveupdate/Kconfig`.

## kho.init-order: Boot sequence

- section: Finding your way
- relevance: 4 - decides from which initcall level a user can call what
- words: 100

In what order, and from where, do `kho_populate()`, `kho_memory_init_early()`,
`kho_memory_init()` and `kho_init()` run, and what does each do? From which
point in boot can a subsystem retrieve a subtree, restore memory, preserve
memory and add a subtree?

# Enabled state

## kho.enabled-state: Enabled and handover-boot checks

- section: Whether handover is active
- relevance: 4 - the two checks answer different questions
- words: 80

What do `kho_is_enabled()` and `is_kho_boot()` each report, from what point in
boot is each reliable, and can either change from true to false after it first
read true? Name the places that clear them.

## kho.disabled-usage: Calling the API when disabled

- section: Whether handover is active
- relevance: 5 - which calls are harmless and which crash is the first thing a new user gets wrong
- words: 110

With Kexec HandOver compiled in but not enabled at boot, what does each group
of calls do: preserving memory, adding or removing a subtree, retrieving a
subtree, restoring memory? Which of them, if any, is unsafe in that state, and
how do in-tree callers guard against it? Start from `kho_init()` and the
callers of `kho_add_subtree()`.

# Preserving memory

## kho.tracker-structure: Preserved memory tracker

- section: Tracking preserved memory
- relevance: 4 - the structure handed to the next kernel, and it has been replaced
- words: 100

Which data structure records the memory that has been preserved, how are a
block's address and its order encoded in it, how deep is it, and which memory
do its nodes come from before and after the slab allocator is up? Start from
`struct kho_radix_tree` and `kho_radix_add_key()`.

## kho.tracker-context: Locking and calling context

- section: Tracking preserved memory
- relevance: 4 - decides where a preserve call may be made from
- words: 60

Which lock protects the tracker of preserved memory, and may the preserve and
unpreserve calls be made from atomic context? Start from `kho_radix_add_key()`
and `kho_radix_del_key()`.

## kho.no-finalize: Finalize and abort

- section: Tracking preserved memory
- relevance: 5 - older kernels had an explicit step and a notifier chain
- words: 80

Between a preserve call and the kexec itself, is there any finalize or abort
step, notifier chain or debugfs control that a user of Kexec HandOver must take
part in? If this tree has none, say so, and say at what moment a preservation
or a subtree becomes part of what the next kernel will see.

## kho.preserve-folio: Folios

- section: Preserve and restore calls
- relevance: 5 - the main call pair
- words: 100

What does `kho_preserve_folio()` record, and what does `kho_restore_folio()` do
to the struct pages in the next kernel: reference counts, order, compound
state? What does it return when the address was never preserved or has already
been restored, and how does it tell? Start from `kho_restore_page()`.

## kho.preserve-pages: Page ranges

- section: Preserve and restore calls
- relevance: 4 - a range is not recorded as a range
- words: 100

How does `kho_preserve_pages()` record a range of pages, what limits how the
range is split, and what does it undo when it fails part of the way through?
How does `kho_restore_pages()` leave the pages, compared with restoring a
folio?

## kho.restore-pairing: Matching restore to preserve

- section: Preserve and restore calls
- relevance: 5 - nothing checks the pairing
- words: 90

What usage of a restore call on memory that was preserved with a different
preserve call is unsafe, and what that looks similar is correct? Does anything
detect a mismatch? Name in-tree code that pairs them correctly.

## kho.unpreserve-rules: Unpreserving

- section: Preserve and restore calls
- relevance: 4 - the arguments must reproduce the original call
- words: 90

What must the arguments of `kho_unpreserve_folio()` and
`kho_unpreserve_pages()` match, what happens when they name memory that was
never preserved or only part of a preserved range, and does either call free
the memory?

## kho.vmalloc: vmalloc areas

- section: Preserve and restore calls
- relevance: 3 - one user so far, several restrictions
- words: 100

Which vmalloc areas can `kho_preserve_vmalloc()` preserve and what does it
return for the others, what does the descriptor it fills in contain and where
must the caller keep it, and what does `kho_restore_vmalloc()` return on
failure? Start from `struct kho_vmalloc`.

## kho.alloc-preserve: Allocate and preserve

- section: Preserve and restore calls
- relevance: 4 - the helper most new code uses
- words: 80

What does `kho_alloc_preserve()` allocate, what are its size limits, and how
does it report failure? Which call undoes it in the same kernel and which one
releases the memory in the next kernel, and what does each take?

## kho.error-unwind: Unwinding a failed setup

- section: Preserve and restore calls
- relevance: 3 - each step has its own undo and none is implied by another
- words: 80

When a user has preserved data, preserved the blob describing it and added the
blob as a subtree, and a later step fails, what has to be undone and in what
order? Which undo is unsafe to leave out, and which in-tree code shows the full
sequence?

# The root FDT and subtrees

## kho.root-fdt: Root FDT

- section: What is handed over
- relevance: 4 - the layout is the contract between two kernels
- words: 100

What does the root FDT that Kexec HandOver passes to the next kernel contain:
the value of its compatible string, the property that locates the preserved
memory map, and the node and properties recorded for each subtree? How large
can it grow? Start from `kho_out_fdt_setup()` and
`include/linux/kho/abi/kexec_handover.h`, and give values from the definitions,
not from the comments around them.

## kho.subtree-add: Adding a subtree

- section: What is handed over
- relevance: 5 - the signature and the contract have both changed
- words: 100

What are the parameters of `kho_add_subtree()`, must the blob be an FDT, who is
responsible for preserving the blob's memory, and which errors does it return
for a duplicate name and for a full root FDT? Does it take a copy of anything?

## kho.subtree-remove: Removing a subtree

- section: What is handed over
- relevance: 3 - it undoes less than its name suggests
- words: 60

How does `kho_remove_subtree()` find the node to remove, what does it return,
and what does it leave for the caller to undo?

## kho.subtree-retrieve: Retrieving a subtree

- section: What is handed over
- relevance: 5 - the first call every consumer makes
- words: 100

What are the parameters of `kho_retrieve_subtree()`, what does it hand back and
what must the caller do before using it, and what does it return when this was
not a handover boot, when the name is absent and when the node is malformed?
Does the blob's memory need a restore call? Name two in-tree callers.

## kho.fdt-endianness: Property byte order

- section: What is handed over
- relevance: 4 - looks like a bug to anyone who knows FDT
- words: 70

In which byte order are the property values of the root FDT and of the in-tree
sub-FDTs written and read, and does that follow the devicetree specification?
Start from `kho_add_subtree()`, `kho_retrieve_subtree()` and `prepare_kho_fdt()`
in `mm/memblock.c`.

## kho.abi-versioning: Versioning what is handed over

- section: What is handed over
- relevance: 4 - a layout change without a version bump corrupts the next kernel silently
- words: 110

Which structures and strings form the contract between the kernel that
preserves and the kernel that restores, where are they defined, and what must a
patch that changes one of them also change? List the compatible strings and
version numbers this tree defines with their current values. Start from
`include/linux/kho/abi/`.

## kho.kexec-metadata: Kexec metadata

- section: What is handed over
- relevance: 2 - small, and a worked example of a non-FDT subtree
- words: 60

What is the kexec metadata subtree: what does it record, in what format, who
writes and who reads it, and what happens when its version is not the one
expected? Start from `struct kho_kexec_metadata`.

## kho.debugfs: debugfs files

- section: What is handed over
- relevance: 2 - read-only now, which the Kconfig help does not say
- words: 70

Which files and directories does Kexec HandOver create in debugfs, are any of
them writable, and does a failure to create them stop handover from working?
Start from `kernel/liveupdate/kexec_handover_debugfs.c`.

# Scratch and the next kernel's boot

## kho.scratch-what: Scratch regions

- section: Scratch regions
- relevance: 4 - the reason handover can boot at all
- words: 110

What are the scratch regions for, how many are there, how are they sized by
default and from the command line, how are they aligned, and what are they used
for while the first kernel runs? Start from `kho_reserve_scratch()`.

## kho.scratch-overlap: Preserving memory inside scratch

- section: Scratch regions
- relevance: 4 - the check is not always compiled in
- words: 90

What stops preserved memory from lying inside a scratch region: do the preserve
calls check for it, in every configuration, and what do they return when they
find it? What keeps such memory out of scratch when nothing checks, and which
allocations does a user have to watch? Start from `kho_scratch_overlap()`.

## kho.incoming-memblock: Early allocations after handover

- section: Scratch regions
- relevance: 3 - explains ordering constraints in arch and EFI code
- words: 100

On a handover boot, where may memblock allocate from before the page allocator
is up, how is that area widened beyond the regions the previous kernel set
aside, and when is the restriction lifted? Start from
`memblock_set_kho_scratch_only()` and `kho_extend_scratch()`.

## kho.incoming-pages: Preserved pages in the next kernel

- section: Scratch regions
- relevance: 4 - what a restore call relies on
- words: 90

How does the next kernel keep preserved pages out of the page allocator, what
does it write into their struct pages and where, and how does that interact
with deferred struct page initialisation? Start from
`kho_preserved_memory_reserve()`.

## kho.kexec-load: Loading the kexec image

- section: Scratch regions
- relevance: 3 - which system call and which image types take part
- words: 100

How does loading a kexec image change when Kexec HandOver is enabled: where
segments are placed, what extra data is added, how each architecture tells the
next kernel where it is, and what is skipped for a crash kernel? Does the
`kexec_load` system call take part? Start from `kho_fill_kimage()` and
`kho_locate_mem_hole()`.

# Serialization blocks

## kho.blocks: Block sets

- section: Serialization blocks
- relevance: 3 - new shared infrastructure for anything that hands over an array
- words: 110

What is a `struct kho_block_set`: how are entries laid out in memory, how does
it grow and shrink, what must the order of removals be, who does the locking,
and what sanity checks does restoring one in the next kernel make? Start from
`kernel/liveupdate/kho_block.c`.

# Live Update Orchestrator

## kho.luo-overview: Orchestrator overview

- section: Orchestrator core
- relevance: 4 - the layer most new users go through instead of calling the core
- words: 100

What is the Live Update Orchestrator, how does it depend on Kexec HandOver
being enabled, and under what name and in what form is its state handed to the
next kernel? Which initcalls set up the incoming and the outgoing state? Start
from `kernel/liveupdate/luo_core.c` and `struct luo_ser`.

## kho.luo-uapi: Userspace interface

- section: Orchestrator core
- relevance: 3 - user-visible ABI
- words: 100

Which device node does the orchestrator provide, how many openers may it have,
which ioctls work on the device and which on a session file descriptor, and
what is the convention for the size field and for extending an ioctl structure?
Start from `include/uapi/linux/liveupdate.h`.

## kho.luo-reboot: Reboot hook

- section: Orchestrator core
- relevance: 4 - the point of no return
- words: 90

Where does the kexec path call into the orchestrator, what runs in what order,
what happens when a step fails, and is it called for a kexec jump that
preserves context? What state are the session locks left in on success? Start
from `liveupdate_reboot()`.

## kho.luo-session: Sessions

- section: Sessions
- relevance: 4 - the unit userspace works with
- words: 100

What is a session, how is it created before the update and found again after
it, and what does closing its file descriptor do in each of those two cases?
What limits a session name, and may a session be retrieved twice?

## kho.luo-locking: Session locking

- section: Sessions
- relevance: 3 - three levels with a fixed order
- words: 70

Which locks does the session code use, in what order are they taken, and which
paths take the outermost one for read and which for write? Start from the
comment at the top of `kernel/liveupdate/luo_session.c`.

## kho.deserialize-failure: Bad incoming state

- section: Sessions
- relevance: 3 - one path panics and the other returns an error for ever
- words: 90

What happens when the orchestrator's incoming state is incompatible or corrupt:
at early boot, and later when sessions and files are rebuilt? When is that
rebuilding triggered, what is cleaned up after a partial failure, and what does
userspace see? Start from `luo_early_startup()` and
`luo_session_deserialize()`.

# File handlers

## kho.file-ops: Handler callbacks

- section: Preserving files
- relevance: 5 - what a subsystem implements to take part
- words: 120

Give a table of the callbacks in `struct liveupdate_file_ops`: which are
required, in which kernel and at which stage each is called, and what each must
do or undo.

## kho.file-args: Callback arguments

- section: Preserving files
- relevance: 4 - two handles with different lifetimes
- words: 90

In `struct liveupdate_file_op_args`, which fields does the core fill in and
which does the handler set, for each callback? What is the difference between
the two data fields, and what do the values of the retrieve status mean?

## kho.file-handler-register: Registering a handler

- section: Preserving files
- relevance: 3 - the return value when live update is off is easy to mishandle
- words: 80

What does `liveupdate_register_file_handler()` check and which errors does it
return, including when live update is not enabled, and how does an in-tree
caller treat that case? How is the handler's module kept loaded while files are
preserved?

## kho.file-identity: One file, one preservation

- section: Preserving files
- relevance: 3 - the identity is not always the struct file
- words: 70

How does the orchestrator stop the same file from being preserved twice, in the
same or in another session, what identifies a file for that purpose, and how
can a handler change it?

## kho.file-retrieve-finish: Retrieve and finish

- section: Preserving files
- relevance: 4 - reference ownership and retry rules
- words: 110

What happens when a file is retrieved a second time and when a retrieve fails
and is tried again? Who holds references on the retrieved file, what does
finishing a session do for files that were never retrieved, and what can stop a
finish?

## kho.freeze-rollback: Freeze and its rollback

- section: Preserving files
- relevance: 3 - partial failure during reboot has to leave a working system
- words: 80

During the reboot call, in what order are files frozen and serialized, and when
one freeze fails what is rolled back, for the failing session and for sessions
already done?

# File-lifecycle-bound objects

## kho.flb: Shared objects bound to files

- section: Shared objects
- relevance: 3 - how global state rides along with the files that need it
- words: 110

What is a `struct liveupdate_flb`, how is it tied to a file handler, when does
each of its callbacks run, and how many can be registered? How is its state
handed to the next kernel?

## kho.flb-accessors: Reaching the shared object

- section: Shared objects
- relevance: 3 - the get calls take a count that must be put
- words: 80

What do `liveupdate_flb_get_incoming()` and `liveupdate_flb_get_outgoing()`
return and when do they fail, what must the caller do afterwards, and what
usage of them is unsafe where something similar is correct?

# memfd

## kho.memfd: memfd preservation

- section: memfd handler
- relevance: 3 - the only in-tree file handler, and the model for the next
- words: 110

Which memfds can be preserved and which are refused, which properties survive
and which are reset, and what is done to the file's folios at preserve time?
What is the handler's compatible string? Start from `mm/memfd_luo.c`.

## kho.memfd-frozen: A memfd between preserve and reboot

- section: memfd handler
- relevance: 3 - userspace keeps running after preserve
- words: 60

After a memfd has been preserved and before the reboot, what may userspace
still do to it and what is blocked, and what is refreshed at freeze time?

# Changing the implementation

## kho.tests: Tests

- section: What a change must preserve
- relevance: 3 - the tests need two boots
- words: 90

Which in-kernel test code and which selftests exercise Kexec HandOver and the
orchestrator, which config options build them, and how is a test that spans a
kexec run? Are there stub headers elsewhere under `tools/` that a change to the
public header must keep building?

## kho.change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - a change is tested against a kernel that does not have it
- words: 100

What must a change to the Kexec HandOver core or the orchestrator keep working
besides the code it touches: handover between kernels with and without the
change, the builds with the feature configured out, deferred struct page
initialisation, both architectures, the documentation that is generated from
the sources?
