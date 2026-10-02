# Questions: MM VMA Operations

- guide: mm-vma.md
- title: MM VMA Operations

The guide built from these questions explains what a VMA is, how to use VMAs
safely, and how to change the VMA implementation safely. Format:
`../../docs/subsystem-questions.md`. One question asks one thing. Questions
render in file order; the questions of one section are answered together.

# What a VMA is

## vma.what-it-represents: What one VMA describes

- section: The structure
- relevance: 3 - the definition everything else rests on
- words: 60

What does one VMA describe, and what has to be the same for every address in
it? Start from `struct vm_area_struct` in `include/linux/mm_types.h`.

## vma.fields: The fields, by purpose

- section: The structure
- relevance: 3 - a map of the structure for anyone reading code that touches it
- words: 150

Group the fields of the structure by what they are for (the range, the owner,
protection and flags, what backs it, reverse mapping, locking, policy and
other attachments) and say in a table what each group holds. Include the
fields that only exist under a config option.

## vma.field-stability: Which fields may change, and under what

- section: The structure
- relevance: 4 - decides what a reader may trust under each lock
- words: 90

Which fields never change while a VMA is in its mm's tree, which change only
under the VMA write lock, and which can change under less than that? Start
from the comments in the structure and `Documentation/mm/process_addrs.rst`.

## vma.page-offset: What the page offset means

- section: The structure
- relevance: 3 - misread offsets put pages at the wrong address
- words: 80

What does a VMA's page offset mean for a file mapping, for an anonymous
mapping and for a mapping of raw page frames, and is there more than one
offset field? Which helpers turn an offset and a VMA into an address? Start
from `vm_pgoff`, `vma_set_anon_pgoff()` and `mm/internal.h`.

## vma.tree: Where an mm keeps its VMAs

- section: Where VMAs live
- relevance: 3 - the container every lookup and change goes through
- words: 70

Which data structure holds an mm's VMAs, what is it keyed by, what is always
true of the entries (overlap, order), and what else in the mm counts them?
Start from `mm_mt` and `map_count` in `struct mm_struct`.

## vma.lookup-api: Finding a VMA

- section: Where VMAs live
- relevance: 3 - the two lookups differ in a way that causes bugs
- words: 80

Which functions find the VMA that contains an address, and which find the
first one at or after it? Which are used to walk all of them? Start from
`find_vma()`, `vma_lookup()` and `for_each_vma()`.

## vma.iterator: The VMA iterator

- section: Where VMAs live
- relevance: 3 - anyone walking or changing VMAs holds one
- words: 80

What is the VMA iterator, what state does it carry between calls, what
protects that state, and which calls reset it? Start from `struct
vma_iterator`, `struct ma_state` and `vma_iter_init()`.

## vma.gaps: Finding room for a new mapping

- section: Where VMAs live
- relevance: 2 - only the address-selection code touches it
- words: 60

How is a free address range found for a new mapping, and what does the tree
keep that makes the search fast? Start from `vm_unmapped_area()`.

## vma.map-count-limit: The limit on the number of VMAs

- section: Where VMAs live
- relevance: 2 - explains one way a split or mmap fails
- words: 50

What limits the number of VMAs in an mm, where is the limit checked, and which
operations can fail because of it? Start from `sysctl_max_map_count`.

## vma.alloc-free: Allocating and freeing a VMA

- section: The life of a VMA
- relevance: 3 - the entry and exit points of every VMA
- words: 70

Where does VMA memory come from, which functions allocate, copy and free one,
and what does a freshly initialised VMA contain? Start from `vm_area_alloc()`,
`vm_area_dup()`, `vm_area_free()` and `vma_init()`.

## vma.rcu-slab: VMA memory is reused under RCU

- section: The life of a VMA
- relevance: 3 - the reason a lockless lookup cannot trust what it finds
- words: 50

Is the VMA slab cache type-safe under RCU, so that a freed VMA stays valid
memory through a read-side section but can be handed to a different mm inside
it? Where is the cache created? Start from `vma_state_init()`.

## vma.attached-detached: Attached and detached

- section: The life of a VMA
- relevance: 4 - the state that says whether anyone else can reach the VMA
- words: 90

What does it mean for a VMA to be attached or detached, which functions change
that, and what does the VMA's reference count hold in each state? Start from
`vma_mark_attached()` and `vma_mark_detached()`.

## vma.visibility: When others can see a VMA

- section: The life of a VMA
- relevance: 4 - what may be done to a VMA depends on who can see it
- words: 90

At which point does a new VMA become reachable by page faults, by reverse-map
walkers and by readers of the tree, and at which point does a dying one stop
being reachable by each? Start from `__mmap_new_vma()`, `vma_link_file()` and
`vms_gather_munmap_vmas()`.

## vma.creators: Every way a VMA is created

- section: How VMAs come into being
- relevance: 3 - a map of the entry points
- words: 100

Which paths create a VMA (mmap, brk, the initial stack, special mappings, fork,
moving a mapping, a driver inserting one), and which function does it in each?
A table.

## vma.mmap-path: The steps of mapping a new region

