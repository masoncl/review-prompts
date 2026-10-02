# KVM Subsystem

## Main structures

### Objects and how they relate

- `struct kvm` lifetime: one counter, `refcount_t users_count`; `kvm_get_kvm()`
  and `kvm_put_kvm()` act on it. There is no separate fd count.
- `struct kvm_vcpu`: closing the vCPU fd frees nothing; `kvm_vcpu_release()`
  only drops the VM reference. vCPUs are freed by `kvm_destroy_vcpus()`, which
  each arch calls from its VM-destroy path.
- `vcpu->mutex`: not held for every vCPU ioctl. `kvm_vcpu_ioctl()` first calls
  `kvm_arch_vcpu_unlocked_ioctl()`, which runs without it; for example
  `KVM_INTERRUPT` on riscv, and `KVM_MEMORY_ENCRYPT_OP` on x86 when
  `vcpu_mem_enc_unlocked_ioctl` is set.
- `struct kvm_device`: two lifetimes. With a `release` op the device is freed
  when its fd closes (`kvm_device_release()`), for example `kvm_vfio_ops` in
  `virt/kvm/vfio.c`. Without one it stays on `kvm->devices` until
  `kvm_destroy_devices()` calls `destroy`.
- ioeventfd: `struct kvm_ioeventfd` is only the uapi ioctl argument. The
  in-kernel object is `struct _ioeventfd` in `virt/kvm/eventfd.c`; it embeds a
  `struct kvm_io_device` and is one entry on a `struct kvm_io_bus`.
- `struct kvm_io_bus`: published in `kvm->buses[]` under `kvm->srcu`, the same
  SRCU as memslots; register and unregister build a new bus under
  `kvm->slots_lock`.
- MMU notifier: there is no struct kvm_mmu_notifier. One `struct mmu_notifier`
  is embedded in `struct kvm` as `mmu_notifier`; see `mmu_notifier_to_kvm()` in
  `virt/kvm/kvm_main.c`.
- `struct kvm_memslots`: two sets per address space, embedded in `struct kvm`
  as `__memslots[][2]`; `kvm->memslots[]` points at the active one. No set is
  allocated per update.
- `struct kvm_memory_slot`: one object is linked into both sets at once,
  through `id_node[2]`, `hva_node[2]` and `gfn_node[2]`, indexed by
  `node_idx`. A changed slot is a new object; the old one is freed after the
  swap, by `kvm_commit_memory_region()`.
- `kvm_memslots()`: returns address space 0 only. `kvm_vcpu_memslots()` picks
  the vCPU's current space; `__kvm_memslots()` takes an `as_id`.
- x86 address spaces: `kvm_arch_nr_memslot_as_ids()` is 2 only under
  `CONFIG_KVM_SMM` and only for a VM without private memory; a VM with
  `kvm->arch.has_private_mem` has one. Other architectures have one.
- guest_memfd scope: not limited to confidential VMs. `CONFIG_KVM_GUEST_MEMFD`
  is selected by arm64 KVM and by x86 KVM on `CONFIG_X86_64`.
  `GUEST_MEMFD_FLAG_MMAP` and `GUEST_MEMFD_FLAG_INIT_SHARED` make the file
  shared, userspace-mappable guest memory.
- guest_memfd objects, in `virt/kvm/guest_memfd.c`: `struct gmem_inode` is the
  backing storage; `struct gmem_file` is one VM's view of it and holds
  `bindings`, an xarray from file page offset to `struct kvm_memory_slot`.
- `KVM_MEM_GUEST_MEMFD` slot: has both `userspace_addr` and `gmem.file`. On
  x86 `fault->is_private` picks the backing per fault, and a fault where it
  differs from the gfn's `KVM_MEMORY_ATTRIBUTE_PRIVATE` attribute
  (`kvm_mem_is_private()`) fails with `-EFAULT`. A slot with
  `KVM_MEMSLOT_GMEM_ONLY` uses guest_memfd for every fault; arm64 accepts only
  such guest_memfd slots.
- guest_memfd invalidation: does not come through the `struct mmu_notifier`,
  whose range callbacks are hva-based and pass `KVM_FILTER_SHARED`, set in
  `kvm_handle_hva_range()`.
  `kvm_gmem_punch_hole()` and `kvm_gmem_release()` reach
  `kvm_mmu_invalidate_start()` and `kvm_mmu_invalidate_end()` through
  `__kvm_gmem_invalidate_start()` and `__kvm_gmem_invalidate_end()`, so
  fault paths retry on the same `mmu_invalidate_seq`.
- `struct gfn_to_hva_cache`: not a `struct gfn_to_pfn_cache`. It caches gfn to
  hva for one memslot generation and has no link to the MMU notifier; x86
  steal time and async-PF data use it.
- `kvm_lock`: a mutex, defined in `virt/kvm/kvm_main.c`; it guards `vm_list`.
- s390 file layout: the sources are in `arch/s390/kvm/s390/` (for example
  `arch/s390/kvm/s390/s390.c`) and `arch/s390/kvm/gmap/`. `arch/s390/kvm/`
  itself holds only `Makefile` and `Kconfig`, and the arch structures are in
  `arch/s390/include/asm/kvm_host_s390.h`.
- x86 TDX mirror tables: a `struct kvm_mmu_page` with `role.is_mirror` is KVM's
  copy of a page table that the TDX module owns (`external_spt`). `struct
  kvm_mmu` carries `mirror_root_hpa` beside the direct root. SPTE changes are
  pushed through the `set_external_spte` op, and a removed page table through
  `free_external_spt`; see `arch/x86/kvm/mmu/tdp_mmu.c`.

## Where to look

**Core files**

| Job | File in this tree |
|---|---|
| x86 MSR handling | `arch/x86/kvm/msrs.c` and `arch/x86/kvm/msrs.h`, not `arch/x86/kvm/x86.c`: `kvm_set_msr_common()`, `kvm_get_msr_common()`, `kvm_vm_ioctl_set_msr_filter()`, `kvm_set_user_return_msr()`, `kvm_emulate_rdmsr()`, `kvm_get_set_one_reg()` |
| x86 register access | `arch/x86/kvm/regs.h` for the inline register-cache accessors and mode tests such as `is_guest_mode()`; `arch/x86/kvm/regs.c` for `kvm_set_cr0()`, `kvm_set_cr4()`, `kvm_set_dr()`, `kvm_get_rflags()` and the regs and sregs ioctl handlers. There is no kvm_cache_regs.h in this tree |
| guest_memfd | `virt/kvm/guest_memfd.c`; its KVM-internal declarations are in `virt/kvm/guest_memfd.h`, not `virt/kvm/kvm_mm.h` |
| Async page faults, x86 side | split over `arch/x86/kvm/x86.c`, `arch/x86/kvm/mmu/mmu.c` (`kvm_arch_setup_async_pf()`, `kvm_arch_async_page_ready()`) and `arch/x86/kvm/msrs.c` (`kvm_pv_enable_async_pf()`) |
| Other generic and x86 KVM code | `virt/kvm/Makefile.kvm` and `arch/x86/kvm/Makefile` give the object lists |

**Entry points**

| Job | Start reading at |
|---|---|
| Dispatch a vCPU ioctl | `kvm_vcpu_ioctl()` in `virt/kvm/kvm_main.c`; the arch hooks are `kvm_arch_vcpu_unlocked_ioctl()` first, then `kvm_arch_vcpu_ioctl()`. There is no kvm_arch_vcpu_async_ioctl() here |
| Read the dirty log, bitmap | `kvm_vm_ioctl_get_dirty_log()`. With `CONFIG_KVM_GENERIC_DIRTYLOG_READ_PROTECT` (x86 and arm64, for example, select it) it is in `virt/kvm/kvm_main.c` and leads to `kvm_get_dirty_log_protect()`; without it the arch defines it, for example s390 through `kvm_get_dirty_log()` |
| Read the dirty log, ring | `kvm_vcpu_fault()` and `kvm_vm_ioctl_reset_dirty_pages()` in `virt/kvm/kvm_main.c`; `kvm_dirty_ring_push()` is the producer side |
| Guest frame to host page, x86 | `kvm_mmu_faultin_pfn()` in `arch/x86/kvm/mmu/mmu.c`, reached from `kvm_mmu_page_fault()` through `kvm_mmu_do_page_fault()`. x86 does not call `kvm_faultin_pfn()` |
| Guest frame to host page, arm64 | `kvm_handle_guest_abort()` in `arch/arm64/kvm/mmu.c`, which picks `pkvm_mem_abort()`, `gmem_abort()` or `user_mem_abort()`; the `__kvm_faultin_pfn()` call is in `kvm_s2_fault_pin_pfn()` |
| Make a request of a vCPU | `kvm_make_request()` in `include/linux/kvm_host.h`; `kvm_vcpu_kick()` is an inline over `__kvm_vcpu_kick()` in `virt/kvm/kvm_main.c`; `kvm_make_request_and_kick()` does both |
| Create a VM, create a vCPU, dispatch a VM ioctl, set a memory region, handle an MMU notifier invalidation | all are in `virt/kvm/kvm_main.c` |

**Symbol exports**

- `EXPORT_SYMBOL_FOR_KVM_INTERNAL()`: usable only by the modules named in
  `KVM_SUB_MODULES`; `kvm` itself is not in that list.
- `KVM_SUB_MODULES` on x86: whichever of `kvm-amd` and `kvm-intel` is built as
  a module; see `arch/x86/include/asm/kvm_types.h`.
- `EXPORT_SYMBOL_GPL()`: allowed only on lines that contain one of the seven
  names in `exports_grep_trailer` in `arch/x86/kvm/Makefile`; any GPL module
  can use those symbols.
- The seven names: `kvm_get_kvm()`, `kvm_get_kvm_safe()`, `kvm_put_kvm()`, and
  the four page-track exports in `arch/x86/kvm/mmu/page_track.c`.
- `EXPORT_SYMBOL_FOR_KVM()`: not used under `virt/kvm/` or `arch/x86/kvm/`; it
  is for kernel code outside the KVM modules and exports to `kvm` plus
  `KVM_SUB_MODULES`.
- `EXPORT_SYMBOL_FOR_KVM()` with `KVM_SUB_MODULES` defined: exports even when
  `kvm` is built in.
- `EXPORT_SYMBOL_FOR_KVM()` without `KVM_SUB_MODULES`: empty on x86, and
  elsewhere empty unless `CONFIG_KVM` is a module.
- There is no EXPORT_SYMBOL_GPL_FOR_KVM_INTERNAL macro in this tree.
- Build check: `check_kvm_exports` in `arch/x86/kvm/Makefile` stops the build
  with `$(error ...)` when make reads that Makefile.
- Build check scope: runs only under `ifdef CONFIG_KVM_X86`, and scans `*.c`
  and `*.h` under both `virt/kvm` and `arch/x86/kvm`.
- Build check method: a whole-word text grep for `EXPORT_SYMBOL_GPL` and
  `EXPORT_SYMBOL`, so a comment that contains either word also fails the build.
- Not caught by the check: `.S` files, and any other macro, for example
  `EXPORT_SYMBOL_NS_GPL()` or a direct `EXPORT_SYMBOL_FOR_MODULES()`.
- A new `EXPORT_SYMBOL_GPL()` export for a non-KVM module needs its name added
  to `exports_grep_trailer` in the same patch.

**New guest-visible features**

- Not in the checklist: reset or kexec survival, unsharing host and guest
  memory, zero-checking flags or padding, argument validation, compat
  handling, MSR index lists, `scripts/checkpatch.pl`.
- Item 1: cites `Documentation/process/coding-style.rst` and
  `Documentation/process/submitting-patches.rst` only.
- Item 3 applies when a patch "introduces or modifies" a userspace API, not
  only when it adds one.
- Item 5: performance improvements "can and should default to on"; only
  features default to off.
- Item 6: new CPU features "should be exposed via" KVM_GET_SUPPORTED_CPUID2
  "or its equivalent for non-x86 architectures"; that name is defined nowhere
  in the tree, the ioctl is `KVM_GET_SUPPORTED_CPUID`.
- Items 8 and 9: changes "should be vendor neutral when possible", and common
  and arch-independent code is preferred; nothing requires a feature to work
  or be tested on every vendor.
- Item 10: user/kernel and guest/host interfaces "must be 64-bit clean":
  naturally aligned on 64-bit, `u64` rather than `ulong`.
- Item 11: a guest-visible feature must be documented in a hardware manual or
  come with documentation; the item names no location for it.
- Tests: item 7 says "should be testable"; the testing section asks for "some
  kind of tests and/or enablement in open source guests and VMMs", not
  selftests specifically.
- Maintainers "reserve the right to require more tests" and may waive the
  requirement.
- New hardware features (new registers, no new APIs): tested via
  kvm-unit-tests; selftests can be used instead in some cases, or for
  save/restore corner cases.
