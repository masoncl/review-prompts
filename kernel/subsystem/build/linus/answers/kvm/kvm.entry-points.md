| Job | Start reading at |
|---|---|
| Dispatch a vCPU ioctl | `kvm_vcpu_ioctl()` in `virt/kvm/kvm_main.c`; the arch hooks are `kvm_arch_vcpu_unlocked_ioctl()` first, then `kvm_arch_vcpu_ioctl()`. There is no kvm_arch_vcpu_async_ioctl() here |
| Read the dirty log, bitmap | `kvm_vm_ioctl_get_dirty_log()`. With `CONFIG_KVM_GENERIC_DIRTYLOG_READ_PROTECT` (x86 and arm64, for example, select it) it is in `virt/kvm/kvm_main.c` and leads to `kvm_get_dirty_log_protect()`; without it the arch defines it, for example s390 through `kvm_get_dirty_log()` |
| Read the dirty log, ring | `kvm_vcpu_fault()` and `kvm_vm_ioctl_reset_dirty_pages()` in `virt/kvm/kvm_main.c`; `kvm_dirty_ring_push()` is the producer side |
| Guest frame to host page, x86 | `kvm_mmu_faultin_pfn()` in `arch/x86/kvm/mmu/mmu.c`, reached from `kvm_mmu_page_fault()` through `kvm_mmu_do_page_fault()`. x86 does not call `kvm_faultin_pfn()` |
| Guest frame to host page, arm64 | `kvm_handle_guest_abort()` in `arch/arm64/kvm/mmu.c`, which picks `pkvm_mem_abort()`, `gmem_abort()` or `user_mem_abort()`; the `__kvm_faultin_pfn()` call is in `kvm_s2_fault_pin_pfn()` |
| Make a request of a vCPU | `kvm_make_request()` in `include/linux/kvm_host.h`; `kvm_vcpu_kick()` is an inline over `__kvm_vcpu_kick()` in `virt/kvm/kvm_main.c`; `kvm_make_request_and_kick()` does both |
| Create a VM, create a vCPU, dispatch a VM ioctl, set a memory region, handle an MMU notifier invalidation | all are in `virt/kvm/kvm_main.c` |
