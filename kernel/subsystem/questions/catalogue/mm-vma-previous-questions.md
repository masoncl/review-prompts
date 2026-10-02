# Questions: MM VMA Operations

- guide: mm-vma.md
- title: MM VMA Operations

Format: `../../docs/subsystem-questions.md`. One question asks one thing.
Questions render in file order. Questions in one section, or quick checks
with the same group, are answered together.

# Sections

## vma.rcu-slab: Is the VMA slab type-safe under RCU

- section: VMA memory reused under RCU
- relevance: 2 - background for the rule below; on its own it changes no review
- words: 40

Is the slab cache that VMAs are allocated from created so that a freed VMA
stays valid memory through an RCU read-side section but can be handed to a
different mm inside it? Where is the cache created? Start from
`vma_state_init()`.

## vma.rcu-lookup-steps: How a fault finds and locks a VMA without the mmap lock

- section: VMA memory reused under RCU
- relevance: 2 - only patches to the lookup itself need it
- words: 110

List, in order, the steps the lockless lookup takes from the tree walk to
handing the caller a read-locked VMA, and say at which step the code can find
out that the VMA now belongs to a different mm. If this tree has no per-VMA
locks, say so and stop. Start from `lock_vma_under_rcu()` and
`vma_start_read()` in `mm/mmap_lock.c`.

## vma.rcu-release-touches-mm: What releasing a per-VMA read lock touches

- section: VMA memory reused under RCU
- relevance: 2 - the fact the rule below depends on
- words: 60

When a per-VMA read lock is released, is anything belonging to the VMA's mm
dereferenced after the reference has been dropped, and what for? Start from
`vma_refcount_put()`.

## vma.rcu-foreign-mm: Releasing the lock on a VMA that belongs to another mm

- section: VMA memory reused under RCU
- relevance: 2 - the rule can only be broken inside the lockless lookup functions in one file
- words: 90

How does the lookup code keep a foreign mm alive across the release of a
read lock on a VMA it found was not its own? When is releasing a per-VMA read
lock a bug for this reason, and which releases are fine as they are? Start
from `vma_start_read()`.

## vma.anon-test: The test for an anonymous VMA

- section: Telling anonymous VMAs from file-backed ones
- relevance: 4 - the wrong test looks right and is used all over mm and drivers
- words: 50

What is the canonical test for an anonymous VMA, and what does it actually
look at: the file pointer, a flag, or something else? Start from
`vma_is_anonymous()`.

## vma.anon-with-file: Anonymous VMAs that still have a file

- section: Telling anonymous VMAs from file-backed ones
- relevance: 4 - this is the case that breaks code which tests the file pointer
- words: 90

How does a VMA that was set up with a file become anonymous, and is its file
pointer cleared when it does? Which code in this tree does that, in mm and in
drivers, counting code that clears the operations table by direct assignment
as well as through the helper? Start from `vma_set_anonymous()` and
`drivers/char/mem.c`.

## vma.anon-kinds: The kinds of VMA by operations table and file

- section: Telling anonymous VMAs from file-backed ones
- relevance: 3 - a compact way to see the two odd cases
- words: 80

Give a four-row table: for each combination of "has an operations table" and
"has a file" that exists in this tree, what the VMA is and what creates it.
Start from `__install_special_mapping()` and `drivers/char/mem.c`.

## vma.file-pointer-uses: What the file pointer is the right test for

- section: Telling anonymous VMAs from file-backed ones
- relevance: 4 - stops correct rmap and refcount code being reported
- words: 70

Which kinds of code correctly test a VMA's file pointer, such as dropping a
file reference or taking and linking into the file's rmap tree? Is a private
mapping of the zero device linked into that file's rmap tree? Start from
`vma_prepare()` and `take_rmap_locks()`.

## vma.anon-vs-file-rule: When testing the file pointer is a bug

- section: Telling anonymous VMAs from file-backed ones
- relevance: 4 - tests on the file pointer are everywhere in mm and drivers
- words: 100

When is a test of a VMA's file pointer a bug, given that an anonymous VMA can
have a file and a non-anonymous one can lack it? What should be reported, and
which tests of the file pointer are correct and must not be?

## vma.range-change-functions: Functions that change a VMA's range in place