- New APIs: the submitter demonstrates the use case; selftests cover API
  corner cases, and basic host and guest operation if no open source VMM uses
  the feature.
- Bigger host-plus-guest features: supported by Linux guests, except Hyper-V
  features testable on Windows guests; selftests cover at least API error
  cases.

## Locks and SRCU

**Mutex acquisition order**

- Global chain, outer to inner: `kvm_usage_lock` → `cpus_read_lock()` →
  `kvm_lock`.
- `kvm->lock` is outside `vcpu->mutex`, not the reverse.
- `kvm_enable_virtualization()` in `virt/kvm/kvm_main.c`: holds
  `kvm_usage_lock` across `cpuhp_setup_state()`; `__cpuhp_setup_state()` in
  `kernel/cpu.c` takes `cpus_read_lock()`.
- `kvm_usage_lock`: static in `virt/kvm/kvm_main.c`, defined only under
  `CONFIG_KVM_GENERIC_HARDWARE_ENABLING`; `kvm_suspend()` and `kvm_resume()`
  assert it is not held.
- `kvm_lock_all_vcpus()` and `kvm_trylock_all_vcpus()`: assert `kvm->lock` and
  take each `vcpu->mutex` with `kvm->lock` as nest lock.
- `kvm_create_vm()`: only initialises the mutexes; there is no lockdep priming
  of the chain there or elsewhere in the kvm directories.
- `kvm_swap_active_memslots()`: has no assertion on `slots_arch_lock`; it only
  unlocks it. `kvm_set_memslot()` takes it, inside `slots_lock`.

**VM state and its locks**

| State | Field | Protection |
|---|---|---|
| vCPU array | `vcpu_array` (xarray; `struct kvm` has no `vcpus` array) | insert under `kvm->lock`; lockless read bounded by `online_vcpus` |
| notifier count | `mn_active_invalidate_count` | `mn_invalidate_lock` (spinlock) |
| notifier sequence | `mmu_invalidate_seq`, `mmu_invalidate_in_progress`, range | `mmu_lock` held for write |
| pfn cache list | `gpc_list` | `gpc_lock`, a spinlock |
| dirty bitmap bits | `dirty_bitmap` of a memslot | set with `set_bit_le()`, no lock |
| dirty ring mode | `dirty_ring_size` / `dirty_ring_with_bitmap` | written under `kvm->lock` / `slots_lock` |
| liveness flags | `vm_dead`, `vm_bugged` | none |

- `mn_active_invalidate_count`: read without `mn_invalidate_lock` by
  `mmu_notifier_retry_cache()` in `virt/kvm/pfncache.c`; pfn caches are
  invalidated before `mmu_lock` is taken, so they cannot use
  `mmu_invalidate_in_progress`.
- Dirty bitmap: `mark_page_dirty_in_slot()` sets bits locklessly; `slots_lock`
  serialises the harvesting ioctls; `kvm_get_dirty_log_protect()` and
  `kvm_clear_dirty_log_protect()` hold `mmu_lock` only around the loop that
  clears words and write-protects.
- `kvm_use_dirty_bitmap()`: asserts `slots_lock`, with
  `CONFIG_HAVE_KVM_DIRTY_RING`.
- `vm_dead` and `vm_bugged`: plain stores in `kvm_vm_dead()` and
  `kvm_vm_bugged()` in `include/linux/kvm_host.h`; `vm_dead` is a plain load
  at ioctl entry; no `READ_ONCE()` or `WRITE_ONCE()`.
- `irqfds.lock`: every taker disables interrupts (`spin_lock_irq()` or
  `spin_lock_irqsave()`), because `irqfd_wakeup()` takes it with interrupts
  off.
- `kvm->lock` is shared by vCPU creation and `dirty_ring_size`.

**Mutexes held across SRCU waits**

- `kvm->lock`, `vcpu->mutex` and `slots_lock` are the three that
  `Documentation/virt/kvm/locking.rst` names; `slots_arch_lock` is not,
  `kvm_swap_active_memslots()` unlocks it before the wait.
- Direct waits on `kvm->srcu` in `virt/kvm/kvm_main.c` are under `slots_lock`:
  `kvm_swap_active_memslots()` and `kvm_io_bus_unregister_dev()`.
- `kvm->lock` and `vcpu->mutex`: reach the wait by nesting `slots_lock`
  inside; for example `KVM_CREATE_IRQCHIP` in `arch/x86/kvm/x86.c` calls
  `kvm_pic_destroy()` under `kvm->lock` on its error path.
- `kvm_vm_ioctl_set_msr_filter()` in `arch/x86/kvm/msrs.c`: drops `kvm->lock`
  before `synchronize_srcu()`.
- **Potentially unsafe usage**: taking `kvm->lock`, `vcpu->mutex` or
  `slots_lock` while in a `kvm->srcu` read side section.
  - Unsafe: with a call that waits for the mutex; the mutex holder waits for
    the reader in `synchronize_srcu_expedited()`, and the reader waits for the
    mutex.
  - Safe: leave the read side first, as `kvm_inhibit_apic_access_page()` in
    `arch/x86/kvm/lapic.c` does: `kvm_vcpu_srcu_read_unlock()`, take
    `slots_lock`, recheck `apic_access_memslot_enabled` under it, unlock,
    `kvm_vcpu_srcu_read_lock()`.
  - Safe: `mutex_trylock()`, which never waits, as
    `kvm_s390_try_set_tod_clock()` does on `kvm->lock` for
    `handle_set_clock()`; on failure the instruction is retried.
  - Safe: `slots_arch_lock` inside the read side, as
    `kvm_s390_vm_set_migration()` in `arch/s390/kvm/s390/s390.c` does;
    `kvm_swap_active_memslots()` unlocks it before
    `synchronize_srcu_expedited()`.

**The arch memslot lock**

- May be taken inside a `kvm->srcu` read side section:
  `kvm_swap_active_memslots()` unlocks it before
  `synchronize_srcu_expedited()`.
- Holder without `slots_lock`: take the lock, then read the memslots pointer,
  and keep the lock until every change to those memslots is complete, as
  `mmu_first_shadow_root_alloc()` in `arch/x86/kvm/mmu/mmu.c` does.
- `kvm_set_memslot()`: returns with the lock released on every path.
- `kvm_arch_prepare_memory_region()` runs with the lock held;
  `kvm_arch_commit_memory_region()` runs without it, so a holder of the lock
  can change `new->arch` while it runs.
- `kvm_invalidate_memslot()`: retakes the lock after the first swap and copies
  `invalid_slot->arch` back to `old->arch`, to pick up changes made while it
  was dropped.
- s390 takes it too: it serialises CMMA migration state in
  `arch/s390/kvm/s390/s390.c`, for example `kvm_s390_vm_set_migration()`.

**Notifiers and memslot swaps**

- Reason for the wait: the notifier callbacks change
  `mmu_invalidate_in_progress` only when a memslot overlaps the range
  (`on_lock` in `kvm_handle_hva_range()`), so a swap between start and end
  would leave it unbalanced.
- `mn_active_invalidate_count`: raised by every start, whether or not a
  memslot overlaps.
- `kvm_swap_active_memslots()`: waits until `mn_active_invalidate_count` is
  zero before it publishes the new memslots, with an open-coded
  `prepare_to_rcuwait()` / `schedule()` loop in `TASK_UNINTERRUPTIBLE`, not
  `rcuwait_wait_event()`.
- `rcu_assign_pointer()` on `kvm->memslots[as_id]`: done with
  `mn_invalidate_lock` still held, so no start can slip in between the check
  and the store.
- `kvm_destroy_vm()`: zeroes a nonzero `mn_active_invalidate_count` after
  `mmu_notifier_unregister()`, since the matching end will never run.

**SRCU protected data**

- `kvm_io_bus_register_dev()`: does not wait; it publishes the new bus and
  frees the old one with `call_srcu()` and `__free_bus()`.
- `kvm_io_bus_unregister_dev()`: waits with `synchronize_srcu_expedited()`,
  then frees.
- `kvm_destroy_vm()`: calls `srcu_barrier(&kvm->srcu)` before
  `cleanup_srcu_struct(&kvm->srcu)`, for those pending `call_srcu()`
  callbacks.
- Order in `kvm_destroy_vm()`: `cleanup_srcu_struct(&kvm->irq_srcu)` first,
  with no barrier, then the barrier and cleanup of `srcu`.
- Memslots: the old set is not freed; it becomes the inactive set in
  `__memslots` and is reused. What is freed is slot objects: the replaced
  `struct kvm_memory_slot` in `kvm_commit_memory_region()`, and the temporary
  INVALID copy in `kvm_set_memslot()`.
- `kvm_set_irq_routing()`: calls `synchronize_srcu_expedited()` on `irq_srcu`
  after it drops `irq_lock`, not under it.
- `kvm_get_bus()` in `include/linux/kvm_host.h`: update side accessor, needs
  `slots_lock`; readers use `kvm_get_bus_srcu()`.

**MMU lock type and mode**

- `KVM_HAVE_MMU_RWLOCK`: defined by x86, arm64, riscv and s390; search for the
  name. Other architectures get a spinlock.
- `kvm_mmu_invalidate_start()`, `kvm_mmu_invalidate_range_add()` and
  `kvm_mmu_invalidate_end()`: assert write mode with
  `lockdep_assert_held_write()`, so arch code holding the lock for read may
  not call them.

**Work under the MMU lock**

- **Potentially unsafe usage**: calling `kvm_mmu_memory_cache_alloc()` under
  `mmu_lock`.
  - Unsafe: more calls than the `min` passed to the last top-up, with no test
    of the object count before them; on an empty cache it hits `WARN_ON()`,
    falls back to `GFP_ATOMIC | __GFP_ACCOUNT`, and `BUG_ON()` fires if that
    fails.
  - Safe: top up for the worst case before taking the lock, as
    `mmu_topup_memory_caches()` in `arch/x86/kvm/mmu/mmu.c` does;
    `__kvm_mmu_topup_memory_cache()` guarantees `min` objects.
  - Safe: test `kvm_mmu_memory_cache_nr_free_objects()` against the worst
    case under the lock before each use, as
    `need_topup_split_caches_or_resched()` does before
    `shadow_mmu_split_huge_page()`.
- `__kvm_mmu_topup_memory_cache()`: guarantees `min` objects, not capacity; it
  returns 0 at once when `nobjs >= min`, and returns 0 after a failed
  allocation if `min` was reached.
- `__kvm_mmu_topup_memory_cache()` also returns `-EIO`: zero capacity, a
  capacity that differs from an earlier top-up, or `init_value` combined with
  `kmem_cache` or `gfp_zero`.
- Memory cache helpers: compiled only where the arch defines
  `KVM_ARCH_NR_OBJS_PER_MEMORY_CACHE`; s390 and powerpc do not.
- Caches are not all per vCPU: x86 `split_desc_cache`,
  `split_page_header_cache` and `split_shadow_page_cache` are per VM and
  `topup_split_caches()` asserts `slots_lock`; `kvm_phys_addr_ioremap()` in
  `arch/arm64/kvm/mmu.c` uses one on the stack.
- x86 TDP MMU eager split: `tdp_mmu_split_huge_pages_root()` always drops
  `mmu_lock` before `tdp_mmu_alloc_sp_for_split()`, which uses
  `GFP_KERNEL_ACCOUNT`; there is no attempt under the lock.

## VMs and vCPUs

**VM references**

- `kvm_get_kvm_safe()`: called only by debugfs `open` handlers (for example
  `kvm_debugfs_open()`, `kvm_mmu_rmaps_stat_open()`) and by
  `vfio_device_get_kvm_safe()` in `drivers/vfio/vfio_main.c`.
- `vm_list` walkers: take no reference at all; those in
  `virt/kvm/kvm_main.c` hold `kvm_lock` for the whole walk, for example
  `vm_stat_get()`.
- A VM on `vm_list` can already have `users_count` zero: `kvm_destroy_vm()`
  removes it under `kvm_lock` only after the last put.
- `kvm_put_kvm_no_destroy()`: every caller undoes a `kvm_get_kvm()` taken for
  an `anon_inode_getfd()` that then made no fd; nothing in `kvm_destroy_vm()`
  teardown calls it.
- `virt/kvm/async_pf.c`: does not call `kvm_get_kvm()`; async page fault work
  holds no VM reference.
- File descriptors holding a reference also include the VM and vCPU stats fds
  (`kvm_vm_stats_release()`, `kvm_vcpu_stats_release()`) and a guest_memfd
  file (`kvm_gmem_release()` in `virt/kvm/guest_memfd.c`).
- powerpc adds two anon inode fds: the fds from `kvm_vm_ioctl_get_htab_fd()`
  and `kvm_vm_ioctl_create_spapr_tce()`.
- irqfd and ioeventfd: hold no VM reference; `virt/kvm/eventfd.c` never calls
  `kvm_get_kvm()`, and `kvm_vm_release()` tears irqfds down with
  `kvm_irqfd_release()`.