- section: How VMAs come into being
- relevance: 4 - most changes and most driver hooks live somewhere on this path
- words: 130

List in order the steps from the mmap call to a finished mapping: the checks,
removing what is already there, the attempt to merge, allocating a VMA, calling
the file's hook, inserting it, and what happens after. Start from `do_mmap()`
and `__mmap_region()` in `mm/vma.c`.

## vma.mmap-replaces: Mapping over existing mappings

- section: How VMAs come into being
- relevance: 3 - the unwinding here is easy to break
- words: 70

When a new mapping is placed over existing ones, when are the old ones removed
relative to the new one being built, and what happens to them if building the
new one fails? Start from `__mmap_setup()` and `vms_abort_munmap_vmas()`.

## vma.fork-copy: How fork copies the VMAs

- section: How VMAs come into being
- relevance: 3 - the child is not an exact copy
- words: 100

How does fork duplicate an mm's tree and VMAs: what is copied as it is, what is
reset or cleared on the child, which VMAs are left out, and where does copying
the page tables come in the order? Start from `dup_mmap()`.

## vma.stack: The stack VMA

- section: How VMAs come into being
- relevance: 3 - the one VMA that grows on a fault
- words: 80

How is the stack VMA created, how does it grow, which lock does growing need,
and what keeps it from growing into its neighbour? Start from
`create_init_stack_vma()`, `expand_stack()` and `expand_downwards()`.

## vma.special-mappings: Special mappings

- section: How VMAs come into being
- relevance: 2 - a handful of users
- words: 60

What is a special mapping, who creates them, and how do they differ from file
and anonymous mappings? Start from `_install_special_mapping()`.

## vma.operations: The operations that change existing VMAs

- section: How VMAs are changed and removed
- relevance: 4 - the vocabulary of the VMA core
- words: 110

What are the primitive operations that change VMAs already in the tree (split,
merge, expand, shrink, copy for a move), what does each do to the tree, and
which system calls rely on each? A table. Start from `mm/vma.h`.

## vma.modify-family: What the modify functions do for a caller

- section: How VMAs are changed and removed
- relevance: 4 - every attribute-changing system call is built on them
- words: 80

What do the modify functions do for a caller that wants to change one attribute
over an address range, and what do they leave for the caller to do itself?
Start from `vma_modify()` and `vma_modify_flags()`.

## vma.munmap-phases: The stages of unmapping a range

- section: How VMAs are changed and removed
- relevance: 3 - the two-stage design is what makes failure recoverable
- words: 110

List in order the stages of unmapping an address range, from splitting at the
edges to freeing the VMAs, and say where the mmap lock may be downgraded. Start
from `do_vmi_munmap()`, `vms_gather_munmap_vmas()` and
`vms_complete_munmap_vmas()`.

## vma.exit-teardown: Tearing down every VMA at exit

- section: How VMAs are changed and removed
- relevance: 3 - races with the OOM reaper live here
- words: 80

How are all of an mm's VMAs and page tables torn down when it exits, in what
order, and how does that coordinate with the OOM reaper? Start from
`exit_mmap()`.

## vma.move: Moving a mapping

- section: How VMAs are changed and removed
- relevance: 3 - the only operation that has two VMAs for one mapping for a while
- words: 90

How is a mapping moved to a new address: where does the new VMA come from, when
are the page tables moved, when does the old VMA go, and what is done if a
step fails part way? Start from `move_vma()` and `copy_vma()`.

## vma.anon-test: The test for an anonymous VMA

- section: The kinds of VMA
- relevance: 4 - the wrong test looks right and is used all over mm and drivers
- words: 50

What is the canonical test for an anonymous VMA, and what does it actually look
at: the file pointer, a flag, or something else? Start from
`vma_is_anonymous()`.

## vma.anon-kinds: The kinds of VMA by operations table and file

- section: The kinds of VMA
- relevance: 3 - a compact way to see the two odd cases
- words: 90

Give a four-row table: for each combination of "has an operations table" and
"has a file" that exists in this tree, what the VMA is and what creates it.

## vma.anon-with-file: Anonymous VMAs that still have a file

- section: The kinds of VMA
- relevance: 4 - this is the case that breaks code which tests the file pointer
- words: 90

How does a VMA that was set up with a file become anonymous, and is its file
pointer cleared when it does? Which code in this tree does that, in mm and in
drivers, counting code that clears the operations table by direct assignment
as well as through the helper? Start from `vma_set_anonymous()` and
`drivers/char/mem.c`.

## vma.kind-flags: Flags that mark a VMA as special

- section: The kinds of VMA
- relevance: 3 - core paths refuse to touch these, and drivers rely on it
- words: 90

Which flags mark a VMA as mapping raw page frames, device memory or huge pages,
or as not to be expanded, copied or dumped, and what do the core paths refuse
to do with a VMA that carries them? Start from `VM_SPECIAL`.

## vma.flag-groups: What the flags word holds

- section: Flags
- relevance: 3 - permission bugs come from confusing the two sets of permission bits
- words: 100

What groups of flags does a VMA carry, how do the permission bits relate to
their "may" counterparts, and where are both derived when a mapping is made?
Start from `do_mmap()` and `calc_vm_prot_bits()`.

