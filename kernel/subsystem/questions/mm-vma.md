# Questions: MM VMA Operations

- guide: mm-vma.md
- title: MM VMA Operations

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/mm-vma-measurement-116.md` is
the wider set the readers were measured on and `catalogue/mm-vma-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## vma.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## vma.core-files: Core files

- section: Finding your way
- relevance: 5 - the first thing anyone needs, and models place half of it in the wrong file

A table and nothing else, job to file: allocating and freeing a VMA; the operations on VMAs
(split, merge, unmap and the body of the mmap path); stack setup for exec; the mmap and brk
system calls with the fork and exit of an address space; the mmap lock and the per-VMA lock; the
userland tests. Where a reader is likely to look for a function in a file that no longer holds
it, say so in the row. Start from `mm/vma.c`.

## vma.entry-points: Entry points

- section: Finding your way
- relevance: 5 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: map a region; unmap one;
change an attribute over a range; split; merge; move a mapping; grow the stack; fork; exit. Give
the current name where it has changed.

## vma.state-structs: State structures

- section: Finding your way
- relevance: 3 - their names say little about what they are for

A table and nothing else, job to the structure the VMA core passes between its own functions for
it: the state of one mmap call; the descriptor handed to a file's hook; a merge; an unmap; a
change to a VMA's range while the reverse-map locks are held. One phrase each on what it is for
where the name does not say. Start from `mm/vma.h`.

## vma.userland-tests: Userland tests

- section: Finding your way
- relevance: 4 - a change to the core that does not update it breaks the tests

How does the userland VMA test program get the core's code and the definitions that code needs
from the rest of the kernel, and what must a change to the core (a new include, a helper from
another header, a new field it touches) update to keep it building? Start from
`tools/testing/vma/`.

# Flags

## vma.flag-representation: Flag representation

- section: Flags
- relevance: 5 - models describe an older layout and deny this one exists

Which types hold a VMA's flags in `struct vm_area_struct`, and how is a single flag named for each
type? How does code written for one type reach the other? Give the pattern of the helper names
that read, test and convert, not every helper. Start from `struct vm_area_struct` and
`include/linux/mm.h`.

## vma.flags-helpers: Flag helpers

- section: Flags
- relevance: 4 - every driver mmap handler uses these

For the helpers a driver or filesystem is likely to call to change a VMA's flags, in both
spellings, give a table to choose from: what happens to bits already set, and whether the helper
takes the VMA write lock, only asserts it, or does neither. Start from `vm_flags_set()`,
`vm_flags_reset()` and `vma_set_flags()`.

## vma.flags-usage: Changing flags

- section: Flags
- relevance: 4 - plausible in any driver

What are the requirements for changing the flags of a VMA with `vm_flags_set()`, `vma_set_flags()`
or another of the helpers that change them, in order to assure safe usage, and do the requirements
differ in an mmap hook on a VMA that nobody else can see yet? Name in-tree code that shows each.

# Per-VMA locks and lookups

## vma.per-vma-lock-parts: Per-VMA lock functions

- section: Per-VMA locks and lookups
- relevance: 4 - the concept is known; the fields, constants and function names are not

Which members of `struct vm_area_struct` make up the per-VMA lock, and which functions read-lock a
VMA, write-lock it and keep new readers out? What does `vma_start_write_killable()` return, and
what must its caller do when it fails? Start from `mm/mmap_lock.c` and
`include/linux/mmap_lock.h`.

## vma.assertions: Locking assertions

- section: Per-VMA locks and lookups
- relevance: 4 - models offer an assertion for either-lock paths that fires under one of the two locks

A table of the helpers that assert an mm or a VMA is locked or stable, to choose from: which of
the mmap read lock, the mmap write lock, a VMA read lock and a VMA write lock each accepts. Which
one is right for a path reachable under either the mmap lock or a per-VMA lock? Do they check
anything without debug options? Start from `include/linux/mmap_lock.h`.

## vma.detach-waits: Detaching a VMA