- **Unsafe usage**: taking the VM reference for a new fd after the fd is
  installed; userspace can close it at once and the release handler calls
  `kvm_put_kvm()`.
  - Safe: `kvm_get_kvm()` before `anon_inode_getfd()`, undone with
    `kvm_put_kvm_no_destroy()` on failure, as `kvm_ioctl_create_device()`
    does; `kvm_device_release()` is the put it pairs with.
  - Safe: `kvm_get_kvm()` between file creation and `fd_install()`, with no
    undo needed, as `kvm_vm_ioctl_get_stats_fd()` and `__kvm_gmem_create()`
    do.

**Dead and bugged VMs**

- `KVM_BUG_ON()`: `WARN_ON_ONCE()` that is skipped when `kvm->vm_bugged` is
  already set, then `kvm_vm_bugged()`; there is no ratelimited print.
- `kvm->vm_bugged`: read only to skip a repeat WARN or a repeat
  `kvm_vm_bugged()`; every ioctl entry test reads `kvm->vm_dead`.
- `KVM_BUG_ON_DATA_CORRUPTION()` with `CONFIG_BUG_ON_DATA_CORRUPTION`: a
  plain `BUG_ON()`.
- `kvm_device_ioctl()`: returns `-EIO` on a dead VM, like `kvm_vm_ioctl()`,
  `kvm_vcpu_ioctl()` and the two compat entry points.
- File operations other than ioctl do not test `vm_dead`: for example
  `kvm_vcpu_mmap()` and `kvm_vm_stats_read()`.
- `KVM_REQ_VM_DEAD` is tested on the guest entry path by x86
  `vcpu_enter_guest()` and arm64 `check_vcpu_requests()`; only x86 and arm64
  code names the request.
- `kvm_vm_dead()` is also called on purpose: `sev_vm_move_enc_context_from()`
  kills the source VM after a successful migration.

**Assertions reachable by guests**

- `KVM_BUG_ON()` examples: the `nested_run_pending` test in
  `__vmx_handle_exit()` and `handle_nmi_window()` in `arch/x86/kvm/vmx/vmx.c`;
  both return `-EIO` on a hit.
- `KVM_BUG_ON_DATA_CORRUPTION()`: used only by the rmap helpers in
  `arch/x86/kvm/mmu/mmu.c`, for example `pte_list_remove()`.
- `KVM_EMULATOR_BUG_ON()` in `arch/x86/kvm/kvm_emulate.h`: the form for x86
  emulator code, which has no `struct kvm`; it goes through
  `emulator_vm_bugged()`.
- `TDX_BUG_ON()` and its numbered variants in `arch/x86/kvm/vmx/tdx.c`: with a
  non-NULL `struct kvm`, same effect as `KVM_BUG_ON()` plus a ratelimited
  print of the SEAMCALL error; with a NULL one, only the WARN and the print.
- A fatal state that a guest can cause: `kvm_vm_dead()` with no WARN, then
  `-EIO`; see `tdx_handle_ept_violation()`.

**vCPU creation**

- `vcpu->mutex`: taken after `xa_insert()` and before `kvm_get_kvm()`, inside
  `kvm->lock`; released after `atomic_inc(&kvm->online_vcpus)`.
- `kvm->lock` does not keep userspace out: `kvm_vcpu_ioctl()` does not take
  it itself. `vcpu->mutex` and `kvm_wait_for_vcpu_online()` do.
- Count limit in the first lock section: `kvm->max_vcpus`, not
  `KVM_MAX_VCPUS`.
- Second lock section: has no test of `online_vcpus` against a limit.
- `vcpu->vcpu_idx`: -1 from allocation until just before `xa_insert()`, and
  reset to -1 on failure; `kvm_lockdep_assert_vcpu_is_locked_or_unreachable()`
  treats a negative index as unreachable.

**vCPU ids**

- Uniqueness: the `kvm->vcpu_ids` bitmap in `struct kvm`; `test_bit()` returns
  `-EEXIST` and `__set_bit()` reserves the id in the first `kvm->lock`
  section.
- Order of tests in that section: count limit (`-EINVAL`), then the bitmap
  (`-EEXIST`), then `kvm_arch_vcpu_precreate()`.
- `kvm_arch_vcpu_precreate()` and `kvm_arch_vcpu_create()`: never see an id
  that another live or in-progress vCPU holds.
- `kvm_get_vcpu_by_id()` in the second lock section: wrapped in
  `WARN_ON_ONCE()`; a hit there is a KVM bug, not a userspace error.
- The bit is cleared only on the failure path of `kvm_vm_ioctl_create_vcpu()`,
  under `kvm->lock`.
- Type of the id: `unsigned long` in `kvm_vm_ioctl_create_vcpu()`,
  `unsigned int` in `kvm_arch_vcpu_precreate()`, `int` in `vcpu->vcpu_id`.

**vCPU ioctl dispatch**

- There is no kvm_arch_vcpu_async_ioctl() here; the hook is
  `kvm_arch_vcpu_unlocked_ioctl()`, defined by every architecture with no
  configuration gate.
- Before the hook, in order: the mm and `vm_dead` test, the `_IOC_TYPE()` test
  against `KVMIO` (`-EINVAL`), then `kvm_wait_for_vcpu_online()`.
- x86 hook: handles only `KVM_MEMORY_ENCRYPT_OP`, and only when
  `vcpu_mem_enc_unlocked_ioctl` in `struct kvm_x86_ops` is set, which only
  `vt_x86_ops` in `arch/x86/kvm/vmx/main.c` does, under
  `CONFIG_KVM_INTEL_TDX`; `KVM_INTERRUPT`, `KVM_NMI` and `KVM_SMI` run under
  `vcpu->mutex`.
- arm64 hook: always returns `-ENOIOCTLCMD`.
- A hook handler may take the locks itself: `tdx_vcpu_unlocked_ioctl()` takes
  `kvm->lock`, every `vcpu->mutex` with `kvm_lock_all_vcpus()`, then
  `kvm->slots_lock`, and then calls `vcpu_load()`.

**Thread that runs a vCPU**

- `vcpu->pid` is not RCU-protected; the store is under
  `write_lock(&vcpu->pid_lock)` and there is no `synchronize_rcu()`.
- `kvm_vcpu_yield_to()`: uses `read_trylock()` and returns 0 when the lock is
  contended; it does not wait.
- `kvm_arch_vcpu_run_pid_change()`: called before the new pid is taken; on
  error `vcpu->pid` is left unchanged, so the next `KVM_RUN` calls it again.
- `kvm_arch_vcpu_run_pid_change()`: a stub that returns 0 without
  `CONFIG_HAVE_KVM_VCPU_RUN_PID_CHANGE`, which only arm64 selects.
- `vcpu->pid` is `NULL` from `kvm_vcpu_init()` until the first `KVM_RUN`.
- **Potentially unsafe usage**: reading `vcpu->pid` without
  `vcpu->pid_lock`.
  - Unsafe: from a task that does not hold `vcpu->mutex`, while a vCPU fd
    still exists; `KVM_RUN` can replace the pointer and `put_pid()` the old
    one.
  - Safe: while holding `vcpu->mutex`, which the only writer, the `KVM_RUN`
    case, holds, as the compare in the `KVM_RUN` case and arm64
    `kvm_arch_vcpu_load()` do.
  - Safe: in `kvm_vcpu_destroy()`, reached only from `kvm_destroy_vcpus()`
    when no vCPU fd is left to issue `KVM_RUN`; each vCPU fd holds a VM
    reference until `kvm_vcpu_release()`.

**Loading a vCPU**

- `vcpu_load()` itself writes the per-CPU `kvm_running_vcpu` and registers
  the notifier; `vcpu->cpu` is written by arch code, for example x86 and
  arm64 `kvm_arch_vcpu_load()`.
- `kvm_sched_out()` and `kvm_sched_in()` clear and set `kvm_running_vcpu`
  too, so `kvm_get_running_vcpu()` is valid across a reschedule.
- Generic `kvm_vcpu_ioctl()` never calls `vcpu_load()` for a handler;
  `kvm_vcpu_pre_fault_memory()` loads for itself.
- x86: `kvm_arch_vcpu_ioctl()` loads once around its whole switch; the
  handlers that `kvm_vcpu_ioctl()` calls directly load one by one, and
  `kvm_arch_vcpu_ioctl_get_regs()` and `kvm_arch_vcpu_ioctl_get_sregs()` are
  in `arch/x86/kvm/regs.c`.
- arm64 and riscv: `vcpu_load()` is called only in
  `kvm_arch_vcpu_ioctl_run()`; other vCPU ioctl handlers run unloaded.
- `preempt_notifier_register()` in `kernel/sched/core.c`: an unconditional
  `hlist_add_head()` onto `current->preempt_notifiers`, so a second
  `vcpu_load()` before `vcpu_put()` links the same node twice.
- **Potentially unsafe usage**: `vcpu_load()` without holding `vcpu->mutex`.
  - Unsafe: on a vCPU another task can reach; `struct kvm_vcpu` has a single
    `preempt_notifier` and `vcpu_load()` checks nothing.
  - Safe: on a vCPU no other task can reach: before it is in
    `kvm->vcpu_array`, as x86 `kvm_arch_vcpu_create()` does, or while it is
    destroyed, as `nested_vmx_free_vcpu()` does;
    `kvm_lockdep_assert_vcpu_is_locked_or_unreachable()` defines the
    condition.
  - Safe: outside the locked part of `kvm_vcpu_ioctl()` when the caller takes
    `vcpu->mutex` itself, as x86 `kvm_arch_vcpu_postcreate()` and
    `tdx_vcpu_unlocked_ioctl()` do.

## Requests and kicks

**vCPU mode**

- x86 `IN_GUEST_MODE` write: `vcpu_enter_guest()` in `arch/x86/kvm/x86.c` uses
  `smp_store_release()`, then `kvm_vcpu_srcu_read_unlock()`, then
  `smp_mb__after_srcu_read_unlock()`. x86 does not use `smp_store_mb()` here.
- Full barrier before the x86 read of requests: the `smp_mb()` in
  `__srcu_read_unlock()` in `kernel/rcu/srcutree.c`, reached through
  `kvm_vcpu_srcu_read_unlock()`; `smp_mb__after_srcu_read_unlock()` is an
  empty inline.
- Other architectures: the full barrier after the `IN_GUEST_MODE` store is not
  always `smp_store_mb()`. For example `kvmppc_prepare_to_enter()` does a
  plain store then `smp_mb()`, and riscv a plain store then
  `kvm_vcpu_srcu_read_unlock()` and `smp_mb__after_srcu_read_unlock()`. Search
  for `IN_GUEST_MODE`.
- x86 `OUTSIDE_GUEST_MODE` write in `vcpu_enter_guest()`: a plain store
  followed by `smp_wmb()`, with IRQs still disabled, both after VM-exit and on
  the cancelled entry.
- `walk_shadow_page_lockless_end()`, when `is_tdp_mmu_active()` is false:
  writes `OUTSIDE_GUEST_MODE`, not `IN_GUEST_MODE`.
- `IN_GUEST_MODE` to `EXITING_GUEST_MODE` has a second writer:
  `__kvm_vcpu_kick()` uses `WRITE_ONCE()`, with no `cmpxchg()` and no
  `smp_mb__before_atomic()`, when the target is this CPU's `kvm_running_vcpu`.
- `kvm_running_vcpu`: set from `vcpu_load()` or `kvm_sched_in()` until
  `vcpu_put()` or `kvm_sched_out()`, so that branch also covers a kick from an
  interrupt handler that interrupted the vCPU thread.
- `kvm_arch_vcpu_should_kick()` on mips and powerpc: returns 1 and does not
  call `kvm_vcpu_exiting_guest_mode()`, so `__kvm_vcpu_kick()` there moves the
  mode only in the `kvm_running_vcpu` branch.

**Request functions**

- `smp_wmb()` in `__kvm_make_request()`: pairs only with
  `smp_mb__after_atomic()` in `kvm_check_request()`. `kvm_test_request()` and
  `kvm_request_pending()` contain no `smp_rmb()` or any other barrier.
- `kvm_make_all_cpus_request()` and `kvm_make_vcpu_request()`: no barrier call
  in either body. The barrier that orders the bit before the mode read is
  `smp_mb__before_atomic()` in `kvm_vcpu_exiting_guest_mode()`, reached
  through `kvm_request_needs_ipi()`.
- There is no kvm_make_all_cpus_request_except() here.
  `kvm_make_all_cpus_request()` and `kvm_make_vcpus_request_mask()` in
  `virt/kvm/kvm_main.c` are two separate loops over `kvm_make_vcpu_request()`.
- `kvm_make_vcpu_request()` after a successful `kvm_vcpu_wake_up()`: returns at
  once. `kvm_request_needs_ipi()` is not called, so the mode is not touched
  and that vCPU gets no IPI, with or without `KVM_REQUEST_WAIT`.