## vma.two-flag-apis: Two ways to spell a flag

- section: Flags
- relevance: 4 - code is mid-conversion and the two have different helpers
- words: 80

This tree can name a VMA flag as a bit in a word or as a bit number in a
bitmap type. How do the two share storage, how is one converted to the other,
and which does new code use? Start from `vma_flags_t` and
`legacy_to_vma_flags()`.

## vma.page-prot: Flags and page protection

- section: Flags
- relevance: 3 - a flags change that skips this leaves stale protections
- words: 70

How is a VMA's page protection derived from its flags, and after which changes
must it be recomputed? Start from `vm_get_page_prot()` and
`vma_set_page_prot()`.

## vma.file-rmap: How a file mapping is linked to its file

- section: Links to the rest of mm
- relevance: 3 - the reason range changes need a lock outside the mm
- words: 70

How is a file-backed VMA linked to its file's address space so that the pages
can find it: which tree, keyed by what, under which lock, and when is it put in
and taken out? Start from `vma_link_file()` and `i_mmap`.

## vma.anon-rmap: How an anonymous mapping is linked for reverse mapping

- section: Links to the rest of mm
- relevance: 3 - fork and merge both manipulate this
- words: 100

How is a VMA tied to the structures that let an anonymous page find it: when
does it get them, what does fork do with them, and what is the root? Start
from `__anon_vma_prepare()`, `anon_vma_fork()` and `anon_vma_clone()`.

## vma.page-tables: VMAs and page tables

- section: Links to the rest of mm
- relevance: 3 - ordering between the two is a recurring source of bugs
- words: 80

A VMA does not own page tables. How are the page tables under its range freed
when it goes, and what must be true of the VMAs before that is done? Start from
`free_pgtables()` and `unmap_region()`.

## vma.vm-ops: The callbacks the VMA core calls

- section: Links to the rest of mm
- relevance: 4 - every driver and filesystem that maps memory implements some
- words: 140

For each callback in a VMA's operations table that the VMA core itself calls
when VMAs are created, split, copied, moved or removed, say when it is called
and under which locks. A table. Leave the fault callbacks to the fault path.
Start from `struct vm_operations_struct`.

## vma.other-attachments: What else hangs off a VMA

- section: Links to the rest of mm
- relevance: 2 - matters when merging and copying
- words: 70

Besides the file and the reverse-map structures, what else can be attached to a
VMA (memory policy, userfaultfd context, a name, tracking state), and what is
done with each when the VMA is copied or freed?

## vma.commit-check-charges: The overcommit check also charges

- section: Accounting
- relevance: 3 - mmap, brk, mremap, shmem and stack growth all use it
- words: 60

Does the overcommit check only test, or does it charge the pages when it
succeeds, and how is a charge given back? Start from
`security_vm_enough_memory_mm()`.

## vma.account-flag: The accounting flag

- section: Accounting
- relevance: 3 - the flag decides whether the charge ever comes back
- words: 70

Which mappings are charged against the overcommit limit, which flag records
that on the VMA, and where is the charge returned when the VMA goes? Start from
`accountable_mapping()` and `vms_gather_munmap_vmas()`.

## vma.vm-stat: The per-mm size counters

- section: Accounting
- relevance: 2 - wrong counters show up in limits and in /proc
- words: 60

Which per-mm counters track how much address space is mapped, by kind, and
which function updates them when a VMA is added, resized or removed? Start
from `vm_stat_account()`.

# The locks

## vma.lock-inventory: The locks that protect a VMA

- section: What each lock protects
- relevance: 5 - nothing else in the guide makes sense without it
- words: 140

Which locks are involved in reading or changing a VMA (the mmap lock, the
per-VMA lock, RCU, the file and anonymous reverse-map locks), what does each
protect about the VMA, and where is their order written down? A table. Start
from `Documentation/mm/process_addrs.rst` and `mm/rmap.c`.

## vma.per-vma-lock-mechanism: How the per-VMA lock is built

- section: What each lock protects
- relevance: 4 - its odd shape explains its odd rules
- words: 100

What is the per-VMA lock made of, what does holding it for read consist of,
what does holding it for write consist of, and how is each released? Start
from `vma_start_read()`, `vma_start_write()` and `vma_end_write_all()`.

## vma.mmap-write-lock-effect: What taking the mmap write lock changes

- section: What each lock protects
- relevance: 5 - the commonest wrong assumption about these locks
- words: 60

What does taking the mmap lock for write change that a per-VMA reader can
observe, and does an attempt to take a per-VMA read lock made afterwards still
succeed? If this tree has no per-VMA locks, say so. Start from
`mmap_write_lock()` and `vma_start_read()`.

## vma.vma-write-lock-effect: What write-locking one VMA does

- section: What each lock protects
- relevance: 5 - this is what actually excludes faults
- words: 80

What does write-locking a VMA do to readers already inside, to readers that
arrive while it waits, and to readers afterwards, and until when does that
last? Start from `vma_start_write()`.

## vma.vma-lock-only-operations: What runs under only a per-VMA lock

