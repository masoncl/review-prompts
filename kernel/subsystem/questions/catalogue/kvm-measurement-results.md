# What the kvm measurement found

Three models were asked the 90 questions in `kvm-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C. Reader C
is the most current, reader A is a release or so behind it, and reader B is
several releases behind that; which models they were does not matter here. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted below.

Readers A and C describe the mechanisms correctly nearly everywhere and miss
names and details. Reader B is out of date on whole mechanisms and had every one
of its 90 answers rewritten by 17% or more, so the build set was chosen by
importance to a reviewer and not only by dropping what readers know.

## What all three readers got wrong

Mostly names and layouts that have moved.

- **The invalidation bracket is start and end, not begin and end.** All three
  wrote kvm_mmu_invalidate_begin(), and readers A and C each said outright that
  they did not recognise `kvm_mmu_invalidate_start()`. The tree has only
  `kvm_mmu_invalidate_start()`, `kvm_mmu_invalidate_range_add()` and
  `kvm_mmu_invalidate_end()`. guest_memfd follows suit:
  `kvm_gmem_invalidate_start()`, not kvm_gmem_invalidate_begin().
- **`arch/x86/kvm/x86.c` has been split.** MSR handling is in
  `arch/x86/kvm/msrs.c` and register access in `arch/x86/kvm/regs.c` and
  `regs.h`. Two readers offered kvm_cache_regs.h, which does not exist.
- **Which architectures make `mmu_lock` an rwlock.** `KVM_HAVE_MMU_RWLOCK` is
  defined by x86, arm64, riscv and s390. Every reader left out at least riscv
  and s390, and reader B thought it was configuration dependent on x86.
- **Symbol exports.** `virt/kvm/` and `arch/x86/kvm/` export with
  `EXPORT_SYMBOL_FOR_KVM_INTERNAL()`, which expands to nothing when there are no
  vendor sub-modules, and `arch/x86/kvm/Makefile` fails the build on a stray
  `EXPORT_SYMBOL_GPL()` outside a short allowlist. Readers A and C had the macro
  names and the wrong scope; reader B said KVM has no export macro of its own.
- **The arm64 fault handler is no longer one function.** `user_mem_abort()`
  hands the snapshot, the frame lookup and the locked install to
  `kvm_s2_fault_get_vma_info()`, `kvm_s2_fault_pin_pfn()` and
  `kvm_s2_fault_map()`. All three put the steps in `user_mem_abort()` itself.
- **A child shadow page never starts invalid.** `kvm_mmu_child_role()` does
  `WARN_ON_ONCE(role.invalid)` and then clears the bit. Readers A and C said the
  bit is inherited as it is; reader B said it is always clear because a parent
  is always valid.
- **guest_memfd.** There is no kvm_arch_gmem_prepare() and no
  HAVE_KVM_ARCH_GMEM_PREPARE. `kvm_gmem_get_pfn()` calls
  `kvm_arch_gmem_make_private()` under `CONFIG_HAVE_KVM_ARCH_GMEM_CONVERT`, on
  every call for a private file and not only the first. Files hang off
  `gmem_file_list` in `struct gmem_inode`, not the mapping's private list, and
  reader B did not know `struct gmem_file` existed. Binding a range that is
  already bound returns `-EEXIST`; one reader said `-EBUSY` and one `-EINVAL`.
- **Why a kick uses the reschedule interrupt.** All three gave cost as the
  reason. The comment in `__kvm_vcpu_kick()` gives another: kicks are allowed
  with interrupts disabled, where the function call interrupt can deadlock.
  Two readers also had the waiting form guarantee that the target has left
  guest mode. Neither form does; only `KVM_REQ_OUTSIDE_GUEST_MODE` does.
- **The x86 generation flip** is in `__kvm_mmu_zap_all_fast_front_half()`, which
  the memslot flush path also reaches without going through
  `kvm_mmu_zap_all_fast()`.
- **vCPU ids** are made unique by the `vcpu_ids` bitmap under `kvm->lock` at the
  start of creation. Two readers credited the later `kvm_get_vcpu_by_id()`
  call, which is only a `WARN_ON_ONCE()`, and the third had neither.
- **Locking every vCPU.** `kvm_trylock_all_vcpus()` returns `-EINTR`; two
  readers said `-EBUSY` and the third had the helpers under other names. Both
  forms use the nest-lock annotation against `kvm->lock`.
- **Hardware enabling.** There is no kvm_rebooting. `kvm_shutdown()` calls
  `kvm_arch_shutdown()` (x86 sets `virt_rebooting`), and suspend, resume and
  shutdown are syscore callbacks. `kvm_create_vm()` always calls
  `kvm_enable_virtualization()`; the module parameter only adds a reference at
  load.
- **Registering on an I/O bus frees the old array with `call_srcu()`**, and
  `kvm_destroy_vm()` has an `srcu_barrier()` for it. Only unregister waits with
  `synchronize_srcu_expedited()`. Readers A and B said both wait; reader C
  hedged.
- **The review checklist.** Each reader padded
  `Documentation/virt/kvm/review-checklist.rst` with requirements it does not
  contain (reset and kexec handling, reserved fields, building on 32-bit hosts).
- **Lockless aging** is `CONFIG_KVM_MMU_LOCKLESS_AGING`, selected by x86 and
  s390. Two readers made it depend on a KVM_GENERIC_MMU_NOTIFIER symbol that
  does not exist; the notifier code is unconditional.

## What readers A and B got wrong as well

- The function that changes memslots is `kvm_set_memory_region()`, static in
  `virt/kvm/kvm_main.c`. Both named __kvm_set_memory_region(), which does not
  exist. Architecture code reaches it only through
  `kvm_set_internal_memslot()`.
- The vCPU ioctl hook that runs without `vcpu->mutex` is
  `kvm_arch_vcpu_unlocked_ioctl()`, not kvm_arch_vcpu_async_ioctl(), and it runs
  after `kvm_wait_for_vcpu_online()`, which waits on `vcpu->mutex` and not on
  `kvm->lock`.
- __gfn_to_pfn_memslot(), which both offered, and kvm_release_pfn_clean(),
  which reader B offered, are gone. A fault resolves a frame with
  `kvm_faultin_pfn()` or `__kvm_faultin_pfn()` and releases it with
  `kvm_release_faultin_page()` while `mmu_lock` is held.
- `slot->gmem.file` is a plain pointer with no reference, written under
  `slots_lock`. Reader A called it an RCU pointer and reader B had the slot hold
  a reference on the file.
- `kvm_mmu_memory_cache_alloc()` on an empty cache warns and falls back to an
  atomic allocation; it does not simply fail.
- The teardown order in `kvm_destroy_vm()`: buses, routing and coalesced MMIO go
  before the MMU notifier is unregistered, and nothing waits for an
  invalidation in progress.
- The test for an atomic page table entry update is
  `spte_needs_atomic_update()`, which ignores the Accessed bit. Reader A named
  spte_has_volatile_bits(), which does not exist, and both counted the Accessed
  bit.

## What only reader B got wrong

Reader B describes an older KVM:

- Memslots as an array with an id-to-index table, freed after a grace period.
  They are two sets per address space, indexed by an rbtree, an interval tree
  and a hash, and the old set becomes the inactive one.
- The write intent of the host address helpers, backwards: it said
  `gfn_to_hva()` does no write check and the read helpers use it.
- The lock order, with `kvm_lock` outermost and `kvm->lock` inside the vCPU
  mutex.
- A change_pte notifier callback, hardware enabling through
  kvm_arch_hardware_enable(), a pfn cache that pins its page and takes usage
  flags, `vcpu_load()` taking SRCU, the generic vCPU ioctl handler loading the
  vCPU, `KVM_REQ_UNBLOCK` as the request that is never recorded.
- Two of the three conditions in `is_page_fault_stale()` missing and one
  invented.
- Changing a slot's userspace address as a move, and its read-only flag as
  changeable. Both are rejected.

## What only reader C got wrong

- `kvm_vm_ioctl_set_pmu_event_filter()` as an example of waiting for SRCU under
  `kvm->lock`; it waits after unlocking.
- That `kvm_create_vm()` enables virtualization only when it was not enabled at
  load.
- That the TDP MMU raises `KVM_REQ_MMU_FREE_OBSOLETE_ROOTS` itself;
  `kvm_tdp_mmu_invalidate_roots()` only sets the bit and its caller raises the
  request.

## What the readers already knew

Readers A and C: the documentation map, the selftest layout, the VM list and
its lock, the memslot sets and lookup, the host address helpers and their error
values, the dirty bitmap, the dirty ring and its reset, the alignment checks
when clearing the dirty log, `vcpu_load()` and `vcpu_put()`, obsolete shadow
pages, `KVM_BUG_ON()`. Reader C also had the retry helpers, the pfn cache
refresh, `slots_arch_lock`, what SRCU protects, the memslot generation and the
memslot update flow essentially right. Reader B had no answer the checker left
alone.

## Where the hand-written guide is stale

- It says every memslot change must go through `kvm_set_memory_region()`. That
  function is static; the only entry for architecture code is
  `kvm_set_internal_memslot()`. `gfn_to_hva_many()`, which it lists beside the
  exported helpers, is static too.
- It says a shadow page linked under an invalid parent is created invalid, and
  builds three further points on that (the FIFO argument, the accounting
  asymmetry, the first of its reportable patterns). `kvm_mmu_child_role()` now
  warns and clears the bit.
- It places the generation flip in `kvm_mmu_zap_all_fast()`; it is in
  `__kvm_mmu_zap_all_fast_front_half()`.
- It says a pfn cache refresh must recheck the sequence after pinning the page.
  The cache takes no pin and drops its reference once valid; the refresh checks
  `mn_active_invalidate_count` and then `mmu_invalidate_seq`, because caches are
  invalidated before `mmu_invalidate_in_progress` is raised.
- Its dirty ring section describes flushing a full ring into a backup bitmap.
  No such flow exists. A full ring stops the vCPU with
  `KVM_REQ_DIRTY_RING_SOFT_FULL`; the bitmap that can accompany a ring takes
  writes made with no running vCPU.
- It says public and private memslots must not overlap and that the check
  belongs in the memory region ioctl. Overlap in guest frame space is rejected
  for every slot by the same check; guest_memfd adds a second one on the file
  range in `kvm_gmem_bind()`.
- It gives `arch/arm64/kvm/` as the home of `slots_arch_lock`. Only x86 and s390
  take it.
- It says readers of memslots need a non-preemptible or RCU-protected
  environment. The protection is SRCU, and readers may sleep.
- It forbids extra barriers around `kvm_make_request()`. They are redundant, not
  unsafe.
- Its `REPORT as bugs` lines are instructions to the reviewer, not facts about
  the code; the built guide states the unsafe usage and the correct one.

Its account of the retry sequence, of `is_page_fault_stale()`, of the write
intent of the host address helpers, of the SRCU and mutex rule and of updating
hardware-written page table entries is still right, and those are kept.

## What was left out of the build set

The hand-written guide is 2,152 words, so the build set is 42 of the 90
questions. It keeps the hand-written guide's subjects and adds a file map and
the helper families the readers had under old names. Left out, by reason:

- Readers A and C answer them and the hand-written guide did not cover them:
  the documentation map, the selftests, the memslot structure, generation and
  lookup, the error values, reading and writing guest memory, the dirty bitmap,
  the dirty ring and its reset, the alignment checks, `vcpu_load()` and
  `vcpu_put()` themselves, the scheduler callbacks, the vCPU mode, the request
  functions and flags, blocking, guest entry accounting, the SRCU helpers, the
  VM list.
- Caught by the compiler or by lockdep, so the entry points table or a
  neighbouring answer carries the name: locking every vCPU, releasing a
  faulted-in page, mapping a guest page, the architecture hooks, the
  configuration symbols, capabilities, in-kernel devices.
- Too narrow, or too long, for a guide loaded on every KVM patch: the table of
  fields in `struct kvm`, what each SRCU protects, the notifier walker, slots in
  the middle of being deleted, hardware enabling, the VM destruction order, VM
  references, finding a vCPU, the I/O bus, irqfd, aging, remote TLB flushes, the
  host address to frame paths, invalidating pfn caches, guest_memfd objects,
  binding and invalidation, memory attributes, the private and shared mismatch
  exit, shadow page accounting, zapping an in-use root.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A          209        27%     27     24   6.12 to 6.18
reader-B          241        77%      0     88   6.7 to 6.13
reader-C          139        16%     49      5   6.12 to 6.19

question                         reader-A      reader-B      reader-C   verdict
kvm.core-files                    7% ( 2)      82% ( 2)      11% ( 4)   weak: reader-B
kvm.entry-points                  3% ( 1)      17% ( 3)      18% ( 3)   middling
kvm.docs                          0% ( 0)      32% ( 1)       0% ( 0)   middling
kvm.arch-hooks                   19% ( 3)      70% ( 3)      86% ( 4)   weak: reader-B, reader-C
kvm.kconfig-options              15% ( 1)      84% ( 6)      11% ( 4)   weak: reader-B
kvm.selftests                     0% ( 0)      64% ( 4)       0% ( 0)   weak: reader-B
kvm.symbol-exports               64% ( 4)      85% ( 3)      49% ( 3)   all weak
kvm.struct-kvm-fields            28% ( 5)      52% ( 8)       4% ( 1)   weak: reader-B
kvm.vm-refcount                  12% ( 1)      74% ( 1)      24% ( 1)   weak: reader-B
kvm.vm-destroy-order             48% ( 3)      85% ( 4)      13% ( 1)   weak: reader-A, reader-B
kvm.vcpu-create                  40% ( 3)      81% ( 2)      39% ( 2)   weak: reader-A, reader-B
kvm.vcpu-lookup                  26% ( 2)      82% ( 5)       6% ( 1)   weak: reader-B
kvm.vcpu-ioctl-dispatch          49% ( 3)      85% ( 2)      13% ( 3)   weak: reader-A, reader-B
kvm.vm-dead-bugged                6% ( 1)      77% ( 2)       7% ( 1)   weak: reader-B
kvm.devices                      36% ( 1)      77% ( 1)      25% ( 4)   weak: reader-B
kvm.lock-order                   49% ( 6)      73% ( 8)      36% ( 4)   weak: reader-A, reader-B
kvm.srcu-vs-mutexes              34% ( 1)      75% ( 2)      10% ( 2)   weak: reader-B
kvm.slots-arch-lock              42% ( 2)      74% ( 3)       0% ( 0)   weak: reader-A, reader-B
kvm.srcu-protected-data          42% ( 4)      85% ( 2)       2% ( 1)   weak: reader-A, reader-B
kvm.vcpu-srcu-helpers             1% ( 1)      75% ( 2)      14% ( 1)   weak: reader-B
kvm.mmu-lock-type                29% ( 3)      75% ( 3)      30% ( 3)   weak: reader-B
kvm.mmu-lock-sleeping            25% ( 2)      77% ( 1)      13% ( 2)   weak: reader-B
kvm.vm-list-walking               0% ( 0)      79% ( 1)       0% ( 0)   weak: reader-B
kvm.hardware-enable              44% ( 3)      85% ( 2)      25% ( 3)   weak: reader-A, reader-B
kvm.lock-all-vcpus               11% ( 2)      85% ( 1)      23% ( 2)   weak: reader-B
kvm.notifier-memslot-sync        10% ( 1)      87% ( 1)      10% ( 0)   weak: reader-B
kvm.memslot-struct               33% ( 3)      74% ( 7)       3% ( 1)   weak: reader-B
kvm.memslots-sets                 4% ( 1)      72% ( 3)       5% ( 1)   weak: reader-B
kvm.memslot-generation           16% ( 3)      91% ( 3)       0% ( 0)   weak: reader-B
kvm.memslot-lookup               15% ( 1)      76% ( 2)      15% ( 1)   weak: reader-B
kvm.memslot-update-entry         35% ( 3)      74% ( 5)      14% ( 2)   weak: reader-B
kvm.memslot-validation           38% ( 3)      75% ( 4)      22% ( 2)   weak: reader-B
kvm.memslot-flag-mutability      13% ( 1)      72% ( 2)       6% ( 1)   weak: reader-B
kvm.memslot-update-flow          36% ( 5)      81% ( 7)       0% ( 0)   weak: reader-B
kvm.memslot-invalid-flag         23% ( 1)      78% ( 3)       3% ( 1)   weak: reader-B
kvm.memslot-readers-usage        22% ( 1)      85% ( 3)      18% ( 2)   weak: reader-B
kvm.hva-helpers                   5% ( 1)      70% ( 5)       0% ( 1)   weak: reader-B
kvm.hva-write-intent-usage       25% ( 2)      79% ( 1)       8% ( 2)   weak: reader-B
kvm.error-values                 12% ( 3)      81% ( 1)       4% ( 1)   weak: reader-B
kvm.pfn-helpers                  23% ( 4)      89% ( 1)      11% ( 1)   weak: reader-B
kvm.faultin-release               7% ( 0)      78% ( 5)       8% ( 1)   weak: reader-B
kvm.hva-to-pfn-paths             29% ( 4)      76% ( 1)      14% ( 1)   weak: reader-B
kvm.guest-read-write             23% ( 4)      73% ( 1)      26% ( 2)   weak: reader-B
kvm.vcpu-map                     56% ( 3)      78% ( 1)      24% ( 1)   weak: reader-A, reader-B
kvm.pfn-cache-api                11% ( 4)      69% ( 4)      27% ( 2)   weak: reader-B
kvm.pfn-cache-refresh            29% ( 1)      92% ( 2)       0% ( 0)   weak: reader-B
kvm.pfn-cache-invalidate         38% ( 1)      75% ( 2)      17% ( 1)   weak: reader-B
kvm.notifier-callbacks           49% ( 4)      84% ( 8)       4% ( 2)   weak: reader-A, reader-B
kvm.invalidate-state             28% ( 3)      91% ( 2)      21% ( 3)   weak: reader-B
kvm.retry-helpers                34% ( 2)      88% ( 2)       1% ( 1)   weak: reader-B
kvm.fault-sequence               45% ( 2)      88% ( 3)      12% ( 1)   weak: reader-A, reader-B
kvm.retry-usage                  35% ( 2)      65% ( 1)       8% ( 1)   weak: reader-B
kvm.x86-fault-stale              17% ( 7)      89% ( 4)      21% ( 3)   weak: reader-B
kvm.other-invalidators           22% ( 3)      89% ( 1)      25% ( 2)   weak: reader-B
kvm.aging                        37% ( 3)      86% ( 1)      29% ( 2)   weak: reader-B
kvm.tlb-flush                    24% ( 1)      77% ( 1)      13% ( 2)   weak: reader-B
kvm.long-loops                   36% ( 4)      88% ( 1)      20% ( 1)   weak: reader-B
kvm.gmem-objects                 51% ( 4)      93% ( 3)      24% ( 1)   weak: reader-A, reader-B
kvm.gmem-bind                    55% ( 4)      85% ( 1)      33% ( 2)   weak: reader-A, reader-B
kvm.gmem-get-pfn                 53% ( 2)      81% ( 1)      29% ( 2)   weak: reader-A, reader-B
kvm.gmem-invalidate              58% ( 2)      87% ( 1)      41% ( 2)   all weak
kvm.mem-attributes               47% ( 1)      86% ( 1)      25% ( 1)   weak: reader-A, reader-B
kvm.private-fault                46% ( 1)      93% ( 1)      21% ( 0)   weak: reader-A, reader-B
kvm.dirty-mark                   26% ( 3)      77% ( 4)      20% ( 3)   weak: reader-B
kvm.dirty-bitmap                  3% ( 1)      74% ( 3)       2% ( 1)   weak: reader-B
kvm.dirty-clear-checks            0% ( 0)      65% ( 2)       0% ( 0)   weak: reader-B
kvm.dirty-ring                    0% ( 1)      69% ( 3)       3% ( 1)   weak: reader-B
kvm.dirty-ring-reset              7% ( 1)      68% ( 2)      10% ( 1)   weak: reader-B
kvm.dirty-ring-with-bitmap       10% ( 1)      75% ( 1)       9% ( 1)   weak: reader-B
kvm.vcpu-load-put                 0% ( 1)      73% ( 3)      17% ( 2)   weak: reader-B
kvm.vcpu-load-usage              30% ( 3)      82% ( 3)      23% ( 1)   weak: reader-B
kvm.preempt-notifiers            36% ( 3)      86% ( 2)      32% ( 1)   weak: reader-B
kvm.vcpu-mode                    37% ( 3)      89% ( 1)      19% ( 1)   weak: reader-B
kvm.requests-api                 31% ( 2)      84% ( 3)      26% ( 1)   weak: reader-B
kvm.request-flags                29% ( 1)      84% ( 5)       0% ( 0)   weak: reader-B
kvm.kick                         43% ( 3)      87% ( 2)      30% ( 2)   weak: reader-A, reader-B
kvm.request-usage                52% ( 3)      67% ( 2)      42% ( 4)   all weak
kvm.blocking                     46% ( 1)      84% ( 2)      12% ( 1)   weak: reader-A, reader-B
kvm.guest-entry-exit             32% ( 2)      79% ( 2)      15% ( 1)   weak: reader-B
kvm.io-bus                       41% ( 5)      77% ( 5)       5% ( 1)   weak: reader-A, reader-B
kvm.irqfd                        22% ( 4)      76% ( 6)      20% ( 3)   weak: reader-B
kvm.x86-obsolete-pages            2% ( 1)      48% ( 2)       5% ( 1)   weak: reader-B
kvm.x86-shadow-page-invalid      27% ( 3)      54% ( 2)       3% ( 1)   weak: reader-B
kvm.x86-child-role               27% ( 1)      49% ( 1)      26% ( 2)   weak: reader-B
kvm.x86-shadow-accounting        13% ( 1)      66% ( 2)       0% ( 0)   weak: reader-B
kvm.x86-zap-root                  0% ( 0)      78% ( 1)      42% ( 1)   weak: reader-B, reader-C
kvm.x86-spte-atomic              72% ( 4)      85% ( 3)      10% ( 1)   weak: reader-A, reader-B
kvm.new-features                 68% ( 6)      79% ( 5)      37% ( 4)   weak: reader-A, reader-B
kvm.warn-usage                   44% ( 4)      84% ( 4)      30% ( 4)   weak: reader-A, reader-B
kvm.capabilities                 33% ( 2)      79% ( 2)      34% ( 0)   weak: reader-B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `kvm.gmem-objects`, `kvm.gmem-bind`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `kvm.struct-kvm-fields`, `kvm.vm-refcount`, `kvm.srcu-protected-data`, `kvm.memslot-struct`, `kvm.memslot-invalid-flag`, `kvm.error-values`, `kvm.faultin-release`, `kvm.notifier-callbacks`, `kvm.tlb-flush`, `kvm.mem-attributes`, `kvm.dirty-bitmap`, `kvm.dirty-ring`, `kvm.vcpu-load-put`, `kvm.vcpu-mode`, `kvm.requests-api`.

## Questions reorganised

- 61 questions became 55, grouped by subject: locks and SRCU, VMs and vCPUs, requests and kicks,
  memslots, guest frame translation, invalidation and the retry protocol, x86 shadow pages, dirty
  tracking, private memory. `kvm.new-features` moved to the orientation part.
- Merged: `kvm.memslots-sets` + `kvm.memslot-struct` to `kvm.memslot-layout`;
  `kvm.memslot-validation` + `kvm.memslot-flag-mutability` to `kvm.memslot-change-rules`;
  `kvm.pfn-helpers` + `kvm.faultin-release` to `kvm.faultin-pfn`; `kvm.vcpu-load-put` +
  `kvm.vcpu-load-usage` to `kvm.vcpu-load`; `kvm.x86-shadow-page-invalid` + `kvm.x86-child-role` to
  `kvm.x86-invalid-pages`; `kvm.gmem-objects` + `kvm.gmem-bind` to `kvm.gmem-files-bindings`.
- No question was dropped whole. What went were the inventories inside them: the error returned by
  each memory region check, the fields of a memslot and of the role a child inherits, the steps of
  `vcpu_load()` in order. `kvm.struct-kvm-fields` stays as a table of state against lock, which is
  what a review looks up, and no longer asks for groups of fields.
