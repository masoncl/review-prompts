# Questions: KHO (Kexec Handover) Subsystem

- guide: kho.md
- title: KHO (Kexec Handover) Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/kho-measurement.md` is the wider
set the readers were measured on and `catalogue/kho-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## kho.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## kho.files: Source files

- section: Finding your way
- relevance: 4 - the code moved and gained an orchestrator no older reader has seen

A table and nothing else, job to file: the Kexec HandOver core; its debugfs interface; the
serialization blocks; the parts of the Live Update Orchestrator; the public headers; the headers
that define what is passed between kernels; the memfd handler; the in-kernel tests and the
selftests. Where a job has no file of its own in this tree, say in the row which file holds the
code. Start from `kernel/liveupdate/Makefile` and `include/linux/kho/abi/`.

# Enabling and boot

## kho.init-order: Boot sequence

- section: Enabling and boot
- relevance: 4 - decides from which initcall level a user can call what

In what order, and from which callers, do `kho_populate()`, `kho_memory_init_early()`,
`kho_memory_init()` and `kho_init()` run? After which of them may a subsystem first call each of
the preserve, restore and subtree functions that `include/linux/kexec_handover.h` declares?

## kho.no-finalize: Finalize and abort

- section: Enabling and boot
- relevance: 5 - older kernels had an explicit step and a notifier chain

Between a preserve call and the kexec itself, is there any finalize or abort step, notifier
chain or debugfs control that a user of Kexec HandOver must take part in? If this tree has
none, say so, and say at what moment a preservation or a subtree becomes part of what the next
kernel will see.

## kho.enabled-state: Enabled and handover-boot checks

- section: Enabling and boot
- relevance: 4 - the two checks answer different questions

What do `kho_is_enabled()` and `is_kho_boot()` each report, from what point in boot is each
reliable, and can either change from true to false after it first read true? If either can,
name the places that clear it.

## kho.disabled-usage: Calling the API when disabled

- section: Enabling and boot
- relevance: 5 - which calls are harmless and which crash is the first thing a new user gets wrong

With Kexec HandOver compiled in but not enabled at boot, what do the preserve, restore and subtree
functions that `include/linux/kexec_handover.h` declares each do or return? What are the
requirements for calling them in that state in order to assure safe usage, and how do in-tree
callers meet them? Start from `kho_init()` and the callers of `kho_add_subtree()`.

# Preserving and restoring memory

## kho.tracker: Preserved memory tracker

- section: Preserving and restoring memory
- relevance: 4 - the structure has been replaced, and it decides where a preserve call may be made from

How does one key of `struct kho_radix_tree` stand for a preserved block of a given order? Which
lock protects the tree, and what are the requirements for the context that calls
`kho_radix_add_key()` or `kho_radix_del_key()`, and so for the context of the preserve and
unpreserve calls? Start from `struct kho_radix_tree`, `kho_radix_add_key()` and
`kho_radix_del_key()`.

## kho.preserve-folio: Folio preserve and restore

- section: Preserving and restoring memory
- relevance: 5 - the main call pair

What does `kho_preserve_folio()` record, and in what state does `kho_restore_folio()` hand back
the folio in the next kernel? What does `kho_restore_folio()` do with an address that was never
preserved or was already restored? Start from `kho_restore_page()`.

## kho.preserve-pages: Page ranges

- section: Preserving and restoring memory
- relevance: 4 - a range is not recorded as a range

How does `kho_preserve_pages()` record a range of pages, and what does it undo when it fails part
of the way through? In what state does `kho_restore_pages()` hand back the pages, compared with
`kho_restore_folio()`?

## kho.alloc-preserve: Allocate and preserve

- section: Preserving and restoring memory
- relevance: 4 - the helper most new code uses

What sizes does `kho_alloc_preserve()` accept, and what does it return on failure? What are the
requirements for undoing it with `kho_unpreserve_free()` in the same kernel, and for releasing its
memory with `kho_restore_free()` in the next kernel, in order to assure safe usage?

## kho.unpreserve-rules: Unpreserve calls

- section: Preserving and restoring memory
- relevance: 4 - the arguments must reproduce the original call

What must the arguments of `kho_unpreserve_folio()` and `kho_unpreserve_pages()` match, what
happens when they name memory that was never preserved or only part of a preserved range, and
does either call free the memory?

## kho.incoming-pages: Incoming preserved pages

- section: Preserving and restoring memory
- relevance: 4 - what a restore call relies on

What may a restore call rely on about a preserved page in the next kernel: what kept it out of
the page allocator, what has been written into its struct page and by what, and is that valid
when struct page initialisation is deferred? Start from `kho_preserved_memory_reserve()`.

## kho.restore-pairing: Matching restore to preserve

- section: Preserving and restoring memory
- relevance: 5 - nothing checks the pairing

What are the requirements for pairing a restore function, such as `kho_restore_folio()` or
`kho_restore_pages()`, with the function that preserved the memory, in order to assure safe usage?
Does anything detect a mismatch? Name in-tree code that pairs them correctly.

## kho.error-unwind: Unwinding a failed setup

- section: Preserving and restoring memory
- relevance: 3 - each step has its own undo and none is implied by another