- section: What each lock protects
- relevance: 5 - the list keeps growing as paths are converted
- words: 100

Which operations run holding only a per-VMA lock and not the mmap lock, and can
any of them free a page table? Start from the callers of
`lock_vma_under_rcu()` and `lock_next_vma()`, and `mm/madvise.c`.

## vma.lock-modes: Which lock a job needs

- section: What each lock protects
- relevance: 3 - lockdep and the asserts catch the wrong choice, but only on paths a test runs
- words: 80

Which kinds of operation on VMAs need the mmap lock held for write, which may
run under it held for read, and which under only a per-VMA lock? Is any change
to a VMA allowed without the write lock?

## vma.no-per-vma-lock-config: Building without per-VMA locks

- section: What each lock protects
- relevance: 2 - the fallback has to keep working
- words: 50

What do the per-VMA lock functions and assertions become when the kernel is
built without per-VMA locks? Start from the `#else` of `CONFIG_PER_VMA_LOCK`
in `include/linux/mmap_lock.h`.

# Using VMAs safely

## vma.pointer-validity: How long a VMA pointer is good for

- section: Finding a VMA and keeping it
- relevance: 5 - almost every use-after-free on a VMA is a misjudgement of this
- words: 100

After a lookup, for how long may the VMA pointer be used when the caller holds
the mmap lock for read, the mmap lock for write, a per-VMA read lock, or only
RCU? What ends it in each case?

## vma.per-vma-lock-api: Taking a per-VMA read lock

- section: Finding a VMA and keeping it
- relevance: 4 - new users keep being added outside the fault path
- words: 90

How does code take and release a per-VMA read lock, what must it fall back to
when it cannot get one, and what may it not do while holding one? Start from
`lock_vma_under_rcu()`, `vma_end_read()` and `vma_start_read_locked()`.

## vma.rcu-lookup-steps: What the lockless lookup checks, in order

- section: Finding a VMA and keeping it
- relevance: 3 - explains what a caller is and is not promised on return
- words: 110

List, in order, the steps the lockless lookup takes from the tree walk to
handing the caller a read-locked VMA, and say which step catches a VMA that has
been reused by another mm and which catches one reused elsewhere in the same
mm. Start from `lock_vma_under_rcu()` and `vma_start_read()`.

## vma.rcu-release-touches-mm: What releasing a per-VMA read lock touches

- section: Finding a VMA and keeping it
- relevance: 3 - the mm has to outlive the release
- words: 60

When a per-VMA read lock is released, is anything belonging to the VMA's mm
used after the reference has been dropped, and what for? Start from
`vma_refcount_put()`.

## vma.rcu-foreign-mm: Releasing a VMA that belongs to another mm

- section: Finding a VMA and keeping it
- relevance: 2 - only code that does its own lockless lookup can get this wrong
- words: 90

What usage of the per-VMA read lock release is unsafe when the VMA may belong
to an mm the caller does not hold, how does the lookup code itself stay safe,
and which releases that look similar are correct?

## vma.tree-state-rcu: Iterator state after the RCU section ends

- section: Finding a VMA and keeping it
- relevance: 3 - a helper that drops RCU internally hides the unlock
- words: 80

Which helpers in the lockless lookup leave the RCU read-side section
internally, what usage of the iterator afterwards is unsafe, and when is reuse
correct? Start from `vma_start_read()` and `lock_next_vma()`.

## vma.killable-lock-return: mmap lock variants that can fail

- section: Finding a VMA and keeping it
- relevance: 1 - generic, and the compiler already insists
- words: 40

Which mmap lock functions can return without the lock, and are they marked so
the compiler warns when the result is ignored? Start from
`mmap_write_lock_killable()`.

## vma.unstable-mm-mark: An mm that must not be trusted

- section: Working on another process's mm
- relevance: 3 - ksm, khugepaged, swapoff, uprobes and procfs all do this
- words: 70

How is an mm whose fork failed, or that the OOM reaper is tearing down, marked,
and must a walker test for the mark before or after taking the mmap lock? Start
from `check_stable_address_space()`.

## vma.failed-fork-tree: What a failed fork leaves behind

- section: Working on another process's mm
- relevance: 3 - decides what a walker can run into
- words: 60

What does a failed fork leave in the child's VMA tree at each point it can
fail, and is the mm always marked when that happens? Start from `dup_mmap()`.

## vma.other-mm-usage: Walking the VMAs of an mm that is not yours

- section: Working on another process's mm
- relevance: 3 - new walkers keep being added
- words: 80

By which routes can code reach an mm that belongs to another process, what
usage is unsafe once it has one, and which walkers are correct without the
stability test? Start from `unuse_mm()` and `get_task_mm()`.

## vma.file-pointer-uses: What the file pointer is the right test for

- section: Telling what kind of VMA you have
- relevance: 4 - this is correct code that a naive rule would forbid
- words: 70

Which kinds of code correctly test a VMA's file pointer, such as dropping a
file reference or locking and linking into the file's reverse-map tree? Is a
private mapping of the zero device linked into that file's tree? Start from
`vma_prepare()` and `take_rmap_locks()`.

## vma.anon-vs-file-usage: Testing the file pointer in place of the anonymous test