- IRQs: `smp_call_function_many()` is reached whenever the kick mask is not
  empty. `smp_call_function_many_cond()` in `kernel/smp.c` asserts IRQs
  enabled and task context whether or not `KVM_REQUEST_WAIT` is set.

**Request flags**

- `KVM_REQUEST_NO_ACTION`: `kvm_make_vcpu_request()` does not call
  `__kvm_make_request()`, so no bit is set in `requests`. Only the wake-up and
  the IPI remain.
- `kvm_make_request_and_kick()` in `include/linux/kvm_host.h`: a third path
  that reads the flags, besides `kvm_make_all_cpus_request()` and
  `kvm_make_vcpus_request_mask()`. It calls `kvm_make_request()` and then
  `__kvm_vcpu_kick(vcpu, req & KVM_REQUEST_WAIT)`.
- `KVM_REQUEST_NO_WAKEUP` through `kvm_make_request_and_kick()`: ignored;
  `__kvm_vcpu_kick()` calls `kvm_vcpu_wake_up()` unconditionally.
- `KVM_REQUEST_WAIT` through `kvm_make_request_and_kick()`: weaker than through
  `kvm_make_all_cpus_request()`. Where `kvm_arch_vcpu_should_kick()` calls
  `kvm_vcpu_exiting_guest_mode()`, a target already in `EXITING_GUEST_MODE`
  or in `READING_SHADOW_PAGE_TABLES` gets no IPI and is not waited for; see
  "Kicks and wakeups".
- `KVM_REQ_OUTSIDE_GUEST_MODE` on x86: it sets no bit in `requests`, so the
  `EXITING_GUEST_MODE` test in `kvm_vcpu_exit_request()` is what ends the
  IRQs-off re-entry loop in `vcpu_enter_guest()`. The sender stays blocked
  until the target leaves that loop; see the comment in
  `tdx_exit_handlers_fastpath()`.

**Making requests safely**

- `kvm_make_request()`: a `BUILD_BUG_ON()`, not a run-time warning. The build
  fails unless the request is a compile-time constant without
  `KVM_REQUEST_NO_ACTION`.
- Run-time request number: use `__kvm_make_request()`, as
  `kvm_make_vcpu_request()` and `kvm_s390_sync_request()` do.
- `KVM_REQ_VM_DEAD`: `kvm_check_request()` and `kvm_clear_request()` each have
  a `BUILD_BUG_ON()` against it. Test it with `kvm_test_request()`, as
  `vcpu_enter_guest()` does; the bit is never cleared.
- Requests with no `kvm_check_request()` exist on purpose. x86
  `KVM_REQ_MCLOCK_INPROGRESS` is made by
  `kvm_make_mclock_inprogress_request()` and cleared by the sender's thread
  with `kvm_clear_request()` in `kvm_end_pvclock_update()`; while set it keeps
  vCPUs out of the guest.
- `kvm_make_request_and_kick()`: request plus kick in one call; not defined
  under `CONFIG_S390`.
- Blocked target: a wake-up alone does not unblock. `kvm_vcpu_block()` sleeps
  again unless `kvm_vcpu_check_block()` finds `kvm_arch_vcpu_runnable()`, a
  pending timer, a signal or `KVM_REQ_UNBLOCK`.
- `kvm_arch_vcpu_runnable()` differs by architecture: powerpc's tests
  `kvm_request_pending()`; x86's tests only the requests named in
  `kvm_vcpu_has_events()` and in `kvm_is_exception_pending()`; arm64's tests
  no request.
- Direct access to `requests`: nothing outside the helpers in
  `include/linux/kvm_host.h` writes it. The only direct reads are the
  tracepoints in `arch/x86/kvm/trace.h` and `arch/powerpc/kvm/trace.h`.
- **Potentially unsafe usage**: making a request and then reading `vcpu->mode`
  directly to decide whether to notify the target.
  - Unsafe: with no full barrier between `kvm_make_request()` and the read.
    The `smp_wmb()` does not order the store to `requests` against the load of
    `vcpu->mode`, so the entry check in `vcpu_enter_guest()` can miss the
    request while the sender sees a mode other than `IN_GUEST_MODE`.
  - Safe: through `kvm_vcpu_kick()` or `kvm_make_all_cpus_request()`, where
    `kvm_vcpu_exiting_guest_mode()` supplies `smp_mb__before_atomic()`.
  - Safe: with `smp_mb__after_atomic()` between the two, as
    `vmx_deliver_nested_posted_interrupt()` in `arch/x86/kvm/vmx/vmx.c` does
    before `kvm_vcpu_trigger_posted_interrupt()`.

**Kicks and wakeups**

- `wait` true: the IPI is `smp_call_function_single(cpu, ack_kick, NULL,
  wait)`; `wait` false: `smp_send_reschedule(cpu)`.
- `wait` true needs IRQs enabled and task context:
  `__smp_call_function_single()` in `kernel/smp.c` has a `WARN_ON_ONCE()` for
  each. `kvm_vcpu_kick()` may be called with IRQs disabled.
- Where `kvm_arch_vcpu_should_kick()` calls `kvm_vcpu_exiting_guest_mode()`:
  `wait` is acted on only when this call's `cmpxchg()` saw `IN_GUEST_MODE` and
  `vcpu->cpu` is another online CPU. A target already in
  `EXITING_GUEST_MODE` or in `READING_SHADOW_PAGE_TABLES` gets no IPI, and the
  call returns without waiting.
- Guarantee: a kick guarantees only that the target is on its way out. To know
  it has left, use a `KVM_REQUEST_WAIT` request through
  `kvm_make_all_cpus_request()`; see the comment above
  `KVM_REQ_OUTSIDE_GUEST_MODE` in `include/linux/kvm_host.h`.
- Target is this CPU's `kvm_running_vcpu`: no IPI, and `wait` is ignored; the
  only effect is the mode write described under "vCPU mode".
- That mode write is read back by x86 `kvm_vcpu_exit_request()`, which tests
  for `EXITING_GUEST_MODE`. arm64's `kvm_vcpu_exit_request()` does not read
  `vcpu->mode`.
- mips and powerpc: `kvm_arch_vcpu_should_kick()` returns 1, so every target
  that is not blocked and last ran on another online CPU gets an IPI,
  whatever its mode.
- `CONFIG_S390`: `__kvm_vcpu_kick()`, `kvm_vcpu_kick()` and
  `kvm_make_request_and_kick()` are not built. s390 uses
  `kvm_s390_sync_request()` and `exit_sie()` in `arch/s390/kvm/s390/s390.c`.

## Memslots

**Active and inactive sets**

- `hva_node[2]`: `struct interval_tree_node`, not `struct rb_node`;
  `hva_tree` is a `struct rb_root_cached` used as an interval tree.
- `node_idx`: written once in `kvm_create_vm()` as the set's index in
  `__memslots[as_id][]`; it names the set, not whether it is active.
- Active set: only `kvm->memslots[as_id]` says which one it is.
- `KVM_MEMSLOT_GEN_UPDATE_IN_PROGRESS`: bit 63 of `generation`, set while
  `kvm_swap_active_memslots()` runs; it does not identify a set.
- New slot object: `kvm_set_memory_region()` allocates one for every change
  except delete; the request's values are written to the new object, never
  to the old one.
- `kvm_copy_memslot()`: only caller is `kvm_invalidate_memslot()`; it leaves
  the node arrays alone.

**Memslot update entry points**

- `kvm_set_internal_memslot()` in `virt/kvm/kvm_main.c`: the only non-static
  function that calls `kvm_set_memory_region()`.
- `kvm_set_memory_region()` and `kvm_set_memslot()`: static; there is no
  __kvm_set_memory_region() in this tree.
- Export: `EXPORT_SYMBOL_FOR_KVM_INTERNAL()`, which exports only to the
  modules in `KVM_SUB_MODULES` and expands to nothing without it.
- Restrictions: `WARN_ON_ONCE()` plus `-EINVAL` when
  `mem->slot < KVM_USER_MEM_SLOTS` or when `mem->flags` is non-zero.
- Id test: compares the whole `mem->slot`, address-space bits included, so
  it bounds the id only for address space 0;
  `kvm_vm_ioctl_set_memory_region()` compares `(u16)mem->slot`.
- `kvm->slots_lock`: `kvm_set_internal_memslot()` neither takes nor asserts
  it; the caller takes it, and `kvm_set_memory_region()` asserts it.
- Ioctl path: `kvm_vm_ioctl_set_memory_region()` takes `slots_lock` itself
  with `guard(mutex)`.
- Callers: x86 `__x86_set_memory_region()` and s390 `kvm_arch_init_vm()`.

**Slots reserved for the kernel**

- `KVM_INTERNAL_MEM_SLOTS`: 3 on x86, 1 on s390
  (`KVM_S390_UCONTROL_MEMSLOT`), 0 elsewhere.

| Limit | User slot | Internal slot |
|---|---|---|
| `npages <= KVM_MEM_MAX_NR_PAGES` | enforced | exempt |
| `mem->flags` non-zero | allowed if `check_memory_region_flags()` passes | `-EINVAL` |
| `kvm_is_visible_memslot()` | true unless `KVM_MEMSLOT_INVALID` | false |
| dirty-log and dirty-ring lookups | reachable | rejected by id |
| alignment and `access_ok()` on `userspace_addr` | enforced | enforced |
| counted in `kvm->nr_memslot_pages` | yes | yes |

- Dirty-log id test: `id >= KVM_USER_MEM_SLOTS` in `kvm_get_dirty_log()`,
  `kvm_get_dirty_log_protect()`, `kvm_clear_dirty_log_protect()` and
  `kvm_reset_dirty_gfn()`.
- `KVM_CAP_NR_MEMSLOTS`: reports `KVM_USER_MEM_SLOTS`.
- s390 ucontrol VM: `s390_kvm_mmu_prepare_memory_region()` rejects every
  slot with `id < KVM_USER_MEM_SLOTS`, so only the internal slot exists.

**Changing an existing slot**

- `KVM_MEM_READONLY`: toggling it on an existing slot is `-EINVAL` on every
  architecture.
- `KVM_MEM_GUEST_MEMFD`: `-EINVAL` if the new flags have it, and `-EINVAL`
  if old and new flags differ in it; both tests are in
  `kvm_set_memory_region()`.
- Existing guest_memfd slot: every request with `memory_size != 0` fails,
  an identical one too, as the test runs before the "nothing to change"
  return.
- Flag validation: `check_memory_region_flags()`; there is no
  kvm_check_memory_region_flags() here.
- Same `base_gfn`, size, `userspace_addr` and flags: returns 0, picks no
  `enum kvm_mr_change` value, does not call `kvm_set_memslot()`.
- Different `base_gfn` plus a flag change: classified `KVM_MR_MOVE`.

**Overlap check on guest frames**

- guest_memfd: no special case; `kvm_check_memslot_overlap()` receives only
  the set, the id and the gfn range, never the flags.
- gfn overlap: `kvm_set_memory_region()` returns `-EEXIST`.

**Memslot update flow**

- `kvm_invalidate_memslot()`: order is copy and flag, `kvm_replace_memslot()`
  on the inactive set, `kvm_swap_active_memslots()`,
  `kvm_arch_flush_shadow_memslot()`, `kvm_arch_guest_memory_reclaimed()`,
  re-take `slots_arch_lock`, copy `invalid_slot->arch` to `old->arch`.
- After `kvm_invalidate_memslot()`: no replay; the active set holds the
  INVALID copy and the inactive set still holds `old`, which is what makes
  the revert possible.
- `kvm_arch_flush_shadow_memslot()`, the replay on the other set and
  `kvm_arch_commit_memory_region()`: run under `slots_lock` with
  `slots_arch_lock` dropped.
- `kvm_arch_memslots_updated()`: called in every swap, after the grace
  period and before the new `generation` is stored.
- Swaps per call: two for `KVM_MR_DELETE` and `KVM_MR_MOVE`, also when
  prepare fails, none when the `invalid_slot` allocation fails; one for
  `KVM_MR_CREATE` and `KVM_MR_FLAGS_ONLY`, none when prepare fails.
- Reverted DELETE/MOVE: the zap done by `kvm_arch_flush_shadow_memslot()` is
  not undone; `old` is live again.
- `invalid_slot`: freed with `kfree()` in `kvm_set_memslot()`, before
  `kvm_commit_memory_region()`, not by the commit step.

**Slots being deleted or moved**

- Test order in `kvm_mmu_faultin_pfn()`: alias, private/shared mismatch,
  `!slot`, then the flag.
- No slot versus INVALID slot in `kvm_mmu_faultin_pfn()`: `!slot` goes to
  `kvm_handle_noslot_fault()`; an INVALID slot returns `RET_PF_RETRY` and
  does not reach `kvm_handle_noslot_fault()`.
