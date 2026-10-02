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
