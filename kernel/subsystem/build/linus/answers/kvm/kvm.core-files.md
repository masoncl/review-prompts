| Job | File in this tree |
|---|---|
| x86 MSR handling | `arch/x86/kvm/msrs.c` and `arch/x86/kvm/msrs.h`, not `arch/x86/kvm/x86.c`: `kvm_set_msr_common()`, `kvm_get_msr_common()`, `kvm_vm_ioctl_set_msr_filter()`, `kvm_set_user_return_msr()`, `kvm_emulate_rdmsr()`, `kvm_get_set_one_reg()` |
| x86 register access | `arch/x86/kvm/regs.h` for the inline register-cache accessors and mode tests such as `is_guest_mode()`; `arch/x86/kvm/regs.c` for `kvm_set_cr0()`, `kvm_set_cr4()`, `kvm_set_dr()`, `kvm_get_rflags()` and the regs and sregs ioctl handlers. There is no kvm_cache_regs.h in this tree |
| guest_memfd | `virt/kvm/guest_memfd.c`; its KVM-internal declarations are in `virt/kvm/guest_memfd.h`, not `virt/kvm/kvm_mm.h` |
| Async page faults, x86 side | split over `arch/x86/kvm/x86.c`, `arch/x86/kvm/mmu/mmu.c` (`kvm_arch_setup_async_pf()`, `kvm_arch_async_page_ready()`) and `arch/x86/kvm/msrs.c` (`kvm_pv_enable_async_pf()`) |
| Other generic and x86 KVM code | `virt/kvm/Makefile.kvm` and `arch/x86/kvm/Makefile` give the object lists |