- section: Per-VMA locks and lookups
- relevance: 4 - this wait is what makes freeing a VMA without an RCU delay safe

What does `vma_mark_detached()` wait for before it returns, and what must its caller hold? Start
from `vma_mark_detached()`.

## vma.detached-vma-free: Freeing a detached VMA

- section: Per-VMA locks and lookups
- relevance: 4 - when the memory of a VMA can be reused decides what a lockless reader has to recheck

Is a detached VMA freed at once or after an RCU grace period, and what keeps a lockless reader
that still holds a pointer to it safe? Start from `vma_mark_detached()`.

## vma.lookup-promises: Lockless lookup guarantees

- section: Per-VMA locks and lookups
- relevance: 3 - says what a caller of the per-VMA lock lookup may assume on return

What does `lock_vma_under_rcu()` guarantee about the VMA it returns, which of those guarantees are
rechecked after the lock is taken and by which function, and what is the caller left to do when
the lookup fails? Start from `lock_vma_under_rcu()` and `vma_start_read()`.

## vma.iterator-after-rcu: VMA iterator after RCU unlock

- section: Per-VMA locks and lookups
- relevance: 3 - a helper that drops RCU internally hides the unlock; two of three readers had it wrong

Do `vma_start_read()` and `lock_next_vma()` leave the RCU read-side section before they return,
and if so on which paths? What are the requirements for using a VMA iterator after one of them
returns in order to assure safe usage? Start from `vma_start_read()` and `lock_next_vma()`.

# Locks and page tables

## vma.vma-lock-only-operations: Per-VMA-lock-only paths

- section: Locks and page tables
- relevance: 5 - whether any of these can free a page table is the fact models get backwards

What may an operation that holds only a per-VMA read lock do to page tables: can any of them free
a page table, through which functions, and what do the rest restrict themselves to? Start from
the callers of `lock_vma_under_rcu()` and `lock_next_vma()`, and `mm/madvise.c`.

## vma.write-lock-usage: mmap write lock and tables

- section: Locks and page tables
- relevance: 5 - the race has shipped, and nothing in a diff shows it

What are the requirements for code that holds the mmap write lock and changes or frees page tables
in order to assure safe usage, and which in-tree code that touches page tables under that lock
without write-locking the VMA is correct? Start from `collapse_huge_page()`,
`kernel/events/uprobes.c` and `mm/ptdump.c`.

## vma.free-pgtables-lock: Freeing page tables

- section: Locks and page tables
- relevance: 4 - models say the mmap write lock; the unmap path says otherwise

Which lock is held when the page tables under an unmapped range are freed, and what makes that
enough? Start from `vms_complete_munmap_vmas()` and `free_pgtables()`.

# Mapping a region

## vma.mmap-phases: mmap phases

- section: Mapping a region
- relevance: 4 - the path is remembered under older names and without its newer hook

Which functions does `__mmap_region()` call for the phases of mapping a new region, at which phase
do the `mmap_prepare` hook and the `mmap` hook of `struct file_operations` run, and what is each
hook handed? Start from `__mmap_region()`.

## vma.hook-may-set: mmap hook fields

- section: Mapping a region
- relevance: 3 - the common mistake is setting the right thing in the wrong hook

What may the `mmap_prepare` hook and the `mmap` hook of `struct file_operations` each change about
the mapping, and through which structure? What has mm core already decided before each hook runs?
What can `mmap_prepare` ask mm core to do once the VMA exists?

## vma.mmap-file-swap: Replacing the file in hooks

- section: Mapping a region
- relevance: 4 - the two hooks have opposite duties and models state them backwards

When an mmap hook replaces the file of the mapping, who owns the reference on the old file and on
the new one, in `mmap_prepare` and in `mmap`? What are the requirements for replacing the file in
each hook in order to assure safe usage? Start from `call_mmap_prepare()`, `__mmap_new_file_vma()`
and `vma_set_file()`.

## vma.anon-with-file: Anonymous VMAs with a file

- section: Mapping a region
- relevance: 4 - this is the case that breaks code which tests the file pointer