- section: Telling what kind of VMA you have
- relevance: 4 - tests on the file pointer are everywhere in mm and drivers
- words: 100

Given that an anonymous VMA can have a file and a non-anonymous one can lack
it, what usage of the file pointer as a test is incorrect, and which tests of
it that look similar are correct?

## vma.rmap-tree-key: What the file reverse-map tree is keyed by

- section: Telling what kind of VMA you have
- relevance: 1 - one past bug
- words: 50

What is the per-file reverse-map tree keyed by, and why does passing a page
frame number to its iterators compile and then find the wrong VMAs? Start from
`mapping_rmap_tree_foreach()`.

## vma.assertion-accepts: What each locking assertion accepts

- section: Asserting what you hold
- relevance: 3 - each per-VMA lock conversion has to fix assertions on the path
- words: 100

For each helper that asserts "this mm is locked" or "this VMA is locked or
stable", what does it accept: the mmap lock, a per-VMA lock, or either? Does
the answer change without per-VMA locks, without lockdep, or without debug
checks? Start from `include/linux/mmap_lock.h`.

## vma.assertion-choice: Which assertion a path should use

- section: Asserting what you hold
- relevance: 3 - the wrong one fires spuriously from the fault path
- words: 60

Which assertion should a path use when it can be reached under either the mmap
lock or a per-VMA lock, what usage is incorrect, and which paths rightly use a
narrower one? Name in-tree users.

## vma.flags-helpers: What each flag helper does

- section: Changing a VMA's flags
- relevance: 4 - every driver mmap handler uses these
- words: 120

For the helpers a driver or filesystem is likely to call to change a VMA's
flags, in both flag spellings, give a table: what happens to bits already set
(kept, cleared, replaced), and whether the helper takes the VMA write lock,
only asserts it, or ignores it. Start from `vm_flags_set()`,
`vm_flags_reset()`, `vma_set_flags()` and `include/linux/mm.h`.

## vma.flags-no-write-lock: Flags that may be set without the write lock

- section: Changing a VMA's flags
- relevance: 2 - one flag today
- words: 40

May any VMA flag be set without the VMA write lock, through which helper, and
under what lock? Start from `vma_set_atomic_flag()`.

## vma.flags-replace-idiom: Replacing a VMA's whole flag set

- section: Changing a VMA's flags
- relevance: 3 - adding where replacing was meant leaves stale permission bits
- words: 70

How does in-tree code replace a VMA's whole flag set, as opposed to adding bits
to it, and in what order with the VMA write lock? Name a caller that shows it.
Start from `mprotect_fixup()`.

## vma.flags-usage: Unsafe ways to change flags

- section: Changing a VMA's flags
- relevance: 4 - plausible in any driver
- words: 90

What usage of the flag helpers is unsafe, and which uses that look
similar are correct, such as from a driver's mmap hook on a VMA nobody else can
see yet?

## vma.fork-cleared-flags: Flags cleared on the child at fork

- section: Changing a VMA's flags
- relevance: 2 - the fact the next item depends on
- words: 50

Which VMA flags are cleared on the child's VMA during fork, where, and under
what condition? Start from `dup_mmap()` and `dup_userfaultfd()`.

## vma.fork-flag-tests: Testing flags during fork

- section: Changing a VMA's flags
- relevance: 2 - one known instance; could recur
- words: 60

When code that runs during fork tests a VMA flag to decide something for the
child, which VMA should it test, and when is testing the parent's correct?
Start from `vma_needs_copy()`.

## vma.two-mmap-hooks: The two mmap hooks

- section: Writing an mmap hook
- relevance: 4 - drivers are being converted from one to the other now
- words: 110

A file can provide one of two hooks that are called when it is mapped. What is
each given to work on, when does each run relative to the merge attempt, the
allocation of the VMA and its insertion, and which should new code provide?
Start from `call_mmap_prepare()`, `mmap_file()` and `struct vm_area_desc`.

## vma.hook-vma-state: The state of the VMA when the older hook runs

- section: Writing an mmap hook
- relevance: 4 - decides what a hook may touch without a lock
- words: 70

When the hook that is handed a VMA runs, is that VMA in the tree, is it
write-locked, and can page faults or reverse-map walkers reach it? Start from
`__mmap_new_vma()`.

## vma.hook-may-set: What a hook may set

- section: Writing an mmap hook
- relevance: 4 - the common mistakes are setting the right thing in the wrong hook
- words: 100

What may an mmap hook set (flags, the operations table, private data, page
protection, the file), how does each hook set them, and what has already been
decided before the hook runs and cannot be changed by it?

## vma.hook-failure: When an mmap hook fails

- section: Writing an mmap hook
- relevance: 3 - leaked references and half-built mappings come from here
- words: 80

When an mmap hook returns an error, what does the core undo, what must the hook
have undone itself, and is the close callback called? Start from
`__mmap_new_file_vma()` and the abort paths of `__mmap_region()`.

## vma.open-close-pairing: When open and close are called

- section: Writing an mmap hook
- relevance: 4 - drivers that count VMAs get this wrong
- words: 90

