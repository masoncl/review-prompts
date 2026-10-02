# What `mm-vma.md` is trying to teach

A catalogue of the lessons in the hand-written `kernel/subsystem/mm-vma.md`,
made before rewriting its questions. Line numbers are that file's. "Asked by"
names the questions in `../mm-vma.md` that cover the lesson today. Rules are
stated as unsafe usage, with the correct usage that looks similar
where the guide gives one.

Kinds: **mechanism** (how something works), **contract** (what an interface
promises its callers), **usage** (what is unsafe, and what is
correct), **procedure** (what a reviewer should go and do), **hygiene**
(coding sense with no tree fact in it).

## 1. A VMA's memory and identity

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 1.1 | VMA memory is type-stable under RCU, not identity-stable: a freed VMA can be handed to another mm inside a read-side section | mechanism | 10-13 | `vma.rcu-slab` |
| 1.2 | The lockless lookup takes a reference first and only then can discover the VMA belongs to another mm | mechanism | 15-22 | `vma.rcu-lookup-steps` |
| 1.3 | Dropping a VMA read lock touches the mm *after* the reference is gone (to wake a waiting writer), so the mm has to outlive the drop | mechanism | 19-20 | `vma.rcu-release-touches-mm` |
| 1.4 | Unsafe: dropping the reference on a VMA whose mm is not the caller's without pinning that mm across the drop | usage | 21-27 | `vma.rcu-foreign-mm` |
| 1.5 | Tree iterator state is only good inside the RCU section, or lock hold, it was filled in; a helper that leaves RCU on its failure path hides the unlock | mechanism, usage | 269-272 | `vma.iterator-caches`, `vma.tree-state-rcu` |
| 1.6 | Another process's mm may be half-built by a failed fork or under the OOM reaper; it is marked, and the test belongs after taking the lock | mechanism, usage | 233-238 | `vma.unstable-mm-mark`, `vma.failed-fork-tree`, `vma.foreign-mm-rule` |

- 1.2: the guide's four steps leave out the two checks that catch reuse
  *within* the same mm (the second sequence check, the address range check).
- 1.4: the rule is scoped to three function names, which is one fix written
  down. The guide gives no correct usage that looks similar (the other drops
  in the same lookup; callers that hold their own mm).

## 2. What each lock excludes

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 2.1 | The mmap write lock does not exclude per-VMA readers; it only advances the mm's sequence count | mechanism | 107-110 | `vma.mmap-write-lock-effect` |
| 2.2 | Write-locking one VMA is what excludes them: it drains readers inside, refuses new ones, and holds until the mmap lock is dropped or downgraded | mechanism | 110-114 | `vma.vma-write-lock-effect` |
| 2.3 | What runs under only a per-VMA lock, and what it does to page tables: faults populate every level; one madvise can clear a PMD and free a PTE table | mechanism | 114-121 | `vma.vma-lock-only-operations` |
| 2.4 | A lockless PMD read is a hint. After a concurrent free the PMD *pointer* is still good, its value and the PTE table are not | mechanism | 123-135 | `vma.lockless-pmd-checks`, `vma.pmd-pointer-after-free` |
| 2.5 | Unsafe: holding the mmap write lock, reading page table state, and acting on it as stable before write-locking the VMA. Correct and similar: taking the page table lock and revalidating; a read-only dump that tolerates change | usage | 137-145 | `vma.write-lock-rule` |
| 2.6 | When a patch moves a path to per-VMA locking, go and find the mmap-write-lock holders that touch the same VMAs' page tables | procedure | 145-149 | `vma.per-vma-conversion-check` |
| 2.7 | Which lock mode a job needs: write for structural change and flags, read or per-VMA for lookup and faults; one flag may be set under a read lock; the lock order is written down in `mm/rmap.c` | contract | 180-187 | `vma.mmap-lock-modes`, `vma.flags-no-write-lock` |
| 2.8 | The killable lock variants can fail, and ignoring the result means running unlocked | contract | 188-191 | `vma.killable-lock-return` |
| 2.9 | Which assertion accepts which lock; a path reachable under either lock needs the one that accepts both | contract, usage | 285-293 | `vma.assertion-accepts`, `vma.assertion-choice` |
| 2.10 | A writer marks the VMA's reference count before waiting for readers, and an interrupted wait has to take the mark back off | mechanism | 259-264 | `vma.lock-refcount-balance` |

- 2.4: "the pointer stays valid" is not true for hugetlb, where unsharing
  detaches a whole PMD table. The guide does not say so.