- `fault->prefetch` with an INVALID slot: returns `-EAGAIN`.
- `fault->prefetch` in `kvm_mmu_faultin_pfn()`: true for faults from
  `kvm_tdp_page_prefault()` and `kvm_arch_async_page_ready()`.
- Retry loop inside one SRCU read section: must stop on the flag, as the
  updater is waiting in `synchronize_srcu_expedited()`; see
  `tdx_handle_ept_violation()`.
- Lookups: `gfn_to_memslot()`, `kvm_vcpu_gfn_to_memslot()` and
  `id_to_memslot()` return a slot that has the flag set.
- INVALID copy: `kvm_copy_memslot()` does not copy `gmem`, so `gmem.file` is
  NULL and `kvm_gmem_get_pfn()` returns `-EFAULT`.
- **Potentially unsafe usage**: translating a gfn through a slot without
  testing `KVM_MEMSLOT_INVALID`.
  - Unsafe: `__gfn_to_hva_memslot()` on a slot from a lookup, to create a
    mapping, when nothing earlier on the path tested the flag; the copy
    keeps the old `userspace_addr`, so a mapping appears after the zap.
  - Safe: `gfn_to_hva_memslot()` and `gfn_to_hva_memslot_prot()`, which go
    through `__gfn_to_hva_many()` and return `KVM_HVA_ERR_BAD`.
  - Safe: after an explicit test, as `kvm_mmu_faultin_pfn()` does before
    `__kvm_mmu_faultin_pfn()`, and as `kvmppc_do_h_enter()` does before
    `__gfn_to_hva_memslot()`.

**Reading memslots**

- `slots_arch_lock`: not in the lockdep expression of `__kvm_memslots()`;
  holding it alone does not satisfy the check.
- `users_count` clause: does not cover VM creation; `kvm_create_vm()` sets
  `users_count` to 1 before `kvm_arch_init_vm()`.
- Init-time code: takes `slots_lock`, as s390 `kvm_arch_init_vm()` does
  around `kvm_set_internal_memslot()`.
- `kvm_free_memslots()`: never calls `__kvm_memslots()`; it walks
  `kvm->__memslots` directly, through `id_node[1]` only.
- Other `slots_lock`-only readers, for example: `kvm_vm_set_mem_attributes()`
  through `kvm_handle_gfn_range()`, and `kvm_mmu_rmaps_stat_show()`.
- **Unsafe usage**: using a slot pointer after a successful
  `kvm_set_internal_memslot()` or `kvm_set_memory_region()` call on that
  slot by the same holder of `slots_lock`.
  - Unsafe: `kvm_commit_memory_region()` frees `old` on `KVM_MR_DELETE`,
    `KVM_MR_MOVE` and `KVM_MR_FLAGS_ONLY`, with `slots_lock` still held.
  - Safe: copy the fields first, as `__x86_set_memory_region()` does with
    `npages` and `userspace_addr` before `kvm_set_internal_memslot()`.
  - Safe: look the slot up again by id after the update, as arm64
    `kvm_mmu_wp_memory_region()` does when called from
    `kvm_arch_commit_memory_region()`.

## Guest frame translation

**Guest frame to host address**

- `gfn_to_hva_memslot_prot()`, `gfn_to_hva_prot()`,
  `kvm_vcpu_gfn_to_hva_prot()`: global in `virt/kvm/kvm_main.c` but carry no
  export macro, so a module listed in `KVM_SUB_MODULES` cannot call them.
- `gfn_to_hva_memslot()`, `gfn_to_hva()`, `kvm_vcpu_gfn_to_hva()`: carry
  `EXPORT_SYMBOL_FOR_KVM_INTERNAL()`.

**Read paths and read-only slots**

- Read-only slots exist only where `kvm_arch_has_readonly_mem()` is true;
  otherwise `check_memory_region_flags()` rejects `KVM_MEM_READONLY`. Search
  for `select HAVE_KVM_READONLY_MEM` to list the architectures.
- **Potentially unsafe usage**: translating with `gfn_to_hva()`,
  `gfn_to_hva_memslot()` or `kvm_vcpu_gfn_to_hva()` on a path that reads.
  - Unsafe: the architecture selects `HAVE_KVM_READONLY_MEM` and the path
    never writes the address; on a read-only slot `__gfn_to_hva_many()`
    returns `KVM_HVA_ERR_RO_BAD` and the read fails as a bad address.
  - Safe: the architecture does not select `HAVE_KVM_READONLY_MEM`, as for
    `kvmppc_mmu_book3s_64_get_pteg()`.
  - Safe: the path then writes the same address, as
    `kvm_update_stolen_time()` in `arch/arm64/kvm/pvtime.c` does with
    `kvm_get_guest()` and `kvm_put_guest()`.
- Read helpers built on write intent, which fail on a read-only slot:
  - `kvm_get_guest()`: `__kvm_get_guest()` uses `gfn_to_hva()`.
  - `kvm_read_guest_cached()`, `kvm_read_guest_offset_cached()`:
    `__kvm_gfn_to_hva_cache_init()` uses `gfn_to_hva_many()`; `-EFAULT`.
  - `kvm_is_gpa_in_memslot()`: uses `gfn_to_hva()`; returns false.
  - `kvm_gpc_activate()`: `__kvm_gpc_refresh()` uses `gfn_to_hva_memslot()`;
    `-EFAULT`.
- **Unsafe usage**: reading `writable` after a call to `gfn_to_hva_prot()`,
  `gfn_to_hva_memslot_prot()` or `kvm_vcpu_gfn_to_hva_prot()` without testing
  the hva first; `gfn_to_hva_memslot_prot()` writes `*writable` only when
  `!kvm_is_error_hva(hva)`.
  - Safe: test `kvm_is_error_hva()` and return before reading it, as
    `__kvm_at_swap_desc()` in `arch/arm64/kvm/at.c` does.
  - Safe: test it in the same condition, before `writable`, as
    `kvm_handle_guest_abort()` does.
- x86 walker: `FNAME(walk_addr_generic)` calls `kvm_vcpu_gfn_to_memslot()` and
  then `gfn_to_hva_memslot_prot()`, not `kvm_vcpu_gfn_to_hva_prot()`; the
  result goes to `walker->pte_writable[]`.
- There is no kvm_read_guest_atomic() here; `kvm_vcpu_read_guest_atomic()`
  calls the static `__kvm_read_guest_atomic()`, which passes a NULL
  `writable`.
- `kvm_host_page_size()`: calls `kvm_vcpu_gfn_to_hva_prot(vcpu, gfn, NULL)`.
- s390: `arch/s390/kvm/s390/gaccess.c` calls none of
  `gfn_to_hva_prot()`, `gfn_to_hva_memslot_prot()` and
  `kvm_vcpu_gfn_to_hva_prot()`, and s390 does not select
  `HAVE_KVM_READONLY_MEM`.

**Error addresses and frames**

- `is_error_noslot_pfn()`: true for every `KVM_PFN_ERR_` value and for
  `KVM_PFN_NOSLOT`; it tests `KVM_PFN_ERR_NOSLOT_MASK`.
- `is_error_pfn()`: false for `KVM_PFN_NOSLOT`; a caller that tests only this
  takes a no-slot frame for a real frame.
- `is_sigpending_pfn()`: true only for `KVM_PFN_ERR_SIGPENDING`.
- `KVM_PFN_ERR_NEEDS_IO`: has no predicate; callers compare the value
  directly.
  - Returned only when the caller passed `FOLL_NOWAIT`, so
    `kvm_faultin_pfn()` never returns it.
  - Caller sets up an async fault or calls again without `FOLL_NOWAIT`; see
    `__kvm_mmu_faultin_pfn()` and `kvm_s390_faultin_gfn()`.
- `KVM_PFN_ERR_SIGPENDING`: `hva_to_pfn()` returns it for any `-EINTR` or
  `-EAGAIN` from `hva_to_pfn_slow()`; it does not test `FOLL_INTERRUPTIBLE`
  itself.
- `KVM_PFN_NOSLOT`: `kvm_follow_pfn()` also returns it for a slot flagged
  `KVM_MEMSLOT_INVALID`, which is not MMIO.
  - x86 `kvm_mmu_faultin_pfn()` tests `KVM_MEMSLOT_INVALID` before the call
    and retries the fault.
- `KVM_PFN_ERR_RO_FAULT`: also returned by `hva_to_pfn_remapped()` for a write
  fault on a non-writable `VM_IO` or `VM_PFNMAP` mapping, in a slot that is
  not read-only.
- `KVM_HVA_ERR_BAD` and `KVM_HVA_ERR_RO_BAD`: no predicate tells them apart;
  compare with `== KVM_HVA_ERR_RO_BAD`, as `kvm_follow_pfn()` does.
- Overrides of both hva values and of `kvm_is_error_hva()`: an architecture
  defines `KVM_HVA_ERR_BAD` itself; search for the name. For example s390, in
  `arch/s390/include/asm/kvm_host_s390.h`, uses `-1UL`, `-2UL` and
  `IS_ERR_VALUE()`.

**Resolving and releasing a frame**

- `__kvm_faultin_pfn()`: both `writable` and `refcounted_page` must be
  non-NULL; otherwise `WARN_ON_ONCE()` and `KVM_PFN_ERR_FAULT`.
- There are no kvm_release_pfn_clean() or kvm_release_pfn_dirty() helpers
  here; release is by `struct page`: `kvm_release_faultin_page()`,
  `kvm_release_page_unused()`, `kvm_release_page_clean()`,
  `kvm_release_page_dirty()`.
- `kvm_release_faultin_page(kvm, page, unused, dirty)`: runs
  `lockdep_assert_once(lockdep_is_held(&kvm->mmu_lock) || unused)` before it
  tests `page` for NULL.
- **Potentially unsafe usage**: calling `kvm_release_faultin_page()` without
  `kvm->mmu_lock`.
  - Unsafe: with `unused` false; the assertion fires even for a NULL page.
  - Safe: with `unused` true, as `kvm_s2_fault_pin_pfn()` in
    `arch/arm64/kvm/mmu.c` does on its error path.
- `mmu_lock` held for read satisfies the assertion; `kvm_s2_fault_map()` holds
  it through `kvm_fault_lock()`, and `kvm_s390_faultin_gfn()` holds it for
  read.

**The pfn cache**

- Users in this tree: only x86 selects `HAVE_KVM_PFNCACHE`; the caches are the
  Xen ones in `arch/x86/kvm/xen.c` and `pv_time` for kvmclock.
- Steal time uses `struct gfn_to_hva_cache`, and the nested posted-interrupt
  descriptor uses `struct kvm_host_map`; neither is a pfn cache.
- `kvm_gpc_mark_dirty_in_slot()` in `include/linux/kvm_host.h`: what users
  call after a write; it asserts `gpc->lock` and does nothing for a cache
  activated by hva.
- `kvm_gpc_check()`, and `kvm_gpc_refresh()` for a cache activated by gpa,
  call `kvm_memslots()`, so the caller holds `kvm->srcu`;
  `kvm_xen_set_evtchn_fast()` and `kvm_xen_set_evtchn()` take it explicitly.
- `kvm_gpc_refresh()`: resolves the hva through `current->mm`, so a caller
  outside the VM's tasks adopts `kvm->mm` first; `kvm_xen_set_evtchn()` does
  it with `kthread_use_mm()`.
- **Unsafe usage**: accessing `gpc->khva` without `gpc->lock` because the
  vCPU is in guest mode, as the kerneldoc of `kvm_gpc_check()` allows;
  `gfn_to_pfn_cache_invalidate_start()` only clears `valid` and kicks no vCPU.
  - Safe: hold `gpc->lock` for read from `kvm_gpc_check()` to the last
    access, as `kvm_setup_guest_pvclock()` does;
    `gfn_to_pfn_cache_invalidate_start()` takes it for write to clear
    `valid`.

**Refreshing the pfn cache**

- `gfn_to_pfn_cache_invalidate_start()`: only clears `gpc->valid`; it does not
  touch `mmu_invalidate_in_progress` or the invalidation range.
- `kvm_mmu_notifier_invalidate_range_start()`: raises
  `kvm->mn_active_invalidate_count` before it calls
  `gfn_to_pfn_cache_invalidate_start()`, and before `mmu_lock` is taken.
- `mmu_notifier_retry_cache()`: has no range test; any MMU notifier
  invalidation in flight on the VM, or any change of `mmu_invalidate_seq`,
  makes the refresh retry.
- `gfn_to_pfn_cache_invalidate_start()`: takes `gpc->lock` for read first and
  for write only on a match; it skips a cache whose `valid` is false.
- `hva_to_pfn_retry()`: clears `valid` before it drops the lock, so an
  invalidation during the refresh never touches the cache; only the recheck
  in `mmu_notifier_retry_cache()` catches it.
- `mmu_invalidate_seq`: bumped by `kvm_mmu_invalidate_end()`, which
  `kvm_handle_hva_range()` calls only when the range intersects a memslot;
  `mn_active_invalidate_count` is raised and lowered for every MMU notifier
  invalidation.

