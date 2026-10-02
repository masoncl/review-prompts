| Job | File in this tree |
|---|---|
| EL2 page allocator | `arch/arm64/kvm/hyp/nvhe/page_alloc.c`; `arch/arm64/kvm/hyp/nvhe/early_alloc.c` serves `__pkvm_init()` until `__pkvm_init_finalise()` calls `hyp_pool_init()` |
| EL2 vectors | `arch/arm64/kvm/hyp/hyp-entry.S` (`__kvm_hyp_vector`, guest running, both builds); `arch/arm64/kvm/hyp/nvhe/host.S` (`__kvm_hyp_host_vector`, host running); `arch/arm64/kvm/hyp/nvhe/hyp-init.S` (`__kvm_hyp_init`, before init) |
| Code shared with the VHE build | the `../` entries of `obj-y` in `arch/arm64/kvm/hyp/vhe/Makefile`, plus headers in `arch/arm64/kvm/hyp/include/hyp/`; the list includes `vgic-v2-cpuif-proxy.c` and `vgic-v5-sr.c` |
| Not shared, same name in `nvhe/` and `vhe/` | `switch.c`, `sysreg-sr.c`, `timer-sr.c`, `debug-sr.c`, `tlb.c`; there is no top-level `sysreg-sr.c`, `timer-sr.c`, `debug-sr.c` or fpsimd.S under `arch/arm64/kvm/hyp/` |
| Page-table walker | `arch/arm64/kvm/hyp/pgtable.c`: built into the nVHE object and, by `arch/arm64/kvm/hyp/Makefile`, as a plain kernel object; `arch/arm64/kvm/hyp/vhe/Makefile` does not build it |
| All other jobs asked | Models have these right: `hyp-main.c`, `mem_protect.c`, `pkvm.c`, `mm.c`, `setup.c`, `ffa.c`, `psci-relay.c`, `sys_regs.c`, `switch.c` in `arch/arm64/kvm/hyp/nvhe/`; host glue `arch/arm64/kvm/pkvm.c` |
