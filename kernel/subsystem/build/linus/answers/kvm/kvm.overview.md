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