- 2.6 is the only reviewer procedure in the guide. It is not a fact about the
  tree, so no question about the tree will produce it.
- 2.9 ends with "legacy `mmap_assert_locked()` in page table walk/zap paths is
  likely incorrect". That is a guess about the kernel, not knowledge.
- 2.10 is internal to three functions in one file.
- 2.1 to 2.5 are the heart of the guide. 2.7 to 2.9 repeat parts of them as
  quick checks.

## 3. Changing a VMA's range

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 3.1 | Split, merge and shrink share one sequence: VMA write lock, take the rmap locks, restructure page tables, write the new range, release | mechanism | 80-88 | `vma.range-change-functions`, `vma.split-merge-window` |
| 3.2 | The split-permission hook runs before any of those locks, so it may only validate | contract | 90-95 | `vma.hooks-before-window` |
| 3.3 | Unsharing, splitting or tearing down page tables for a split belongs between taking and releasing the rmap locks. That window excludes faults and rmap walks, not hardware walkers or GUP-fast | usage | 96-99 | `vma.window-rule`, `vma.window-not-excluded` |
| 3.4 | A helper that normally takes its own locks needs a caller-holds-the-locks form inside the window, and should assert them | usage | 100-103 | `vma.window-lock-variant` |
| 3.5 | Completing a merge also notifies uprobes, which installs page table entries; a caller about to move those tables has to suppress it | mechanism | 216-219 | `vma.merge-uprobe-side-effect` |

- The section has rules and no correct usage that looks similar.
- It does not mention the stack growers, which change a VMA's range without
  this sequence (they only grow it).
- 3.5 has one user in the tree.

## 4. Merge, modify and copy: what a caller must know

Five quick checks in the guide are about this one family of functions.

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 4.1 | Two failure conventions: the modify functions return an error pointer, never NULL; merge, extend and copy return NULL, never an error pointer; a separate test tells out-of-memory from "no merge possible" | contract | 205-207, 239-240, 248-250 | `vma.modify-returns`, `vma.merge-returns` |
| 4.2 | Success may hand back a different VMA and free the one passed in | contract | 207-208, 244-247 | `vma.merge-frees-input` |
| 4.3 | On failure the merge state's start, end and offset may be left changed | contract | 208-209 | **nobody** |
| 4.4 | Unsafe: putting the result straight into the only copy of the pointer (a struct member, a loop variable) before checking it; using the old pointer after success | usage | 239-243, 248-253 | `vma.merge-result-rule` |
| 4.5 | One call cannot fail: the userfaultfd variant over a whole VMA. One caller relies on it and does not check | contract | 253-258 | `vma.modify-cannot-fail` |
| 4.6 | Merging a never-faulted VMA with a faulted one has to pass the anon rmap root to the survivor | mechanism | 192-193 | `vma.merge-anon-propagation` |
| 4.7 | The inherited-across-fork test has to look at whichever side has an anon rmap root; the three cases are not symmetric | usage | 194-198 | `vma.merge-fork-test-side` |
| 4.8 | A flag that counts for merging has to be in the proposed flags before the merge decision; added later, the VMA never merges again, silently | usage | 211-215 | `vma.merge-flag-compare`, `vma.flags-before-merge` |

- 4.3 was lost when the questions were split up.
- 4.1, 4.2 and 4.4 are each stated two or three times in the guide.

## 5. What kind of VMA this is

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 5.1 | Anonymous means "no operations table". It says nothing about the file pointer | mechanism | 37-41 | `vma.anon-test` |
| 5.2 | A VMA can be anonymous and still have a file: a private mapping of the zero device | mechanism | 43-51 | `vma.anon-with-file` |
| 5.3 | A VMA can be non-anonymous and have no file: the special mappings | mechanism | 62-64 | `vma.anon-kinds` |
| 5.4 | Which test answers which question: the operations test for fault, collapse, huge page and page-offset decisions; the file pointer for the file reference, rmap locking and linkage, uprobes | usage | 53-61 | `vma.file-pointer-uses` |
| 5.5 | Unsafe: a file-pointer test standing in for the anonymous test. Correct and similar: a file-pointer test that is about the file | usage | 66-71 | `vma.anon-vs-file-rule` |
| 5.6 | The file rmap tree is keyed by page offset; a page frame number has the same C type and finds the wrong VMAs | usage | 199-204 | `vma.rmap-tree-key` |

- 5.2: "today nothing else does this" is wrong for this tree. Four GPU and
  accelerator drivers clear the operations table by hand.
- 5.6 is one past bug.