## Invalidation and the retry protocol

**Invalidation state**

- There is no kvm_mmu_invalidate_begin() in this tree; the function is
  `kvm_mmu_invalidate_start()` in `virt/kvm/kvm_main.c`.
- Range reset: `kvm_mmu_invalidate_start()` sets `mmu_invalidate_range_start`
  and `mmu_invalidate_range_end` to `INVALID_GPA`, and only when the count
  goes from 0 to 1.
- `kvm_mmu_invalidate_end()`: never writes the range; after the last end the
  fields keep the last union until the next 0 to 1 start.
- Several adds per invalidation: x86 `kvm_arch_pre_set_memory_attributes()`
  calls `kvm_mmu_invalidate_range_add()` for the hugepage ranges around the
  head and tail, so the recorded range can be wider than the range being
  changed.

**Notifier callbacks**

- There is no __kvm_handle_hva_range() here; `kvm_handle_hva_range()` in
  `virt/kvm/kvm_main.c` is the hva walker and returns `kvm_mn_ret_t`.
- `on_lock` of `kvm_mmu_notifier_invalidate_range_start()`:
  `kvm_mmu_invalidate_start()`.
- `range->lockless`: the only field that changes locking;
  `kvm_handle_hva_range()` then never takes `mmu_lock` and calls the handler
  under SRCU alone.
- A lockless handler may lock for itself: s390 `kvm_age_gfn()` and
  `kvm_test_age_gfn()` take `mmu_lock` for read.
- `range->may_block`: only copied into `struct kvm_gfn_range`; no effect on
  when `kvm_handle_hva_range()` locks.
- `kvm_age_hva_range()`: sets `lockless` from
  `CONFIG_KVM_MMU_LOCKLESS_AGING`, which x86 and s390 select.
- `lockless` with a non-null `on_lock`: `WARN_ON_ONCE()` and return before
  any handler is called.
- Flush with `lockless`: `kvm_flush_remote_tlbs()` runs with no `mmu_lock`
  held.
- `kvm_mmu_notifier_clear_flush_young()`: `flush_on_ret` is
  `!IS_ENABLED(CONFIG_KVM_ELIDE_TLB_FLUSH_IF_YOUNG)`; x86 selects that
  option, so no x86 aging callback flushes.

**Invalidation outside notifiers**

- There is no kvm_gmem_invalidate_begin() here; guest_memfd uses
  `kvm_gmem_invalidate_start()` and `__kvm_gmem_invalidate_start()` in
  `virt/kvm/guest_memfd.c`.
- `kvm_mmu_invalidate_end()` asserts three things: the write lock,
  `KVM_BUG_ON()` if the count is negative after the decrement, and
  `WARN_ON_ONCE(kvm->mmu_invalidate_range_start == INVALID_GPA)`.
- `kvm_mmu_invalidate_end()` has no check that the count was non-zero before
  the decrement, other than the negative test.
- No-range warning: masked while another invalidation overlaps, since the
  range is reset only on the 0 to 1 start.
- Range before first unlock: after `kvm_mmu_invalidate_start()`, call
  `kvm_mmu_invalidate_range_add()` before `mmu_lock` is dropped; a fault that
  takes the lock in between finds the count non-zero and the range still
  `INVALID_GPA`, which `mmu_invalidate_retry_gfn()` warns about, see "Retry
  helpers".
- Zap inside the window: x86 `kvm_unmap_gfn_range()` asserts
  `mmu_invalidate_in_progress` non-zero or `slots_lock` held.
- Both or neither: where start and end are each conditional on finding a
  slot or binding, that set must not change between them.
  - guest_memfd: `filemap_invalidate_lock()` or
    `filemap_invalidate_lock_shared()` held across both.
  - `kvm_vm_set_mem_attributes()`: `slots_lock` held across both.
- `__kvm_gmem_invalidate_start()`: unlocks `mmu_lock` before returning;
  `__kvm_gmem_invalidate_end()` retakes it; in `kvm_gmem_punch_hole()` the
  truncate runs in between.
- `kvm_gmem_release()` and `kvm_gmem_error_folio()`: also bracket with
  start and end; neither truncates.
- `kvm_zap_gfn_range()` in `arch/x86/kvm/mmu/mmu.c`: start, add, zap, flush,
  end under one `write_lock()`, but both zap helpers are called with yielding
  allowed, so the lock can be dropped inside the window.
- `mmu_invalidate_seq` is also incremented directly, with no start/end pair,
  under `mmu_lock`: for example `invalidate_vncr_va()` in
  `arch/arm64/kvm/nested.c` and `kvmppc_radix_flush_memslot()`.

**Fault handler sequence**

- arm64 `user_mem_abort()` holds none of the steps itself; the helpers below
  hold them.

| Step | arm64, `arch/arm64/kvm/mmu.c` |
|---|---|
| snapshot | `kvm_s2_fault_get_vma_info()`, into `s2vi->mmu_seq`; called from `kvm_s2_fault_pin_pfn()`, not from `user_mem_abort()` |
| barrier | no `smp_rmb()` call; `mmap_read_unlock()` is the next statement |
| resolve | `kvm_s2_fault_pin_pfn()`, with `__kvm_faultin_pfn()` |
| lock, check, install, release | `kvm_s2_fault_map()` |

- `kvm_s2_fault_get_vma_info()`: reads the VMA data before the snapshot, both
  under `mmap_read_lock()`.
- `kvm_s2_fault_compute_prot()` non-zero return: runs between resolve and
  lock; `user_mem_abort()` then releases with `kvm_release_page_unused()`.
- `kvm_fault_lock()`: read lock, or write lock when
  `is_protected_kvm_enabled()`.
- `gmem_abort()`: used when `kvm_slot_has_gmem()` and the VM is not
  `kvm_vm_is_protected()`; all steps in one function, with an explicit
  `smp_rmb()` and `kvm_gmem_get_pfn()`.
- `pkvm_mem_abort()`: used when `kvm_vm_is_protected()`; takes no snapshot and
  makes no retry check; it pins with `pin_user_pages()` and `FOLL_LONGTERM`,
  and arm64 `kvm_unmap_gfn_range()` returns early for such a VM.
- There is no __gfn_to_pfn_memslot() here; `__kvm_faultin_pfn()` in
  `virt/kvm/kvm_main.c` resolves the frame.
- x86 shadow paging: `FNAME(page_fault)` in `arch/x86/kvm/mmu/paging_tmpl.h`
  takes the write lock, checks, and installs with `FNAME(fetch)`.
- x86 lock mode: `kvm_tdp_mmu_page_fault()` read; `direct_page_fault()` and
  `FNAME(page_fault)` write.
- x86 `kvm_mmu_faultin_pfn()`: reads `kvm_mem_is_private()` after the
  snapshot, so an attribute change is caught by the same check.

**Retry helpers**

- `smp_rmb()` between the two reads: only in `mmu_invalidate_retry()`;
  `mmu_invalidate_retry_gfn()` has none, and
  `mmu_invalidate_retry_gfn_unsafe()` has none.
- `mmu_invalidate_retry()`: no lockdep assertion.
  - Book3S HV HPT calls it under `lock_rmap()` and not `mmu_lock`, in
    `kvmppc_book3s_hv_page_fault()` and `kvmppc_do_h_enter()`.
- `mmu_invalidate_retry_gfn()`: `lockdep_assert_held()`, so read or write.
- `mmu_invalidate_retry_gfn()` with count non-zero and a range field still
  `INVALID_GPA`: `WARN_ON_ONCE()` and return 1.
- `mmu_invalidate_retry_gfn_unsafe()`: `READ_ONCE()` on the count and the
  sequence only; the range fields are plain reads and may be stale.
- Users outside x86 of the gfn form, for example: loongarch
  `kvm_map_page()`, riscv `kvm_riscv_mmu_dirty_log_write_fault_fast()`, s390
  `kvm_s390_faultin_gfn()`.
- riscv `kvm_riscv_mmu_map()` and arm64 `kvm_s2_fault_map()`, `gmem_abort()`
  and `kvm_translate_vncr()`: use `mmu_invalidate_retry()`.
- `mmu_invalidate_retry_gfn_unsafe()` users, for example: x86
  `kvm_mmu_faultin_pfn()`, before and after the lookup, and s390
  `kvm_s390_faultin_gfn()`.

**Using the retry check**

- **Unsafe usage**: calling, between the locked check and the install, a
  helper that may yield `mmu_lock`.
  - Unsafe: `kvm_mmu_invalidate_start()` asserts the write lock, so the
    check holds only while the lock is held.
  - Safe: call it in its no-yield mode, as `FNAME(fetch)` does with
    `mmu_sync_children(vcpu, sp, false)`; on contention that returns
    `-EINTR` and the fault returns `RET_PF_RETRY`.
- **Potentially unsafe usage**: making the last check before install without
  `mmu_lock`.
  - Unsafe: when the lock held instead is not one the unmap path takes for
    that gfn; an invalidation can then start after the check.
  - Safe: under `lock_rmap()` on the gfn's rmap entry, with the HPTE put on
    that rmap chain under the same hold, as `kvmppc_do_h_enter()` does;
    `kvm_unmap_rmapp()` takes that lock for each gfn it unmaps.
- **Potentially unsafe usage**: returning for retry after
  `mmu_invalidate_retry_gfn_unsafe()` fires.
  - Unsafe: after the frame was resolved, without releasing the page.
  - Safe: before the lookup, when no page is held, as the first check in
    `kvm_mmu_faultin_pfn()`.
  - Safe: after the lookup, releasing the page as unused first, as
    `kvm_mmu_faultin_pfn()` does through `kvm_mmu_finish_page_fault()` and
    `kvm_s390_faultin_gfn()` does through `kvm_release_faultin_page()`.
- Retry inside the kernel: allowed if the lock is dropped, the page released
  and the snapshot taken again; loongarch `kvm_map_page()` and
  `kvm_s390_faultin_gfn()` loop this way.
- Users that are not fault handlers follow the same order: for example
  `vmx_set_apic_access_page_addr()` and `__sev_snp_reload_vmsa()`, which
  request a reload on retry.

**Stale fault check on x86**

- Second test: `!sp && kvm_test_request(KVM_REQ_MMU_FREE_OBSOLETE_ROOTS,
  vcpu)`; `is_page_fault_stale()` does not test `VALID_PAGE()`.
- Third test: gated on `fault->slot`; a fault with no slot skips
  `mmu_invalidate_retry_gfn()`.
- `__kvm_mmu_zap_all_fast_front_half()`: toggles `mmu_valid_gen` between 0
  and 1, invalidates `KVM_DIRECT_ROOTS` only, and makes the request, all
  under one write-lock hold.
- Senders of `KVM_REQ_MMU_FREE_OBSOLETE_ROOTS`, the full set:
  - `__kvm_mmu_zap_all_fast_front_half()`, to all vCPUs
  - `__kvm_mmu_prepare_zap_page()`, to all vCPUs, when it zaps a page with
    non-zero `root_count` that was not already obsolete
  - `FNAME(fetch)`, to its own vCPU, when the root is a dummy root
- Zap-all on memslot delete or move: only when `kvm->arch.vm_type` is
  `KVM_X86_DEFAULT_VM` and `KVM_X86_QUIRK_SLOT_ZAP_ALL` is enabled.
- Slot-only zap: no `mmu_valid_gen` toggle and no `mmu_invalidate_seq` bump;
  `kvm_mmu_faultin_pfn()` catches it earlier by testing `KVM_MEMSLOT_INVALID`.

**Remote TLB flushes**

- There is no CONFIG_HAVE_KVM_ARCH_TLB_FLUSH_ALL and no
  kvm_arch_flush_remote_tlbs_memslot() here.
- Override: the arch defines `__KVM_HAVE_ARCH_FLUSH_REMOTE_TLBS` or
  `__KVM_HAVE_ARCH_FLUSH_REMOTE_TLBS_RANGE` in its `asm/kvm_host.h` and
  supplies the matching function; each is independent of the other.
- x86: defines both only when `IS_ENABLED(CONFIG_HYPERV)`; otherwise it gets
  the generic stubs.
- Stub return values: `kvm_arch_flush_remote_tlbs()` returns `-ENOTSUPP`,
  `kvm_arch_flush_remote_tlbs_range()` returns `-EOPNOTSUPP`; generic code
  tests only for zero.
- `kvm_flush_remote_tlbs_memslot()`: asserts `slots_lock` and nothing else.

**Long walks under MMU lock**

- Generic code: nothing under `virt/kvm/` yields `mmu_lock` itself;
  `kvm_handle_hva_range()`, `kvm_handle_gfn_range()` and the dirty-log loops
  never drop it mid-walk, only the arch handler they call may yield.