What does `vma_is_anonymous()` test, and does `vma_set_anonymous()` clear the VMA's file pointer?
What are the requirements for code that needs to know whether a VMA is anonymous in order to
assure safe usage? Start from `vma_set_anonymous()` and `drivers/char/mem.c`.

## vma.mmap-replaces: Mapping over existing mappings

- section: Mapping a region
- relevance: 3 - what survives a failure is not what it used to be

When a new mapping is placed over existing ones and building it fails, what happens to the old
mappings, and does it depend on how far it got? Start from `__mmap_setup()` and
`vms_abort_munmap_vmas()`.

## vma.mmap-unwind: Undoing a failed mmap

- section: Mapping a region
- relevance: 4 - each new step on the mmap path needs a matching undo

What must a step added to the mmap path provide so that a later failure undoes it, which
failures are undone at the labels that end the function and which through the unmap state, and
what is left in place on purpose? Start from the labels at the end of `__mmap_region()`.

# vm_ops callbacks

## vma.vm-ops: Callback timing

- section: vm_ops callbacks
- relevance: 4 - every driver and filesystem that maps memory implements some

A table of the callbacks in the operations table that the VMA core itself calls when VMAs are
created, split, copied, moved or removed: when each is called, under which locks, and what a
failure return from it aborts. Start from `struct vm_operations_struct`.

## vma.open-close-pairing: open and close pairing

- section: vm_ops callbacks
- relevance: 4 - drivers that keep state per VMA get this wrong

Is the `open` callback of `struct vm_operations_struct` called for the VMA that mmap itself
creates? What are the requirements for a driver that keeps state per VMA, in its mmap hook and in
its `open` and `close` callbacks, in order to assure safe usage when the VMA is later split,
copied or removed?

## vma.close-and-merge: close and merging

- section: vm_ops callbacks
- relevance: 3 - explains merges that silently do not happen

Is close ever called for a VMA that a merge removes, and how does having a close callback
restrict merging? Start from `can_merge_remove_vma()` and `vma_complete()`.

# Merge and modify

## vma.merge-conditions: Merge conditions

- section: Merge and modify
- relevance: 4 - a new per-VMA attribute has to be added here or merging corrupts it

Where are the conditions for merging two adjacent VMAs, or a VMA and a proposed mapping, tested,
which of them would a reader not expect beyond adjacency, flags, file and offset, and what must a
change that adds a per-VMA attribute do there so that VMAs that differ in it are never joined?
Start from `is_mergeable_vma()`, `can_vma_merge_left()` and `can_vma_merge_right()`.

## vma.merge-flag-compare: Flags in merge decisions

- section: Merge and modify
- relevance: 3 - more than one flag is left out of the comparison

How are two VMAs' flags compared when deciding whether they can merge, which flags are left out
of the comparison, and what happens to those on the merged VMA? Start from `is_mergeable_vma()`.

## vma.merge-fork-test-side: Fork test during merge

- section: Merge and modify
- relevance: 3 - checking the wrong side passes any test that faults both sides first

Which test decides whether a VMA was inherited across fork, and in each case (only one side has
a reverse-map root, only the other, both) which VMA is it applied to? Start from
`is_mergeable_anon_vma()`.

## vma.merge-results: Merge and modify results

- section: Merge and modify
- relevance: 4 - the failure is a use-after-free or an error pointer dereference

How do `vma_modify_flags()` and the other modify functions report failure, and how do
`vma_merge_new_range()`, `vma_merge_extend()` and `copy_vma()` report it? What are the
requirements for using the returned VMA, and the pointer that was passed in, after each returns,
in order to assure safe usage? Name in-tree code that shows it. Start from `vma_modify_flags()`
and `vma_merge_new_range()`.

## vma.merge-state-on-failure: Merge state after failure

- section: Merge and modify
- relevance: 3 - a caller that reuses the state reuses wrong values