## 6. VMA flags

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 6.1 | The flag helpers differ in two ways: add, clear or replace; and take the VMA write lock, only assert it, or ignore it | contract | 153-159 | `vma.flags-helpers` |
| 6.2 | Unsafe: an add helper where a replace was meant. Stale permission bits survive | usage | 161-163 | `vma.flags-replace-idiom`, `vma.flags-rule` |
| 6.3 | The child's flags at fork are not the parent's: mlock bits always go, userfaultfd bits usually. A decision for the child tests the child's VMA. A combined mask can mix bits that differ with bits that do not | mechanism, usage | 220-226 | `vma.fork-cleared-flags`, `vma.fork-flag-tests` |
| 6.4 | Flags before the merge decision | | | see 4.8 |
| 6.5 | One flag may be set without the write lock | | | see 2.7 |
| 6.6 | The accounting flag has to survive on a VMA that survives | | | see 7.3 |

- 6.1: the guide knows one flags API. This tree has two, and the second one's
  plain helpers take no lock at all.
- 6.3: the "combined mask" sentence is cryptic. It means the mask fork uses to
  decide whether to copy page tables.

## 7. Who owns what: references and charges

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 7.1 | During mmap the caller and the new VMA each own a file reference. A callback's replacement file arrives with its own. Unsafe: taking another one unconditionally | mechanism, usage | 167-176 | `vma.mmap-file-refs`, `vma.mmap-file-swap-hooks`, `vma.mmap-file-swap-duty`, `vma.mmap-file-rule` |
| 7.2 | The overcommit check is not only a check: success has already charged the pages. Every later error path gives them back | contract, usage | 294-300 | `vma.commit-check-charges`, `vma.commit-accounting-rule` |
| 7.3 | The charge comes back at unmap only for a VMA that still carries the accounting flag. Unsafe: clearing the flag on a VMA that stays | usage | 227-232 | `vma.vm-account-preservation` |

- 7.1: the guide does not separate the two hooks. The descriptor hook runs
  before the VMA takes its reference and the legacy hook after, which is what
  decides who must do what. It does not name the helper that swaps a file
  safely.

## 8. Not about VMAs

| # | Lesson | Kind | Guide | Asked by |
|---|---|---|---|---|
| 8.1 | Address zero is a valid place for a VMA to start, so an address makes a bad "was this set" flag | hygiene | 265-268 | `vma.address-as-boolean` |
| 8.2 | The mm struct ends in a variable tail of per-CPU regions. A statically defined mm needs the macro that reserves it, and a new region means touching three places | contract | 273-279 | `vma.mm-struct-tail` |
| 8.3 | A memfd file has to come from the memfd helper, which adds security setup and file mode bits the plain shmem and hugetlb helpers do not | contract | 280-284 | `vma.memfd-creation` |

- 8.2 belongs with the mm struct and boot code. The tree has a static mm in a
  test that the guide does not list.
- 8.3 belongs with shmem or memfd.

## What the catalogue shows

- **It teaches hazards, not the subsystem.** Forty lessons, every one of the
  form "this goes wrong". It presupposes the map: what it means for a VMA to
  be attached or detached, the life of a VMA from allocation to free, what the
  tree and its iterator are, what the two rmap trees are for, why a range
  change needs rmap locks at all. A reader without that cannot place the
  hazards.
- **Three kinds of thing are mixed together**: how a mechanism works, what an
  interface promises, and an instruction to a reviewer. The six `REPORT as
  bugs` lines are the third kind. Restated as unsafe usage, only
  two of the six (2.5 and 5.5) also say what correct usage looks like.
- **Two themes carry the guide**: what each lock excludes (part 2) and what
  the merge and modify functions promise (part 4). Both are scattered: locking
  over one section and four quick checks, merge results over five quick
  checks that overlap.
- **About a third is one fix written as a rule**: 1.4 as scoped, 2.10, 3.5,
  5.6, 8.1, 8.2, 8.3. They name the functions of the fix, not a usage.
- **Wrong or unsupported as written**: 5.2 ("nothing else does this"), the
  last sentence of 2.9 ("likely incorrect"), 2.4 without its hugetlb
  exception.
- **Needed for these themes and absent** (all surfaced by builds against the
  tree): the second flags API; the drivers that make a VMA anonymous by hand;
  the order of the two mmap hooks and the safe file-swap helper; the stack
  growers; walkers that hold no mmap lock at all and free page tables; `/proc`
  readers that now run under the per-VMA lock.
- **Coverage today**: every lesson has at least one question except 4.3.
  Twenty-five lines of the question file still say "reported" or "a bug".