Which VMA operations call the open callback and which call close, is open
called for the VMA that mmap itself creates, and what must a driver that keeps
state per VMA therefore do in its mmap hook?

## vma.may-split-hook: The hook that may refuse a split

- section: Writing an mmap hook
- relevance: 3 - the hook runs earlier than its authors expect
- words: 80

When is the callback that may refuse a split called, under which locks, what is
it therefore limited to doing, and can a split still fail after it has agreed?
Name an in-tree implementation that gets it right. Start from `__split_vma()`.

## vma.mmap-file-refs: The two file references during mmap

- section: Replacing the file from an mmap hook
- relevance: 3 - needed to judge any hook that touches the file
- words: 60

During mmap, which file references exist, who owns each, and where is each
taken and dropped? Start from `ksys_mmap_pgoff()` and
`__mmap_new_file_vma()`.

## vma.mmap-file-swap-hooks: Replacing the file from each hook

- section: Replacing the file from an mmap hook
- relevance: 3 - the two hooks have opposite duties
- words: 90

Through which mmap hooks can a driver replace the file, does each run before or
after the VMA takes its own reference, and how does mm core notice the
replacement? Start from `call_mmap_prepare()` and `mmap_file()`.

## vma.mmap-file-swap-duty: What a hook that replaces the file must do

- section: Replacing the file from an mmap hook
- relevance: 3 - a leaked file reference is silent
- words: 70

What must a hook that replaces the file do with the old reference and the new
one, and which helper does it safely? Name an in-tree hook that uses it. Start
from `vma_set_file()`.

## vma.mmap-file-usage: Unsafe handling of the file reference

- section: Replacing the file from an mmap hook
- relevance: 3 - silent leak or use-after-free
- words: 80

What handling of file references in an mmap hook, or in mm core around one, is
unsafe, and what that looks similar is correct?

## vma.modify-returns: How the modify functions report failure

- section: Changing the attributes of a range
- relevance: 4 - every new caller in mprotect, madvise, mlock, mempolicy or userfaultfd meets this
- words: 50

How do the VMA modify functions report failure, and with which errors? Start
from `vma_modify_flags()` in `mm/vma.c`.

## vma.merge-returns: How the merge and copy functions report failure

- section: Changing the attributes of a range
- relevance: 4 - NULL means two different things
- words: 70

How do the merge, extend and copy functions report failure, and how does a
caller tell "no merge was possible" from "out of memory"? Start from
`vma_merge_new_range()` and `copy_vma()`.

## vma.merge-frees-input: A successful merge may free the VMA it was given

- section: Changing the attributes of a range
- relevance: 4 - use-after-free
- words: 50

On success, may the merge and modify functions return a different VMA from the
one passed in, and may they free the one passed in? Start from
`vma_merge_existing_range()`.

## vma.merge-state-on-failure: What a failed merge leaves in the merge state

- section: Changing the attributes of a range
- relevance: 3 - a caller that reuses the state after a failure reuses wrong values
- words: 50

After a merge attempt fails, which fields of the merge state may have been
changed and are not restored? Start from `struct vma_merge_struct` and
`vma_merge_new_range()`.

## vma.modify-cannot-fail: When a modify call cannot fail

- section: Changing the attributes of a range
- relevance: 3 - explains the one caller that does not check
- words: 50

Is there a way for a modify call to be unable to fail, under what condition,
and which in-tree caller relies on it? Start from `vma_modify_flags_uffd()`.

## vma.iterating-while-modifying: Walking a range and changing each VMA

- section: Changing the attributes of a range
- relevance: 4 - the loop is rewritten in every attribute-changing system call
- words: 100

Code such as mprotect, mlock and madvise walks the VMAs in a range and changes
each. How does it keep its iterator and its previous-VMA pointer right across a
merge or a split? Name the caller that is the best model. Start from
`madvise_update_vma()` and `mprotect_fixup()`.

## vma.merge-result-usage: Unsafe use of a merge or modify result

- section: Changing the attributes of a range
- relevance: 4 - the failure is a use-after-free or an error pointer dereference
- words: 80

What ways of storing and using the result of a merge or modify call are unsafe
or incorrect, and which in-tree callers that look wrong are correct?

## vma.merge-flag-compare: How flags are compared when merging

- section: Flags and merging
- relevance: 3 - explains why a late flag breaks merging
- words: 50

How are two VMAs' flags compared when deciding whether they can merge, and
which flags are left out of the comparison? Start from `is_mergeable_vma()`.

## vma.flags-before-merge: Where to add a flag so that it takes part in merging

- section: Flags and merging
- relevance: 3 - subtle and silent
- words: 80

Where must a subsystem add its own flag to a new mapping so that it takes part
in the merge decision, what goes wrong if it is added later, and which late
additions are harmless? Name an in-tree example of the right place. Start from
`ksm_vma_flags()`.

## vma.commit-accounting-usage: Error paths after the overcommit check

- section: Accounting for callers
- relevance: 3 - an error path added later is an easy miss and leaks silently
- words: 70

What handling of a caller's error paths after a successful overcommit check is
incorrect, and which callers show the correct forms?