- section: Where page tables may be restructured during a split or merge
- relevance: 3 - tells a reviewer which functions the rule below is about
- words: 70

Which functions change a VMA's start, end or page offset in place, and for
each, who takes the VMA write lock: the function itself or its callers? Start
from `__split_vma()`, `commit_merge()` and `vma_shrink()` in `mm/vma.c`.

## vma.split-merge-window: The window in which page tables may be restructured

- section: Where page tables may be restructured during a split or merge
- relevance: 3 - severe and subtle, but only patches to the VMA core or a split hook can get it wrong
- words: 90

Between which two calls are a VMA's page tables safe to restructure during a
split or merge, which locks are held there, and which restructuring helpers
are called inside it? Start from `vma_prepare()`, `vma_complete()` and
`vma_adjust_trans_huge()`.

## vma.hooks-before-window: Hooks that run before the window opens

- section: Where page tables may be restructured during a split or merge
- relevance: 3 - a driver or filesystem author writes these hooks
- words: 80

Which hooks does a split call before the VMA and rmap locks are held, under
which lock do they run, and what must they leave for the window? Name one
in-tree implementation that gets it right. Start from `__split_vma()`.

## vma.window-lock-variant: Helpers with a caller-holds-the-locks variant

- section: Where page tables may be restructured during a split or merge
- relevance: 2 - one helper today
- words: 60

Is there a page table helper that normally takes its own locks and has a
variant for use inside the window, and how does the variant check that the
locks are held? Start from `hugetlb_split()` and `hugetlb_unshare_pmds()`.

## vma.window-not-excluded: Walkers the window does not exclude

- section: Where page tables may be restructured during a split or merge
- relevance: 3 - the locks look exhaustive and are not
- words: 40

Which page table walkers are not excluded by the locks held in that window,
and how does code that must exclude them do so?

## vma.window-rule: What to report about restructuring outside the window

- section: Where page tables may be restructured during a split or merge
- relevance: 3 - severe, but narrow
- words: 80

What should be reported about page table restructuring done from a split
hook, or before or after the window, and what that looks similar is fine?

## vma.mmap-write-lock-effect: What taking the mmap write lock changes

- section: What the mmap write lock does not exclude
- relevance: 5 - the misconception the whole section exists to correct
- words: 60

What does taking the mmap lock for write change that a per-VMA reader can
observe, and does an attempt to take a per-VMA read lock made afterwards still
succeed? If this tree has no per-VMA locks, say so and stop. Start from
`mmap_write_lock()` and `vma_start_read()`.

## vma.vma-write-lock-effect: What write-locking one VMA does

- section: What the mmap write lock does not exclude
- relevance: 5 - this is what actually excludes faults
- words: 80

What does write-locking a VMA do to readers already inside, to readers that
arrive while it waits, and to readers afterwards, and until when does that
last? Start from `vma_start_write()`.

## vma.vma-lock-only-operations: What runs under only a per-VMA lock

- section: What the mmap write lock does not exclude
- relevance: 5 - the list keeps growing as paths are converted
- words: 90

Which operations run holding only a per-VMA lock and not the mmap lock, and
can any of them free a page table? Through which functions? Start from
`lock_vma_under_rcu()` callers, `mm/madvise.c` and `zap_pte_range()`.

## vma.pmd-pointer-after-free: Is a PMD pointer still usable after a PTE table is freed

- section: What the mmap write lock does not exclude
- relevance: 4 - people argue "the pointer is still valid" to dismiss the race
- words: 50

After an operation under a per-VMA lock has freed a PTE table, is a pointer
to the PMD entry that pointed to it still valid memory, and is the same true
for a hugetlb VMA?

## vma.lockless-pmd-checks: Functions that read a PMD without a lock

- section: What the mmap write lock does not exclude
- relevance: 4 - these are the calls the race goes through
- words: 60

Which functions read a PMD without a lock to decide whether a range is still
valid or can be collapsed, and what does the in-tree caller that acts on the
result do first? Start from `check_pmd_still_valid()` and
`collapse_huge_page()`.

## vma.write-lock-rule: When relying on page table state under the mmap write lock is a bug

- section: What the mmap write lock does not exclude
- relevance: 5 - the race has shipped, and nothing in a diff shows it
- words: 100