- `cond_resched_lock()`: not called on `mmu_lock` in any kvm directory; yield
  sites use `cond_resched_rwlock_write()` or `cond_resched_rwlock_read()`, or
  unlock fully.
- `may_block` in `struct kvm_gfn_range`: the arch walk yields only if it is
  set; aging passes false, `kvm_mmu_notifier_invalidate_range_start()` passes
  `mmu_notifier_range_blockable()`.
- `tdp_mmu_iter_cond_resched()`: does not call `tdp_iter_restart()`; it sets
  `iter->yielded`, and `tdp_iter_next()` restarts from the root.
- After `tdp_mmu_iter_cond_resched()` returns true the caller must
  `continue`; `tdp_mmu_iter_set_spte()` and `__tdp_mmu_set_spte_atomic()`
  warn if `iter->yielded` is set.
- `tdp_mmu_iter_need_resched()`: refuses to yield until
  `next_last_level_gfn` differs from `yielded_gfn`.
- Leaving a yield-safe root loop early: the caller must call
  `kvm_tdp_mmu_put_root()`, as `kvm_tdp_mmu_try_split_huge_pages()` does,
  unless it keeps the reference, as `kvm_tdp_mmu_alloc_root()` does.
- `tdp_mmu_split_huge_pages_root()`: unlocks fully to allocate, then sets
  `iter.yielded` itself.
- `__walk_slot_rmaps()`: yields only if `can_yield`; does not restart, the
  rmap iterator continues from its current gfn.
- `kvm_zap_obsolete_pages()`: yields without calling
  `kvm_mmu_commit_zap_page()`; it commits once after the loop, and restarts
  the list walk after a yield.
- `mmu_sync_children()`: re-walks from the parent after each yield.
- arm64 `stage2_apply_range()`: re-reads `mmu->pgt` for every chunk and
  returns if it is NULL, 0 if the lock was dropped and `-EINVAL` if not.
- arm64 `kvm_mmu_split_huge_pages()`: unlocks fully, then re-reads
  `kvm->arch.mmu.pgt`.
- **Potentially unsafe usage**: yielding `mmu_lock` with SPTEs zapped and
  not yet flushed.
  - Unsafe: for SPTEs zapped from a valid root for an invalidation; a second
    invalidation of the range finds nothing to zap, and
    `kvm_handle_hva_range()` flushes only if a handler returned true.
  - Safe: flush first, as `tdp_mmu_zap_leafs()` does by passing `flush` to
    `tdp_mmu_iter_cond_resched()`, and `__kvm_rmap_zap_gfn_range()` does with
    `flush_on_yield`.
  - Safe: shadow pages of an obsolete generation, after
    `__kvm_mmu_zap_all_fast_front_half()` requested
    `KVM_REQ_MMU_FREE_OBSOLETE_ROOTS` in the same lock hold, as
    `kvm_zap_obsolete_pages()` does.
  - Safe: SPTEs under an invalid TDP root; `tdp_mmu_zap_leafs()` sets `flush`
    only when `!root->role.invalid`.
  - Safe: write-protection for dirty logging, flushed after unlock under
    `slots_lock` with `kvm_flush_remote_tlbs_memslot()`, as
    `kvm_mmu_slot_apply_flags()` does.
  - Safe: a zap of everything for `kvm_arch_flush_shadow_all()`, which
    generic code calls from `kvm_mmu_notifier_release()`, as
    `kvm_mmu_zap_all()` and `kvm_tdp_mmu_zap_all()` do; the mm is exiting or
    the VM is being destroyed, and `kvm_vcpu_ioctl()` returns `-EIO` when
    `kvm->mm != current->mm`.

## x86 shadow pages and SPTEs

**Invalid shadow pages**

- `__kvm_mmu_prepare_zap_page()` in `arch/x86/kvm/mmu/mmu.c`: sets
  `sp->role.invalid = 1` on every page it zaps, root or not.
- `__kvm_mmu_prepare_zap_page()` asserts nothing about the bit; its only
  assertion is `lockdep_assert_held_write(&kvm->mmu_lock)`.
- Zapping an already invalid page is an expected path: `mmu_free_root_page()`
  calls `kvm_mmu_prepare_zap_page()` when `root_count` reaches zero on an
  invalid root, and `kvm_mmu_free_roots()` then commits the list.
- Hash list: an invalid page stays hashed until `kvm_mmu_free_shadow_page()`.
- Lookup: `for_each_valid_sp()` skips the page through `is_obsolete_sp()`,
  before `kvm_mmu_find_shadow_page()` compares `role.word`.
- There is no kvm_mmu_get_page() function here, only the tracepoint
  `trace_kvm_mmu_get_page()`; `__kvm_mmu_get_shadow_page()` does the lookup or
  the allocation.
- `kvm_mmu_child_role()`: copies the parent role, does
  `WARN_ON_ONCE(role.invalid)`, then clears `role.invalid` in the child role.
- TDP MMU: `kvm_tdp_mmu_invalidate_roots()` sets the bit on roots only, and
  does not zap them.
- An invalid TDP MMU root stays on `kvm->arch.tdp_mmu_roots` until the final
  `kvm_tdp_mmu_put_root()`, and keeps its SPTEs until they are zapped, for
  example by `tdp_mmu_zap_root()`.
- Root iteration through `tdp_mmu_root_match()` in
  `arch/x86/kvm/mmu/tdp_mmu.c` skips invalid roots unless the root types
  include `KVM_INVALID_ROOTS`.
- `tdp_mmu_init_child_sp()`: copies the parent role and lowers `level`; it
  neither warns on nor clears `role.invalid`.
- `kvm_tdp_mmu_put_root()`: `KVM_BUG_ON()` if the final reference is put on a
  root that is not invalid.

**Obsolete shadow pages**

- TDP MMU pages: obsolete for `is_obsolete_sp()` when `role.invalid` is set;
  only the generation comparison is skipped for them.
- The generation toggle is in `__kvm_mmu_zap_all_fast_front_half()` in
  `arch/x86/kvm/mmu/mmu.c`, which asserts `slots_lock` and `mmu_lock` held
  for write.
- `__kvm_mmu_zap_all_fast_front_half()` has two callers:
  `kvm_mmu_zap_all_fast()` and `kvm_arch_flush_shadow_memslot()`, the latter
  only when its `zap_all` condition holds.
- Obsolete roots in `kvm_zap_obsolete_pages()`: not skipped, there is no
  `root_count` test in the walk.
- A root with nonzero `root_count`: `__kvm_mmu_prepare_zap_page()` removes it
  from `active_mmu_pages` with `list_del()` and does not put it on the
  invalid list.
- Restart from the tail in `kvm_zap_obsolete_pages()`: makes progress only
  because every page given to `__kvm_mmu_prepare_zap_page()` leaves
  `active_mmu_pages`.
- An invalid page found on `active_mmu_pages` by `kvm_zap_obsolete_pages()`:
  skipped with `WARN_ON_ONCE(sp->role.invalid)` and `continue`, not zapped.

**Atomic SPTE updates**

- `spte_needs_atomic_update()` in `arch/x86/kvm/mmu/spte.c`: has no presence
  test; the caller must check `is_shadow_present_pte()` first.
- `spte_needs_atomic_update()` returns true for `!spte_ad_enabled(spte)`, so
  for every A/D-disabled SPTE, not only one that is access-tracked now.
- `spte_needs_atomic_update()` ignores the Accessed bit only. A clear Dirty
  bit on a writable A/D-enabled SPTE makes the function return true.
- There is no mmu_spte_update_no_track() here; `mmu_spte_update()` in
  `arch/x86/kvm/mmu/mmu.c` picks the form itself.
- `mmu_spte_update()` and `mmu_spte_clear_track_bits()`: call
  `__update_clear_spte_slow()` only when the old SPTE is shadow-present and
  `spte_needs_atomic_update()` is true; a present SPTE that does not need it
  gets `__update_clear_spte_fast()`.
- `__update_clear_spte_slow()` with `CONFIG_X86_64`: one `xchg()` of the SPTE.
- `__update_clear_spte_slow()` without `CONFIG_X86_64`: `xchg()` of the low 32
  bits, then a plain store of the high half.
- Shadow MMU aging: `kvm_rmap_age_gfn_range()` uses `cmpxchg64()` with no
  retry, for A/D SPTEs and for access tracking; it does not call
  `clear_bit()`.
- `__rmap_clear_dirty()`: uses `test_and_clear_bit()` on `PT_WRITABLE_SHIFT`
  when `spte_ad_need_write_protect()` is true, else `mmu_spte_update()`
  through `spte_clear_dirty()`.
- There is no function kvm_tdp_mmu_spte_need_atomic_write(); the test is
  `kvm_tdp_mmu_spte_need_atomic_update()` in `arch/x86/kvm/mmu/tdp_iter.h`.
- TDP MMU aging: `kvm_tdp_mmu_age_spte()` calls `__tdp_mmu_set_spte_atomic()`
  under RCU and ignores a failure.
- `tdp_mmu_clear_spte_bits()`: its one caller is `clear_dirty_pt_masked()`,
  with `mmu_lock` held for write.
- Zap under the read lock, non-mirror SPTE: `tdp_mmu_set_spte_atomic()` writes
  `SHADOW_NONPRESENT_VALUE` directly, with no freeze step; there is no
  tdp_mmu_zap_spte_atomic() here.
- `tdp_mmu_set_spte_atomic()` on a mirror SPTE: `try_cmpxchg64()` to
  `FROZEN_SPTE`, then `__kvm_tdp_mmu_write_spte()` of the new value, or of the
  old value if the external update failed.
- `handle_removed_pt()` with `shared`: loops on
  `kvm_tdp_mmu_write_spte_atomic()` to `FROZEN_SPTE` for every entry, without
  consulting `spte_needs_atomic_update()`.

## Dirty tracking

**Marking a page dirty**

- Both `WARN_ON_ONCE()` checks: compiled under `CONFIG_HAVE_KVM_DIRTY_RING`
  and do not test `kvm->dirty_ring_size`, so they can also fire on a VM that
  uses only the bitmap.
- No-vCPU warning: also skipped when `refcount_read(&kvm->users_count)` is 0.
- `kvm_arch_allow_write_without_running_vcpu()`: arm64 is the only override
  (`arch/arm64/kvm/vgic/vgic-its.c`); x86 has none and gets the
  `return false` version in `virt/kvm/dirty_ring.c`.
- The hook only silences the warning; it has no part in choosing ring or
  bitmap.
- arm64 window: `table_write_in_progress` is set around every
  `vgic_write_guest_lock()` call (`arch/arm64/kvm/vgic/vgic.h`), which covers
  ITS table writes, `vgic_v3_save_pending_tables()` and
  `vgic_v3_lpi_sync_pending_status()`.
- Gate for recording: `memslot && kvm_slot_dirty_track_enabled(memslot)`, the
  `KVM_MEM_LOG_DIRTY_PAGES` flag, not `memslot->dirty_bitmap`.
- `memslot->dirty_bitmap` is tested only after `kvm->dirty_ring_size && vcpu`
  fails; a slot that turns logging on in ring-only mode gets no bitmap from
  `kvm_prepare_memory_region()`.
- **Potentially unsafe usage**: calling `mark_page_dirty_in_slot()`,
  `mark_page_dirty()` or `kvm_write_guest()` with no running vCPU.
  - Unsafe: under `CONFIG_HAVE_KVM_DIRTY_RING`, when the hook returns false
    and `users_count` is non-zero; the `WARN_ON_ONCE()` in
    `mark_page_dirty_in_slot()` fires, and with a ring and no bitmap the write
    is not recorded.
  - Safe: inside the window the hook reports, on a VM with
    `kvm->dirty_ring_with_bitmap` set or no ring, as `vgic_write_guest_lock()`
    does; the bit goes to the bitmap.
  - Safe: on an architecture that does not select
    `CONFIG_HAVE_KVM_DIRTY_RING`, as s390 `adapter_indicators_set()` does; the
    `WARN_ON_ONCE()` in `mark_page_dirty_in_slot()` is compiled out and the
    bit goes to the bitmap.

**Dirty bitmap**

- `kvm_get_dirty_log_protect()` and `kvm_clear_dirty_log_protect()`: static,
  built only with `CONFIG_KVM_GENERIC_DIRTYLOG_READ_PROTECT`.
- Without that option: `kvm_get_dirty_log()` is built instead; it copies the
  live bitmap and neither clears nor protects, and `KVM_CLEAR_DIRTY_LOG` is
  not handled.
- Kerneldoc above `kvm_get_dirty_log_protect()` and
  `kvm_vm_ioctl_get_dirty_log()`: lists "copy to userspace, then caller
  flushes"; the code flushes inside `kvm_get_dirty_log_protect()` before
  `copy_to_user()`, and the caller flushes nothing.
- TLB flush locking: runs after `KVM_MMU_UNLOCK()` in both GET and CLEAR, in
  generic code; `kvm_flush_remote_tlbs_memslot()` asserts `kvm->slots_lock`.