## vma.vm-account-preservation: Clearing the accounting flag on a VMA that survives

- section: Accounting for callers
- relevance: 2 - a few sites; the leak is permanent and silent
- words: 70

What goes wrong when the accounting flag is cleared on a VMA that stays in the
tree, which in-tree code clears it, and how does each keep the charge right?
Start from `mm/mremap.c` and `mprotect_fixup()`.

# Changing the implementation safely

## vma.tree-invariants: What must always be true of the tree

- section: Invariants of the tree
- relevance: 4 - every change to the core either keeps these or is a bug
- words: 100

What must be true of an mm's VMA tree and the VMAs in it after every operation
(overlap, order, agreement between entries and the VMAs' own ranges, the count,
the attached state), and which debug code checks it? Start from
`validate_mm()`.

## vma.preallocation: Preallocating tree nodes

- section: Invariants of the tree
- relevance: 4 - the reason a range change cannot fail half way
- words: 90

Why are tree nodes preallocated before a VMA's range is changed, which calls do
it, and what is done with the preallocation on a path that then stores nothing?
Start from `vma_iter_prealloc()` and `vma_iter_free()`.

## vma.store-helpers: Writing to the tree

- section: Invariants of the tree
- relevance: 3 - the wrong helper trips a debug check or loses an entry
- words: 70

Which helpers write a VMA into the tree, overwrite a range and clear a range,
and what does each check about the iterator and the VMA first? Start from
`vma_iter_store_new()` and `mm/vma.h`.

## vma.range-change-functions: Functions that change a VMA's range in place

- section: The order of a range change
- relevance: 3 - says which functions the sequence below is about
- words: 80

Which functions change a VMA's start, end or page offset in place, and for
each, who takes the VMA write lock: the function itself or its callers? Start
from `__split_vma()`, `commit_merge()` and `vma_shrink()`.

## vma.split-merge-window: The sequence of a range change

- section: The order of a range change
- relevance: 4 - reordering any step races with faults or reverse-map walks
- words: 100

List in order what a split, a merge and a shrink each do between write-locking
the VMA and releasing the reverse-map locks, including where page tables may be
restructured and where the new range is written. Start from `vma_prepare()`,
`vma_complete()` and `vma_adjust_trans_huge()`.

## vma.why-rmap-reinsert: Why a range change takes the VMA out of the reverse-map trees

- section: The order of a range change
- relevance: 4 - the reason the sequence exists
- words: 70

Why does changing a VMA's range take it out of the file and anonymous
reverse-map trees and put it back afterwards, and what would a concurrent
reverse-map walk get wrong otherwise? Start from `vma_prepare()`.

## vma.window-lock-variant: Helpers with a caller-holds-the-locks form

- section: The order of a range change
- relevance: 2 - one helper today
- words: 60

Is there a page table helper that normally takes its own locks and has a form
for use inside that sequence, and how does that form check that the locks are
held? Start from `hugetlb_split()` and `hugetlb_unshare_pmds()`.

## vma.window-not-excluded: What the sequence does not exclude

- section: The order of a range change
- relevance: 3 - the locks look exhaustive and are not
- words: 50

Which page table walkers are not excluded by the locks held during a range
change, and how does code that must exclude them do so?

## vma.range-change-usage: Restructuring page tables in the wrong place

- section: The order of a range change
- relevance: 3 - severe, but only the VMA core and split hooks can do it
- words: 80

What placement of page table splitting, unsharing or freeing relative to that
sequence is unsafe, and what that looks similar is correct?

## vma.stack-growers-exception: Range changes that skip the sequence

- section: The order of a range change
- relevance: 3 - a second, lighter path that has to stay correct on its own terms
- words: 70

Which functions change a VMA's range without that sequence, which locks do they
take instead, and why is that enough for them? Start from `expand_upwards()`
and `expand_downwards()`.

## vma.merge-uprobe-side-effect: Completing a merge can install page table entries

- section: The order of a range change
- relevance: 2 - one user, but it cost a memory leak
- words: 50

Can completing a VMA merge populate page table entries, and how does a caller
that is about to move those page tables suppress it? Start from
`vma_complete()`.

## vma.merge-conditions: What two VMAs need in common to merge

- section: The rules of merging
- relevance: 4 - a new per-VMA attribute has to be added here or merging corrupts it
- words: 130

List every condition two adjacent VMAs, or a VMA and a proposed mapping, must
meet to be merged: flags, file, offsets, reverse-map structures, policy,
userfaultfd context, name, callbacks. Start from `is_mergeable_vma()`,
`can_vma_merge_left()` and `can_vma_merge_right()`.

## vma.merge-cases: The shapes a merge can take

- section: The rules of merging
- relevance: 3 - the code is organised around these cases
- words: 100

What are the shapes a merge can take (into the VMA before, into the one after,
joining both, for a new range and for an existing one), and in each, which VMA
survives and which are removed? Start from the comments above
`vma_merge_existing_range()` and `vma_merge_new_range()`.

## vma.merge-state: The merge state structure

- section: The rules of merging
- relevance: 3 - every merge and modify call is driven by one
- words: 100