When a user has preserved data, preserved the blob describing it and added the blob with
`kho_add_subtree()`, and a later step fails, what are the requirements for undoing those steps,
their order included, in order to assure safe usage? Name in-tree code that shows the full
sequence.

# Subtrees, root FDT and ABI

## kho.subtree-add: Adding a subtree

- section: Subtrees, root FDT and ABI
- relevance: 5 - the signature and the contract have both changed

What are the requirements for the name and the blob passed to `kho_add_subtree()`, in order to
assure safe usage, and how long must each stay valid? Which errors can the call return, and for
what?

## kho.subtree-retrieve: Retrieving a subtree

- section: Subtrees, root FDT and ABI
- relevance: 5 - the first call every consumer makes

What does `kho_retrieve_subtree()` hand back, and what are the requirements for using the blob it
names, in order to assure safe usage? Which errors does the function return, and for what? Name
in-tree code that shows it.

## kho.handover-fdt: Root FDT

- section: Subtrees, root FDT and ABI
- relevance: 4 - the layout is the contract between two kernels, and its byte order looks like a bug

What does the root FDT that Kexec HandOver passes to the next kernel record for each subtree and
for the preserved memory map, and how large can it grow? In which byte order are its property
values, and those of the in-tree sub-FDTs, written and read? Start from `kho_out_fdt_setup()`,
`include/linux/kho/abi/kexec_handover.h` and `prepare_kho_fdt()` in `mm/memblock.c`, and give
names from the definitions, not from the comments around them.

## kho.abi-versioning: ABI versions and compatible strings

- section: Subtrees, root FDT and ABI
- relevance: 4 - a layout change without a version bump corrupts the next kernel silently

What are the requirements for a patch that changes a definition under `include/linux/kho/abi/`,
and which macro must it change together with each definition? Where a comment and a definition
give different values for a compatible string or a version number, name the macro and give the
value from the definition. Start from `include/linux/kho/abi/`.

## kho.change-checklist: Changing the core

- section: Subtrees, root FDT and ABI
- relevance: 4 - a change is tested against a kernel that does not have it

What does a change to the Kexec HandOver core or the Live Update Orchestrator have to keep
building and working that a handover between two copies of the changed kernel does not exercise?
For each, say where the thing to check lives.

# Scratch regions

## kho.scratch-what: Count, size and pageblock type

- section: Scratch regions
- relevance: 4 - the reason handover can boot at all

How many scratch regions does `kho_reserve_scratch()` reserve, and what decides their number and
their default size? Which migrate type do their pageblocks get, and what may therefore be
allocated from them while the first kernel runs? Start from `kho_reserve_scratch()`.

## kho.scratch-overlap: Preserving memory inside scratch

- section: Scratch regions
- relevance: 4 - the check is not always compiled in

What are the requirements for where memory passed to a preserve call lies relative to the scratch
regions, in order to assure safe usage? When do the preserve calls check this with
`kho_scratch_overlap()`, and what do they return when it finds an overlap? Start from
`kho_scratch_overlap()`.

# Live Update Orchestrator

## kho.luo-overview: Orchestrator overview

- section: Live Update Orchestrator
- relevance: 4 - the layer most new users go through instead of calling the core

How does the Live Update Orchestrator depend on Kexec HandOver being enabled? How is its state
handed to the next kernel, and from where in boot are the incoming and the outgoing state set up?
Start from `kernel/liveupdate/luo_core.c` and `struct luo_ser`.

## kho.luo-session: LUO sessions

- section: Live Update Orchestrator
- relevance: 4 - the unit userspace works with

What do `luo_session_create()` and `luo_session_retrieve()` require of a session name, and what
does a second retrieve of the same session return? What does closing the file descriptor of a
session do before the update and after it? Start from `luo_session_release()`.

## kho.luo-reboot: Reboot hook

- section: Live Update Orchestrator
- relevance: 4 - the point of no return

Under what conditions does the kexec path call `liveupdate_reboot()`? What does
`liveupdate_reboot()` undo when one of its steps fails, and in what state does it leave the locks
it took when it succeeds? Start from `liveupdate_reboot()`.

## kho.file-ops: File handler callbacks

- section: Live Update Orchestrator
- relevance: 5 - what a subsystem implements to take part

For a subsystem that implements a file handler, one table of callback to duty for
`struct liveupdate_file_ops`: which callbacks it cannot leave out, in which kernel and at which
stage each is called, and what each must do or undo of what another did.

## kho.file-args: Callback arguments

- section: Live Update Orchestrator
- relevance: 4 - two handles with different lifetimes

In `struct liveupdate_file_op_args`, which members must a file handler set, and in which callback?
How long do `serialized_data` and `private_data` each live, and what does `retrieve_status` tell a
later callback?

## kho.file-retrieve-finish: Retrieve and finish

- section: Live Update Orchestrator
- relevance: 4 - reference ownership and retry rules

What does `luo_retrieve_file()` return when a file is retrieved a second time, and when an earlier
retrieve of it failed? Who holds references on the file it returns?

## kho.file-set-finish: Finishing a file set

- section: Live Update Orchestrator
- relevance: 4 - a finish also handles files that were never retrieved, and it can fail

What does `luo_file_finish()` do for files that were never retrieved, and what makes it fail?

# Model gaps

## kho.model-gaps: Other mistakes models make

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