Which members of `struct vma_merge_struct` can a failed merge attempt leave changed? What are the
requirements for reusing a `struct vma_merge_struct` after a failed attempt in order to assure
safe usage? Start from `struct vma_merge_struct`.

# Range changes and the maple tree

## vma.page-offsets: Page offsets

- section: Range changes and the maple tree
- relevance: 4 - models know one offset field; whether there is another decides how rmap and merging work

Which page offsets does a `struct vm_area_struct` carry, which of them do reverse mapping and
merging use for an anonymous VMA and which for a file, and what must code that splits, moves or
grows a VMA do to keep them right? Start from `struct vm_area_struct` and `mm/internal.h`.

## vma.rmap-trees: Reverse-map trees

- section: Range changes and the maple tree
- relevance: 4 - models search for helper names that may not be here

What are the file and the anonymous reverse-map trees keyed by, and what does this tree call the
helpers that insert into, remove from and iterate each, where a reader searches for the
interval-tree names? Give the pattern of the names. Start from `mm/interval_tree.c` and
`vma_link_file()`.

## vma.range-change-sequence: Range change sequence

- section: Range changes and the maple tree
- relevance: 4 - reordering any step races with faults or reverse-map walks

What order of steps must a split, a merge and a shrink keep between write-locking the VMA and
releasing the reverse-map locks, why does the VMA come out of the reverse-map trees for it, and
what does a reordering race with? Start from `vma_prepare()` and `vma_complete()`.

## vma.stack-growers: Stack growth

- section: Range changes and the maple tree
- relevance: 3 - a second, lighter way to change a VMA's range

Which locks do the functions that grow the stack VMA take, what do they skip that the other
range-changing functions do, and why is that enough for them? Start from `expand_downwards()`.

## vma.tree-writes: Writing to the maple tree

- section: Range changes and the maple tree
- relevance: 3 - the wrong helper trips a debug check, and an unallocated store can fail half way

Which helper is used when to write a VMA into the maple tree or to clear a range? What are the
requirements for a store into the tree in the middle of an operation that cannot be undone, in
order to assure safe usage? Which configuration option turns on `validate_mm()`? Start from
`vma_iter_prealloc()` and `validate_mm()`.

## vma.map-count-check: VMA count limit

- section: Range changes and the maple tree
- relevance: 2 - one of two similarly named functions skips it

Where is the limit on the number of VMAs checked, and does every function that splits a VMA check
it, or do some leave the check to the caller? Start from `sysctl_max_map_count`.

# Fork and foreign address spaces

## vma.fork-copy: Copying VMAs at fork

- section: Fork and foreign address spaces
- relevance: 3 - the child is not an exact copy, and a failed fork leaves a marked mm

What is reset or left out when fork copies a VMA into the child, and what does a fork that fails
part way leave in the child's tree and on its mm? Start from `dup_mmap()`.

## vma.unstable-mm: Unstable address spaces

- section: Fork and foreign address spaces
- relevance: 3 - ksm, khugepaged, swapoff, uprobes and procfs all walk other processes' mms

How is an mm whose fork failed, or that the OOM reaper is tearing down, marked? What are the
requirements for code that walks another process's mm in order to assure safe usage, and must it
test for the mark before or after taking the mmap lock? Start from `check_stable_address_space()`.

# Overcommit accounting

## vma.commit-check-charges: Overcommit charging

- section: Overcommit accounting
- relevance: 3 - every error path after it has to give the charge back

When does the overcommit check charge the pages, relative to testing the limit, and how is a
charge given back by a caller that fails later? Start from `security_vm_enough_memory_mm()`.

## vma.account-flag-preservation: Accounting flag on live VMAs

- section: Overcommit accounting
- relevance: 2 - a few sites; the leak is permanent and silent, and readers name the wrong functions

What are the requirements for setting or clearing `VM_ACCOUNT` on a VMA that stays in the tree, in
order to assure safe usage of the overcommit charge? Name in-tree code that shows it. Start from
`unmap_source_vma()` and `mprotect_fixup()`.

# Model gaps

## vma.model-gaps: Other mistakes models make

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