What does a caller fill in on the structure that drives a merge, what do the
merge functions set on it, and what do its option bits ask for? Start from
`struct vma_merge_struct` and `enum vma_merge_state` in `mm/vma.h`.

## vma.merge-anon-propagation: Passing on the anonymous reverse-map root

- section: The rules of merging
- relevance: 3 - the merge code has been rewritten recently
- words: 60

When a VMA that has never faulted merges with one that has, where is the
anonymous reverse-map root given to the survivor, and what undoes it on
failure? Start from `dup_anon_vma()`.

## vma.merge-fork-test-side: Which VMA the merge-time fork test looks at

- section: The rules of merging
- relevance: 3 - checking the wrong side passes any test that faults both sides first
- words: 90

Which test decides whether a VMA was inherited across fork, what does it look
at, and in each case (only one side has a reverse-map root, only the other,
both) which VMA is it applied to? What application of it is incorrect? Start
from `is_mergeable_anon_vma()`.

## vma.close-hook-and-merge: A close callback restricts merging

- section: The rules of merging
- relevance: 3 - explains merges that silently do not happen
- words: 60

How does a VMA that has a close callback restrict which merges are allowed, and
why? Start from `can_merge_remove_vma()`.

## vma.read-lock-order: Why the read lock does its checks in that order

- section: The per-VMA lock implementation
- relevance: 4 - reordering them reintroduces bugs that have already been fixed once
- words: 100

Taking a per-VMA read lock does an early sequence check, takes a reference,
compares the mm, and checks the sequence again. What does each step protect
against, and what goes wrong if the mm comparison is moved before the reference
or after the second sequence check? Start from `vma_start_read()`.

## vma.lock-ordering: Memory ordering the per-VMA lock relies on

- section: The per-VMA lock implementation
- relevance: 3 - the comments carry the argument; a change has to keep it true
- words: 90

Which memory ordering does the per-VMA lock rely on between a writer marking a
VMA locked and a reader checking it, and where do the comments state the
argument? Start from `vma_start_read()`, `__vma_start_write()` and
`mmap_lock_speculate_try_begin()`.

## vma.detach-waits: What detaching a VMA waits for

- section: The per-VMA lock implementation
- relevance: 4 - this wait is what makes freeing a VMA without an RCU delay safe
- words: 80

What does detaching a VMA wait for, and how does that make it safe to free the
VMA straight away even though a lockless reader may still hold a pointer to it?
Start from `vma_mark_detached()` and `__vma_exclude_readers_for_detach()`.

## vma.lock-refcount-balance: An interrupted writer must take its mark back

- section: The per-VMA lock implementation
- relevance: 2 - three functions in one file
- words: 60

A writer marks the VMA's reference count before waiting for readers to leave.
In which task states can it wait, and what must the interrupted path undo?
Start from `vma_start_write_killable()` and `__vma_start_exclude_readers()`.

## vma.mmap-unwind: Undoing a failed mmap

- section: Failure and unwinding
- relevance: 4 - each new step on the mmap path needs a matching undo
- words: 130

For each point at which mapping a new region can fail, what has been done by
then (the charge, the file reference, the mappings removed to make room, page
table entries a hook installed) and what undoes each? Start from the labels at
the end of `__mmap_region()`.

## vma.split-failure: When a split fails

- section: Failure and unwinding
- relevance: 3 - callers assume the tree is unchanged
- words: 60

What can make a split fail, and is the tree, and the VMA being split, left
exactly as they were when it does? Start from `__split_vma()`.

## vma.munmap-failure: When unmapping fails part way

- section: Failure and unwinding
- relevance: 3 - detached VMAs have to go back
- words: 70

What happens to the VMAs that have already been detached if unmapping a range
fails part way, and what state are they put back in? Start from
`vms_abort_munmap_vmas()` and `reattach_vmas()`.

## vma.core-notifications: Who the VMA core tells

- section: What else the core must keep working
- relevance: 3 - a new path through the core has to make the same calls
- words: 120

Which other subsystems does the VMA core call when a VMA is created, changed or
removed (uprobes, khugepaged, KSM, perf, the security hooks, userfaultfd), and
from which functions? A table.

## vma.userland-tests: The userland build of the VMA core

- section: What else the core must keep working
- relevance: 4 - a change to the core that does not update it breaks the tests
- words: 100

The VMA core is also compiled into a userland test program. Which kernel files
does it compile, where do the definitions it needs from the rest of the kernel
come from, and what must a change to the core or to those definitions update so
that it still builds and passes? Start from `tools/testing/vma/`.

## vma.nommu: VMAs without an MMU

- section: What else the core must keep working
- relevance: 2 - a separate implementation that shares some helpers
- words: 60

What implements mapping and unmapping when the kernel is built without an MMU,
and which of the VMA core's functions and structures does it share? Start from
`mm/nommu.c`.

## vma.config-variants: Configurations that change the shape of the core

- section: What else the core must keep working
- relevance: 2 - a change tested in one configuration can break another
- words: 70

Which configuration options add or remove fields of the VMA or change which
code paths the core takes, such as per-VMA locks, the direction the stack
grows, NUMA policy and VMA names?