When is it a bug for code that holds the mmap write lock to rely on page
table state it has read, and which in-tree code touches page tables under the
mmap write lock without write-locking the VMA and is fine? Start from
`kernel/events/uprobes.c` and `mm/ptdump.c`.

## vma.per-vma-conversion-check: Reviewing a conversion to per-VMA locking

- section: What the mmap write lock does not exclude
- relevance: 4 - this is the patch that introduces the bug
- words: 40

A patch converts a path from the mmap read lock to a per-VMA lock. What
should the reviewer go and look for elsewhere in the tree?

## vma.flags-helpers: What each flag helper does to existing bits and to the lock

- section: Helpers that change VMA flags
- relevance: 3 - every driver mmap handler uses these
- words: 110

For the helpers a driver or filesystem is likely to call to change a VMA's
flags, give a table: what happens to bits already set (kept, cleared,
replaced), and whether the helper takes the VMA write lock, only asserts it,
or ignores it. Start from `vm_flags_set()`, `vm_flags_reset()` and
`vm_flags_init()` in `include/linux/mm.h`.

## vma.flags-no-write-lock: Flags that may be set without the write lock

- section: Helpers that change VMA flags
- relevance: 2 - one flag today
- words: 40

May any VMA flag be set without the VMA write lock, through which helper, and
under what lock? Start from `vma_set_atomic_flag()`.

## vma.flags-replace-idiom: Replacing a VMA's whole flag set

- section: Helpers that change VMA flags
- relevance: 3 - the add-where-replace-was-meant mistake leaves stale permission bits
- words: 60

How does in-tree code replace a VMA's whole flag set, as opposed to adding
bits to it? Name a caller that shows it. Start from `mprotect_fixup()`.

## vma.flags-rule: What to report about flag changes

- section: Helpers that change VMA flags
- relevance: 3 - plausible in any driver
- words: 90

What should be reported about how code changes a VMA's flags, and which uses
are fine, such as from a driver's mmap hook on a VMA nobody else can see yet?

## vma.mmap-file-refs: The two file references during mmap

- section: Who owns the file reference when an mmap callback swaps the file
- relevance: 3 - needed to judge any hook that touches the file
- words: 60

During mmap, which file references exist, who owns each, and where is each
taken and dropped? Start from `ksys_mmap_pgoff()` and `__mmap_new_file_vma()`.

## vma.mmap-file-swap-hooks: Hooks that can replace the file

- section: Who owns the file reference when an mmap callback swaps the file
- relevance: 3 - drivers are being converted to the new hook now
- words: 80

Through which mmap hooks can a driver replace the file, does each run before
or after the VMA takes its own reference, and how does mm core notice the
replacement? Start from `call_mmap_prepare()` and `mmap_file()`.

## vma.mmap-file-swap-duty: What a hook that replaces the file must do

- section: Who owns the file reference when an mmap callback swaps the file
- relevance: 3 - a leaked file reference is silent
- words: 60

What must a hook that replaces the file do with the old reference and the new
one, and which helper does it safely? Name an in-tree hook that uses it. Start
from `vma_set_file()`.

## vma.mmap-file-rule: What to report about file references in mmap

- section: Who owns the file reference when an mmap callback swaps the file
- relevance: 3 - silent leak or use-after-free
- words: 70

What should be reported in an mmap hook, and in mm core, about references on
a replaced file, and what that looks similar is fine?

# Quick checks

## vma.mmap-lock-modes: Which mmap lock mode an operation needs

- group: mmap lock basics
- relevance: 1 - known to anyone patching mm; lockdep and asserts catch the wrong mode at once
- words: 60

Which kinds of operation need the mmap lock held for write, and which may run
under the read lock or only a per-VMA lock? Where is the mm lock order written
down? Start from `mm/rmap.c`.

## vma.killable-lock-return: mmap lock variants that can fail

- group: mmap lock basics
- relevance: 1 - "check the return value"; generic
- words: 40

Which mmap lock functions can return without the lock, and are they marked so
the compiler warns when the result is ignored? Start from
`mmap_write_lock_killable()`.

## vma.merge-anon-propagation: Where a merge passes on the anon rmap root

- group: merging and the anon rmap root
- relevance: 3 - the merge code has been rewritten recently
- words: 50

