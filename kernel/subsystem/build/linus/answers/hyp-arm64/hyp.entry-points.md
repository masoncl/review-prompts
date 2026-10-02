| Job | Host side | EL2 side |
|---|---|---|
| Host takes a stage-2 fault | `is_pkvm_stage2_abort()` in `arch/arm64/mm/fault.c`; it tests `ESR_ELx_S1PTW`, which `host_inject_mem_abort()` sets | `handle_host_mem_abort()`, then `host_inject_mem_abort()` in `arch/arm64/kvm/hyp/nvhe/mem_protect.c` |
| A vCPU is run | `kvm_arm_vcpu_enter_exit()` in `arch/arm64/kvm/arm.c` | `handle___kvm_vcpu_run()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c` for pKVM too; VHE: `__kvm_vcpu_run()` in `arch/arm64/kvm/hyp/vhe/switch.c`, which calls the static `__kvm_vcpu_run_vhe()`. There is no handle___pkvm_vcpu_run() |
| A guest exit is fixed up | none | `fixup_guest_exit()`, static in `arch/arm64/kvm/hyp/nvhe/switch.c` and in `arch/arm64/kvm/hyp/vhe/switch.c`; shared part `__fixup_guest_exit()` in `arch/arm64/kvm/hyp/include/hyp/switch.h`; nVHE handler table via `kvm_get_exit_handler_array()` |
| A hyp VM is created | `pkvm_init_host_vm()` from `kvm_arch_init_vm()`; `pkvm_create_hyp_vm()` and `pkvm_create_hyp_vcpu()` from `kvm_arch_vcpu_run_pid_change()` | `__pkvm_reserve_vm()`, `__pkvm_init_vm()`, `__pkvm_init_vcpu()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c` |
| A page changes owner, host request | `kvm_share_hyp()` in `arch/arm64/kvm/mmu.c`; `pkvm_pgtable_stage2_map()` and `pkvm_force_reclaim_guest_page()` in `arch/arm64/kvm/pkvm.c` | `handle___pkvm_host_share_hyp()`, `handle___pkvm_host_donate_guest()`, `handle___pkvm_host_share_guest()`, `handle___pkvm_force_reclaim_guest_page()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`, then `arch/arm64/kvm/hyp/nvhe/mem_protect.c` |
| A page changes owner, guest request | none | `kvm_handle_pvm_hvc64()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`, then `__pkvm_guest_share_host()` |
| A page changes owner, EL2 internal | none | `__pkvm_host_donate_hyp()` and `__pkvm_hyp_donate_host()`: no entry in `host_hcall[]`, called only from EL2 code |
| Hypercall, SMC, panic | Models have these right | Models have these right |