- `KVM_MMU_LOCK()`: `write_lock()` only where the arch defines
  `KVM_HAVE_MMU_RWLOCK`, otherwise `spin_lock()`; see `virt/kvm/kvm_mm.h`.
- GET with `kvm->manual_dirty_log_protect`: copies the live bitmap as is;
  clears no bit, takes no `mmu_lock`, never touches the second half.
- GET without manual protect: clears each non-zero word with `xchg()`, not an
  atomic_long helper.
- `kvm_alloc_dirty_bitmap()`: `__vcalloc(2, dirty_bytes, GFP_KERNEL_ACCOUNT)`.
- Second half outside generic code: x86 does not use it;
  `kvm_vm_ioctl_get_dirty_log_hv()` in `arch/powerpc/kvm/book3s_hv.c` uses it
  as its output buffer, by open-coded pointer arithmetic rather than
  `kvm_second_dirty_bitmap()`.

**Dirty ring**

- `kvm_dirty_ring_push()` publish step: `smp_wmb()` followed by a plain store
  of `KVM_DIRTY_GFN_F_DIRTY` in `kvm_dirty_gfn_set_dirtied()`; it does not use
  `smp_store_release()`.
- `smp_store_release()`: used only by `kvm_dirty_gfn_set_invalid()` on the
  reset side, after slot and offset have been read.
- `dirty_index` and `reset_index`: kernel-private in `struct kvm_dirty_ring`;
  the mapped pages hold only the `struct kvm_dirty_gfn` array, so `flags` is
  the whole handshake with userspace.
- `kvm_dirty_ring_reset()` and `kvm_reset_dirty_gfn()`: call no TLB flush
  themselves.
- TLB flush after reset: `kvm_vm_ioctl_reset_dirty_pages()` calls
  `kvm_flush_remote_tlbs()` once for all rings, after it drops `slots_lock`,
  and only when at least one entry was reset.
- `kvm_dirty_ring_reset()` signature: `(kvm, ring, int *nr_entries_reset)`;
  returns 0, or `-EINTR` when a signal is pending.
- `*nr_entries_reset`: one counter shared across all vCPUs of the ioctl; the
  walk stops when it reaches `INT_MAX`.
- `kvm_cpu_dirty_log_size()`: takes `struct kvm *`; weak default returning 0
  in `virt/kvm/dirty_ring.c`, x86 override in `arch/x86/kvm/mmu/mmu.c` returns
  `kvm->arch.cpu_dirty_log_size`.

**Ring together with bitmap**

- Config symbol: there is no CONFIG_HAVE_KVM_DIRTY_RING_WITH_BITMAP here;
  `CONFIG_NEED_KVM_DIRTY_RING_WITH_BITMAP` in `virt/kvm/Kconfig` is the one,
  selected only by arm64.
- Writes that reach the bitmap: every `mark_page_dirty_in_slot()` call with no
  running vCPU on a logging slot, whether or not
  `kvm_arch_allow_write_without_running_vcpu()` returns true.
- `kvm_use_dirty_bitmap()` without `CONFIG_HAVE_KVM_DIRTY_RING`: an inline
  stub in `include/linux/kvm_dirty_ring.h` that returns `true` and asserts no
  lock.
- `kvm_prepare_memory_region()`: reuses `old->dirty_bitmap` before it asks
  `kvm_use_dirty_bitmap()`; there the helper decides only a fresh allocation.

## guest_memfd and memory attributes

**guest_memfd files and bindings**

- `struct gmem_inode` in `virt/kvm/guest_memfd.c`: holds `policy`,
  `vfs_inode`, `gmem_file_list` and `flags`; the size is `vfs_inode.i_size`.
- `gmem_file_list`: the list that `entry` of `struct gmem_file` links on;
  walk it with `kvm_gmem_for_each_file()`. Nothing in `virt/kvm` uses a
  list in the `struct address_space`.
- Shareability state on the inode: only `GUEST_MEMFD_FLAG_INIT_SHARED` in
  `flags`; `kvm_gmem_is_private_mem()` ignores its `index` argument, so the
  whole inode is private or shared.
- VM reference: taken by `__kvm_gmem_create()`, dropped as the last step of
  `kvm_gmem_release()`. `kvm_gmem_bind()` takes no VM reference and keeps no
  file reference.
- `slot->gmem.file`: a plain `struct file *` written with `WRITE_ONCE()`,
  not `__rcu`; `kvm_gmem_get_file()` takes a reference on it with
  `get_file_active()`.
- `kvm_gmem_release()`: zaps with `__kvm_gmem_invalidate_start()` and
  `__kvm_gmem_invalidate_end()`.
- `kvm_gmem_unbind()` has three cases:
  - `slot->gmem.file` is NULL (release already ran): returns at once.
  - pointer set but `get_file_active()` fails (last `fput()` done,
    `kvm_gmem_release()` has not yet cleared the pointer): clears the
    bindings through `slot->gmem.file->private_data`; safe only because the
    caller holds `kvm->slots_lock`, which `kvm_gmem_release()` needs before
    it frees the `struct gmem_file`.
  - file alive: clears the bindings under `filemap_invalidate_lock()`.
- VM destruction: every `slot->gmem.file` is already NULL, because each file
  holds the VM until `kvm_gmem_release()` has cleared its bindings.

**Checks made at binding**

- Overlap with an existing binding: `kvm_gmem_bind()` returns `-EEXIST`;
  every other failure after `fget()` returns `-EINVAL`.
- `offset`: type `uoff_t`, so there is no sign test; the range tests are
  `PAGE_ALIGNED(offset)` and `offset + size > i_size_read(inode)` only.
- Wrap of `offset + size`: not tested in `kvm_gmem_bind()`;
  `kvm_set_memory_region()` rejects it with `-EINVAL` before the call.
- `kvm_gmem_release()`: takes `kvm->slots_lock` itself, then
  `filemap_invalidate_lock()` inside it.
- `kvm_gmem_bind()` and `kvm_gmem_unbind()`: neither asserts
  `kvm->slots_lock`; the `lockdep_assert_held()` is in
  `kvm_set_memory_region()`.
- `kvm_gmem_unbind()`: does not call `synchronize_rcu()`; it relies on
  `synchronize_srcu_expedited()` in `kvm_swap_active_memslots()` having run
  before the old memslot is freed.

**Frames from guest_memfd**

- There is no kvm_arch_gmem_prepare(), kvm_gmem_prepare_folio() or
  CONFIG_HAVE_KVM_ARCH_GMEM_PREPARE here; the hook is
  `kvm_arch_gmem_make_private()` under `CONFIG_HAVE_KVM_ARCH_GMEM_CONVERT`,
  called directly from `kvm_gmem_get_pfn()` with the folio locked.
- `kvm_arch_gmem_make_private()`: runs on every `kvm_gmem_get_pfn()` call
  where `kvm_gmem_is_private_mem()` holds, whether or not the folio is
  uptodate, so an implementation must tolerate repeat calls.
- x86 implementation `sev_gmem_make_private()` in `arch/x86/kvm/svm/sev.c`:
  returns 0 for a non-SNP VM, and for an RMP entry already assigned.
- `folio_test_uptodate()`: gates only `clear_highpage()` and
  `folio_mark_uptodate()` in `kvm_gmem_get_pfn()`; it says nothing about the
  hook.
- Hook failure: the folio reference is dropped and the error returned;
  `*pfn` has already been written, `*page` has not.
- `max_order`: may be NULL; `kvm_gmem_get_pfn()` substitutes a local.
- `kvm_gmem_populate()`: goes through `__kvm_gmem_get_pfn()`, so it runs no
  hook and no zeroing; it marks the folio uptodate after `post_populate`
  succeeds, under `filemap_invalidate_lock()`.
- There is no kvm_arch_gmem_invalidate() here. `kvm_arch_gmem_reclaim()`
  (`CONFIG_HAVE_KVM_ARCH_GMEM_RECLAIM`) runs from `kvm_gmem_free_folio()`.
- `kvm_arch_gmem_invalidate_range()` (`CONFIG_HAVE_KVM_ARCH_GMEM_INVALIDATE`):
  a separate hook, run under `mmu_lock` from `__kvm_gmem_invalidate_start()`
  and from x86 `kvm_arch_flush_shadow_memslot()`.
- `get_file_active()` protects the file only; the memslot stays valid
  because the caller is inside `kvm->srcu` or holds `kvm->slots_lock`.

**Faults that use guest_memfd**

- There is no kvm_mmu_faultin_pfn_private() and no fault_from_gmem() here;
  `__kvm_mmu_faultin_pfn()` in `arch/x86/kvm/mmu/mmu.c` open-codes
  `fault->is_private || kvm_memslot_is_gmem_only(fault->slot)` and calls
  `kvm_mmu_faultin_pfn_gmem()`.
- `KVM_MEMSLOT_GMEM_ONLY`: set by `kvm_gmem_bind()` when the inode has
  `GUEST_MEMFD_FLAG_MMAP`; shared faults on such a slot use guest_memfd too.
- `fault->is_private`: always `err & PFERR_PRIVATE_ACCESS` in
  `kvm_mmu_do_page_fault()`; for `KVM_X86_SW_PROTECTED_VM`,
  `kvm_mmu_page_fault()` sets that bit from `kvm_mem_is_private()`.
- `kvm_gmem_get_pfn()` failure in `kvm_mmu_faultin_pfn_gmem()`: prepares the
  memory-fault exit and returns the error unchanged, for example
  `-EHWPOISON`, not only `-EFAULT`.
- There is no private_max_mapping_level hook here; the op is
  `gmem_max_mapping_level`, called from `kvm_gmem_max_mapping_level()` via
  `kvm_mmu_max_mapping_level()`, not from `kvm_mmu_faultin_pfn_gmem()`.
- Mapping level of a guest_memfd fault: `fault->max_level` is
  `PG_LEVEL_4K`, because `__kvm_gmem_get_pfn()` always reports order 0.

**Memory attributes**

- Pre pass `on_lock`: `kvm_mmu_invalidate_start()` in
  `virt/kvm/kvm_main.c`.
- `kvm_vm_set_mem_attributes()` does not call `xa_store_range()`; it
  reserves per gfn with `xa_reserve()`, then stores per gfn with
  `xa_store()`.
- Clearing (`attributes` is 0): the `xa_reserve()` loop is skipped, so
  nothing after the early return can fail.
- Pre handler: `kvm_pre_set_memory_attributes()`, which calls
  `kvm_mmu_invalidate_range_add()` and then
  `kvm_arch_pre_set_memory_attributes()`; it is not
  `kvm_mmu_unmap_gfn_range()`.
- Post pass order: `kvm_mmu_invalidate_end()` is the `on_lock`, so it runs
  before the first `kvm_arch_post_set_memory_attributes()` call, in the same
  `mmu_lock` hold.
- Range that overlaps no memslot: `kvm_handle_gfn_range()` takes no
  `mmu_lock` and runs neither `on_lock` nor hook; the xarray is still
  updated and `mmu_invalidate_seq` does not change.
- Hooks: called once per overlapping memslot in each address space, with
  the range clamped to that memslot.

## Model gaps

### Other mistakes models make

- Models take an x86 memslot delete or move to always toggle `mmu_valid_gen`.
  When its `zap_all` condition is false, `kvm_arch_flush_shadow_memslot()`
  calls `kvm_unmap_gfn_range()` and `kvm_mmu_zap_memslot_pages_and_flush()`
  instead of the fast zap.
- Models take the x86 fast zap to be one function. `kvm_mmu_zap_all_fast()`
  calls `__kvm_mmu_zap_all_fast_front_half()` under `mmu_lock`, then
  `__kvm_mmu_zap_all_fast_back_half()`, which asserts `mmu_lock` is not held.
- Models take `struct kvm_gfn_range` to carry only slot, range, `arg` and
  `may_block`. It also has `attr_filter` and `lockless`.
  `kvm_handle_hva_range()` sets `KVM_FILTER_SHARED`; guest_memfd takes the
  filter from `kvm_gmem_get_invalidate_filter()`.
- Models take `GUEST_MEMFD_FLAG_INIT_SHARED` to be accepted on any VM. x86
  `kvm_arch_supports_gmem_init_shared()` returns false for a VM with private
  memory, and `kvm_gmem_create()` then fails with `-EINVAL`.
- Models take the review checklist to hold more than it does.
  `Documentation/virt/kvm/review-checklist.rst` has eleven items and a
  section on testing.
- Models miss that `kvm_mmu_child_role()` clears `passthrough` in the child
  role, as well as `invalid`.
- Models take `struct kvm_mmu` to hold the guest paging mode and walk
  callbacks. Those are in `struct kvm_pagewalk`, reached through `mmu->w`,
  which points at `vcpu->arch.gva_walk` or `vcpu->arch.ngpa_walk`; see
  `arch/x86/include/asm/kvm_host.h`.