When a VMA that has never faulted merges with one that has, where is the anon
rmap root given to the survivor? Start from `dup_anon_vma()`.

## vma.merge-fork-test-side: Which VMA the merge-time fork test looks at

- group: merging and the anon rmap root
- relevance: 3 - checking the wrong side passes any test that faults both sides first
- words: 80

Which test decides whether a VMA was inherited across fork, what does it look
at, and in each case (only one side has an anon rmap root, only the other,
both) which VMA is it applied to? What should be reported? Start from
`is_mergeable_anon_vma()`.

## vma.rmap-tree-key: What the file rmap tree is keyed by

- relevance: 1 - one past bug; not a mistake people keep making
- words: 50

What is the per-file rmap interval tree keyed by, and why does passing a page
frame number to its iterators compile and then find the wrong VMAs? Start from
`mapping_rmap_tree_foreach()`.

## vma.modify-returns: How the modify functions report failure

- group: results of merge and modify
- relevance: 4 - every new caller in mprotect, madvise, mlock, mempolicy or userfaultfd meets this
- words: 50

How do the VMA modify functions report failure, and with which errors? Start
from `vma_modify_flags()` in `mm/vma.c`.

## vma.merge-returns: How the merge and copy functions report failure

- group: results of merge and modify
- relevance: 4 - NULL means two different things
- words: 60

How do the merge, extend and copy functions report failure, and how does a
caller tell "no merge was possible" from "out of memory"? Start from
`vma_merge_new_range()` and `copy_vma()`.

## vma.merge-frees-input: A successful merge may free the VMA it was given

- group: results of merge and modify
- relevance: 4 - use-after-free
- words: 50

On success, may the merge and modify functions return a different VMA from
the one passed in, and may they free the one passed in? Start from
`vma_merge_existing_range()`.

## vma.modify-cannot-fail: When a modify call cannot fail

- group: results of merge and modify
- relevance: 3 - explains the one caller that does not check
- words: 50

Is there a way for a modify call to be unable to fail, under what condition,
and which in-tree caller relies on it? Start from `vma_modify_flags_uffd()`.

## vma.merge-result-rule: What to report about using merge and modify results

- group: results of merge and modify
- relevance: 4 - the failure is a use-after-free or an error pointer dereference
- words: 70

What should be reported about how a caller stores and uses the result of a
merge or modify call, which in-tree callers that look wrong are fine, and
which caller gets it all right?

## vma.merge-flag-compare: How flags are compared when merging

- group: flags and merging
- relevance: 3 - explains why a late flag breaks merging
- words: 50

How are two VMAs' flags compared when deciding whether they can merge, and
which flags are left out of the comparison? Start from `is_mergeable_vma()`.

## vma.flags-before-merge: Where to add a flag so that it takes part in merging

- group: flags and merging
- relevance: 3 - subtle and silent
- words: 70

Where must a subsystem add its own flag to a new mapping so that it takes part
in the merge decision, and what should be reported about a flag added later?
Name an in-tree example of the right place. Start from `ksm_vma_flags()`.

## vma.merge-uprobe-side-effect: Completing a merge can install page table entries

- relevance: 1 - written from one fix
- words: 50

Can completing a VMA merge populate page table entries, and how does a caller
that is about to move those page tables suppress it? Start from
`vma_complete()`.

## vma.fork-cleared-flags: Flags cleared on the child at fork

- group: flags at fork
- relevance: 2 - the fact the next check depends on
- words: 50

Which VMA flags are cleared on the child's VMA during fork, where, and under
what condition? Start from `dup_mmap()` and `dup_userfaultfd()`.

## vma.fork-flag-tests: Fork-time tests of VMA flags

- group: flags at fork
- relevance: 2 - one known instance; could recur
- words: 60

When code that runs during fork tests a VMA flag to decide something for the
child, which VMA should it test, and when is testing the parent's fine? Start
from `vma_needs_copy()`.

## vma.vm-account-preservation: Clearing the accounting flag on a VMA that survives

- group: overcommit accounting
- relevance: 2 - a few sites; the leak is permanent and silent
- words: 70

Where is memory charged for a VMA given back at unmap, what gates it, and
what should be reported about code that clears the accounting flag on a VMA
that stays linked? Start from `do_vmi_munmap()` and `mm/mremap.c`.

## vma.unstable-mm-mark: Marking an mm that must not be trusted

- group: walking another mm
- relevance: 3 - ksm, khugepaged, swapoff, uprobes and procfs all walk other processes' mms
- words: 60

How is an mm whose fork failed, or that the OOM reaper is tearing down,
marked, and must a walker test for it before or after taking the mmap lock?
Start from `check_stable_address_space()`.

## vma.failed-fork-tree: What a failed fork leaves in the child's VMA tree

- group: walking another mm
- relevance: 3 - decides what a walker can run into
- words: 50

What does a failed fork leave in the child's VMA tree, and is the mm always
marked when that happens? Start from `dup_mmap()`.

## vma.foreign-mm-rule: What to report about walking another process's VMAs

- group: walking another mm
- relevance: 3 - new walkers keep being added
- words: 60

What should be reported about code that walks the VMAs of an mm that is not
the current task's, and which walkers are fine without the test? Start from
`unuse_mm()`.

## vma.lock-refcount-balance: Undoing the writer's mark when its wait is interrupted

- relevance: 1 - internal to the lock implementation
- words: 50

When a writer's wait for readers to drain can be interrupted, what must the
interrupted path undo? If the per-VMA lock here is not built on a reference
count, say so and stop. Start from `vma_start_write_killable()`.

## vma.address-as-boolean: Addresses used as "was this set"

- relevance: 0 - coding sense with no tree fact in it
- words: 30

Can a VMA start at address zero, and so why is testing an address for
non-zero the wrong way to ask "was this set"?

## vma.iterator-caches: What the VMA tree iterator caches

- group: iterator state and RCU
- relevance: 3 - the fact the next check depends on
- words: 50

What does the VMA tree's iterator state cache, what protects it, and which
calls reset it so it can be reused? Start from `struct ma_state` and
`mas_reset()`.

## vma.tree-state-rcu: Reusing iterator state after the RCU section ends

- group: iterator state and RCU
- relevance: 3 - a helper that drops RCU internally hides the unlock
- words: 70

Which helpers in the lockless VMA lookup leave the RCU read-side section
internally, and what should be reported about iterator state used afterwards?
When is reuse fine? Start from `vma_start_read()` and `lock_vma_under_rcu()`.

## vma.mm-struct-tail: The variable-size tail of the mm struct

- relevance: 1 - arch and boot code only
- words: 60

What must a statically defined mm use to reserve room for the per-CPU regions
packed after the struct, and which static definitions in this tree need it?
Start from `MM_STRUCT_FLEXIBLE_ARRAY_INIT`.

## vma.memfd-creation: Creating a memfd file

- relevance: 1 - one fix; new memfd-like interfaces are rare
- words: 50

Which helper creates a memfd file, and when is calling the plain shmem or
hugetlb file setup functions directly a bug? Start from `memfd_alloc_file()`.

## vma.assertion-accepts: What each locking assertion accepts

- group: lock assertions
- relevance: 3 - each per-VMA lock conversion has to fix assertions on the path
- words: 90

For each helper that asserts "this mm is locked" or "this VMA is locked or
stable", what does it accept: the mmap lock, a per-VMA lock, or either? Does
the answer change without per-VMA locks or without lockdep? Start from
`include/linux/mmap_lock.h`.

## vma.assertion-choice: Which assertion a path should use

- group: lock assertions
- relevance: 3 - the wrong one fires spuriously from the fault path
- words: 50

Which assertion should a path use when it can be reached under either the
mmap lock or a per-VMA lock, and what should be reported? Name an in-tree user.

## vma.commit-check-charges: The overcommit check also charges

- group: overcommit accounting
- relevance: 3 - mmap, brk, mremap, shmem and stack growth all use it
- words: 50

Does the overcommit check only test, or does it charge the pages when it
succeeds, and how is a charge given back? Start from
`security_vm_enough_memory_mm()`.

## vma.commit-accounting-rule: What to report about error paths after the overcommit check

- group: overcommit accounting
- relevance: 3 - an error path added later is an easy miss and leaks silently
- words: 60

What should be reported about a caller's error paths after a successful
overcommit check, and which callers show the safe forms?
