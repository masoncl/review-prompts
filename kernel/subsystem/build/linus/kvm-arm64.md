# KVM on arm64

## Main structures

### Objects and how they relate

- Names absent from this tree: struct kvm_pinned_page, struct kvm_vgic_dist,
  struct irq_phys_map, __kvm_call_hyp. The distributor is `struct vgic_dist`;
  `kvm_call_hyp_nvhe()` issues the HVC through `arm_smccc_1_1_hvc()`.
- pKVM scope: with `is_protected_kvm_enabled()`, EL2 owns the stage-2 of
  every guest, protected or not. `pkvm_init_host_vm()` reserves a handle for
  each VM, and the first run creates its `struct pkvm_hyp_vm`.
- `struct kvm_pgtable` on the host under pKVM: not a page table. The
  page-table fields are in a union with `pkvm_mappings`, an interval tree of
  `struct pkvm_mapping` that records what the host asked EL2 to map.
- `struct kvm_s2_mmu`: `pgt` is a pointer. The host allocates it in
  `kvm_init_stage2_mmu()`; at EL2 it points at the `pgt` embedded in
  `struct pkvm_hyp_vm`.
- `struct kvm_vmid`: `kvm_arm_vmid_update()` runs from
  `kvm_arch_vcpu_load()`, not on each guest entry. Under pKVM the load skips
  it, and EL2 sets the VMID from the handle in `init_pkvm_hyp_vm()`.
- Shadow lookup key: `tlb_vttbr` and `tlb_vtcr` hold the guest hypervisor's
  own register values. The hardware VTTBR comes from `kvm_get_vttbr()`.
- `vcpu->arch.hw_mmu` after `kvm_vcpu_put_hw_mmu()`: NULL, unless the vCPU
  was scheduled out outside WFI emulation and so kept its reference.
- Stage-2 fault targets in `kvm_handle_guest_abort()`: `io_mem_abort()` only
  when there is no memslot or the fault is a write to a read-only slot,
  `handle_access_fault()` for an access flag fault; then `pkvm_mem_abort()`
  for a protected VM, `gmem_abort()` for a guest_memfd slot,
  `user_mem_abort()` otherwise.
- `struct kvm_s2_fault_desc`: the argument of the three memory-abort
  handlers; it carries the vCPU, the memslot and the nested translation.
- `struct vgic_irq` refcount: used for LPIs only. `vgic_put_irq()` does
  nothing for a non-LPI, and `vgic_try_get_irq_ref()` takes no count for an
  INTID below `VGIC_MIN_LPI`.
- `struct vgic_irq` list membership: on an `ap_list` only while `irq->vcpu`
  is set. `irq->vcpu` is the list owner and can differ from `target_vcpu`;
  see `vgic_target_oracle()`.
- `struct irq_ops`: per-interrupt overrides hung off `irq->ops`, set with
  `kvm_vgic_set_irq_ops()`. The timer uses it; the host mapping itself is in
  the `hw`, `host_irq` and `hwintid` fields.
- GICv5 guests: PPIs only. `vgic_get_irq()` returns NULL for a v5 VM, and
  v5 INTIDs carry a type field (`vgic_v5_make_ppi()`).
- GICv5 PPIs: never queued on an `ap_list`;
  `vgic_v5_ppi_queue_irq_unlock()` only kicks the vCPU. Register state is in
  `struct vgic_v5_cpu_if`, the VM-wide PPI masks in `struct vgic_v5_vm`.
- GICv5 exclusions: `vgic_v5_probe()` does not register the device under
  pKVM, and `vgic_v5_init()` returns `-EINVAL` if a vCPU has NV.
- `struct arch_timer_context`: has no vCPU pointer and no cached CTL or
  CVAL. `timer_context_to_vcpu()` derives the vCPU from `timer_id`, and the
  values are vCPU system registers read with `__vcpu_sys_reg()`.

## Where to look

**Core files**

- Paths are relative to `arch/arm64/kvm/`.
- Ioctl entry points `kvm_arch_vm_ioctl()` and `kvm_arch_vcpu_ioctl()` and the
  run loop `kvm_arch_vcpu_ioctl_run()`: `arm.c`.
- PMU: `pmu-emul.c` and `pmu.c`.
- GICv2, GICv3, ITS and GICv4: `vgic/vgic-v2.c`, `vgic/vgic-v3.c`,
  `vgic/vgic-its.c` and `vgic/vgic-v4.c`.

| Job | File | Easy to miss in this tree |
|---|---|---|
| Exit handling | `handle_exit.c` | Hyp runs first: `hyp_exit_handlers[]` in `hyp/vhe/switch.c` and `hyp/nvhe/switch.c`. Protected VMs use `pvm_exit_handlers[]` in `hyp/nvhe/switch.c` instead. |
| System register emulation | `sys_regs.c` | `kvm_handle_sys_reg()` calls `triage_sysreg_trap()` in `emulate-nested.c` first for every guest, nested or not; on a host with `ARM64_HAS_FGT` it injects UNDEF for bits set in `kvm->arch.fgu[]`. Protected VMs: `kvm_handle_pvm_sysreg()` in `hyp/nvhe/sys_regs.c`. |
| Feature-to-register-bit tables | `config.c` | Arrays of `struct reg_bits_to_feat_map`, named like `hfgrtr_feat_map[]`, wrapped in `struct reg_feat_map_desc`. Also cover, for example, `SCTLR_EL1`, `SCTLR_EL2`, `TCR2_EL2`, `MDCR_EL2`, `VTCR_EL2` and the GICv5 `ICH_HFGRTR_EL2`, `ICH_HFGWTR_EL2`, `ICH_HFGITR_EL2`. Read through `compute_fgu()` and `get_reg_fixed_bits()`; `kvm_vcpu_load_fgt()` is here too. `compute_fgu()` runs for every VM from `kvm_calculate_traps()`. |
| Stage-2 fault handling | `mmu.c` | `kvm_handle_guest_abort()` ends by picking one of three resolvers: `pkvm_mem_abort()` (protected VM), `gmem_abort()` (memslot with guest_memfd), `user_mem_abort()`. On a shadow stage-2 with `nested_stage2_enabled` it calls `kvm_walk_nested_s2()` in `nested.c` first. |
| Reset | `reset.c` | System register reset values are in `sys_regs.c`: `kvm_reset_vcpu()` calls `kvm_reset_sys_regs()`. |
| PSCI and other hypercalls | `psci.c`, `hypercalls.c`, `pvtime.c`, `trng.c` | There is no kvm_hvc_call_handler(); the entry is `kvm_smccc_call_handler()`. `hyp/nvhe/psci-relay.c` handles the host's own PSCI calls, not the guest's. |
| Exception injection | `inject_fault.c` | There is no kvm_inject_dabt(); use `kvm_inject_sea()`, or inline `kvm_inject_sea_dabt()` and `kvm_inject_sea_iabt()` in `arch/arm64/include/asm/kvm_emulate.h`. `kvm_inject_exception()` is static in `hyp/exception.c`. |
| Timer | `arch_timer.c` | Hyp side is both `hyp/nvhe/timer-sr.c` and `hyp/vhe/timer-sr.c`; the VHE file holds only `__kvm_timer_set_cntvoff()`. |
| Debug | `debug.c` | There is no kvm_arm_setup_debug(); `kvm_vcpu_load_debug()` and `kvm_vcpu_put_debug()` do that job. `KVM_SET_GUEST_DEBUG` is `kvm_arch_vcpu_ioctl_set_guest_debug()` in `guest.c`. |
| FP/SIMD | `fpsimd.c` | There is no fpsimd.S under `hyp/`; hyp code calls the inline `fpsimd_save_state()` and `sve_save_state()` family in `arch/arm64/include/asm/fpsimd.h`. No SME guest state: `kvm_arch_vcpu_ctxsync_fp()` sets `sme_state` to `NULL`. |
| Nested virtualisation | `nested.c`, `emulate-nested.c`, `at.c`, `vgic/vgic-v3-nested.c` | `pauth.c` belongs here too: `kvm_auth_eretax()`, built only with `CONFIG_ARM64_PTR_AUTH`. |
| Host side of pKVM | `pkvm.c` | Also holds the host's stage-2 back end: `KVM_PGT_FN()` in `mmu.c` picks the `pkvm_pgtable_stage2_map()` family whenever `is_protected_kvm_enabled()`. |
| GICv3 CPU interface registers | `vgic-sys-reg-v3.c` | At the top level, not in `vgic/`. Serves userspace access only (`vgic_v3_cpu_sysregs_uaccess()`); guest ICC traps are emulated by `__vgic_v3_perform_cpuif_access()` in `hyp/vgic-v3-sr.c`, or by `access_gic_sgi()`, `access_gic_sre()` and `access_gic_dir()` in `sys_regs.c`. |
| GICv5 model | `vgic/vgic-v5.c`, `hyp/vgic-v5-sr.c` | `vgic_v5_probe()` registers `KVM_DEV_TYPE_ARM_VGIC_V5`, a real GICv5 guest, and with `ARM64_HAS_GICV5_LEGACY` also `KVM_DEV_TYPE_ARM_VGIC_V3`. A v5 guest has no SPIs: `vgic_init()` skips `kvm_vgic_dist_init()`. `KVM_DEV_TYPE_ARM_VGIC_V5` is not registered under pKVM; `vgic_v5_init()` rejects nested vCPUs. Guest trap handlers such as `access_gicv5_ppi_enabler()` are in `sys_regs.c`. |

## Modes and the hypervisor

**Modes of operation**

- `kvm-arm.mode=protected`: `aliases[]` in
  `arch/arm64/kernel/pi/idreg-override.c`, which spells it
  `kvm_arm.mode=protected`, maps it to `arm64_sw.hvhe=1`, not
  to `id_aa64mmfr1.vh=0`. On a VHE-capable CPU booted at EL2 pKVM therefore
  runs as hVHE; `__finalise_el2` in `arch/arm64/kernel/hyp-stub.S` keeps the
  kernel at EL1 when the hVHE override is set.
- `kvm-arm.mode=nvhe` (`kvm_arm.mode=nvhe` in `aliases[]`): maps to
  `arm64_sw.hvhe=0 id_aa64mmfr1.vh=0`, so it also turns hVHE off.
- `hvhe_filter()`: accepts the override only for value 1, boot at EL2 and a
  non-zero VH field in `id_aa64mmfr1_el1`. `hvhe_possible()`, the `.matches`
  test of `ARM64_KVM_HVHE`, then reads the override. There is no
  kvm_arm.hvhe alias.
- `kvm_mode`: the static in `arch/arm64/kvm/arm.c`; written only by
  `early_kvm_mode_cfg()`, and nothing changes it afterwards.
- `early_kvm_mode_cfg()` at the wrong exception level, with
  `is_hyp_mode_available()` true: `protected` with the kernel at EL2 does
  `pr_warn_once()`, returns 0 and leaves `kvm_mode` unchanged; `nvhe` at EL2
  and `nested` at EL1 hit `WARN_ON()` and return `-EINVAL`.
- `is_protected_kvm_enabled()`: true whenever `kvm_get_mode()` was
  `KVM_MODE_PROTECTED` at cap finalisation (`is_kvm_protected_mode()` in
  `arch/arm64/kernel/cpufeature.c`). It does not say KVM initialised;
  `is_pkvm_initialized()` says the host has been deprivileged.
- Predicates inside the hypervisor objects (`arch/arm64/include/asm/virt.h`):

| Predicate | VHE object | nVHE object | Host code |
|---|---|---|---|
| `has_vhe()` | constant true | constant false | final cap |
| `has_hvhe()` | constant false | final cap | final cap |
| `is_protected_kvm_enabled()` | constant false | final cap | final cap |
| `is_kernel_in_hyp_mode()` | `BUILD_BUG_ON()` | `BUILD_BUG_ON()` | reads `CurrentEL` |

- `is_hyp_nvhe()`: calls `is_kernel_in_hyp_mode()`, so host code only.
- **Potentially unsafe usage**: testing `has_vhe()`, `has_hvhe()` or
  `is_protected_kvm_enabled()` in host code.
  - Unsafe: before system capabilities are finalised; `cpus_have_final_cap()`
    in `arch/arm64/include/asm/cpufeature.h` does `BUG()`.
  - Safe: once `system_capabilities_finalized()` is true, as `kvm_arm_init()`
    and `finalize_pkvm()` do from initcalls.
  - Safe: early code tests `is_kernel_in_hyp_mode()` or `kvm_get_mode()`
    instead, as `early_kvm_mode_cfg()`, `CHOOSE_HYP_SYM()` in
    `arch/arm64/include/asm/kvm_asm.h` and `is_kvm_protected_mode()` do.
- Register layout at EL2: test `has_vhe() || has_hvhe()`, as
  `__activate_cptr_traps()` in `arch/arm64/kvm/hyp/include/hyp/switch.h`
  does; `!has_vhe()` alone picks the wrong layout under hVHE.

**Hypervisor source directories**

- Files in `arch/arm64/kvm/hyp/` built into both the VHE and nVHE objects:
  `vgic-v3-sr.c`, `vgic-v5-sr.c`, `vgic-v2-cpuif-proxy.c`, `aarch32.c`,
  `entry.S`, `hyp-entry.S`, `exception.c`. The lists are the `../` entries in
  `vhe/Makefile` and `nvhe/Makefile`.
- `sysreg-sr.c`, `timer-sr.c`, `debug-sr.c`, `tlb.c`, `switch.c`: separate
  files of the same name in `vhe/` and `nvhe/`; none is shared.
- `pgtable.c`: built into the nVHE object and, by
  `arch/arm64/kvm/hyp/Makefile`, as plain kernel code with neither
  `__KVM_VHE_HYPERVISOR__` nor `__KVM_NVHE_HYPERVISOR__`. It is not in
  `vhe/Makefile`. In the host build `has_vhe()` is a runtime cap test.
- `hyp-constants.c`: in neither object; `arch/arm64/kvm/Makefile` compiles it
  to generate `hyp_constants.h`.
- nVHE also links `arch/arm64/kernel/smccc-call.o` and, from
  `arch/arm64/lib/`, `tishift.o` with the page and mem routines.
- Conditional nVHE files: `list_debug.c` under `CONFIG_LIST_HARDENED`;
  `clock.c`, `trace.c`, `events.c` under `CONFIG_NVHE_EL2_TRACING`.
- Shared source compiles to different code per object: the
  `read_sysreg_el1()` family in `arch/arm64/include/asm/kvm_hyp.h` is fixed
  VHE encodings (`_EL12` for `read_sysreg_el1()`) in the VHE object and an
  alternative keyed on `ARM64_KVM_HVHE` in the nVHE object.
- `exception.c`: `#error` unless one of the two hypervisor macros is
  defined, so it cannot be reused from host code.

**nVHE object build**

- Section renaming is done only by `hyp.lds.S` through `HYP_SECTION()` and
  `BEGIN_HYP_SECTION()`; `objcopy` only prefixes symbols and `gen-hyprel`
  renames nothing.
- Sections the script renames: `.idmap.text`, `.text`,
  `.data..ro_after_init`, `.rodata`, `.data..percpu`, `.bss`, `.data`.
  Writable initialised data is therefore allowed.
- Under `CONFIG_NVHE_EL2_TRACING` the script also builds `.hyp.event_ids`,
  from inputs that `define_events.h` already names `.hyp.event_ids.*`.
- Other input sections, for example `__kvm_ex_table`, are not named in
  `hyp.lds.S`; `arch/arm64/kernel/vmlinux.lds.S` places `__kvm_ex_table`
  inside the hyp text range.
- No step in `nvhe/Makefile` checks for stray sections or undefined symbols.
  A reference to an unaliased kernel symbol fails only at the `vmlinux` link,
  as an undefined `__kvm_nvhe_` symbol.
- `gen-hyprel` fails the build on an unexpected RELA type in a `.hyp`
  section and on any `SHT_REL` section.
- `gen-hyprel` picks relocations by the section that holds them, not by
  target: every `R_AARCH64_ABS64` in a `.hyp` section is converted by
  `kvm_apply_hyp_relocations()`, including a pointer to an aliased kernel
  symbol.
- kCFI is not removed: only `CC_FLAGS_FTRACE`, `CC_FLAGS_SCS` and the
  profile-use flags are filtered, and `gen-hyprel` accepts
  `R_AARCH64_ABS32` for the type hashes.
- UBSAN: on in trap mode when `CONFIG_UBSAN_KVM_EL2` is set
  (`UBSAN_SANITIZE := y`, `CFLAGS_UBSAN_TRAP`).
- Other sanitizers: the Makefile has no per-sanitizer disable lines. The
  `.nvhe.o` files are not in `obj-y`, so `is-kernel-object` in
  `scripts/Makefile.lib` is empty and the flags are not added.
- `-fno-stack-protector` and `-DDISABLE_BRANCH_PROFILING`: set in
  `nvhe/Makefile` itself.
- `memcpy()`, `memset()`, `clear_page()`, `copy_page()`: compiled into the
  object from `arch/arm64/lib/` and bound with `KVM_NVHE_ALIAS_HYP()` to the
  hyp copy of the `__pi_` symbol. `KVM_NVHE_ALIAS()` is for kernel symbols.
- Hyp globals that mirror host values are separate variables; the host
  assigns each one through `kvm_nvhe_sym()`, most of them in
  `kvm_hyp_init_symbols()` in `arch/arm64/kvm/arm.c`. A new one needs such an
  assignment.
- `is_kernel_in_hyp_mode()`: does not compile in hyp code
  (`BUILD_BUG_ON()`). `CHOOSE_VHE_SYM()` expands to
  `__nvhe_undefined_symbol`, so it fails at link.
- **Potentially unsafe usage**: dereferencing `vcpu->kvm` or
  `vcpu->arch.hw_mmu` in nVHE code without `kern_hyp_va()`.
  - Unsafe: when the vCPU can be the host's `struct kvm_vcpu`, which holds
    kernel addresses; that is every guest when pKVM is off.
  - Safe: after `is_protected_kvm_enabled()` has tested true, as in
    `vcpu_is_protected()`; `handle___kvm_vcpu_run()` then passes only the
    hyp copy, whose `kvm` pointer `nvhe/pkvm.c` set to `&hyp_vm->kvm`.
  - Safe: `kern_hyp_va(vcpu->kvm)` in code shared with VHE; `__kern_hyp_va()`
    in `arch/arm64/include/asm/kvm_mmu.h` is empty in the VHE object.
  - Safe: behind a `vcpu_has_nv()` test, which is constant false in the nVHE
    object, as in `__activate_cptr_traps_vhe()`.

**Calling into the hypervisor**

- `kvm_call_hyp_nvhe()` on a refused call: after the `WARN_ON()` it sets
  `res.a1 = -EOPNOTSUPP` and returns that, not what the hypervisor left in
  x1.
- `kvm_call_hyp()` on VHE: direct call followed by `isb()`.
  `kvm_call_hyp_ret()` on VHE: direct call with no `isb()`.
- Inside the nVHE object all three macros are plain calls `f(...)`; see the
  `__KVM_NVHE_HYPERVISOR__` branch in `arch/arm64/include/asm/kvm_host.h`.
- `enum __kvm_host_smccc_func` has three regions, split by `MARKER()`
  entries. A `MARKER()` takes no slot; it has the value of the next entry.

| Region | Ends before | Callable |
|---|---|---|
| early | `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` | until pKVM is finalised |
| common, starts at `__pkvm_prot_finalize` | `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` | always |
| pKVM only | `__KVM_HOST_SMCCC_FUNC_MAX` | once pKVM is finalised |

- `host_hcall[]` uses designated initialisers, so the order of
  `HANDLE_FUNC()` lines does not matter; the enum position does.
- Missing `HANDLE_FUNC()`: for the last enum value the
  `BUILD_BUG_ON(ARRAY_SIZE(host_hcall) != __KVM_HOST_SMCCC_FUNC_MAX)` in
  `handle_host_hcall()` fails; anywhere else the slot is NULL and the call is
  refused at run time.
- `DECLARE_REG()` in `arch/arm64/kvm/hyp/include/nvhe/trap_handler.h`:
  declares `___check_reg_` plus the register number, so two `DECLARE_REG()`
  of one register in the same scope do not compile.
- Handler that never writes `cpu_reg(host_ctxt, 1)`: the host gets back the
  x1 it passed, so the caller must not use the value of
  `kvm_call_hyp_nvhe()`.
- vCPU pointer argument under pKVM: `__get_host_hyp_vcpus()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c` accepts it only if it equals
  `host_vcpu` of the loaded hyp vCPU, else yields NULL; for example
  `handle___kvm_vcpu_run()` uses it through `get_host_hyp_vcpus()`.

**Refused host hypercalls**

- `handle_host_hcall()` has two bounds, both chosen by the static key
  `kvm_protected_mode_initialized` alone:
  - key set: `hcall_min` is `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`, so the early
    region is refused;
  - key clear: `hcall_max` is `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`, so every
    pKVM-only call is refused.
- The key is clear for the whole life of a non-protected nVHE or hVHE
  system, and under pKVM until `pkvm_drop_host_privileges()` runs from
  `finalize_pkvm()`, a `device_initcall_sync` in `arch/arm64/kvm/pkvm.c`.
- No pKVM-only handler tests `is_protected_kvm_enabled()` itself; the range
  check is the only gate. A pKVM-only call placed in the common region runs
  on plain nVHE.
- Index 0 (`__KVM_HOST_SMCCC_FUNC___kvm_hyp_init`) has no `HANDLE_FUNC()`
  line, so while the key is clear it is refused as a NULL slot.
- Stub HVCs (x0 below `HVC_STUB_HCALL_NR`): with `ARM64_KVM_PROTECTED_MODE`,
  `__host_hvc` in `arch/arm64/kvm/hyp/nvhe/host.S` skips the stub test, so
  they reach `handle_host_hcall()` and are refused out of range. Without it
  they go to `__kvm_handle_stub_hvc`.
- `handle_host_hcall()` returns `void` and does not use
  `array_index_nospec()`.
- `handle___kvm_vcpu_run()` with x0 success and `-EINVAL` in x1, both only
  under pKVM: when no hyp vCPU is loaded or the pointer is not its
  `host_vcpu`, and when `SVCR` is non-zero on an SME system.
- Handlers that fail without writing x1, for example
  `handle___pkvm_vcpu_load()` and `handle___pkvm_tlb_flush_vmid()` on a bad
  handle: the host cannot tell failure from success.

**VHE and nVHE world switch**

- VHE entry points are `kvm_vcpu_load_vhe()` and `kvm_vcpu_put_vhe()` in
  `arch/arm64/kvm/hyp/vhe/switch.c`; there are no
  kvm_vcpu_load_sysregs_vhe() or kvm_vcpu_put_sysregs_vhe() here.
- Load/put on VHE, every run on nVHE, beyond the EL1, EL0 and AArch32
  sysregs:

| State | VHE at load/put | nVHE in `__kvm_vcpu_run()` |
|---|---|---|
| `VTTBR_EL2`, `VTCR_EL2` | `__load_stage2()` | `__load_stage2()`, then `__load_host_stage2()` |
| `HSTR_EL2`, `PMUSERENR_EL0`, `HCRX_EL2`, fine-grained traps, MPAM traps | `__activate_traps_common()` | `__activate_traps_common()` |
| GICv3 trap bits | `__vgic_v3_activate_traps()` from `arch/arm64/kvm/vgic/vgic-v3.c` | `__hyp_vgic_restore_state()` |

- `MDCR_EL2`: the nVHE `__activate_traps()` writes it at every entry; the
  VHE `__activate_traps()` does not write it.
- vGIC list registers: every run on both, but on VHE the host does it in
  `kvm_vgic_flush_hwstate()` and `kvm_vgic_sync_hwstate()` (see
  `can_access_vgic_from_kernel()`), outside `__kvm_vcpu_run()`.
- vGIC APRs: load/put on both, with the VMCR of a GICv3 guest restored at
  load; nVHE uses the `__vgic_v3_restore_vmcr_aprs` and
  `__vgic_v3_save_aprs` hypercalls. `__vgic_v3_save_state()` saves the VMCR
  on every run.
- `CNTHCTL_EL2` on nVHE: `__timer_enable_traps()` at every entry; under hVHE
  the EL1 physical access bits are shifted left by 10.
- Every entry on both, in addition to `HCR_EL2`, the CPTR controls and the
  return state: `POR_EL0` (with `MDSCR_EL1` in
  `__sysreg_restore_common_state()`) and the vector base.
- VHE with nested virt: `HCR_EL2` is recomputed at every entry by
  `__compute_hcr()`, not taken from `vcpu->arch.hcr_el2` alone.
- Under pKVM every guest, protected or not, runs on the hyp copy in
  `struct pkvm_hyp_vcpu`; `handle___kvm_vcpu_run()` passes the host vCPU to
  `__kvm_vcpu_run()` only when pKVM is off.
- pKVM adds load/put hypercalls: `kvm_arch_vcpu_load()` calls
  `__pkvm_vcpu_load` and `kvm_arch_vcpu_put()` calls `__pkvm_vcpu_put`.
- FP under pKVM: `kvm_hyp_handle_fpsimd()` saves the host FP state at EL2
  and `fpsimd_sve_sync()` restores it after the run; without pKVM the host
  does both.
- `__timer_enable_traps()` for a protected guest: always leaves physical
  counter access untrapped.

**Exits handled in the hypervisor**

- There is no kvm_hyp_handle_ptrauth() in this tree, and none of the three
  hyp tables has an `ESR_ELx_EC_PAC` entry.
- `__fixup_guest_exit()` dispatches only when the raw `*exit_code` equals
  `ARM_EXCEPTION_TRAP`. A trap with `ARM_EXIT_WITH_SERROR_BIT` set goes to
  the host unhandled and is replayed after the SError is injected.
- `__fixup_guest_exit()` does nothing for an IRQ exit, and for SError or
  illegal-return exits it only stores `ESR_EL2`; it emulates no vGIC or
  erratum trap itself.
- Table selection: VHE `fixup_guest_exit()` passes its `hyp_exit_handlers`
  directly. `kvm_get_exit_handler_array()` exists only in
  `arch/arm64/kvm/hyp/nvhe/switch.c` and tests `vcpu_is_protected()`.
- A non-protected guest under pKVM uses `hyp_exit_handlers`, not
  `pvm_exit_handlers`.
- Entries that differ from the nVHE `hyp_exit_handlers`:

| Table | EC | Handler |
|---|---|---|
| VHE | `ESR_ELx_EC_SYS64` | `kvm_hyp_handle_sysreg_vhe()` |
| VHE | `ESR_ELx_EC_ERET` | `kvm_hyp_handle_eret()` |
| VHE | `0x3F` | `kvm_hyp_handle_impdef()` |
| pVM | `ESR_ELx_EC_HVC64` | `kvm_handle_pvm_hvc64()` |
| pVM | `ESR_ELx_EC_SYS64` | `kvm_handle_pvm_sys64()` |
| pVM | `ESR_ELx_EC_SVE` | `kvm_handle_pvm_restricted()` |
| pVM | `ESR_ELx_EC_CP15_32` | none |

- `kvm_hyp_handle_iabt_low` and `kvm_hyp_handle_watchpt_low`: macros for
  `kvm_hyp_handle_memory_fault()`; a change to it affects three ECs.
- Handlers that return false after changing state, so the host sees the
  changed state:
  - `kvm_hyp_handle_dabt_low()` may set `*exit_code` to
    `ARM_EXCEPTION_EL1_SERROR`;
  - `kvm_hyp_handle_impdef()` always returns false; with
    `ARM64_WORKAROUND_PMUV3_IMPDEF_TRAPS` it first rewrites
    `vcpu->arch.fault.esr_el2` to a synthetic `ESR_ELx_EC_SYS64`;
  - `kvm_hyp_handle_zcr_el2()` always returns false, and may first load
    guest FP state through `kvm_hyp_handle_fpsimd()`;
  - `pkvm_memshare_call()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`, when
    `__pkvm_guest_share_host()` returns `-ENOENT`, fakes a data abort in
    `vcpu->arch.fault` so the host maps the page.
- `kvm_handle_pvm_sysreg()`: injects an undefined exception and returns true
  when no descriptor matches; returns false when the descriptor has a NULL
  `access`.
- `kvm_handle_pvm_hvc64()`: handles the vendor-hyp features, meminfo, share
  and unshare calls; every other function ID returns false to the host.
- **Potentially unsafe usage**: a handler returning true without calling
  `__kvm_skip_instr()`.
  - Unsafe: when nothing else changed that would stop the same trap; the
    `do`/`while` loop around `__guest_enter()` re-enters the guest on the
    same instruction, which traps again.
  - Safe: the trap cause was removed, as `kvm_hyp_handle_fpsimd()` does by
    making the guest the FP owner before `__activate_cptr_traps()`.
  - Safe: the handler wrote `ELR_EL2` itself, as `kvm_hyp_handle_mops()` and
    `kvm_hyp_handle_eret()` do.
  - Safe: an exception was injected, as `kvm_handle_pvm_restricted()` does
    with `inject_undef64()`.
  - Safe: a retry is intended, as `kvm_hyp_handle_memory_fault()` does when
    `__populate_fault_info()` fails.
  - Safe: an HVC exit, as in `kvm_handle_pvm_hvc64()`; `ELR_EL2` already
    points past the HVC, and `__pkvm_memshare_page_req()` subtracts 4 to
    replay it.

## Configuration, first run and teardown

**First run sequence**

- Lock held across the sequence: only `vcpu->mutex`, from `kvm_vcpu_ioctl()`.
  Each step that needs `kvm->arch.config_lock` takes it itself; nothing
  holds it from one step to the next.
- Steps after the `vcpu_has_run_once()` early return, in order:

  | Step | Scope | Skipped on a later call by |
  |---|---|---|
  | `kvm_init_mpidr_data()` | VM | `mpidr_data` set, or one online vCPU |
  | `kvm_vgic_map_resources()` | VM, in-kernel irqchip | `ready` in `struct vgic_dist` |
  | `kvm_finalize_sys_regs()` | VM; NV also vCPU | `sysreg_masks` set (mask setup); `kvm_vm_has_ran_once()` (GIC fields); the NV per-vCPU rewrite always runs |
  | `kvm_vcpu_allocate_vncr_tlb()` | vCPU, NV | `vcpu->arch.vncr_tlb` set |
  | `kvm_vgic_vcpu_nv_init()` | vCPU, NV | nothing; same owner is accepted |
  | `kvm_calculate_traps()` | vCPU and VM | `KVM_ARCH_FLAG_FGU_INITIALIZED`, VM part |
  | `kvm_timer_enable()` | vCPU | `timer->enabled` |
  | `kvm_arm_pmu_v3_enable()` | vCPU, PMU | nothing; it only validates |
  | `vgic_v5_finalize_ppi_state()` | VM, GICv5 | `GICV5_ARCH_PPI_SW_PPI` in the mask |
  | set `PKVM_HOST_STATE_DIRTY` | vCPU, pKVM, non-protected VM | nothing |
  | `pkvm_create_hyp_vm()` | VM, pKVM | `pkvm_hyp_vm_is_created()` |
  | `pkvm_create_hyp_vcpu()` | vCPU, pKVM | `VCPU_PKVM_FINALIZED` |
  | set `KVM_ARCH_FLAG_HAS_RAN_ONCE` | VM | nothing; every vCPU sets it |

- There is no kvm_arch_vcpu_run_map_fp() and no kvm_arm_vcpu_init_debug() in
  this tree.
- Pid change on a vCPU that has run: only the `kvm_vcpu_initialized()` and
  `kvm_arm_vcpu_is_finalized()` checks run.
- Per-vCPU has-run state: not written here; `kvm_vcpu_ioctl()` in
  `virt/kvm/kvm_main.c` sets `vcpu->pid` after the function returns 0.
- Failed first run: steps that finished stay done; a step with a guard is
  skipped on the retry, the others run again. A new step must be safe to run
  once per vCPU and again after a failure.
- `kvm_vgic_map_resources()` failure: calls `kvm_vm_dead()`, so later ioctls
  return `-EIO` and there is no retry.
- `kvm_timer_enable()` with an in-kernel irqchip: `timer_irqs_are_valid()`
  sets `KVM_ARCH_FLAG_TIMER_PPIS_IMMUTABLE` when the PPIs are valid, so timer
  PPIs are frozen before `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set, and stay frozen
  if a later step fails.
- Order, vgic first: `kvm_vgic_set_owner()` returns `-EAGAIN` until
  `vgic_initialized()`; `kvm_timer_enable()`, through
  `timer_irqs_are_valid()`, and `kvm_vgic_vcpu_nv_init()` call it.
- Order, ID registers before the flag: `kvm_set_vm_id_reg()` does
  `KVM_BUG_ON()` once `kvm_vm_has_ran_once()`, so the GIC field fix-up in
  `kvm_finalize_sys_regs()` runs only while the flag is clear.
- Order, GICv5 PPIs after the timer: `vgic_v5_finalize_ppi_state()` exposes
  only PPIs that have an owner, plus `GICV5_ARCH_PPI_SW_PPI`, read from
  vCPU 0.
- Order, pKVM last: `__pkvm_init_vm` takes `vcpu_features` and, for a
  non-protected VM, `kvm->arch.flags` from the host (see
  `pkvm_init_features_from_host()`), and `pkvm_create_hyp_vcpu()` needs the
  VM that `pkvm_create_hyp_vm()` made.

**Has-run predicates**

- Backing state:

  | Predicate | Tests | Can go false again |
  |---|---|---|
  | `vcpu_has_run_once()` | `!!READ_ONCE((vcpu)->pid)` | no |
  | `kvm_vm_has_ran_once()` | `KVM_ARCH_FLAG_HAS_RAN_ONCE` in `kvm->arch.flags` | no |
  | `kvm_vcpu_initialized()` | vCPU flag `VCPU_INITIALIZED` | yes |

- `VCPU_INITIALIZED` cleared on the host vCPU: by
  `kvm_arch_vcpu_ioctl_run()` when `vcpu_mode_is_bad_32bit()`.
- `fixup_guest_exit()` in `arch/arm64/kvm/hyp/nvhe/switch.c`: clears
  `VCPU_INITIALIZED` for a protected vCPU in AArch32, but on the hyp vCPU's
  copy of `cflags`; the host's `kvm_vcpu_initialized()` does not change.
- After `kvm_arch_vcpu_ioctl_run()` clears `VCPU_INITIALIZED`,
  `vcpu_has_run_once()` is still true; code must not assume that has-run
  implies initialised.
- Window: `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set inside
  `kvm_arch_vcpu_run_pid_change()`, `vcpu->pid` after it returns. The VM
  predicate can be true while no vCPU's predicate is.
- `vcpu_has_run_once()` users: `kvm_arch_vcpu_run_pid_change()`,
  `kvm_arch_vcpu_ioctl_vcpu_init()`, `vcpu_reset_hcr()` and
  `kvm_vgic_create()`. It gates no register write and no finalise.
- `kvm_vm_has_ran_once()` users: search for the name; they are in
  `arch/arm64/kvm/sys_regs.c`, `arch/arm64/kvm/pmu-emul.c` and
  `arch/arm64/kvm/hypercalls.c`. No capability in
  `kvm_vm_ioctl_enable_cap()` tests it.
- `kvm_arm_pmu_v3_set_attr()`: refuses every attribute with `-EBUSY` once
  `vcpu->arch.pmu.created`; only `KVM_ARM_VCPU_PMU_V3_FILTER` and
  `KVM_ARM_VCPU_PMU_V3_SET_PMU` also test `kvm_vm_has_ran_once()`.
- Other gates in use, for example: `KVM_ARCH_FLAG_TIMER_PPIS_IMMUTABLE` for
  timer PPIs, `kvm->created_vcpus` for `KVM_CAP_ARM_MTE`,
  `vgic_initialized()` in `kvm_arch_vcpu_precreate()`.
- Register writes after first run: `set_id_reg()`, `set_pmmir()` and
  `kvm_arm_set_fw_reg_bmap()` return 0 for an unchanged value and `-EBUSY`
  for a change; `set_pmmir()` and `kvm_arm_set_fw_reg_bmap()` return
  `-EINVAL` first for a bit outside their valid mask; `set_pmcr()` ignores a
  changed `N` silently.
- **Potentially unsafe usage**: testing `kvm_vm_has_ran_once()` without
  `kvm->arch.config_lock`.
  - Unsafe: when the result decides a write to VM-wide state; the flag is set
    under that lock, and `kvm_set_vm_id_reg()` asserts the lock and does
    `KVM_BUG_ON()` if the VM has run.
  - Safe: a read-only fast path, as `get_id_reg()` does; the flag is never
    cleared, and when it is clear the function takes the lock.
- **Potentially unsafe usage**: gating a write to VM-wide configuration on
  `vcpu_has_run_once()`.
  - Unsafe: with only the calling vCPU's `vcpu->mutex` held and no VM-wide
    test under `kvm->arch.config_lock`; another vCPU's `vcpu->pid` is
    written by its own `KVM_RUN` under its own mutex.
  - Safe: with every vCPU's mutex held and every vCPU tested, as
    `kvm_vgic_create()` does after `kvm_trylock_all_vcpus()`.
  - Safe: as a shortcut in front of steps that each test VM-wide state again
    under `kvm->arch.config_lock`, as `kvm_arch_vcpu_run_pid_change()` does;
    for example `kvm_finalize_sys_regs()` tests `kvm_vm_has_ran_once()`.
  - Safe: for state private to that vCPU, from its own ioctl, as
    `vcpu_reset_hcr()` does for `hcr_el2`.

**Configuration lock**

- Order, outermost first: `kvm->lock`, `vcpu->mutex`, `kvm->slots_lock`,
  `kvm->srcu` read side, `kvm->arch.config_lock`, then `its->cmd_lock` and
  `its->its_lock`.
- Where written down: the comment at the top of
  `arch/arm64/kvm/vgic/vgic.c` gives two chains, one from `kvm->lock` and one
  that reads `kvm->slots_lock`, `kvm->srcu`, `kvm->arch.config_lock`.
- Lockdep priming, both under `CONFIG_LOCKDEP`: `kvm_arch_init_vm()` takes
  `kvm->lock` then `config_lock`; `kvm_arch_vcpu_create()` takes
  `vcpu->mutex` then `config_lock`.
- `kvm->slots_lock` and `kvm->srcu`: nothing primes them against
  `config_lock`; lockdep learns that order only from real paths.
- `kvm_vgic_create()`: does no priming; it asserts `kvm->lock`, which the
  caller took, and uses `kvm_trylock_all_vcpus()`, returning `-EBUSY`.
  arm64 has no caller of `kvm_lock_all_vcpus()`.
- Protected state: find it with a search for
  `lockdep_assert_held(&kvm->arch.config_lock)` and for the lock name; it
  includes `kvm->arch.mpidr_data`, `kvm->arch.sysreg_masks`, the pKVM
  `is_created` state and `VCPU_PKVM_FINALIZED`.
- Not protected by it: bits of `kvm->arch.flags` set in
  `kvm_vm_ioctl_enable_cap()`, and the counter offset, which
  `kvm_vm_ioctl_set_counter_offset()` writes under `kvm->lock` plus all vCPU
  mutexes.
- `config_lock` inside an SRCU read side: `kvm_handle_guest_abort()` holds
  `kvm->srcu` around `io_mem_abort()`, and `vgic_mmio_write_v3_misc()` takes
  `config_lock`.
- **Unsafe usage**: waiting for a `kvm->srcu` grace period while holding
  `kvm->arch.config_lock`; `kvm_io_bus_unregister_dev()` calls
  `synchronize_srcu_expedited()`.
  - Safe: drop `config_lock` and keep `kvm->slots_lock`, as
    `kvm_vgic_destroy()` does before `vgic_unregister_redist_iodev()`.
  - Safe: `kvm_io_bus_register_dev()` under `config_lock`, as
    `vgic_v2_map_resources()` does; it uses `call_srcu()` and does not wait.
- Path with three locks: first run holds `vcpu->mutex`, then
  `kvm_vgic_map_resources()` takes `kvm->slots_lock` and `config_lock`.
- Path with `kvm->lock`, all vCPU mutexes and `config_lock`:
  `KVM_DEV_ARM_VGIC_SAVE_PENDING_TABLES` in `vgic_set_common_attr()`.
  `KVM_DEV_ARM_VGIC_CTRL_INIT` takes only `config_lock`.

**vCPU initialisation call**

- Target: `kvm_vcpu_set_target()` accepts `KVM_ARM_TARGET_GENERIC_V8` or the
  value of `kvm_target_cpu()`, which is derived from the host CPU; anything
  else is `-EINVAL`.
- Unknown bits: `-ENOENT`, not `-EINVAL`; tested before host support.
- `KVM_ARM_VCPU_PMU_V3_STRICT` without `KVM_ARM_VCPU_PMU_V3`: `-EINVAL` in
  `kvm_vcpu_init_check_features()`.
- `KVM_ARM_VCPU_PMU_V3_STRICT` on a host without guest PMUv3: `-EINVAL`;
  `system_supported_vcpu_features()` drops it together with
  `KVM_ARM_VCPU_PMU_V3`.
- `KVM_ARM_VCPU_HAS_EL2_E2H0` without `ARM64_HAS_HCR_NV1`: `-EINVAL` from
  `kvm_vcpu_init_nested()`, which `kvm_setup_vcpu()` calls only when
  `vcpu_has_nv()`. `kvm_vcpu_init_check_features()` has no test for this bit.
- `kvm_setup_vcpu()` can also fail a valid feature set: `-ENODEV` from
  `kvm_arm_set_default_pmu()`, `-ENOMEM` from `kvm_vcpu_init_nested()`.
- Storage: only the VM-wide `kvm->arch.vcpu_features`; there is no per-vCPU
  feature bitmap and the target is not stored.
- Helpers: `vcpu_has_feature()` and `kvm_vcpu_has_feature()`, both
  `__vcpu_has_feature()` in `arch/arm64/include/asm/kvm_host.h`.
- `vcpu_has_sve()`: does not test the bitmap; it tests
  `KVM_ARCH_FLAG_GUEST_HAS_SVE`, which `kvm_vcpu_enable_sve()` sets during
  `kvm_reset_vcpu()`.
- `vcpu_has_nv()` and `vcpu_has_ptrauth()`: test the bitmap and a host
  capability; `vcpu_has_nv()` is constant false in code built with
  `__KVM_NVHE_HYPERVISOR__`, and `vcpu_has_ptrauth()` is constant false
  without `CONFIG_ARM64_PTR_AUTH`.

**Repeated vCPU initialisation**

- VM that has run: `kvm_vcpu_set_target()` and `__kvm_vcpu_set_target()` test
  neither `kvm_vm_has_ran_once()` nor `vcpu_has_run_once()`; the call is not
  refused for having run.
- Repeat on an initialised vCPU: `kvm_vcpu_set_target()` compares with
  `kvm_vcpu_init_changed()` and calls `kvm_reset_vcpu()` without
  `kvm->arch.config_lock`; `kvm_setup_vcpu()` is not run again.
- vCPU whose `VCPU_INITIALIZED` was cleared: takes the first-call path through
  `__kvm_vcpu_set_target()`, so the features must still match the VM's.
- `stage2_unmap_vm()` or `icache_inval_all_pou()`: runs only if this vCPU has
  run; init of a vCPU that never ran does neither, even on a VM that has run.
- `vcpu_reset_hcr()`: sets `hcr_el2` to `HCR_GUEST_FLAGS` only while
  `!vcpu_has_run_once()`; after a run it only ORs in `HCR_TVM` on hosts
  without `ARM64_HAS_STAGE2_FWB`.
- Repeat before SVE is finalised: `kvm_vcpu_enable_sve()` sets
  `vcpu->arch.sve_max_vl` back to `kvm_sve_max_vl`, discarding a length
  written through `KVM_REG_ARM64_SVE_VLS`.

**Feature finalisation**

- "Absent" test: `kvm_arm_vcpu_finalize()` uses `vcpu_has_sve()`, which reads
  the VM flag `KVM_ARCH_FLAG_GUEST_HAS_SVE`, not the feature bitmap.
- Check order in `kvm_arm_vcpu_finalize()`: `-EINVAL` for no SVE is tested
  before `-EPERM` for already finalised.
- Allocation and what is frozen: in `kvm_vcpu_finalize_sve()` in
  `arch/arm64/kvm/reset.c`.

**vCPU reset**

- Callers and vCPU state:

  | Caller | vCPU loaded |
  |---|---|
  | `check_vcpu_requests()` on `KVM_REQ_VCPU_RESET` | yes |
  | `__kvm_vcpu_set_target()`, first `KVM_ARM_VCPU_INIT` | no |
  | `kvm_vcpu_set_target()`, repeated `KVM_ARM_VCPU_INIT` | no |
  | `kvm_arch_vcpu_ioctl()` for `KVM_SET_ONE_REG`, `KVM_GET_ONE_REG`, on `KVM_REQ_VCPU_RESET` | no |

- Loaded means inside `kvm_arch_vcpu_ioctl_run()`, the only arm64 ioctl
  handler that calls `vcpu_load()`; `KVM_ARM_VCPU_INIT` runs unloaded.
- First action of `kvm_reset_vcpu()`: copy `vcpu->arch.reset_state` and clear
  its `reset` under `mp_state_lock`, before `preempt_disable()`. There is no
  kvm_pmu_vcpu_reset() in this tree.
- Every caller consumes a pending `reset_state`, so a reset from
  `KVM_ARM_VCPU_INIT` or the one-reg path applies the PSCI entry point too.
- Request order: `check_vcpu_requests()` handles `KVM_REQ_SLEEP` before
  `KVM_REQ_VCPU_RESET`; the `smp_rmb()` at the end of `kvm_vcpu_sleep()`
  pairs with the `smp_wmb()` in `kvm_psci_vcpu_on()`, so a vCPU woken by
  `CPU_ON` sees the reset request in the same pass.
- `kvm_reset_vcpu_core()` and `kvm_reset_vcpu_psci()`: defined in
  `arch/arm64/include/asm/kvm_emulate.h`, not in `arch/arm64/kvm/reset.c`.
- `kvm_reset_vcpu_psci()`: also clears `PENDING_EXCEPTION`, `EXCEPT_MASK` and
  `INCREMENT_PC`.

**VM destruction order**

- Order inside `kvm_arch_destroy_vm()`, after it frees `pmu_filter` and
  `supported_cpus`: `kvm_vgic_destroy()`, `pkvm_destroy_hyp_vm()` (only with
  `is_protected_kvm_enabled()`), `kvm_uninit_stage2_mmu()`,
  `kvm_destroy_mpidr_data()`, free of `sysreg_masks`, `kvm_destroy_vcpus()`,
  `kvm_unshare_hyp()` of the `struct kvm`, `kvm_destroy_nested()`,
  `kvm_arm_teardown_hypercalls()`.
- Stage-2 on the `kvm_destroy_vm()` path: already torn down by
  `kvm_arch_flush_shadow_all()`, reached through
  `kvm_mmu_notifier_release()`, at the latest from
  `mmu_notifier_unregister()`, before `kvm_arch_destroy_vm()`; the call
  inside finds `mmu->pgt` `NULL`.
- Stage-2 on the `kvm_create_vm()` error path that never registered the
  notifier: the call inside `kvm_arch_destroy_vm()` is the only teardown.
- pKVM dependency runs against the in-function order:
  `pkvm_pgtable_stage2_destroy_range()` issues `__pkvm_start_teardown_vm` and
  uses `kvm->arch.pkvm.handle`; `__pkvm_destroy_hyp_vm()` then issues
  `__pkvm_finalize_teardown_vm`, which fails unless `is_dying`, and zeroes
  the handle.
- With the handle zero, `pkvm_pgtable_stage2_destroy_range()` returns at
  once, so stage-2 teardown that had not run before `pkvm_destroy_hyp_vm()`
  reclaims nothing.
- `pkvm_destroy_hyp_vm()` before `kvm_destroy_vcpus()`:
  `__pkvm_finalize_teardown_vm` unpins each host vCPU, its SVE state and the
  host `struct kvm`; `kvm_arm_vcpu_destroy()` and the later
  `kvm_unshare_hyp()` unshare them.
- `kvm_vgic_destroy()`: runs `__kvm_vgic_vcpu_destroy()` on each vCPU;
  `kvm_arch_vcpu_destroy()` later runs it again on each vCPU through
  `kvm_vgic_vcpu_destroy()`.

## Running a vCPU

**Run loop order**

- Order before entry: `kvm_xfer_to_guest_mode_handle_work()`,
  `check_vcpu_requests()`, `preempt_disable()`, `kvm_nested_flush_hwstate()`,
  `kvm_pmu_flush_hwstate()` (if `kvm_vcpu_has_pmu()`), `local_irq_disable()`,
  `kvm_vgic_flush_hwstate()`, `kvm_pmu_update_vcpu_events()`,
  `smp_store_mb(vcpu->mode, IN_GUEST_MODE)`, last check,
  `kvm_arch_vcpu_ctxflush_fp()`.
- Timer: the loop has no timer flush; there is no kvm_timer_flush_hwstate()
  in this tree.
- `kvm_arm_vmid_update()`: not called in the loop; its only caller is
  `kvm_arch_vcpu_load()`.
- Nested and PMU flush: run with preemption off and IRQs on.
- `kvm_vgic_flush_hwstate()` in nested state: raises
  `KVM_REQ_GUEST_HYP_IRQ_PENDING` if `kvm_vgic_vcpu_pending_irq()`, calls
  `vgic_v3_flush_nested()` and returns.
- vgic flush before the last check: the request it raises is seen by
  `kvm_request_pending()` in `kvm_vcpu_exit_request()`, which abandons the
  entry so the next pass injects the IRQ.
- Last check: `ret <= 0 || kvm_vcpu_exit_request()`; it tests a userspace
  irqchip level change, `vcpu_on_unsupported_cpu()`, `kvm_request_pending()`
  and `xfer_to_guest_mode_work_pending()`.
- Signals: handled by `kvm_xfer_to_guest_mode_handle_work()` at the top of
  the next pass, not at the last check.
- Order after exit, all with IRQs off: `kvm_pmu_sync_hwstate()` (if
  `kvm_vcpu_has_pmu()`), `kvm_vgic_sync_hwstate()`, `kvm_timer_sync_user()`
  (userspace irqchip only), `kvm_timer_sync_nested()` (if `is_hyp_ctxt()`),
  `kvm_arch_vcpu_ctxsync_fp()`.
- `kvm_arch_vcpu_ctxsync_fp()`: warns unless IRQs are off.
- `kvm_nested_sync_hwstate()`: runs after `local_irq_enable()` and
  `handle_exit_early()`, before `preempt_enable()`.
- Abandoned entry, in order: `vcpu->mode = OUTSIDE_GUEST_MODE`, `isb()`,
  `kvm_pmu_sync_hwstate()` (if `kvm_vcpu_has_pmu()`), `kvm_timer_sync_user()`
  (userspace irqchip only), `kvm_vgic_sync_hwstate()`, `local_irq_enable()`,
  `preempt_enable()`, `continue`.
- Abandoned entry does not call `kvm_nested_sync_hwstate()`,
  `kvm_timer_sync_nested()` or `kvm_arch_vcpu_ctxsync_fp()`.

**Load and put**

- Ordering stated in comments of `kvm_arch_vcpu_load()`: two only.
  `kvm_arm_vmid_update()` before VTTBR_EL2 is programmed (eager on VHE), and
  `kvm_timer_vcpu_load()` before `kvm_vgic_load()`.
- Ordering enforced but not commented there: `kvm_vcpu_load_debug()` before
  `kvm_vcpu_load_vhe()`; `kvm_vcpu_load_debug()` has a `KVM_BUG_ON()` on
  `SYSREGS_ON_CPU`.
- `kvm_vcpu_load_fgt()`: runs between debug and VHE load; it fills
  `vcpu->arch.fgt`, which the trap activation writes to hardware.
- `last_vcpu_ran` flush: triggers when `*last_ran != vcpu->vcpu_idx`, that is
  when this vCPU was not the last one of that MMU loaded on this CPU.
- There is no kvm_vcpu_load_sysregs_vhe() here; `kvm_vcpu_load_vhe()` in
  `arch/arm64/kvm/hyp/vhe/switch.c` does sysregs, traps and stage 2.

| Mode | Extra difference |
|---|---|
| pKVM | `vcpu_set_pauth_traps()` does nothing; `kvm_arch_vcpu_put()` sets `PKVM_HOST_STATE_DIRTY` for a non-protected VM |
| nested | `kvm_vcpu_load_hw_mmu()` picks an MMU only if `hw_mmu` is `NULL`; outside hyp context it may raise `KVM_REQ_MAP_L1_VNCR_EL2` |
| nested | `kvm_vcpu_put_hw_mmu()` keeps `hw_mmu` when `vcpu->scheduled_out` and not `IN_WFI` |
| nested | `vcpu_set_pauth_traps()` takes `HCR_API` and `HCR_APK` from the guest's `HCR_EL2` when `is_nested_ctxt()` |

- Callers besides `vcpu_load()` and `kvm_sched_in()`: four arm64 functions do
  `kvm_arch_vcpu_put()` then `kvm_arch_vcpu_load()` on a loaded vCPU, all with
  preemption disabled; search for callers of `kvm_arch_vcpu_load()`.
- `kvm_debug_handle_oslar()` in `arch/arm64/kvm/debug.c`: the put/load pair
  that is easy to miss.
- `kvm_emulate_nested_eret()` sets `IN_NESTED_ERET` and `kvm_inject_nested()`
  sets `IN_NESTED_EXCEPTION` around the pair; both make the FP steps return
  early, and `IN_NESTED_ERET` makes `vgic_v4_put()` request a doorbell.

**vCPU requests**

- `KVM_REQ_VGIC_PROCESS_UPDATE`: handled in `check_vcpu_requests()` by
  `kvm_vgic_process_async_update()`, right after `KVM_REQ_IRQ_PENDING` is
  cleared.
- `check_nested_vcpu_requests()`: handles exactly `KVM_REQ_NESTED_S2_UNMAP`,
  `KVM_REQ_MAP_L1_VNCR_EL2` and `KVM_REQ_GUEST_HYP_IRQ_PENDING`; every other
  arm64 request is handled in `check_vcpu_requests()`.
- `KVM_REQ_GUEST_HYP_IRQ_PENDING`: calls `kvm_inject_nested_irq()`; it is
  last because the injection may do a put/load.
- `check_nested_vcpu_requests()`: called from the end of
  `check_vcpu_requests()`, so only when `kvm_request_pending()` was true and
  no earlier branch returned.
- `KVM_REQ_SUSPEND`: `check_vcpu_requests()` returns the value of
  `kvm_vcpu_suspend()` directly, so a pass that handles it skips
  `kvm_dirty_ring_check_request()` and `check_nested_vcpu_requests()`.
- A request still pending after `check_vcpu_requests()` returns 1: the last
  check abandons the entry and the loop runs `check_vcpu_requests()` again.

**vCPU flag sets**

- Widths: `cflags` and `iflags` are `u8`, `sflags` is `u16`;
  `NESTED_SERROR_PENDING` and `IN_NESTED_EXCEPTION` are bits 8 and 9.
- `cflags` members: `VCPU_INITIALIZED`, `VCPU_SVE_FINALIZED`,
  `VCPU_PKVM_FINALIZED`; there is no GUEST_HAS_SVE or GUEST_HAS_PTRAUTH vCPU
  flag (SVE is `KVM_ARCH_FLAG_GUEST_HAS_SVE` in `kvm->arch.flags`).
- `cflags` written from `KVM_RUN`: `kvm_arch_vcpu_ioctl_run()` clears
  `VCPU_INITIALIZED` on a bad 32-bit state, and `VCPU_PKVM_FINALIZED` is set
  from `kvm_arch_vcpu_run_pid_change()`.
- `cflags` under pKVM: copied to the hyp vCPU once, in
  `init_pkvm_hyp_vcpu()`; later host changes do not reach it, and nVHE hyp
  clears `VCPU_INITIALIZED` and `VCPU_SVE_FINALIZED` on its own copy.
- `iflags` also holds `PKVM_HOST_STATE_DIRTY`: the host sets and clears it;
  hyp reads it from the host vCPU and never clears it.
- `iflags` in hyp: `inject_sync64()` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`
  sets the exception flags itself, besides `__kvm_adjust_pc()` clearing them.
- `sflags` is touched by code under `arch/arm64/kvm/hyp/`:
  `PMUSERENR_ON_CPU` is written by `__activate_traps_common()` on VHE and
  nVHE, and `SYSREGS_ON_CPU` is written and read by VHE code.
- `sflags` under pKVM: never copied between host and hyp vCPU.
- Accessors: `vcpu_set_flag()` and `vcpu_clear_flag()` disable preemption,
  except in the nVHE object, because load/put, run from preempt notifiers,
  write flags too.
- **Unsafe usage**: writing a vCPU flag from code that can run while another
  thread is in an ioctl of that vCPU; the accessors are a plain
  read-modify-write.
  - Safe: with `vcpu->mutex` held, which `kvm_vcpu_ioctl()` takes, as
    `kvm_incr_pc()` in an exit handler is; `kvm_inject_sea()` asserts the
    mutex.
  - Safe: state set from another thread kept outside the sets, as
    `kvm_arm_halt_guest()` does with `vcpu->arch.pause` plus `KVM_REQ_SLEEP`;
    the comment on `pause` in `struct kvm_vcpu_arch` gives the reason.
- Choosing a set: `iflags` if a pKVM hyp vCPU must see a change made after
  creation, since it is the only set copied on each run; it has three free
  bits.

**Pending exception state**

- `kvm_pend_exception()`: its only check is `WARN_ON()` of `INCREMENT_PC`; a
  second call replaces the target.
- `INCREMENT_PC` is the low bit of `EXCEPT_MASK`: the second
  `kvm_pend_exception()` warns when the first target has that bit set, for
  example `EXCEPT_AA64_EL1_SERR` or `EXCEPT_AA32_IABT`, and is silent after
  `EXCEPT_AA64_EL1_SYNC` or `EXCEPT_AA64_EL2_SYNC`.
- There is no kvm_adjust_pc() here; callers use `__kvm_adjust_pc()` directly
  or through `kvm_call_hyp()`.
- `kvm_inject_exception()`: implements only `EXCEPT_AA64_EL1_SYNC`,
  `EXCEPT_AA64_EL1_SERR`, `EXCEPT_AA64_EL2_SYNC`, `EXCEPT_AA64_EL2_IRQ` and
  `EXCEPT_AA64_EL2_SERR` for AArch64; any other value is dropped and the flags
  are still cleared.
- Commit point on nVHE: `__kvm_vcpu_run()` calls `__kvm_adjust_pc()` before
  the guest sysregs are restored, so the ELR and SPSR it wrote to memory are
  loaded.
- Commit point on VHE: `__kvm_vcpu_run_vhe()` calls it after
  `__activate_traps()` and before `sysreg_restore_guest_state_vhe()`.
- Return to userspace: `kvm_arch_vcpu_ioctl_run()` commits at `out:` with
  `kvm_call_hyp(__kvm_adjust_pc, vcpu)` before `vcpu_put()`; nothing stays
  pending across the return.
- `out:` is also reached by the `!vcpu->wants_to_run` path, after
  `kvm_handle_mmio_return()` may have called `kvm_incr_pc()`.
- Under pKVM that call runs `__kvm_adjust_pc()` on the host's vCPU, not on
  the hyp vCPU; see `handle___kvm_adjust_pc()`.
- `commit_pending_events()` in `arch/arm64/kvm/guest.c`: commits a pending
  exception at once for `KVM_SET_VCPU_EVENTS` and clears `vcpu->mmio_needed`.

**Injecting an exception safely**

- There is no kvm_inject_dabt() or kvm_inject_pabt() here; `kvm_inject_sea()`
  with `kvm_inject_sea_dabt()` and `kvm_inject_sea_iabt()` does that job.
- `kvm_inject_sea()` and `kvm_inject_serror_esr()`: assert `vcpu->mutex` with
  `lockdep_assert_held()`.
- `kvm_inject_sea()`, `kvm_inject_serror_esr()`, `kvm_inject_s2_fault()`:
  return `int` and may do a put/load through `kvm_inject_nested()`; abort
  handlers return the value of `kvm_inject_sea()` and `kvm_inject_serror()`.
- **Unsafe usage**: calling `kvm_incr_pc()` and `kvm_pend_exception()` for
  the same exit; each has a `WARN_ON()` of the other's flag, and
  `INCREMENT_PC` is a bit of `EXCEPT_MASK`, so the target is corrupted or the
  increment is lost.
  - Safe: one or the other; `kvm_handle_mmio_return()` tests
    `kvm_pending_external_abort()` before `kvm_incr_pc()`.
  - Safe: committing in between with `__kvm_adjust_pc()`, as
    `kvm_inject_nested()` does on its put/load path before it pends the EL2
    exception; its direct-inject path pends without committing.
- Host order: `exception_target_el()` is always EL1 without NV; with NV it
  picks the ESR and FAR register from `*vcpu_cpsr()`; `inject_abt64()` pends
  first, then writes FAR and ESR with `vcpu_write_sys_reg()`.
- Patching the ESR: inject, then read back, modify and write with
  `vcpu_read_sys_reg()` and `vcpu_write_sys_reg()`, as
  `kvm_inject_size_fault()` and `kvm_inject_dabt_excl_atomic()` do.
- Hyp order with sysregs live, `inject_sync64()` in
  `arch/arm64/kvm/hyp/nvhe/sys_regs.c`:
  - read ELR_EL2 and SPSR_EL2 into `*vcpu_pc()` and `*vcpu_cpsr()`;
  - copy VBAR_EL1 and SCTLR_EL1 to memory, since `enter_exception64()` reads
    them;
  - `kvm_pend_exception()`, then `__kvm_adjust_pc()`;
  - write ESR_EL1, then ELR_EL1 and SPSR_EL1 from ELR_EL2 and SPSR_EL2;
  - only then write the new PC and PSTATE to ELR_EL2 and SPSR_EL2.
- Injecting abort handlers, for example: `kvm_handle_guest_abort()` in
  `arch/arm64/kvm/mmu.c` and `io_mem_abort()` in `arch/arm64/kvm/mmio.c`.

**FP and SIMD ownership**

- Ownership: `fp_owner` in the per-CPU `struct kvm_host_data`, read through
  `host_data_ptr(fp_owner)`; nothing in `struct kvm_vcpu_arch` tracks it.
- There is no fpsimd_kvm_prepare() here; `kvm_arch_vcpu_load_fp()` calls
  `fpsimd_save_and_flush_cpu_state()` and then sets `FP_STATE_FREE`, unless
  it returned early (no FP/SIMD on the system, or a nested transition).

| State | Set by |
|---|---|
| `FP_STATE_FREE` | `kvm_arch_vcpu_load_fp()`, `kvm_arch_vcpu_ctxflush_fp()` |
| `FP_STATE_GUEST_OWNED` | `kvm_hyp_handle_fpsimd()` |
| `FP_STATE_HOST_OWNED` | pKVM hyp only: `fpsimd_sve_flush()` and `fpsimd_sve_sync()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c` |

- pKVM hyp vCPU: `fpsimd_sve_sync()` saves the guest state and restores the
  host's after a run in which the guest took the registers, so the host
  never sees `FP_STATE_GUEST_OWNED` and `kvm_arch_vcpu_ctxsync_fp()` and
  `kvm_arch_vcpu_put_fp()` bind and save nothing.

**Guest FP state load**

- There is no __fpsimd_restore_state() here; `kvm_hyp_handle_fpsimd()` uses
  `fpsimd_load_state()` or `__hyp_sve_restore_guest()`.
- Nested transition: `kvm_arch_vcpu_load_fp()` and `kvm_arch_vcpu_put_fp()`
  both return early when `IN_NESTED_ERET` or `IN_NESTED_EXCEPTION` is set.
- Effect: nothing is saved or flushed and `fp_owner` is unchanged, so a
  guest that owned the registers still owns them after the transition.
- Both early returns warn once if `host_owns_fp_regs()`.
- Other put/load pairs, for example `kvm_reset_vcpu()`, set neither flag and
  do the full FP save and flush.
- `kvm_arch_vcpu_put_fp()`: never writes `fp_owner`; the next
  `kvm_arch_vcpu_load_fp()` sets `FP_STATE_FREE`.
- After a transition with state kept live, traps and vector length follow the
  new context at the next entry: see `__activate_cptr_traps_vhe()` and
  `fpsimd_lazy_switch_to_guest()` in
  `arch/arm64/kvm/hyp/include/hyp/switch.h`.

## Guest system registers

**Register accessors and location**

- `__vcpu_sys_reg(v, r)`: yields a value, not an lvalue; `__vcpu_sys_reg(v, r) = x`
  does not compile.
- `__vcpu_assign_sys_reg(v, r, val)` and `__vcpu_rmw_sys_reg(v, r, op, val)`:
  the two `__vcpu_` register accessors that write memory; `op` is for example
  `|=`.
- `SYSREGS_ON_CPU`: the vcpu flag that `locate_register()` tests; there is no
  sysregs_loaded_on_cpu field.
- `__vcpu_load_switch_sysregs()` sets the flag and
  `__vcpu_put_switch_sysregs()` clears it, in
  `arch/arm64/kvm/hyp/vhe/sysreg-sr.c`; there is no kvm_vcpu_put_sysregs_vhe().
- There is no __vcpu_read_sys_reg_from_cpu(), __vcpu_write_sys_reg_to_cpu(),
  get_el2_to_el1_mapping() or PURE_EL2_SYSREG here; `locate_register()`,
  `read_sr_from_cpu()` and `write_sr_to_cpu()` in `arch/arm64/kvm/sys_regs.c`
  do that job.
- Mapped EL2 register with a translation function and guest E2H clear
  (`SR_LOC_XLATED`): `vcpu_read_sys_reg()` returns the memory copy, with no
  reverse translation.
- `vcpu_write_sys_reg()` on a loaded register: writes the CPU (translated if
  `SR_LOC_XLATED`) and then memory (untranslated), which is what makes the
  read above correct.
- `SR_LOC_SPECIAL`: `CNTHCTL_EL2` and `CPTR_EL2`, only when `is_hyp_ctxt()` and
  guest E2H is set; otherwise `CNTHCTL_EL2` is in memory and `CPTR_EL2`
  follows the mapped rule.
- `CPTR_EL2` as `SR_LOC_SPECIAL`: read returns memory unless the host has
  `ARM64_HAS_NV2P1`; write goes to the CPU and to memory.
- `CNTHCTL_EL2` as `SR_LOC_SPECIAL`: read merges the CPU's `CNTKCTL_EL1` bits
  (`CNTKCTL_VALID_BITS`) with the memory copy unless `ARM64_HAS_NV2P1`.
- `NVHCR_EL2`: `locate_register()` puts it on the CPU when not
  `is_hyp_ctxt()` and in memory when `is_hyp_ctxt()`, the reverse of the
  mapped EL2 registers; it warns unless `kvm_has_nv3()`.
- Value read from the CPU on the `SR_LOC_LOADED` path: `vcpu_read_sys_reg()`
  masks it with `kvm_vcpu_apply_reg_masks()` when
  `reg >= __SANITISED_REG_START__`; the `SR_LOC_SPECIAL` reads from the CPU
  are not masked.
- nVHE hyp objects (`__KVM_NVHE_HYPERVISOR__`): `vcpu_read_sys_reg()` and
  `vcpu_write_sys_reg()` are macros for `__vcpu_sys_reg()` and
  `__vcpu_assign_sys_reg()`, in `arch/arm64/include/asm/kvm_emulate.h`.
- **Potentially unsafe usage**: `__vcpu_sys_reg()` or
  `__vcpu_assign_sys_reg()` on a vCPU with `SYSREGS_ON_CPU` set.
  - Unsafe: in code that wants the guest's current value, for a register
    that `vcpu_read_sys_reg()` would read from the CPU in the current context
    (`SR_LOC_LOADED` without `SR_LOC_XLATED`, `CNTHCTL_EL2` as
    `SR_LOC_SPECIAL`, or `CPTR_EL2` as `SR_LOC_SPECIAL` with
    `ARM64_HAS_NV2P1`); the read is stale and the save in
    `__vcpu_put_switch_sysregs()` overwrites the write.
  - Safe: for a register that `locate_register()` reports as
    `SR_LOC_MEMORY`, as `check_fgt_bit()` in `arch/arm64/kvm/emulate-nested.c`
    does for the guest's fine-grained trap registers.
  - Safe: in the save code itself, which stores the value it has just read
    from the CPU, as `__sysreg_save_vel2_state()` in
    `arch/arm64/kvm/hyp/vhe/sysreg-sr.c` does.
  - Safe: `vcpu_read_sys_reg()` and `vcpu_write_sys_reg()` instead, which
    call `locate_register()`, as `inject_abt64()` in
    `arch/arm64/kvm/inject_fault.c` does for ESR and FAR.
  - Safe: in the hyp switch code, for a value that code stored itself, as
    `fpsimd_lazy_switch_to_guest()` in
    `arch/arm64/kvm/hyp/include/hyp/switch.h` does for `ZCR_EL1`;
    `fpsimd_lazy_switch_to_host()` wrote the CPU value to memory at the last
    exit.

**Register storage**

- Order of `enum vcpu_sysreg`: a plain block numbered by declaration (EL0/EL1
  registers that are not VNCR-capable, PMU, pointer auth, MTE, 32-bit, EL2
  registers without masks), then the `__SANITISED_REG_START__` block (EL2
  registers with masks), then the `__VNCR_START__` block.
- VNCR block: holds many EL1 registers (`SCTLR_EL1`, `TCR_EL1`, ...) as well as
  EL2 ones (`VTTBR_EL2`, `HCRX_EL2`, ...); it is not "the EL2 registers".
- There is no __SANITISED_REG_END__; the sanitised range runs to `NR_SYS_REGS`
  and so contains the whole VNCR block.
- `MARKER()`: defined in `arch/arm64/include/asm/kvm_asm.h`; it emits the marker
  and an `__after_` entry one lower, so the marker takes no number of its own:
  `__SANITISED_REG_START__ == SCTLR_EL2`.
- Holes: VNCR numbers follow `arch/arm64/include/asm/vncr_mapping.h`, so many
  values between `__VNCR_START__` and `NR_SYS_REGS` name no register.
- `NR_SYS_REGS`: one above the highest VNCR number, not a count of registers;
  `sys_regs[]` and `struct kvm_sysreg_masks` are sized with the holes.
- With NV: only entries at or above `__VNCR_START__` are in `vncr_array`;
  `HCR_EL2`, `SCTLR_EL2` and the other EL2 registers below it stay in
  `sys_regs[]`.
- `___ctxt_sys_reg()`: picks `vncr_array` on
  `cpus_have_final_cap(ARM64_HAS_NESTED_VIRT)` and a non-NULL `vncr_array`; it
  does not test `vcpu_has_nv()`.
- nVHE hyp objects: the `vncr_array` branch is compiled out under
  `__KVM_NVHE_HYPERVISOR__`; they always index `sys_regs[]`.

**Ranges over the register enum**

- Guaranteed by the enum itself: every register declared after a marker is
  numerically at or above it, and `NR_SYS_REGS` is above every entry; inside
  the VNCR block the numbers follow the page offsets in
  `arch/arm64/include/asm/vncr_mapping.h`, not the declaration order.
- There is no grouping by "loaded on the CPU"; EL1 registers are split between
  the plain block and the VNCR block.
- `set_sysreg_masks()` in `arch/arm64/kvm/nested.c`: has `BUILD_BUG_ON()` for a
  register below `__SANITISED_REG_START__`; a register that gets RES0/RES1
  masks must be declared after that marker.
- Pointer-auth keys: each `HI` entry must directly follow its `LO` entry; the
  `stp`/`ldp` pairs in `arch/arm64/include/asm/kvm_ptrauth.h` rely on it.
- Code that selects by name: `locate_register()` and `locate_direct_register()`
  in `arch/arm64/kvm/sys_regs.c`; `__copy_vcpu_state()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`, which skips the timer registers with one
  `case` each.
- **Unsafe usage**: `<`, `>` or `case A ... B` between two named
  `enum vcpu_sysreg` registers.
  - Safe: comparison against `__SANITISED_REG_START__`, `__VNCR_START__` or
    `NR_SYS_REGS`, as `___ctxt_sys_reg()` and `__kvm_get_sysreg_resx()` do; the
    `MARKER()` and `VNCR()` macros define that order.
  - Safe: one `case` per register, as `__copy_vcpu_state()` does.
- **Potentially unsafe usage**: base register plus index.
  - Unsafe: when nothing makes the family's numbers consecutive, for example
    VNCR entries whose page offsets are not 8 bytes apart.
  - Safe: `PMEVCNTR0_EL0 + idx` and `PMEVTYPER0_EL0 + idx`, as
    `counter_index_to_reg()` and `counter_index_to_evtreg()` in
    `arch/arm64/kvm/pmu-emul.c` do; the enum reserves the slots with
    `PMEVCNTR30_EL0 = PMEVCNTR0_EL0 + 30`.
  - Safe: `ICH_LRN()`, `ICH_AP0RN()`, `ICH_AP1RN()` in
    `arch/arm64/kvm/vgic/vgic-v3-nested.c`; the offsets in
    `arch/arm64/include/asm/vncr_mapping.h` are 8 bytes apart.
- **Potentially unsafe usage**: a loop over every number from a marker to
  `NR_SYS_REGS`.
  - Unsafe: when the body assumes each number is a register; the range has
    holes.
  - Safe: when the body is harmless on a hole, as the loop at the end of
    `kvm_init_nv_sysregs()` is: it rewrites each slot with its own masked
    value.

**Trap descriptors**

- `REG_RAZ`: tested only by `sysreg_visible_as_raz()` in
  `__kvm_read_sanitised_id_reg()` and `arm64_check_features()`, both for ID
  registers; `perform_access()`, `kvm_sys_reg_get_user()` and
  `kvm_sys_reg_set_user()` do not test it.
- `REG_RAZ` on an ID register whose `.reset` is
  `kvm_read_sanitised_id_reg()`: the reset value is 0, so guest and userspace
  read 0; a non-zero userspace write, before the VM has run and without
  `REG_USER_WI`, fails with `-EINVAL` from `set_id_reg()`.
- `REG_RAZ` and guest writes: nothing ignores them; `access_id_reg()` treats a
  write as `write_to_read_only()`, which injects UNDEF.
- `REG_RAZ | REG_USER_WI`: returned by `aa32_id_visibility()`; `REG_RAZ` is not
  combined with `REG_HIDDEN` anywhere.
- There is no user_visibility hook; `REG_USER_WI` from `.visibility` is the
  userspace-only flag, and `kvm_sys_reg_set_user()` returns 0 on it before
  `.set_user` runs.
- `kvm_sys_reg_table_init()`: also checks the GICv3 table returned by
  `vgic_v3_get_sysreg_table()`.
- `check_sysreg_table()` reset check (`.reg` set but no `.reset`): applied only
  when `reset_check` is true, which is `sys_reg_descs` only.
- pKVM table `pvm_sys_reg_descs` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`:
  checked by `kvm_check_pvm_sysreg_table()`; a failure hits `BUG_ON()` in
  `arch/arm64/kvm/hyp/nvhe/setup.c`.

**Trap handling flow**

- Lookup: `get_trap_config()` loads a `union trap_config` from the xarray
  `sr_forward_xa` by encoding; the AArch64 trap path does no `find_reg()`, and
  there is no encoding_to_sr().
- `kvm_handle_sys_reg()`: calls `triage_sysreg_trap()` before it decodes the
  ESR into `struct sys_reg_params`.
- Order of decisions:
  1. `tc.val == 0`: go to step 6.
  2. `tc.fgt` set and the bit set in `kvm->arch.fgu[tc.fgt]`: UNDEF, for every
     VM.
  3. No `vcpu_has_nv()`: go to step 6.
  4. `is_hyp_ctxt()` and not `vcpu_is_host_el0()`: go to step 6.
  5. Guest fine-grained trap (`check_fgt_bit()`), then coarse traps
     (`compute_trap_behaviour()`): forward with `kvm_inject_nested_sync()`.
  6. `tc.sri == 0`: no descriptor, the access is refused here.
  7. `perform_access()`: `REG_HIDDEN` gives UNDEF, then `.access` runs.
- Step 2 on a host without `ARM64_HAS_FGT`: never fires, because
  `populate_nv_trap_config()` does not store the fine-grained part of the
  config; the UNDEF for a disabled feature then comes only from step 7 or the
  access function.
- Step 5 in hyp context at EL0: `check_fgt_bit()` returns false, and a coarse
  trap forwards only if it has `BEHAVE_FORWARD_IN_HOST_EL0`.
- Step 6 in the feature ID space (`in_feat_id_space()`): `kvm_inject_sync()`
  with the original ESR when the VM has `ID_AA64MMFR2_EL1` `IDS`, UNDEF
  otherwise.
- Step 7 comes after step 5: for an NV guest, forwarding to the guest
  hypervisor wins over `REG_HIDDEN`.
- Descriptor table: `sys_reg_descs[sr_idx]` when Op0 is 2 or 3, otherwise
  `sys_insn_descs[sr_idx]`; Rt is written back only for a read with Op0 2 or 3.
- Missing `.access`: `bad_trap()`, which is `WARN_ONCE()` plus UNDEF; there is
  no `BUG_ON()`.
- Read/write direction: not checked by `perform_access()`; access functions
  call `write_to_read_only()` or `read_from_write_only()` themselves.
- `unhandled_cp_access()`: AArch32 coprocessor path only.

## ID registers and traps

**ID register storage**

- `__vm_id_reg()` in `arch/arm64/include/asm/kvm_host.h`: maps an encoding
  to its slot; there is no IDREG() macro.
- Outside `id_regs[]`: `ctr_el0`, `midr_el1`, `revidr_el1`, `aidr_el1` are
  separate fields of `struct kvm_arch`, reached through the same helper.
- Unknown encoding: `__vm_id_reg()` warns and returns NULL, which
  `kvm_read_vm_id_reg()` dereferences.
- Initialisation: `reset_vm_ftr_id_reg()`, called by `kvm_reset_sys_regs()`
  from `kvm_reset_vcpu()`; there is no kvm_reset_id_regs() or
  kvm_init_sysreg().
- First reset: reached from `__kvm_vcpu_set_target()`, which holds
  `config_lock` around `kvm_reset_vcpu()`.
- Later resets: the other callers of `kvm_reset_vcpu()` run without
  `config_lock`; `reset_vm_ftr_id_reg()` returns on
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED` before it reaches
  `kvm_set_vm_id_reg()`.
- `kvm_set_vm_id_reg()`: asserts `kvm->arch.config_lock`, does not take it.
- Writers: every call site of `kvm_set_vm_id_reg()` holds `config_lock`; the
  one outside `arch/arm64/kvm/sys_regs.c` is `kvm_vgic_finalize_idregs()`,
  so creating a vGIC rewrites three ID registers.
- `get_id_reg()`: takes `config_lock` until `kvm_vm_has_ran_once()`, then
  reads without it.
- pKVM non-protected VM: `vm_copy_id_regs()` copies `id_regs[]` from the
  host, and fails with `-EINVAL` if the host has not initialised them.
- pKVM, outside `id_regs[]`: `pkvm_init_features_from_host()` copies
  `ctr_el0` always and `midr_el1` only for a non-protected VM with
  `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS`.
- pKVM protected VM: `kvm_init_pvm_id_regs()` fills CRm 4 to 7 only.

**Feature test for a VM**

- Before the first `kvm_reset_sys_regs()`: `id_regs[]` is zero, so an
  unsigned field tests absent and a signed field whose limit is 0 tests
  present, for example `ID_AA64PFR0_EL1` `FP` against `IMP`.
- Features enabled by a vCPU feature bit or VM flag have their own test:
  `vcpu_has_nv()`, `vcpu_has_sve()`, `vcpu_has_ptrauth()`, `kvm_has_mte()`.
- `ID_AA64PFR0_EL1` `EL2`: `sanitise_id_aa64pfr0_el1()` does not clear it,
  so `kvm_has_feat()` on it can be true for a VM without NV.
- `kvm_has_fpmr()` and `kvm_has_s1poe()`: also test the host, with
  `system_supports_fpmr()` and `system_supports_poe()`.
- Host capability test: `kvm_has_feat()` makes none. Host code touches
  hardware on the guest test alone, as `__kvm_at_s1e01_fast()` does for
  `TCR2_EL1`; `arm64_check_features()` accepts a field only if it equals the
  limit or is the safe value against it.
- Hyp save and restore helpers test the host capability first, as
  `ctxt_has_tcrx()` does with `ARM64_HAS_TCR2`; under pKVM
  `vm_copy_id_regs()` copies the host's values unchecked.
- Fields KVM sets itself are not bounded by the host, for example CSV2,
  CSV3 and GIC in `sanitise_id_aa64pfr0_el1()`, and the fields
  `limit_nv_id_reg()` forces.
- **Potentially unsafe usage**: storing a decision taken from
  `kvm_has_feat()` in VM or vCPU state.
  - Unsafe: stored at vCPU create, init or reset time, when `set_id_reg()`
    still accepts another value and `kvm_finalize_sys_regs()` has not yet
    edited the GIC fields.
  - Safe: stored from `kvm_calculate_traps()`, which
    `kvm_arch_vcpu_run_pid_change()` calls after `kvm_finalize_sys_regs()`,
    as `vcpu_set_hcrx()` is; `set_id_reg()` refuses a change only once
    `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set, at the end of that function.
  - Safe: not stored but tested at each use, as `tcr2_visibility()` does.
  - Safe: at hyp vCPU init for a protected VM, as `pvm_init_traps_hcr()`
    does; it reads the hyp copy, which `pkvm_vcpu_init_sysregs()` filled
    just before and `set_id_reg()` never writes.

**ID register descriptor kinds:** All are in `arch/arm64/kvm/sys_regs.c`;
`ID_DESC()` and `ID_DESC_DEFAULT_CALLBACKS` are the shared body of the first
five rows, not kinds of their own.

| Macro | Guest reads | Userspace write | `val` |
|---|---|---|---|
| `ID_SANITISED(name)` | stored value | only the `.reset` value | 0 |
| `ID_WRITABLE(name, mask)` | stored value | fields in mask | mask |
| `ID_FILTERED(sysreg, name, mask)` | stored value | the setter named `set_` plus name, for example `set_id_aa64pfr0_el1()`, then as `ID_WRITABLE()` | mask |
| `AA32_ID_WRITABLE(name)` | stored value; zero without 32-bit EL0 | low 32 bits; without 32-bit EL0 any value returns 0 and is dropped | `GENMASK(31, 0)` |
| `ID_HIDDEN(name)`, `ID_UNALLOCATED(crm, op2)` | zero | only 0 | 0 |
| `IMPLEMENTATION_ID(reg, mask)` | stored value with `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS`, else the running CPU's | `set_imp_id_reg()` | mask |

- There is no AA32_ID_SANITISED() here; `AA32_ID_WRITABLE()` does that job.
- `aa32_id_visibility()`: tests `kvm_supports_32bit_el0()`, and returns
  `REG_RAZ | REG_USER_WI` when it is false.
- RAZ registers whose `.reset` is `kvm_read_sanitised_id_reg()`: zero comes
  from the stored value, since that `.reset` returns 0; `access_id_reg()`
  does not test `REG_RAZ`.
- `ID_DFR0_EL1`: declared without a macro, with `set_id_dfr0_el1()`,
  `read_sanitised_id_dfr0_el1()` and `aa32_id_visibility()`.
- `set_imp_id_reg()`: a write of the stored value returns 0; another value
  needs the flag (`-EINVAL`), a VM that has not run (`-EBUSY`) and no bit
  outside the mask (`-EINVAL`); it does not call `arm64_check_features()`.
- `ID_SANITISED()` and the other non-RAZ kinds built on `ID_DESC()`: the
  register needs an entry in `arm64_ftr_regs`, or `read_sanitised_ftr_reg()`
  warns and returns 0.

**Userspace ID register writes**

- Limit: `rd->reset(vcpu, rd)`, computed again at each write; not the stored
  value and not the raw host value.
- Direction: set per field by its `struct arm64_ftr_bits` type through
  `kvm_arm64_ftr_safe_value()`, so not every field may only be lowered.
- Writable field: one whose whole `arm64_ftr_mask()` lies inside `rd->val`.
- Everything else must equal the limit bit for bit: fields outside the mask,
  fields partly inside it, and bits with no `struct arm64_ftr_bits`.
- Error code: `arm64_check_features()` returns `-E2BIG`; `set_id_reg()`
  returns `-EINVAL` to userspace in its place.
- No `struct arm64_ftr_reg` for the register: `-EINVAL`.
- RAZ register, before the VM has run: only 0 is accepted.
- Once the VM has run: the comparison is with the stored value, which
  includes the edits of `kvm_finalize_sys_regs()`, not with the limit.
- Custom setters run before `set_id_reg()`: their fix-ups apply to the value
  that is compared, and their `-EINVAL` comes before `-EBUSY`; see
  `set_id_aa64dfr0_el1()`.

**Late ID register changes**

- `kvm_set_vm_id_reg()` returns `void`: on a VM that has run, `KVM_BUG_ON()`
  warns once and calls `kvm_vm_bugged()`, and the value is not stored.
- The caller sees no error; later ioctls on the VM, its vCPUs and its
  devices return `-EIO`.
- Same result for an encoding `__vm_id_reg()` does not know.
- Every call site avoids the late case first: `set_id_reg()`,
  `set_imp_id_reg()` and `kvm_finalize_sys_regs()` test
  `kvm_vm_has_ran_once()`; `reset_vm_ftr_id_reg()` tests
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED`; `kvm_vgic_create()` tests
  `vcpu_has_run_once()` on each vCPU.
- Mask array: covers Op0=3, Op1 in {0, 1, 3}, CRn=0, CRm 0 to 7;
  `KVM_ARM_FEATURE_ID_RANGE_SIZE` entries.
- Index: `KVM_ARM_FEATURE_ID_RANGE_IDX()` in
  `arch/arm64/include/uapi/asm/kvm.h`; `KVM_ARM_FEATURE_ID_RANGE_INDEX()` is
  the one-argument wrapper private to `arch/arm64/kvm/sys_regs.c`.
- `kvm_vm_ioctl_get_reg_writable_masks()`: reports the static `val` of
  descriptors that have `set_user`; it consults no VM state.
- A reported bit is no promise: `MIDR_EL1`, `REVIDR_EL1` and `AIDR_EL1` are
  reported without `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS`, and
  `arm64_check_features()` and custom setters still apply.
- `KVM_CAP_ARM_SUPPORTED_REG_MASK_RANGES`: returns `BIT(0)`, a bitmap of
  supported ranges.

**Exposing a new ID field**

- Example: `ID_AA64MMFR3_EL1` `TCRX`; search for `kvm_has_tcr2()` to see
  the trap, visibility and context-switch pieces.
- What must agree with the descriptor:
  - `struct arm64_ftr_bits` entry in `arch/arm64/kernel/cpufeature.c`:
    `init_cpu_ftr_reg()` zeroes any field without one.
  - `__kvm_read_sanitised_id_reg()` and the helpers it calls, such as
    `sanitise_id_aa64pfr0_el1()`, in `arch/arm64/kvm/sys_regs.c`: the limit.
  - `limit_nv_id_reg()` in `arch/arm64/kvm/nested.c`: the limit under NV.
  - `pvm_calc_id_reg()` and its `MAX_FEAT()` tables in
    `arch/arm64/kvm/hyp/nvhe/sys_regs.c`: protected VMs.
  - Feature maps in `arch/arm64/kvm/config.c`; see "Feature dependency
    tables".
  - `SR_FGT()` entries in `arch/arm64/kvm/emulate-nested.c`: `aggregate_fgt()`
    builds the FGT masks from them.
  - `tools/testing/selftests/kvm/arm64/set_id_regs.c`.
- Allow-list registers: `ID_AA64MMFR3_EL1`, `ID_AA64ISAR3_EL1` and
  `ID_AA64PFR2_EL1` keep only named fields, in both the limit and the
  writable mask; a new field stays hidden until added to the limit, and
  not writable until added to the mask.
- Protected VM: a register `pvm_calc_id_reg()` does not handle reads as 0, so
  a new field in such a register is hidden there by default.
- Non-protected pKVM VM: hyp tests the copy made by `vm_copy_id_regs()`, and
  takes `hcrx_el2` from the host in `pkvm_vcpu_init_traps()`.
- **Potentially unsafe usage**: adding a field to
  `arch/arm64/tools/sysreg` and `arch/arm64/kernel/cpufeature.c`.
  - Unsafe: for a register whose limit is not an allow-list, when KVM
    neither masks the field nor handles the feature; the guest sees it with
    no KVM change. `set_id_aa64pfr0_el1()` carries the MPAM clean-up for
    this.
  - Safe: for a register whose limit is an allow-list, as `ID_AA64MMFR3_EL1`
    is in `__kvm_read_sanitised_id_reg()`.
  - Safe: when the same patch masks the field in the limit, as
    `sanitise_id_aa64pfr1_el1()` does for `ID_AA64PFR1_EL1_GCS`.
- **Unsafe usage**: letting a field through the limit when the registers it
  advertises are not enabled, context switched and made to UNDEF when
  the field is lowered.
  - Safe: all keyed on one test, as for `TCRX`: `vcpu_set_hcrx()` sets
    `HCRX_EL2_TCR2En`, `tcr2_visibility()` hides `TCR2_EL1`, and
    `ctxt_has_tcrx()` gates save and restore.

**Feature dependency tables**

- There is no NEEDS_FEAT_FIXED() and no FIXED_VALUE flag here; fixed bits
  are `FORCE_RES0()` and `FORCE_RES1()`.
- Flags that pick RES1 over RES0 when the feature is absent: `AS_RES1`,
  `RES1_WHEN_E2H0`, `RES1_WHEN_E2H1`.
- `REQUIRES_E2H1`: the bits are also reserved when the VM has `FEAT_E2H0`.
- `NEEDS_FEAT()` with three arguments after the bits: `idreg_feat_match()`
  reads `kvm->arch.id_regs[]` directly, so the register must be one stored
  there; anything else needs the predicate form.
- Predicate form: one argument after the bits sets `CALL_FUNC`.
- `DECLARE_FEAT_MAP()` and `DECLARE_FEAT_MAP_FGT()`: wrap a table in a
  `struct reg_feat_map_desc` with a feature for the whole register.
- `get_reg_fixed_bits()`: returns `struct resx`; without the whole-register
  feature every non-RESx bit is RES0. There is no compute_res0_bits().
- `compute_fgu()`: ignores the whole-register feature and `NEVER_FGU`
  entries, ORs RES0 and RES1 results, and overwrites `fgu[group]`.
- Boot check: `check_feature_map()`, called by `kvm_sys_reg_table_init()`
  after `populate_nv_trap_config()`; it is a run-time check.
- `check_feat_map()`: the OR of the entries, leaving out `FORCE_RESx`
  entries that overlap the architectural RESx bits, must equal the non-RESx
  bits exactly, so it reports missing and surplus bits alike.
- Non-RESx bits: for an FGT register `mask | nmask` of its
  `struct fgt_masks`, built from `SR_FGT()` entries; otherwise the
  complement of the register's generated RES0 and RES1 masks, for example
  `~(HCRX_EL2_RES0 | HCRX_EL2_RES1)`.
- Failed check: one `kvm_err()` line; nothing fails.
- New table: nothing registers it; each user names the tables one by one,
  for example `check_feature_map()`, `get_reg_fixed_bits()` and
  `kvm_init_nv_sysregs()`, and for an FGT group `compute_fgu()` and
  `kvm_calculate_traps()`.

**Trap computation**

- Must be final: ID registers including the edits of
  `kvm_finalize_sys_regs()`, `ctr_el0`, `kvm->arch.vcpu_features`,
  `KVM_ARCH_FLAG_MTE_ENABLED`, and the vGIC model.
- NV also needs `kvm->arch.sysreg_masks`: with `ARM64_HAS_NV3`,
  `vcpu_set_hcrx()` reads `HCR_EL2` through `vcpu_el2_e2h_is_set()`.
- `KVM_ARCH_FLAG_HAS_RAN_ONCE`: still clear on the first vCPU's call; it is
  set at the end of `kvm_arch_vcpu_run_pid_change()`.
- Lock: `kvm_calculate_traps()` takes `kvm->arch.config_lock` itself, so the
  caller must not hold it.
- `kvm_finalize_sys_regs()`, `kvm_calculate_traps()` and the flag update are
  three separate `config_lock` sections.

| Computed | Scope | By |
|---|---|---|
| bits ORed into `vcpu->arch.hcr_el2` | each vCPU's first run | `vcpu_set_hcr()` |
| trap bits in `vgic_hcr` | each vCPU's first run | `vcpu_set_ich_hcr()` |
| `vcpu->arch.hcrx_el2`, assigned | each vCPU's first run | `vcpu_set_hcrx()` |
| `kvm->arch.fgu[]` | once per VM | `compute_fgu()` |

- Not computed here: `vcpu->arch.fgt[]` (see "Fine-grained trap state") and
  the RES0/RES1 masks (see "System register finalisation").
- Repeat calls: a failure later in `kvm_arch_vcpu_run_pid_change()` leaves
  `vcpu_has_run_once()` false, so the next `KVM_RUN` calls it again.

**System register finalisation**

- It does not initialise ID registers and does not set
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED`; `kvm_reset_sys_regs()` does both.
- It does not apply `limit_nv_id_reg()`; `__kvm_read_sanitised_id_reg()`
  does.
- Steps, under `config_lock`:
  1. NV only: `kvm_init_nv_sysregs()`, before the `kvm_vm_has_ran_once()`
     test, so on every vCPU's first run.
  2. Return if `kvm_vm_has_ran_once()`.
  3. No in-kernel irqchip: clear `ID_AA64PFR0_EL1` `GIC`,
     `ID_AA64PFR2_EL1` `GCIE` and `ID_PFR1_EL1` `GIC`.
  4. In-kernel irqchip: `kvm_vgic_finalize_idregs()` sets the same three
     fields from `vgic_model`.
- `kvm_init_nv_sysregs()`, once per VM: allocates and fills
  `kvm->arch.sysreg_masks`; skipped when the pointer is set.
- `kvm_init_nv_sysregs()`, per vCPU: re-applies the masks to that vCPU's
  stored sanitised registers.
- Failure: `-ENOMEM` from the allocation fails `KVM_RUN` before any trap is
  computed.
- Steps 3 and 4 repeat for each vCPU that starts before
  `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set; the edits are idempotent.
- Position: after `kvm_vgic_map_resources()`; for NV,
  `kvm_vcpu_allocate_vncr_tlb()` and `kvm_vgic_vcpu_nv_init()` run between it
  and `kvm_calculate_traps()`.

**Fine-grained trap state**

- `kvm->arch.fgu[]`: one `u64` per `enum fgt_group_id`; a read/write
  register pair shares the group.
- `vcpu->arch.fgt[]`: same index, with separate `.r` and `.w` members.
- `vcpu_fgt()`: takes a register name from `enum vcpu_sysreg`, and picks the
  group and member.
- `fgu[]` is computed without `ARM64_HAS_FGT`, but consulted only with it:
  `populate_nv_trap_config()` stores the FGT group of an encoding only when
  the host has the cap, and `triage_sysreg_trap()` tests `fgu[]` only for an
  encoding that has a group.
- With `ARM64_HAS_FGT`: `triage_sysreg_trap()` injects UNDEF for any trapped
  access whose bit is set, whatever caused the trap.
- `ICH_HFGRTR_GROUP` and `ICH_HFGITR_GROUP`: GICv5 groups; their `fgt[]`
  values are computed in `kvm_vcpu_load_fgt()` only with `ARM64_HAS_FGT` and
  `ARM64_HAS_GICV5_CPUIF`, and written by `__activate_traps_ich_hfgxtr()`
  only with `ARM64_HAS_GICV5_CPUIF`.

| Mode | FGT registers written | By |
|---|---|---|
| VHE | at vCPU load | `kvm_vcpu_load_vhe()` |
| nVHE | on every guest entry | `__activate_traps()` in `arch/arm64/kvm/hyp/nvhe/switch.c` |

- Both reach `__activate_traps_hfgxtr()` through
  `__activate_traps_common()`.
- VHE: `kvm_arch_vcpu_load()` calls `kvm_vcpu_load_fgt()` before
  `kvm_vcpu_load_vhe()`, so a change to an input of `fgt[]` reaches hardware
  only at the next load.
- `HAFGRTR_EL2`: written only when `cpu_has_amu()`.
- Nested guest: `__compute_fgt()` merges L1's register when
  `is_nested_ctxt()`; `kvm_emulate_nested_eret()` and `kvm_inject_nested()`
  do a put and load around the context change.
- pKVM non-protected VM: `handle___pkvm_vcpu_load()` copies the host
  vCPU's `fgt[]` into the hyp vCPU.

**Guest HCR_EL2 value**

- `vcpu_reset_hcr()`: called from `kvm_arch_vcpu_ioctl_vcpu_init()`, not from
  `kvm_reset_vcpu()`.
- Base value: `HCR_GUEST_FLAGS` from `vcpu_reset_hcr()`, assigned only while
  `vcpu_has_run_once()` is false.
- `vcpu_set_hcr()`: only ORs bits in and clears `HCR_RW`; it sets `HCR_TID5`
  when the VM has no MTE.
- At each `kvm_arch_vcpu_load()`: `HCR_TWI`, `HCR_TWE`, and through
  `vcpu_set_pauth_traps()` `HCR_API` and `HCR_APK`.
- `vcpu_set_pauth_traps()`: does nothing when `is_protected_kvm_enabled()`.
- At run time, for example: `HCR_TVM` in `kvm_set_way_flush()` and
  `kvm_toggle_cache()`, `HCR_VSE` in `kvm_inject_serror_esr()`, `HCR_VI` and
  `HCR_VF` in `vcpu_interrupt_line()`.
- At write time: `___activate_traps()` adds `HCR_TVM` under
  `ARM64_WORKAROUND_CAVIUM_TX2_219_TVM`, without storing it.
- nVHE exit: restores the per-CPU `kvm_init_params` value, built in
  `cpu_prepare_hyp_mode()` from `HCR_HOST_NVHE_FLAGS` or
  `HCR_HOST_NVHE_PROTECTED_FLAGS`.
- pKVM: every VM, protected or not, runs on the hyp vCPU's own `hcr_el2`,
  built by `pkvm_vcpu_reset_hcr()` in `pkvm_vcpu_init_traps()`.
- Protected guest: `pvm_init_traps_hcr()` then adds traps from the hyp ID
  registers.
- From the host, at load: `handle___pkvm_vcpu_load()` takes `HCR_TWI` and
  `HCR_TWE` for a protected vCPU.
- From the host, at each run: `flush_hyp_vcpu()` takes `HCR_TWI`, `HCR_TWE`
  and `HCR_VSE`; no other host bit reaches the hyp copy.

## Stage-2 page tables

**MMU lock mode**

- `kvm_fault_lock()` in `arch/arm64/include/asm/kvm_mmu.h`: write lock when
  `is_protected_kvm_enabled()`, read lock otherwise; it tests nothing else
  (not the fault type, not nested).
- Callers of `kvm_fault_lock()`: `kvm_s2_fault_map()` (the tail of
  `user_mem_abort()`) and `gmem_abort()`.
- `pkvm_mem_abort()`, used when `kvm_vm_is_protected()`: takes plain
  `write_lock()`.
- `handle_access_fault()`: plain `read_lock()`, also under pKVM.
- Aging from the notifier: write lock, taken by `kvm_handle_hva_range()`;
  `arch/arm64/kvm/Kconfig` does not select `CONFIG_KVM_MMU_LOCKLESS_AGING`.
- Protected VM: `kvm_unmap_gfn_range()`, `kvm_age_gfn()`,
  `kvm_test_age_gfn()` and `kvm_stage2_unmap_range()` return before touching
  anything.
- Splitting under pKVM: `kvm_mmu_split_huge_pages()` returns 0 before it
  reaches `pkvm_pgtable_stage2_split()`, because `split_page_chunk_size`
  stays 0; `kvm_pkvm_ext_allowed()` rejects
  `KVM_CAP_ARM_EAGER_SPLIT_CHUNK_SIZE`.
- **Potentially unsafe usage**: calling a `KVM_PGT_FN()` target under pKVM
  with `kvm->mmu_lock` held for read.
  - Unsafe: when the target inserts into or removes from
    `pgt->pkvm_mappings`; `pkvm_pgtable_stage2_map()` and
    `pkvm_pgtable_stage2_unmap()` have `lockdep_assert_held_write()`.
  - Safe: `pkvm_pgtable_stage2_mkyoung()` under the read lock, as
    `handle_access_fault()` does; it only issues a hypercall and does not
    touch `pgt->pkvm_mappings`.

**Shared walks**

- There is no KVM_INVALID_PTE_LOCKED here; the locked marker is
  `KVM_INVALID_PTE_TYPE_LOCKED` in the `KVM_INVALID_PTE_TYPE_MASK` field,
  tested by `stage2_pte_is_locked()`.
- `stage2_try_break_pte()` on a table entry: invalidates with
  `kvm_tlb_flush_vmid_range()` over the span of that entry; the whole VMID is
  flushed only when `system_supports_tlb_range()` is false.
- `stage2_attr_walker()`: returns `-EAGAIN` for any invalid entry, so a walker
  that meets another walker's locked entry fails before it tries `cmpxchg()`.

**Callers of shared walks**

- There is no KVM_PGTABLE_WALK_HANDLE_FAULT here. `kvm_pgtable_walk_continue()`
  in `arch/arm64/kvm/hyp/pgtable.c`: `-EAGAIN` ends the walk and is returned,
  unless the walker has `KVM_PGTABLE_WALK_IGNORE_EAGAIN`.
- Callers that pass `KVM_PGTABLE_WALK_SHARED`: `kvm_s2_fault_map()`,
  `gmem_abort()` and `handle_access_fault()` in `arch/arm64/kvm/mmu.c`; none
  of them passes `KVM_PGTABLE_WALK_IGNORE_EAGAIN`.
- `-EAGAIN` becomes 0 in `kvm_s2_fault_map()` and `gmem_abort()`, not in
  `user_mem_abort()` or `kvm_handle_guest_abort()`;
  `kvm_handle_guest_abort()` then turns 0 into 1 and the guest is re-entered.
- `kvm_s2_fault_map()` and `gmem_abort()`: set `ret` to the same `-EAGAIN`
  when `mmu_invalidate_retry()` fires, so the conversion covers both cases.

**Walker flags**

- There is no KVM_PGTABLE_WALK_HANDLE_FAULT here; the flag is
  `KVM_PGTABLE_WALK_IGNORE_EAGAIN` and its sense is the opposite.

| Flag | Effect when set |
|---|---|
| `KVM_PGTABLE_WALK_SHARED` | as in "Shared walks"; also `stage2_map_walker_try_leaf()` skips its shortcut for a change of software bits only, and `kvm_pgtable_visitor_cb()` warns if the RCU read lock is not held |
| `KVM_PGTABLE_WALK_IGNORE_EAGAIN` | `-EAGAIN` from a visitor counts as success: the walk goes on and returns 0 |
| `KVM_PGTABLE_WALK_SKIP_BBM_TLBI` | `stage2_try_break_pte()` does no TLB invalidation; nothing else tests it |
| `KVM_PGTABLE_WALK_SKIP_CMO` | `stage2_map_walker_try_leaf()` does no cache maintenance for the new entry; nothing else tests it |

- Without `KVM_PGTABLE_WALK_IGNORE_EAGAIN`: the first `-EAGAIN` ends the walk
  and is returned, whether or not the walk is in a fault handler.
- `KVM_PGTABLE_WALK_IGNORE_EAGAIN` is set by `kvm_pgtable_stage2_wrprotect()`
  and by `__host_stage2_idmap()` in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `stage2_unmap_walker()` tests neither skip flag.
- `stage2_unmap_defer_tlb_flush()` reads no walk flag; it tests
  `system_supports_tlb_range()` and `ARM64_HAS_STAGE2_FWB`.
- `KVM_PGTABLE_WALK_SKIP_BBM_TLBI`: its one user,
  `kvm_pgtable_stage2_create_unlinked()`, builds a table that is not linked
  yet; `stage2_split_walker()` then does the TLBI when it breaks the block
  entry.

**Page-table library**

- `KVM_PGT_FN(fn)`: defined in `arch/arm64/kvm/mmu.c` and used only there;
  expands to `fn`, or to `p ## fn` when `is_protected_kvm_enabled()`.
- `struct kvm_pgtable` under pKVM: `pkvm_mappings` shares a union with
  `ia_bits`, `start_level`, `pgd`, `mm_ops`, `flags` and `force_pte_cb`;
  besides `pkvm_mappings` only `mmu` is usable.
- `kvm_stage2_destroy()` takes the range from `pgt->mmu->vtcr`, not from
  `pgt->ia_bits`, for that reason.
- `kvm_init_stage2_mmu()` under pKVM: returns before it sets
  `mmu->last_vcpu_ran` and `mmu->pgd_phys`.
- pKVM variants ignore the `mm_ops` and walk-flag arguments.
- `struct kvm_pgtable_mm_ops` has no member named `fault_cache`.
- Callbacks the stage-2 code tests for NULL before calling:
  `dcache_clean_inval_poc` and `icache_inval_pou`; `kvm_pgtable_hyp_unmap()`
  tests `page_count`. The others are called unconditionally.
- `page_count`: the library reads a result of 1 as "this table holds no
  counted entry" (`stage2_unmap_walker()`, `stage2_free_table_post()`,
  `kvm_pgtable_stage2_free_unlinked()`), so nothing else may hold a
  reference on a table page.

**Stage-2 MMU structure**

- `kvm_vcpu_load_hw_mmu()` in `arch/arm64/kvm/nested.c`: picks
  `&kvm->arch.mmu` only when `is_hyp_ctxt()`; every other context gets a
  shadow from `get_s2_mmu_nested()`, also when the guest's `HCR_EL2.VM` is
  clear.
- Guest `HCR_EL2.VM` clear: `lookup_s2_mmu()` matches a shadow with
  `nested_stage2_enabled` false by VMID alone, and `kvm_handle_guest_abort()`
  skips `kvm_walk_nested_s2()` for it.
- `get_s2_mmu_nested()` runs under `write_lock(&kvm->mmu_lock)`.
- pKVM: `kvm_arch_vcpu_load()` jumps past the selection; EL2 sets its own
  `hw_mmu` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- There is no kvm_s2_mmu_nested and no nested_revmap in this tree.
- `split_page_cache` and `split_page_chunk_size`: read only on
  `kvm->arch.mmu`; on a shadow `kvm_init_stage2_mmu()` only initialises them.
- `shadow_pt_debugfs_dentry` (under `CONFIG_PTDUMP_STAGE2_DEBUGFS`): shadow
  only.

**Stage-2 teardown**

- `kvm_free_stage2_pgd()` on a shadow: calls `kvm_init_nested_s2_mmu()` while
  it still holds the write lock, whether or not `pgt` was set.
- `kvm_stage2_destroy()`: runs without `kvm->mmu_lock`; it calls
  `stage2_destroy_range()`, which calls
  `KVM_PGT_FN(kvm_pgtable_stage2_destroy_range)` one
  `kvm_granule_size(KVM_PGTABLE_MIN_BLOCK_LEVEL)` at a time with
  `cond_resched()` between, then
  `KVM_PGT_FN(kvm_pgtable_stage2_destroy_pgd)`.
- Host teardown does not call `kvm_pgtable_stage2_destroy()`; only
  `kvm_guest_destroy_stage2()` at EL2 does.
- `stage2_apply_range()` on `mmu->pgt == NULL`: returns `-EINVAL` on the first
  chunk, 0 once it has dropped the lock; `__unmap_stage2_range()` warns on
  non-zero.
- `kvm_mmu_split_huge_pages()`: re-reads `kvm->arch.mmu.pgt` after it retakes
  the lock and returns `-EINVAL` if it is NULL.
- Fault paths: `kvm_s2_fault_map()`, `gmem_abort()`, `pkvm_mem_abort()` and
  `handle_access_fault()` do not test `pgt` for NULL.
- Callers of `kvm_free_stage2_pgd()`: `kvm_uninit_stage2_mmu()`,
  `kvm_arch_flush_shadow_all()` (reached from `kvm_mmu_notifier_release()`),
  and the error path of `kvm_vcpu_init_nested()` on MMUs not yet published.

**Freeing table pages safely**

- References are on the page that holds the entry (`ctx->ptep`): one from
  `zalloc_page`, one per counted entry.
- `stage2_pte_is_counted()`: any non-zero entry, so annotations count.
- `stage2_free_walker()`: dispatches to `stage2_free_leaf()` and
  `stage2_free_table_post()`.
- `stage2_free_table_post()` on a table that still has counted entries
  (`page_count(childp) != 1`): returns 0 and frees nothing.
- `stage2_free_table_post()` on an empty table: puts both references, then
  clears the entry, so a later chunk of `stage2_destroy_range()` does not
  walk into the freed page.
- Replacing a valid entry: `stage2_try_break_pte()` drops the old entry's
  reference after the TLBI; `stage2_make_pte()` takes one for the new entry.
- `stage2_map_walk_table_pre()`: returns the error before
  `mm_ops->free_unlinked_table()` when the replace fails; this walker has
  then not unlinked the subtree.
- `level` passed to `mm_ops->free_unlinked_table()` and
  `kvm_pgtable_stage2_free_unlinked()`: the level of the entry that pointed
  at the table; the walk starts at `level + 1`.
- `kvm_pgtable_stage2_free_unlinked()`: warns if the root's `page_count()` is
  not 1 after the walk, and puts it anyway.
- **Potentially unsafe usage**: dropping the last reference on a table page
  with `mm_ops->put_page()` or `kvm_pgtable_stage2_free_unlinked()` from a
  visitor.
  - Unsafe: when the page was linked in a table that a walk flagged
    `KVM_PGTABLE_WALK_SHARED` can be in; that walker still reads the page
    inside the `rcu_read_lock()` taken by `kvm_pgtable_walk_begin()`.
  - Safe: `mm_ops->free_unlinked_table()` after the entry is replaced, as
    `stage2_map_walk_table_pre()` does; `stage2_free_unlinked_table()` defers
    the free with `call_rcu()`.
  - Safe: when the page was never linked, as `stage2_map_walk_leaf()` and
    `stage2_split_walker()` do after `stage2_try_break_pte()` fails.
  - Safe: in a walk without `KVM_PGTABLE_WALK_SHARED` under the write lock,
    as `stage2_unmap_walker()` does on the host; `__unmap_stage2_range()`
    asserts the write lock.

## Stage-2 faults

**Guest abort dispatch**

- Names: kvm_inject_dabt(), kvm_inject_pabt() and kvm_inject_vabt() are not in
  this tree. `kvm_inject_sea()` in `arch/arm64/kvm/inject_fault.c` takes an
  `iabt` flag; `kvm_inject_sea_dabt()` and `kvm_inject_sea_iabt()` are inline
  wrappers in `arch/arm64/include/asm/kvm_emulate.h`.
- Before the lookup, translation fault, two IPA ranges:
  - `fault_ipa >= BIT_ULL(get_kvm_ipa_limit())`: `kvm_inject_size_fault()`.
  - at or above the `VTCR_EL2_IPA()` size but below that limit:
    `kvm_inject_sea()`.
- `kvm_handle_guest_sea()`: returns 1 with nothing injected when
  `apei_claim_sea()` claims the abort; otherwise `kvm_inject_serror()`, or a
  `KVM_EXIT_ARM_SEA` exit when `KVM_ARCH_FLAG_EXIT_SEA` is set and
  `host_owns_sea()` is false.
- `kvm->srcu`: taken before the nested walk, not just around the memslot
  lookup.
- Nested walk: `-EAGAIN` from `kvm_walk_nested_s2()` returns 1 with no
  injection; any other failure of it or of `kvm_s2_handle_perm_fault()`
  injects with `kvm_inject_s2_fault()`.
- Missing syndrome: tested in `io_mem_abort()` in `arch/arm64/kvm/mmio.c`,
  after the lookup. It injects (`kvm_inject_sea_dabt()`) only for a protected
  VM; otherwise `KVM_EXIT_ARM_NISV` or `-ENOSYS`.
- Cache-maintenance skip (`kvm_incr_pc()`): only when `kvm_is_error_hva(hva)`.
  A CMO that hits the write-to-read-only-slot case goes on to
  `io_mem_abort()`.
- Final dispatch order: `kvm_vm_is_protected()` selects `pkvm_mem_abort()`
  first; only otherwise `kvm_slot_has_gmem()` chooses between `gmem_abort()`
  and `user_mem_abort()`.
- Exclusive/atomic FSC: `esr_fsc_is_excl_atomic_fault()` passes the
  "Unsupported FSC" filter. `kvm_inject_dabt_excl_atomic()` has one caller,
  `kvm_s2_fault_compute_prot()`, so it runs after the lookup and only on the
  `user_mem_abort()` path.

**Fault handler stages**

- `user_mem_abort()` in `arch/arm64/kvm/mmu.c` is a chain of four calls:

| Order | Function | `mmu_lock` | Continue when it returns |
|---|---|---|---|
| 1 | `topup_mmu_memcache()`, skipped on some permission faults | not held | 0 |
| 2 | `kvm_s2_fault_pin_pfn()` | not held | 1 |
| 3 | `kvm_s2_fault_compute_prot()` | not held | 0 |
| 4 | `kvm_s2_fault_map()` | takes and drops it | n/a |

- `kvm_s2_fault_pin_pfn()`: 0 means handled (hwpoison signal sent), not
  "continue"; `user_mem_abort()` returns any value other than 1 as is.
- `kvm_s2_fault_compute_prot()`: 1 means an exclusive/atomic abort was
  injected.
- `kvm_s2_fault_pin_pfn()` calls `kvm_s2_fault_get_vma_info()` (VMA lookup
  under `mmap_read_lock()`, size from `kvm_s2_resolve_vma_size()`), then
  `__kvm_faultin_pfn()`.
- `kvm_s2_fault_compute_prot()`, before the lock: holds the `-ENOEXEC` test,
  the exclusive/atomic injection, the `prot` computation including the
  nested adjustments, and the MTE `-EFAULT` refusal.
- `kvm_s2_fault_map()`, under the lock: `mmu_invalidate_retry()`,
  `transparent_hugepage_adjust()`, `sanitise_mte_tags()`, the map or
  relax-perms call, and the page release.
- State passing: there is no struct kvm_s2_fault.
  - `struct kvm_s2_fault_desc`: built once in `kvm_handle_guest_abort()`,
    passed `const` to `user_mem_abort()`, `gmem_abort()` and
    `pkvm_mem_abort()`.
  - `struct kvm_s2_fault_vma_info`: zero-initialised in `user_mem_abort()`,
    written only by stage 2, `const` in stages 3 and 4.
  - `prot`: out-parameter of stage 3, passed by value to stage 4.
- Names: `user_mem_abort()` has no logging_active and no `force_pte` local;
  when `memslot_is_logging()`, `kvm_s2_resolve_vma_size()` sets
  `s2vi->max_map_size` to `PAGE_SIZE`.
- `pkvm_mem_abort()` in `arch/arm64/kvm/mmu.c`: takes every fault that
  reaches the final dispatch of `kvm_handle_guest_abort()` for a
  `kvm_vm_is_protected()` VM, whatever the slot type.
  - It does not sample `mmu_invalidate_seq` or call `mmu_invalidate_retry()`.
  - It calls `pkvm_pgtable_stage2_map()` directly, always `PAGE_SIZE` and
    `KVM_PGTABLE_PROT_RWX`.
- Non-protected VM on a pKVM host: goes through `user_mem_abort()` or
  `gmem_abort()`; `KVM_PGT_FN()` selects the `pkvm_pgtable_stage2_map()`
  family.

**Inputs sampled outside the lock**

- `kvm_s2_fault_get_vma_info()`: samples `kvm->mmu_invalidate_seq` into
  `s2vi->mmu_seq`, last thing before `mmap_read_unlock()`.
- Sampled before the sequence read, under `mmap_read_lock()`: `vma_pagesize`,
  `max_map_size`, `gfn`, `mte_allowed`, `vm_flags`, `is_vma_cacheable`.
- Sampled after it, in `kvm_s2_fault_pin_pfn()`: `pfn`, `page`,
  `map_writable`, then `device` and `map_non_cacheable` derived from `pfn`,
  `vm_flags` and `is_vma_cacheable`.
- `vma`: local to `kvm_s2_fault_get_vma_info()`; nothing sets it to NULL, and
  later stages have no pointer to it.
- Barrier: the `user_mem_abort()` path has no explicit `smp_rmb()` after the
  read and relies on `mmap_read_unlock()`; `gmem_abort()` holds no mmap lock
  and has an explicit `smp_rmb()`.
- `mmu_invalidate_retry()`: checked in `kvm_s2_fault_map()`, first thing after
  `kvm_fault_lock()`.
- Not covered by the retry check: the error returns taken before the lock.
  `kvm_s2_fault_pin_pfn()` (`-EFAULT` for cacheable PFNMAP without
  `kvm_supports_cacheable_pfnmap()`) and `kvm_s2_fault_compute_prot()`
  (`-ENOEXEC`, `-EFAULT` for `!mte_allowed`) act on the sampled values
  unvalidated.

**Fault-path memory cache**

- `get_mmu_memcache()` and `topup_mmu_memcache()` are in
  `arch/arm64/kvm/mmu.c`; there is no prepare_mmu_memcache().
- `get_mmu_memcache()`: tests `is_protected_kvm_enabled()` only, so a
  non-protected VM on a pKVM host also gets `vcpu->arch.pkvm_memcache`.
- Top-up conditions differ per handler:

| Handler | Tops up when |
|---|---|
| `user_mem_abort()` | `!perm_fault`, or `memslot_is_logging()`, or `is_protected_kvm_enabled()` |
| `gmem_abort()` | `!perm_fault` only; otherwise `memcache` stays NULL |
| `pkvm_mem_abort()` | always; any failure is returned as `-ENOMEM` |

- `user_mem_abort()`: the dirty-logging term has no write-fault test.
- `topup_hyp_memcache()`: also allocates `mc->mapping`, a
  `struct pkvm_mapping`, if it is NULL.
- `pkvm_pgtable_stage2_map()` in `arch/arm64/kvm/pkvm.c`: takes
  `cache->mapping` with `swap()` and writes through it, so a map call under
  pKVM needs a top-up since the previous successful map.
- EL2 minimum: `__guest_check_pgtable_memcache()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` returns `-ENOMEM` when the vCPU's
  cache holds fewer than `kvm_mmu_cache_min_pages()` pages, even if the map
  would allocate nothing.
- `topup_hyp_memcache()` and `free_hyp_memcache()`: return at once when
  `!is_protected_kvm_enabled()`.
- Host-side `vcpu->arch.pkvm_memcache`: freed only in
  `kvm_arch_vcpu_destroy()`; `free_hyp_memcache()` also frees `mc->mapping`.
- Pages already moved to EL2: `__pkvm_finalize_teardown_vm()` pushes them to
  `kvm->arch.pkvm.stage2_teardown_mc`, which `__pkvm_destroy_hyp_vm()` frees
  with `free_hyp_memcache()`.

**Releasing the faulted-in page**

- Release helper per exit of the `user_mem_abort()` chain:

| Exit | Released by | Helper | Lock |
|---|---|---|---|
| `__kvm_faultin_pfn()` gave an error pfn | nobody | none | n/a |
| cacheable PFNMAP, no `kvm_supports_cacheable_pfnmap()` | `kvm_s2_fault_pin_pfn()` | `kvm_release_faultin_page()`, `unused` true | not held |
| `kvm_s2_fault_compute_prot()` returned nonzero | `user_mem_abort()` | `kvm_release_page_unused()` | not held |
| any exit of `kvm_s2_fault_map()` | `kvm_s2_fault_map()` | `kvm_release_faultin_page()`, `unused` = `!!ret` | held |

- `kvm_s2_fault_compute_prot()` nonzero covers `-ENOEXEC`, the MTE `-EFAULT`,
  and 1 after an exclusive/atomic injection.
- `kvm_s2_fault_map()` exits include the `mmu_invalidate_retry()` hit and a
  `transparent_hugepage_adjust()` error; `ret` is still `-EAGAIN` or the
  error there, so `unused` is true.
- `dirty` argument: `prot & KVM_PGTABLE_PROT_W`, the final permission, not
  `map_writable` from the faultin; same in `gmem_abort()`.
- `s2vi->page`: NULL when the pfn has no refcounted page; on NULL both
  helpers put nothing, but `kvm_release_faultin_page()` makes its lock
  assertion first.
- **Unsafe usage**: returning after `kvm_s2_fault_pin_pfn()` returned 1
  without releasing `s2vi.page`; the reference from `__kvm_faultin_pfn()`
  leaks.
  - Safe: `kvm_release_page_unused()` before the return, as
    `user_mem_abort()` does when `kvm_s2_fault_compute_prot()` returns
    nonzero.
  - Safe: returning the result of `kvm_s2_fault_map()`, as
    `user_mem_abort()` does; `kvm_s2_fault_map()` releases the page at its
    `out_unlock` label, which every path reaches.
  - Safe: returning with no release when `kvm_s2_fault_pin_pfn()` returned 0
    or an error, as `user_mem_abort()` does; `__kvm_faultin_pfn()` leaves the
    page NULL with an error pfn, and the `-EFAULT` exit after it has already
    released the page.
- **Unsafe usage**: releasing `s2vi->page` after `kvm_s2_fault_map()`
  returned; it has released the page on every path, so this is a second put.
  - Safe: return its result directly, as `user_mem_abort()` does.
- **Potentially unsafe usage**: calling `kvm_release_faultin_page()` without
  `mmu_lock` held.
  - Unsafe: with `unused` false; under `CONFIG_LOCKDEP` the
    `lockdep_assert_once()` in `kvm_release_faultin_page()` in
    `include/linux/kvm_host.h` fires.
  - Safe: with `unused` true, which that assertion exempts, as
    `kvm_s2_fault_pin_pfn()` does.
- `pkvm_mem_abort()`: does not call `__kvm_faultin_pfn()` or either release
  helper.
  - It calls `account_locked_vm()`, then `pin_user_pages()` with
    `FOLL_HWPOISON | FOLL_LONGTERM | FOLL_WRITE` under `mmap_read_lock()`.
  - Success: the pin and the locked-vm charge are kept;
    `__pkvm_pgtable_stage2_reclaim()` in `arch/arm64/kvm/pkvm.c` drops both
    with `unpin_user_pages_dirty_lock()` and `account_locked_vm()`.
  - Map failure, including `-EAGAIN` (returned as 0): `unpin_user_pages()`
    then `account_locked_vm(mm, 1, false)`.
  - Pin failure: only the charge is undone; `-EHWPOISON` sends the signal
    and returns 0.
  - Folio not `folio_test_swapbacked()`: `-EIO`, pin and charge undone.

**Memory tagging for guests**

- pKVM host: `kvm_pkvm_ext_allowed()` in
  `arch/arm64/include/asm/kvm_pkvm.h` returns false for `KVM_CAP_ARM_MTE`, so
  `kvm_vm_ioctl_enable_cap()` returns `-EINVAL` for every VM when
  `is_protected_kvm_enabled()`.
- guest_memfd, both directions:
  - enabling the cap returns `-EINVAL` if any existing memslot has
    `kvm_slot_has_gmem()`;
  - `kvm_arch_prepare_memory_region()` returns `-EINVAL` for a gmem slot once
    `kvm_has_mte()`.
- Locks for enabling: `kvm->lock`, then `kvm->slots_lock` for the memslot
  scan.
- AArch32: `kvm_vcpu_init_check_features()` in `arch/arm64/kvm/arm.c` returns
  `-EINVAL` for `KVM_ARM_VCPU_EL1_32BIT` when `kvm_has_mte()`; there is no
  vcpu_allowed_register_width().
- Fault path condition, same for the refusal and for the tag clearing: not a
  permission fault, `!s2vi->map_non_cacheable`, and `kvm_has_mte()`. The test
  is not on `s2vi->device`.
- Non-cacheable PFNMAP fault with MTE on: the MTE test is skipped, the fault
  is not refused by it.
- Refusal (`!s2vi->mte_allowed`, `-EFAULT`): in `kvm_s2_fault_compute_prot()`,
  before `mmu_lock`.
- `sanitise_mte_tags()`: called only from `kvm_s2_fault_map()`, under
  `mmu_lock`, on the mapping size after `transparent_hugepage_adjust()`.
- `sanitise_mte_tags()`: returns at once for `is_zero_pfn()`; does not call
  `mte_sync_tags()`.
- `gmem_abort()` and `pkvm_mem_abort()`: no tag check and no call to
  `sanitise_mte_tags()`; the exclusions above keep MTE VMs off both paths.

## Interrupt controller and timer

**VGIC lock order**

- Order in the comment, outermost first: `kvm->lock`, `vcpu->mutex`,
  `kvm->arch.config_lock`, `its->cmd_lock`, `its->its_lock`,
  `vgic_dist->lpi_xa.xa_lock`, `vgic_cpu->ap_list_lock`,
  `vgic_irq->irq_lock`.
- IRQs off: required for the last three locks; `kvm_vgic_early_init()` sets up
  `lpi_xa` with `XA_FLAGS_LOCK_IRQ`.
- **Potentially unsafe usage**: taking `ap_list_lock` or `irq_lock` with plain
  `raw_spin_lock()`.
  - Unsafe: with interrupts enabled; `kvm_arch_timer_handler()` reaches both
    locks through `kvm_vgic_inject_irq()` on the same CPU.
  - Safe: where interrupts are already off, as in `vgic_prune_ap_list()`:
    `kvm_arch_vcpu_ioctl_run()` calls `kvm_vgic_sync_hwstate()` before
    `local_irq_enable()`, and `kvm_vgic_process_async_update()` wraps the
    call in `local_irq_save()`.
  - Safe: nested inside an outer `raw_spin_lock_irqsave()`, as
    `vgic_queue_irq_unlock()` takes `irq_lock` inside `ap_list_lock`.
- `DEBUG_SPINLOCK_BUG_ON()`: empty without `CONFIG_DEBUG_SPINLOCK`.
- Second vCPU's `ap_list_lock`: taken with `raw_spin_lock_nested()` and
  `SINGLE_DEPTH_NESTING`; see `vgic_prune_ap_list()`.

**Interrupt references**

- `vgic_get_irq()`: takes `(kvm, intid)`, serves SPIs and LPIs only, and
  returns NULL for a GICv5 VM.
- Private interrupts: looked up with `vgic_get_vcpu_irq()`, which returns a
  pointer into `private_irqs` and takes no count.
- An LPI with count 0 can still be in `lpi_xa`; `vgic_try_get_irq_ref()` fails
  on it, so `vgic_get_lpi()` returns NULL.
- Freeing an LPI that was stored in `lpi_xa`, always with `kfree_rcu()`:
  - `vgic_release_lpi_locked()`, from the final `vgic_put_irq()`;
  - `vgic_release_lpi_locked()`, from `vgic_release_deleted_lpis()`;
  - `vgic_add_lpi()` in `arch/arm64/kvm/vgic/vgic-its.c`, when it replaces a
    dead entry for the same INTID.

**Dropping LPI references under locks**

- `vgic_put_irq()` on an LPI: the final put takes `lpi_xa.xa_lock` through
  `refcount_dec_and_lock_irqsave()`.
- `lpi_xa.xa_lock`: a `spinlock_t` that ranks above both raw locks.
- **Unsafe usage**: calling `vgic_put_irq()` on an interrupt that may be an
  LPI while holding an `ap_list_lock` or an `irq_lock`.
  - Safe: unlock first, then put, as `kvm_vgic_inject_irq()` does after
    `vgic_queue_irq_unlock()` has dropped every lock.
  - Safe: inside `arch/arm64/kvm/vgic/vgic.c`, call
    `vgic_put_irq_norelease()` under the lock, keep its result, and call
    `vgic_release_deleted_lpis()` after the last raw lock is dropped, as
    `vgic_prune_ap_list()` does.
- Holding a second reference: does not make the put acceptable; with
  `CONFIG_LOCKDEP`, `vgic_put_irq()` takes and drops `xa_lock` on every LPI
  put, before the decrement.
- Lockdep annotation: a real acquire through `guard(spinlock_irqsave)`,
  guarded by `IS_ENABLED(CONFIG_LOCKDEP)`; it does not call `might_lock()`.
- `vgic_put_irq()` on a non-LPI: returns before it touches `lpi_xa`.
- `vgic_put_irq_norelease()`: `__must_check`, wraps `__vgic_put_irq()`, returns
  true when the count reached 0.
- Dead LPI: stays in `lpi_xa` with count 0; no field marks it.
- `vgic_release_deleted_lpis()`: walks all of `lpi_xa` and releases every
  entry whose count is 0, not only the caller's.
- `vgic_put_irq_norelease()` and `vgic_release_deleted_lpis()`: `static` in
  `arch/arm64/kvm/vgic/vgic.c`; code in other files has only the unlock-first
  form.

**VGIC creation and initialisation**

- Stage flags: `in_kernel`, `initialized`, `ready` in `struct vgic_dist`; there
  is no vgic_ready() macro.
- `dist->ready`: read only by `kvm_vgic_map_resources()`; no configuration
  path tests it.
- `kvm_vgic_create()` errors, in the order tested:

  | Error | Case |
  |---|---|
  | `-ENODEV` | GICv2 asked for, `can_emulate_gicv2` false |
  | `-EBUSY` | `kvm_trylock_all_vcpus()` failed |
  | `-EBUSY` | `created_vcpus` differs from `online_vcpus` |
  | `-EEXIST` | irqchip already in kernel |
  | `-EBUSY` | a vCPU has run |
  | `-E2BIG` | more online vCPUs than the model's maximum |

- Private interrupts: allocated by `kvm_vgic_create()` for existing vCPUs and
  by `kvm_vgic_vcpu_init()` for later ones; `vgic_init()` does not allocate
  them.
- `vgic_init()` on GICv5: calls `vgic_v5_init()` and allocates no SPIs.
- Explicit init: required for GICv3 and GICv5; `vgic_lazy_init()`,
  `vgic_v3_map_resources()` and `vgic_v5_map_resources()` return `-EBUSY`
  without it.
- GICv2 lazy init runs from:
  - `vgic_lazy_init()`, on the `KVM_IRQ_LINE` path in `arch/arm64/kvm/arm.c`
    and in `arch/arm64/kvm/vgic/vgic-irqfd.c`;
  - `vgic_v2_attr_regs_access()`;
  - `vgic_v2_map_resources()`, on the first run.
- Base addresses: refused with `-EEXIST` by `vgic_check_iorange()` when
  already set; there is no test of `initialized` or `ready`.
- Redistributor regions: checked by `vgic_v3_alloc_redist_region()`, also
  with no stage test.
- Refused once `initialized`:
  - new vCPU: `-EBUSY` from `kvm_arch_vcpu_precreate()`;
  - `KVM_DEV_ARM_VGIC_GRP_MAINT_IRQ`: `-EBUSY`;
  - a changed `GICD_TYPER2`: `-EBUSY` in `vgic_mmio_uaccess_write_v3_misc()`.
- `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`: `-EBUSY` once `nr_spis` is non-zero, so a
  second write before init is refused too.
- `GICD_IIDR` revision write: no stage test.
- Refused before `initialized`, GICv3: register access returns `-EBUSY`,
  except what `reg_allowed_pre_init()` lets through.
- `kvm_vgic_inject_irq()` before `initialized`: returns 0 and injects nothing.
- `kvm_vgic_map_resources()` failure: calls `kvm_vm_dead()`; an unset address
  gives `-ENXIO`.

**Pending list and list registers**

- `vgic_queue_irq_unlock()`: calls `irq->ops->queue_irq_unlock` first when
  set, and returns its result.
- First SPI queued (`active_spis` goes from 0): every vCPU gets
  `KVM_REQ_IRQ_PENDING` when `vgic_model_needs_bcst_kick()` is true.
- `kvm_vgic_flush_hwstate()`: does not call `vgic_prune_ap_list()`.
- `vgic_prune_ap_list()`: runs from `kvm_vgic_sync_hwstate()` after the fold,
  and from `kvm_vgic_process_async_update()`.
- Overflow test: `summarize_ap_list()` fills `struct ap_list_summary`;
  `irqs_outside_lrs()` decides whether to sort. There is no
  compute_ap_list_depth() and no vgic_set_underflow().
- Sort order in `vgic_irq_cmp()`:
  1. deliverable to this vCPU;
  2. group enabled in the VMCR;
  3. pending and not active;
  4. lower priority value;
  5. `hw` set.
- Maintenance bits: set by `vgic_v3_configure_hcr()` or
  `vgic_v2_configure_hcr()` at the end of `vgic_flush_lr_state()`.
- `last_lr_irq` (per-CPU host data): the last interrupt put in an LR.
- `vgic_fold_state()`: returns at once when `last_lr_irq` is NULL.
- EOIcount: `__vgic_v3_save_state()` copies it into `vgic_hcr` only when
  `ICH_HCR_EL2_LRENPIE` was set.
- EOIcount fold: `vgic_v3_fold_lr_state()` walks the `ap_list` after
  `last_lr_irq` and deactivates one active interrupt per count.
- EOIcount fold of a `hw` interrupt: also deactivates the physical one with
  `vgic_v3_deactivate_phys()`.
- LPI: `vgic_v3_fold_lr()` always clears its active state; EOIcount is not
  bumped for an LPI outside the LRs.
- DIR write, EOImode 1: `access_gic_dir()` in `arch/arm64/kvm/sys_regs.c`
  calls `vgic_v3_deactivate()`; `vgic_mmio_write_dir()` calls it too, or
  `vgic_v2_deactivate()` on a GICv2 host.
- `vgic_v3_deactivate()` cases:

  | State of the interrupt | Action |
  |---|---|
  | on no `ap_list` | nothing |
  | `on_lr` set | `vgic_mmio_write_cactive()`, then `KVM_REQ_VGIC_PROCESS_UPDATE` |
  | on an `ap_list`, not in an LR | fold a pseudo-LR, then `KVM_REQ_VGIC_PROCESS_UPDATE` |

- DIR fast path: `___vgic_v3_write_dir()` in `arch/arm64/kvm/hyp/vgic-v3-sr.c`
  handles an interrupt found active in an LR without a full exit.
- GICv2 SGI with several sources: one source per LR; `vgic_v3_populate_lr()`
  sets `pending_latch` again while sources remain.

**Direct injection of LPIs**

- `kvm_vgic_v4_set_forwarding()` returns 0 without mapping when:
  - `vgic_supports_direct_msis()` is false;
  - `vgic_get_its()` returns an error pointer;
  - `vgic_its_resolve_lpi()` fails;
  - `irq->hw` is already set.
- Errors returned by set: from `its_map_vlpi()`, and from
  `irq_set_irqchip_state()` when the pending state is transferred.
- Set, locks: `its->its_lock`, then `irq_lock` with IRQs off.
- Set, state: `irq->hw`, `irq->host_irq`, and `vlpi_count` of the target
  `struct its_vpe`.
- Set takes no reference; the ITE's reference holds under `its_lock`.
- `kvm_vgic_v4_unset_forwarding()`: returns `void`, takes `(kvm, host_irq)`.
- Unset, checks: `vgic_supports_direct_msis()`, then
  `__vgic_host_irq_get_vlpi()`, which scans `lpi_xa` under RCU for `hw` set
  and a matching `host_irq`.
- Unset, locks: `irq_lock` with IRQs off; it does not take `its_lock`.
- Unset, state: under `irq_lock`, decrements `vlpi_count`, clears `irq->hw`,
  calls `its_unmap_vlpi()`; then drops the lookup reference with
  `vgic_put_irq()`.
- `kvm_arch_update_irqfd_routing()`: calls unset under `kvm->irqfds.lock`, a
  spinlock taken in `virt/kvm/eventfd.c`; unset must not sleep.

**GICv3 CPU interface traps**

- Global bits: computed by `kvm_compute_ich_hcr_trap_bits()` in
  `arch/arm64/kvm/vgic/vgic-v3.c`, an alternative callback that patches the
  constant in `vgic_ich_hcr_trap_bits()`.
- `vgic_v3_probe()`: only reads the result, through
  `vgic_v3_enable_cpuif_traps()`, to enable `vgic_v3_cpuif_trap`.
- Sources:

  | Source | Bits |
  |---|---|
  | `kvm-arm.vgic_v3_group0_trap` | `ICH_HCR_EL2_TALL0` |
  | `kvm-arm.vgic_v3_group1_trap` | `ICH_HCR_EL2_TALL1` |
  | `kvm-arm.vgic_v3_common_trap` | `ICH_HCR_EL2_TC` |
  | `ARM64_WORKAROUND_CAVIUM_30115` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1` |
  | `ARM64_WORKAROUND_GICv3_BROKEN_SEIS` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1`, `ICH_HCR_EL2_TDIR` |
  | no `ARM64_HAS_ICH_HCR_EL2_TDIR` | `ICH_HCR_EL2_TC` |

- `dir_trap`: has no command-line parameter.
- `vgic_hcr`: the value of `vgic_ich_hcr_trap_bits()` is never stored in it;
  `compute_ich_hcr()` ORs it in at each `__vgic_v3_restore_state()`.
- Other users of `vgic_ich_hcr_trap_bits()`: `__vgic_v3_activate_traps()` and
  `vgic_v3_flush_nested()`.
- `vcpu_set_ich_hcr()`: on a host where `vgic_host_has_gicv3()` is true, ORs
  `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1` and `ICH_HCR_EL2_TC` into
  `vgic_hcr` for a GICv2 model or no in-kernel irqchip; called from
  `kvm_calculate_traps()`.
- `vgic_v3_configure_hcr()`: assigns `vgic_hcr` from `ICH_HCR_EL2_En` on every
  flush, at the end of `vgic_flush_lr_state()`.
- `vgic_v3_configure_hcr()` with no in-kernel irqchip: returns before it
  touches `vgic_hcr`.
- `ICH_HCR_EL2_TDIR` per vCPU, set when any of:
  - the hardware lacks `ARM64_HAS_ICH_HCR_EL2_TDIR` (shadow bit only);
  - `irqs_active_outside_lrs()`;
  - `active_spis` of the VM is non-zero.
- `ICH_HCR_EL2_vSGIEOICount`: set when no SGI targets this vCPU on the
  `ap_list`, whether or not it got an LR.

**GICv3 CPU interface switch**

- `__vgic_v3_restore_state()`: writes `ICH_HCR_EL2` first, unconditionally,
  then the used LRs; it does not write the VMCR.
- `__vgic_v3_activate_traps()`: writes `ICH_HCR_EL2` earlier, with trap bits
  and `ICH_HCR_EL2_En` only, when `vgic_v3_cpuif_trap` is on,
  `its_vpe.its_vm` is set or `vgic_sre` is 0.
- VMCR, GICv3 guest: written at load by `__vgic_v3_restore_vmcr_aprs()`, only
  when `vgic_sre` is non-zero.
- VMCR, GICv2 guest: written by `__vgic_v3_activate_traps()` after it clears
  `ICC_SRE_EL1`, when `ICH_HCR_EL2_En` is set in `vgic_hcr`.
- VHE: `__vgic_v3_restore_state()` runs from `kvm_vgic_flush_hwstate()`; traps
  are activated at load.
- nVHE: `__hyp_vgic_restore_state()` in `arch/arm64/kvm/hyp/nvhe/switch.c`
  activates traps, then restores, on every entry.
- Saved on every exit by `__vgic_v3_save_state()`:

  | State | Condition |
  |---|---|
  | used LRs | `used_lrs` non-zero |
  | `ICH_VMCR_EL2` | always |
  | EOIcount | `ICH_HCR_EL2_LRENPIE` set in `vgic_hcr` |

- Saved only at put: the active priority registers, by
  `__vgic_v3_save_aprs()`; there is no __vgic_v3_save_vmcr_aprs().
- Protected mode: `vgic_v3_load()` and `vgic_v3_put()` skip the VMCR and APR
  calls; `kvm_arch_vcpu_load()` and `kvm_arch_vcpu_put()` make them.

**Timer contexts**

- `get_timer_map()`:

  | Case | direct | emulated |
  |---|---|---|
  | NV, `is_hyp_ctxt()` | hvtimer, hptimer | vtimer, ptimer |
  | NV, not `is_hyp_ctxt()` | vtimer, ptimer | hvtimer, hptimer |
  | VHE, no NV | vtimer, ptimer | none |
  | nVHE | vtimer | ptimer |

- `direct_ptimer`: NULL on nVHE; users that can run there test it, or pass it
  to a helper that accepts NULL, for example `kvm_timer_pending()` and
  `timer_get_offset()`.
- `vm_offset` in `timer_context_init()`: `voffset` for `TIMER_VTIMER`,
  `poffset` for the other three.
- `vm_offset` of a protected VM: NULL, which reads as offset 0.
- NV vtimer: `kvm_timer_vcpu_reset()` points `vm_offset` at `poffset` and
  `vcpu_offset` at the `CNTVOFF_EL2` slot.
- `kvm_vm_ioctl_set_counter_offset()`: holds `kvm->lock` and every vCPU mutex;
  it does not take `config_lock`.
- `-EBUSY` from it: only when `kvm_trylock_all_vcpus()` fails; there is no
  test that a vCPU has run.
- `-EINVAL` from it: protected VM, or `reserved` non-zero.
- Legacy counter write: `arch_timer_set_user()` in `arch/arm64/kvm/sys_regs.c`
  writes the VM-wide offset with `timer_set_offset()`, unless
  `KVM_ARCH_FLAG_VM_COUNTER_OFFSET` is set.
- `arch_timer_set_user()` and `kvm_timer_vcpu_init()`: take no VM-wide lock
  for the write.

## Protected mode

**pKVM objects**

- `struct pkvm_hyp_vm`: the vCPU array is `vcpus[]`, sized by
  `kvm.created_vcpus`; there is no separate count or refcount field.
- Hyp VM reference count: the `refcount` of the `struct hyp_page` backing the
  hyp VM, changed under `vm_table_lock` by `pkvm_load_hyp_vcpu()`,
  `pkvm_put_hyp_vcpu()`, `get_pkvm_hyp_vm()` and `put_pkvm_hyp_vm()`.
- `loaded_hyp_vcpu` in `struct pkvm_hyp_vcpu`: points at the per-CPU variable
  of the same name in `arch/arm64/kvm/hyp/nvhe/pkvm.c`; NULL when not loaded.
- How a hypercall names its object, for example:

| Hypercall | VM named by | vCPU named by |
|---|---|---|
| `__pkvm_init_vm` | host `struct kvm *`; EL2 reads `arch.pkvm.handle` from it | - |
| `__pkvm_init_vcpu` | handle | host `struct kvm_vcpu *` |
| `__pkvm_vcpu_load` | handle | `vcpu_idx` |
| `__kvm_vcpu_run` | - | host `struct kvm_vcpu *`, checked against the loaded hyp vCPU |
| `__pkvm_host_share_guest`, `__pkvm_host_donate_guest`, `__pkvm_host_relax_perms_guest`, `__pkvm_host_mkyoung_guest` | - | none; the hyp vCPU loaded on this CPU |
| `__pkvm_host_unshare_guest`, `__pkvm_host_wrprotect_guest`, `__pkvm_host_test_clear_young_guest`, `__pkvm_tlb_flush_vmid` | handle | - |

- `get_vm_by_handle()`: returns NULL for a handle that is reserved but whose
  hyp VM is not created (`RESERVED_ENTRY`), and asserts `vm_table_lock`.
- Handle 0 on the host means "no handle":
  `pkvm_pgtable_stage2_destroy_range()` and `__pkvm_destroy_hyp_vm()` test it.
- `get_np_pkvm_hyp_vm()`: returns NULL for a protected VM, so
  `__pkvm_host_unshare_guest`, `__pkvm_host_wrprotect_guest` and
  `__pkvm_host_test_clear_young_guest` fail with `-EINVAL` on one.
- `kvm_vm_is_protected()`: a macro in `arch/arm64/include/asm/kvm_host.h`,
  `is_protected_kvm_enabled() && (kvm)->arch.pkvm.is_protected`.
- At EL2 the hyp vCPU's `vcpu.kvm` points at the hyp VM's embedded
  `struct kvm`, so `vcpu_is_protected()` there reads the hypervisor's copy.

**Protected VMs and hypervisor vCPUs**

- `pkvm_init_host_vm()` in `arch/arm64/kvm/pkvm.c` sets
  `kvm->arch.pkvm.is_protected` from `KVM_VM_TYPE_ARM_PROTECTED`; it is the
  only host writer.
- `kvm_arch_init_vm()`: returns `-EINVAL` for `KVM_VM_TYPE_ARM_PROTECTED` when
  `is_protected_kvm_enabled()` is false.
- Creating a protected VM: `pkvm_init_host_vm()` warns once and calls
  `add_taint(TAINT_USER, LOCKDEP_STILL_OK)`.
- Hypervisor's copy of the flag: taken once by `init_pkvm_hyp_vm()`, called
  from `__pkvm_init_vm()`, which runs at the first `KVM_RUN` of the VM, not at
  `KVM_CREATE_VM`.
- Every VM gets a hyp VM and hyp vCPUs once pKVM is on, protected or not; the
  host's `struct kvm_vcpu` is never run directly.
- `init_pkvm_hyp_vcpu()` copies from the host vCPU: `vcpu_id`, `vcpu_idx`,
  `arch.cflags`; when the hyp VM has `KVM_ARM_VCPU_SVE`,
  `pkvm_vcpu_init_sve()` adds `sve_max_vl` and pins the host's `sve_state`.
- Non-protected hyp vCPU: timer offsets point into the pinned host
  `struct kvm` (`arch.timer_data`); a protected one gets none.
- `__pkvm_init_vcpu` on a protected VM fails with `-EINVAL` when
  `pkvm_check_pvm_cpu_features()` rejects the hyp VM's ID registers.
- `id_regs[]` of the hyp VM: set by `pkvm_vcpu_init_sysregs()`, not by
  `pkvm_init_features_from_host()`; see "Protected guest registers and traps".

**Hypervisor VM life cycle**

- There is no __pkvm_teardown_vm here; teardown is `__pkvm_start_teardown_vm`,
  then per-page reclaim, then `__pkvm_finalize_teardown_vm`.

| Step | Host function | Hypercall | Host locks taken |
|---|---|---|---|
| Reserve handle, at `KVM_CREATE_VM` | `pkvm_init_host_vm()` | `__pkvm_reserve_vm` | none |
| Create hyp VM, first `KVM_RUN` of any vCPU | `pkvm_create_hyp_vm()` | `__pkvm_init_vm` | `kvm->slots_lock`, then `kvm->arch.config_lock` |
| Create hyp vCPU, first `KVM_RUN` of that vCPU | `pkvm_create_hyp_vcpu()` | `__pkvm_init_vcpu` | `kvm->arch.config_lock` |
| Start teardown, first range of stage-2 free | `pkvm_pgtable_stage2_destroy_range()` | `__pkvm_start_teardown_vm` | none |
| Return guest pages | same | protected: `__pkvm_reclaim_dying_guest_page`; else `__pkvm_host_unshare_guest` | none |
| Finalize, hyp VM was created | `pkvm_destroy_hyp_vm()` | `__pkvm_finalize_teardown_vm` | `kvm->arch.config_lock` |
| Drop handle, hyp VM never created | `pkvm_destroy_hyp_vm()` | `__pkvm_unreserve_vm` | `kvm->arch.config_lock` |

- Both create steps are called from `kvm_arch_vcpu_run_pid_change()` with
  `vcpu->mutex` held by `KVM_RUN`; order is `vcpu->mutex` →
  `kvm->slots_lock` → `kvm->arch.config_lock`.
- `kvm->lock` is not held on any of these paths.
- `kvm->slots_lock` in `pkvm_create_hyp_vm()`: serialises `is_created` against
  `kvm_arch_prepare_memory_region()`.
- Start of teardown: reached from `kvm_arch_flush_shadow_all()` →
  `kvm_uninit_stage2_mmu()`, so it can run from `kvm_flush_shadow_all()` in
  `virt/kvm/kvm_main.c` before `kvm_arch_destroy_vm()`.
- `pkvm_destroy_hyp_vm()` issues finalize or unreserve, never both.
- `__pkvm_start_teardown_vm` and `__pkvm_finalize_teardown_vm`: `-EINVAL`
  while the hyp VM has a reference (a loaded vCPU counts); see
  `get_pkvm_unref_hyp_vm_locked()`.
- After `__pkvm_start_teardown_vm`: `pkvm_load_hyp_vcpu()` returns NULL for
  that VM.
- `__pkvm_init_vm` fails: EL2 returns the donated VM and PGD pages and unpins
  the host `struct kvm`; `__pkvm_create_hyp_vm()` frees both with
  `free_pages_exact()`; the handle stays reserved until
  `pkvm_destroy_hyp_vm()`.
- `__pkvm_init_vcpu` fails: EL2 unpins the host vCPU and returns the page;
  `__pkvm_create_hyp_vcpu()` frees it; the hyp VM and other hyp vCPUs stay.
- `kvm_arch_init_vm()`: nothing after `pkvm_init_host_vm()` can fail; a new
  failure point added after it has to unreserve the handle.
- Hyp VM size is fixed from `created_vcpus` at `__pkvm_init_vm`;
  `register_hyp_vcpu()` returns `-EINVAL` for a `vcpu_idx` at or beyond it.
- `__pkvm_create_hyp_vm()`: `-EINVAL` when `kvm->created_vcpus` is 0.

**Hypercalls before first run**

- `kvm_arch_vcpu_load()` issues `__pkvm_vcpu_load` on every load once pKVM is
  on; before creation `pkvm_load_hyp_vcpu()` finds nothing and
  `handle___pkvm_vcpu_load()` returns without an error.
- `pkvm_get_loaded_hyp_vcpu()`: NULL unless a `__pkvm_vcpu_load` succeeded on
  this CPU and no `__pkvm_vcpu_put` followed. A load cannot succeed before the
  hyp VM exists, or after another vCPU's first run created the hyp VM but
  before this vCPU's own `__pkvm_init_vcpu`.
- Handlers that use the loaded hyp vCPU and return `-EINVAL` on NULL:
  - `handle___pkvm_host_share_guest()`,
    `handle___pkvm_host_relax_perms_guest()` and
    `handle___pkvm_host_mkyoung_guest()`: also `-EINVAL` if the hyp vCPU is
    protected.
  - `handle___pkvm_host_donate_guest()`: also `-EINVAL` if the hyp vCPU is
    not protected.
  - `handle___pkvm_vcpu_in_poison_fault()`.
- `handle___pkvm_vcpu_put()` and `handle___pkvm_vcpu_sync_state()`: return
  silently on NULL.
- `pkvm_pgtable_stage2_mkyoung()` on the host wraps the hypercall in
  `WARN_ON()`, so a NULL loaded vCPU there produces a warning.
- **Unsafe usage**: an ioctl or capability that calls
  `pkvm_pgtable_stage2_map()`, `pkvm_pgtable_stage2_relax_perms()` or
  `pkvm_pgtable_stage2_mkyoung()` for a vCPU that has not been through
  `kvm_arch_vcpu_run_pid_change()`.
  - Unsafe: no hyp vCPU is loaded on this CPU, so each hypercall returns
    `-EINVAL` and nothing is mapped.
  - Safe: the stage-2 fault path (`user_mem_abort()`, `gmem_abort()`,
    `pkvm_mem_abort()` in `arch/arm64/kvm/mmu.c`), which runs inside
    `kvm_arch_vcpu_ioctl_run()` after `pkvm_create_hyp_vm()`,
    `pkvm_create_hyp_vcpu()` and then `vcpu_load()`.
  - Safe: `pkvm_pgtable_stage2_unmap()`, `pkvm_pgtable_stage2_wrprotect()`
    and `pkvm_pgtable_stage2_test_clear_young()` before first run; their
    hypercalls name the VM by handle and need no loaded hyp vCPU, and before
    the hyp VM exists `pgt->pkvm_mappings` is empty, so they issue no
    hypercall.
- Order matters: a `vcpu_load()` done before creation is not repaired by
  creation; only `handle___pkvm_vcpu_load()` sets the loaded hyp vCPU.
- `__guest_check_pgtable_memcache()`: share and donate return `-ENOMEM`
  unless the hyp vCPU's memcache holds `kvm_mmu_cache_min_pages()` pages,
  even when the map allocates nothing.
- Creating the hyp VM early fixes what `__pkvm_init_vm` copies, for example
  the vCPU count, `vcpu_features` and, for a non-protected VM, `arch.flags`;
  `vm_copy_id_regs()` returns `-EINVAL` unless the host has
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED`.

**Flushing and syncing vCPU state**

- Register context (`arch.ctxt`):

| Guest | `flush_hyp_vcpu()` | `sync_hyp_vcpu()` |
|---|---|---|
| Protected | whole `arch.ctxt`, host to hyp, every run | whole `arch.ctxt`, hyp to host, every run |
| Non-protected | `__copy_vcpu_state()` only if `PKVM_HOST_STATE_DIRTY` | only `regs.pc` and `regs.pstate` |

- `__copy_vcpu_state()`: copies `regs`, the four `spsr_` fields, `fp_regs`
  and `sys_regs[]`, but skips `CNTVOFF_EL2`, `CNTV_CVAL_EL0`, `CNTV_CTL_EL0`,
  `CNTP_CVAL_EL0` and `CNTP_CTL_EL0`.
- Copied host to hyp on every run for both kinds: `arch.mdcr_el2` (whole),
  `arch.iflags`, `arch.vsesr_el2`, `arch.pid`, debug state
  (`flush_debug_state()`), and from the vGIC `vgic_hcr`, `used_lrs` (clamped
  to `hyp_gicv3_nr_lr`) and that many `vgic_lr[]`.
- Copied hyp to host on every run for both kinds: `arch.fault`,
  `arch.iflags`, debug state, `vgic_hcr`, `vgic_vmcr`, used `vgic_lr[]`.
- `fpsimd_sve_flush()` copies nothing; it marks FP state as host-owned.
- Full sync request: `handle_exit_pkvm_state()` in
  `arch/arm64/kvm/handle_exit.c` issues `__pkvm_vcpu_sync_state` for a
  non-protected VM when the exit is `ARM_EXCEPTION_TRAP`,
  `ARM_EXCEPTION_EL1_SERROR` or has `ARM_SERROR_PENDING()`.
- `handle_exit_pkvm_state()` runs first in `handle_exit_early()`, with
  preemption off, before any exit handler reads guest registers.
- `handle___pkvm_vcpu_sync_state()`: does nothing for a protected vCPU or
  when no hyp vCPU is loaded.
- `handle___pkvm_vcpu_put()`: also does the full sync for a non-protected
  vCPU, unless `PKVM_HOST_STATE_DIRTY` is set.
- After an exit that is not a trap or SError (for example
  `ARM_EXCEPTION_IRQ`), the host's `arch.ctxt` of a non-protected vCPU is
  stale except for `pc` and `pstate`.

**Host changes to vCPU state**

- The mark is `PKVM_HOST_STATE_DIRTY`, a bit of `arch.iflags`, defined in
  `arch/arm64/include/asm/kvm_host.h`; it is used for non-protected VMs only.
- Set by the host in three places: `kvm_arch_vcpu_run_pid_change()` (first
  run), `kvm_arch_vcpu_put()` after `__pkvm_vcpu_put`, and
  `handle_exit_pkvm_state()` after `__pkvm_vcpu_sync_state`.
- Cleared only by `handle_exit_pkvm_state()`, on an exit that needs no sync.
- `flush_hyp_vcpu()` on finding the mark: copies host to hyp with
  `__copy_vcpu_state()`; it does not clear the mark.
- With the mark clear, `flush_hyp_vcpu()` copies no `arch.ctxt`, and
  `handle___pkvm_vcpu_put()` overwrites the host's `arch.ctxt` from the
  hypervisor's.
- Protected vCPU: the mark is ignored; `flush_hyp_vcpu()` copies the host's
  whole `arch.ctxt` on every run.
- **Unsafe usage**: writing `arch.ctxt` of a non-protected vCPU while it is
  loaded and `PKVM_HOST_STATE_DIRTY` is clear, as after an
  `ARM_EXCEPTION_IRQ` exit.
  - Unsafe: the write never reaches the hyp vCPU and is overwritten at the
    next `__pkvm_vcpu_sync_state` or `__pkvm_vcpu_put`.
  - Safe: in a handler called from `handle_exit()` for
    `ARM_EXCEPTION_TRAP`; `handle_exit_pkvm_state()` has synced and set the
    mark. `handle_hvc()` writing results through `kvm_smccc_call_handler()`
    is one.
  - Safe: while the vCPU is not loaded; `kvm_arch_vcpu_put()` set the mark.
    `kvm_handle_mmio_return()` runs before `vcpu_load()` in
    `kvm_arch_vcpu_ioctl_run()`.
  - Safe: before the first run; `kvm_arch_vcpu_run_pid_change()` sets the
    mark.
  - Safe: state that `flush_hyp_vcpu()` copies on every run whatever the
    mark: `arch.iflags`, `HCR_VSE` with `arch.vsesr_el2`, vGIC list
    registers, `arch.mdcr_el2`, debug state.
- Timer registers skipped by `__copy_vcpu_state()` never travel through
  flush or sync for a non-protected vCPU.

**Restrictions on protected VMs**

- `kvm_pkvm_ext_allowed()` has three outcomes, not two:

| Capability | Result |
|---|---|
| In the explicit list at the top of the switch | allowed for every VM |
| `KVM_CAP_ARM_MTE`, `KVM_CAP_ARM_EAGER_SPLIT_CHUNK_SIZE`, `KVM_CAP_ARM_SUPPORTED_BLOCK_SIZES` | refused for every VM |
| Anything else | allowed only if the VM is not protected, or `kvm` is NULL |

- `KVM_CAP_ARM_PMU_V3` and `KVM_CAP_ARM_SVE` are not in the explicit list, so
  both are refused for a protected VM.
- Host callers test `is_protected_kvm_enabled()` first:
  `kvm_vm_ioctl_check_extension()`, `kvm_vm_ioctl_enable_cap()`, and
  `kvm_arch_vm_ioctl()` through `kvm_pkvm_ioctl_allowed()`.
- `kvm_pkvm_ioctl_allowed()`: maps the ioctl to a capability with
  `vm_ioctl_caps[]` in `arch/arm64/kvm/arm.c` and passes it to
  `kvm_pkvm_ext_allowed()`; an ioctl missing from that table gets `-EINVAL`
  from `kvm_arch_vm_ioctl()` for every VM once pKVM is on.
- vCPU features are decided at EL2 by `pkvm_init_features_from_host()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`, during `__pkvm_init_vm`.
- `pkvm_init_features_from_host()` for a protected VM: allows
  `KVM_ARM_VCPU_PSCI_0_2` always, and `KVM_ARM_VCPU_PMU_V3`,
  `KVM_ARM_VCPU_PTRAUTH_ADDRESS`, `KVM_ARM_VCPU_PTRAUTH_GENERIC`,
  `KVM_ARM_VCPU_SVE` only if `kvm_pkvm_ext_allowed()` allows the matching
  capability; the result is ANDed with the host's `vcpu_features`.
- `pkvm_init_features_from_host()` for a non-protected VM: copies the host's
  `vcpu_features` unchanged.
- `KVM_ARM_VCPU_INIT` with a feature refused for a protected VM: no error on
  that account; `kvm_vcpu_init_check_features()` has no protected-VM test and
  does not call `kvm_pkvm_ext_allowed()`.
- The refused feature stays set in the host's `kvm->arch.vcpu_features` and
  is absent from the hyp VM's, from the first `KVM_RUN` on.
- `kvm_vcpu_init_check_features()` errors are unrelated to pKVM, for example
  `-ENOENT` for an unknown bit, `-EINVAL` for a feature the system lacks.

**Memslot and backing memory limits**

- Refused by `kvm_arch_prepare_memory_region()` for a protected VM, all with
  `-EPERM`:

| What | When |
|---|---|
| `KVM_MR_DELETE`, `KVM_MR_MOVE` | only once `pkvm_hyp_vm_is_created()` |
| `new->flags` with `KVM_MEM_LOG_DIRTY_PAGES` or `KVM_MEM_READONLY` | always, including `KVM_MR_FLAGS_ONLY` |

- `KVM_MR_FLAGS_ONLY` and `KVM_MR_CREATE` without those flags are not refused
  by this test for a protected VM, before or after creation.
- `kvm_arch_prepare_memory_region()` does not refuse dirty logging or
  read-only slots for a non-protected VM under pKVM.
- `kvm_arch_prepare_memory_region()` has no pKVM test in its VMA loop and
  none on `guest_memfd` slots; a `VM_PFNMAP` slot is not refused on account
  of pKVM at this point.
- Refused for a protected VM at fault time, in `pkvm_mem_abort()`:
  - backing whose folio is not swap-backed (page cache of a regular file):
    `-EIO`; anonymous and shmem memory pass.
  - backing that `pin_user_pages()` cannot pin with `FOLL_LONGTERM |
    FOLL_WRITE`: `-EFAULT`.
  - a page beyond the memlock limit: error from `account_locked_vm()`.
- Protected VM mappings: `PAGE_SIZE` and `KVM_PGTABLE_PROT_RWX` only;
  `pkvm_pgtable_stage2_map()` returns `-EINVAL` otherwise.
- Protected VM pages stay pinned until `__pkvm_pgtable_stage2_reclaim()` at
  teardown; `kvm_unmap_gfn_range()`, `kvm_age_gfn()`, `kvm_test_age_gfn()`
  and `kvm_stage2_unmap_range()` do nothing for one.
- Refused for every VM once pKVM is on:
  - `kvm_phys_addr_ioremap()`: `-EPERM`.
  - device or non-cacheable mappings: `__pkvm_host_share_guest()` returns
    `-EINVAL` for any `prot` bit outside `KVM_PGTABLE_PROT_RWX`.
  - physical ranges that are not memory or are `MEMBLOCK_NOMAP`: `-EPERM`
    from `check_range_allowed_memory()`.
  - block mappings other than `PMD_SIZE`: see
    `fault_supports_stage2_huge_mapping()` and
    `__guest_check_transition_size()`.
  - `KVM_CAP_ARM_MTE` and eager page splitting: see "Restrictions on
    protected VMs"; `pkvm_pgtable_stage2_split()` warns and returns
    `-EINVAL`.

**Protected guest registers and traps**

- There is no fixed_config.h, PVM_ID_AA64 allow macro, pvm_read_id_reg() or
  get_pvm_id_ helper here; the limits are `struct pvm_ftr_bits` tables such
  as `pvmid_aa64pfr0[]` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`.
- `pvm_calc_id_reg()`: applies a table to the hypervisor's copy of the host's
  sanitised value; `SYS_ID_AA64ISAR0_EL1` passes through unmasked,
  `SYS_ID_AA64DFR0_EL1` and `SYS_ID_AA64MMFR4_EL1` are fixed constants, any
  register without a case reads 0.
- `kvm_init_pvm_id_regs()`: fills only the AArch64 ID range, once per VM,
  under `vm_table_lock` (asserted).
- A table entry with `vm_supported` set depends on the hyp VM's
  `vcpu_features`, which `pkvm_init_features_from_host()` has already
  filtered.
- `init_pkvm_hyp_vcpu()` sets ID registers before traps, because
  `pvm_init_traps_hcr()` and `pvm_init_traps_mdcr()` read them with
  `kvm_has_feat()`.
- Where each trap register of a hyp vCPU comes from:

| Register | Protected | Non-protected |
|---|---|---|
| `arch.hcr_el2` | `pkvm_vcpu_reset_hcr()` then `pvm_init_traps_hcr()` | `pkvm_vcpu_reset_hcr()` |
| `HCR_TWI`, `HCR_TWE`, `HCR_VSE` | host, every run | host, every run |
| `arch.hcrx_el2` | `vcpu_set_hcrx()` at EL2 | host's value at `__pkvm_init_vcpu` |
| `arch.mdcr_el2` | `pvm_init_traps_mdcr()`, then replaced by the host's in `flush_hyp_vcpu()` on every run | host's, every run |
| `arch.fgt` | never written at EL2 | host's, copied by `handle___pkvm_vcpu_load()` |
| CPTR | `__activate_cptr_traps()` at each entry | same |

- There is no CPTR setup in `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- `kvm_handle_pvm_sys64()` in `arch/arm64/kvm/hyp/nvhe/switch.c` tries
  `kvm_hyp_handle_sysreg()` first, then `kvm_handle_pvm_sysreg()`.
- `pvm_sys_reg_descs[]` outcomes: not listed, undefined exception injected;
  `HOST_HANDLED()` (`access` NULL), exit to the host; otherwise handled at
  EL2.

**Page ownership**

- Where each state lives:

| Component | Storage | Lock |
|---|---|---|
| Host | `__host_state` in `struct hyp_page` (`hyp_vmemmap`) | `host_mmu.lock` |
| Hypervisor | `__hyp_state_comp` in `struct hyp_page`, stored complemented | `pkvm_pgd_lock` |
| Guest | software bits of the guest stage-2 PTE | `lock` of `struct pkvm_hyp_vm` |

- Neither the host stage-2 PTE nor the hyp stage-1 PTE holds the state at run
  time; `fix_host_ownership_walker()` in `arch/arm64/kvm/hyp/nvhe/setup.c`
  reads the hyp stage-1 software bits once at init to fill `hyp_vmemmap`.
- `enum pkvm_page_state` has five values; besides the three stored ones there
  are `PKVM_NOPAGE` and `PKVM_POISON`.
- Guest `PKVM_NOPAGE` and `PKVM_POISON` are not stored in software bits;
  `guest_get_page_state()` infers them from an invalid PTE and from
  `KVM_GUEST_INVALID_PTE_TYPE_POISONED`.
- Host `PKVM_NOPAGE` is stored in `__host_state`.
- Lock order: `host_mmu.lock` first, then `pkvm_pgd_lock` or the guest
  `lock`; `vm_table_lock` is taken before `host_mmu.lock` where both are held
  (`__pkvm_host_force_reclaim_page_guest()`, `__pkvm_init_vcpu()`).
- `__host_check_page_state_range()`: asserts `host_mmu.lock` and fails with
  `-EPERM` for a range that is not memory or is `MEMBLOCK_NOMAP`.
- The assertions are real only with `CONFIG_NVHE_EL2_DEBUG`; see
  `hyp_assert_lock_held()`.
- Page donated to a protected guest: host state `PKVM_NOPAGE`, guest PTE
  `PKVM_PAGE_OWNED`, and the host stage-2 holds an invalid PTE of type
  `KVM_HOST_INVALID_PTE_TYPE_DONATION` with owner `PKVM_ID_GUEST` plus the VM
  handle and gfn; see `host_stage2_encode_gfn_meta()`.
- Shares with a non-protected guest are counted per page in
  `host_share_guest_count` of `struct hyp_page`, not in `refcount`.
- `refcount` of `struct hyp_page` counts, for example, hyp pins
  (`hyp_pin_shared_mem()`) and hyp VM references.
- `__pkvm_host_share_guest()`: a block share increments the count of every
  page in the block; `-EBUSY` at `U32_MAX`; `-EPERM` for a page that is
  `PKVM_PAGE_SHARED_OWNED` with a zero count (shared with the hypervisor or
  FF-A).
- `__pkvm_host_unshare_guest()`: the host state returns to `PKVM_PAGE_OWNED`
  only when the count reaches zero.

## Nested virtualisation

**Guest hypervisor state**

- `is_hyp_ctxt()` in `arch/arm64/include/asm/kvm_emulate.h`: returns
  `vcpu_is_el2(vcpu) || (e2h && tge) || tge`, so virtual `HCR_EL2.TGE` alone
  makes a non-EL2 mode a hypervisor context; E2H is not required.
- `kvm_inject_nested()` and `kvm_hyp_handle_eret()`: treat `PSR_MODE_EL0t`
  as host EL0 only when `vcpu_el2_e2h_is_set()` and `vcpu_el2_tge_is_set()`
  both hold.
- `HCR_EL2`: not VNCR-backed in this tree. It is a plain `enum vcpu_sysreg`
  entry between `__SANITISED_REG_START__` and `__VNCR_START__`, stored in
  `sys_regs[]`.
- `NVHCR_EL2`: the `VNCR()` entry at page offset 0x078 (`VNCR_NVHCR_EL2` in
  `arch/arm64/include/asm/vncr_mapping.h`). There is no VNCR_HCR_EL2.
- `__compute_hcr()` in `arch/arm64/kvm/hyp/vhe/switch.c`, in hyp context:
  copies `HCR_EL2` into `NVHCR_EL2` before entry.
- `fixup_nv_guest_exit()`: copies `NVHCR_EL2` back into `HCR_EL2` on every
  exit taken with `VCPU_IN_HYP_CONTEXT` set, so `is_hyp_ctxt()` reads KVM's
  copy as of the last exit.
- With `ARM64_HAS_NV3` and `vcpu_el2_e2h_is_set()`: both copies use the
  hardware register `SYS_NVHCR_EL2` instead of the page slot.
- `SCTLR_EL2`, `TCR_EL2`, `TTBR0_EL2`, `TTBR1_EL2`, `VBAR_EL2`, `ESR_EL2`,
  `FAR_EL2`, `ELR_EL2`, `SPSR_EL2`: plain `sys_regs[]` entries, not
  VNCR-backed. `locate_register()` in `arch/arm64/kvm/sys_regs.c` maps them
  to the hardware EL1 register while in hyp context with `SYSREGS_ON_CPU`
  set.
- `vncr_array`: a `u64 *` field of `struct kvm_cpu_context`, one page from
  `kvm_vcpu_init_nested()`. There is no struct of that name.
- `VCPU_IN_HYP_CONTEXT`: per-CPU host data flag, set or cleared by
  `__compute_hcr()` on each entry of an NV vCPU. It is not per-vCPU state.
- `fixup_nv_guest_exit()`: uses the flag to turn EL1t/EL1h in the saved
  PSTATE back into EL2t/EL2h, then `BUG_ON()`s if the flag and
  `is_hyp_ctxt()` disagree.
- `__compute_hcr()` in hyp context: sets `HCR_NV | HCR_NV2 | HCR_AT |
  HCR_TTLB`; `HCR_NV1` only when `vcpu_el2_e2h_is_set()` is false.
- Names absent from this tree: vcpu_mode_el2, get_el2_to_el1_mapping,
  __vcpu_put_sysregs, __vcpu_load_sysregs, compute_hcr. The jobs are done by
  `vcpu_is_el2()`, `locate_register()`, `__vcpu_put_switch_sysregs()`,
  `__vcpu_load_switch_sysregs()` and `__compute_hcr()`.
- `kvm_inject_el2_exception()`: only calls `kvm_pend_exception()` and, for
  sync and SError, writes `ESR_EL2`. `enter_exception64()` in
  `arch/arm64/kvm/hyp/exception.c`, reached from `__kvm_adjust_pc()`, writes
  `ELR_EL2`, `SPSR_EL2`, PC and PSTATE.
- `kvm_inject_nested()` from vEL2, or from EL0 with E2H and TGE: pends the
  exception and returns, with no put/load; the state changes at the next
  `__kvm_adjust_pc()`.
- `kvm_inject_nested()` from any other mode: `__kvm_adjust_pc()`,
  `kvm_arch_vcpu_put()`, pend, `__kvm_adjust_pc()` again,
  `kvm_arch_vcpu_load()`, all with preemption disabled.
- `kvm_emulate_nested_eret()`: does `kvm_arch_vcpu_put()` and
  `kvm_arch_vcpu_load()` itself, even for a return that stays at vEL2. The
  exception is a failed ERETAx with FPACCOMBINE and no illegal return: it
  injects with `kvm_inject_nested_sync()` and returns first.
- `kvm_hyp_handle_eret()` declines, leaving the slow path, when:
  - `ARM64_HAS_NV3` and `vcpu_el2_e2h_is_set()`
  - `is_nested_ctxt()`
  - the target mode is not EL2t, EL2h, or EL0t with E2H and TGE
  - ERETAx fails `kvm_auth_eretax()` or the vCPU lacks ptrauth

**Shadow stage-2 MMUs**

- `kvm->arch.nested_mmus`: an array of pointers (`struct kvm_s2_mmu **`),
  allocated once by `kvm_init_nested()` for `KVM_MAX_VCPUS *
  S2_MMU_PER_VCPU` entries, for every VM. It is never reallocated.
- `kvm_vcpu_init_nested()`: allocates one chunk of `S2_MMU_PER_VCPU`
  structs, initialises them, then publishes the pointers and raises
  `nested_mmus_size` under the `mmu_lock` write lock.
- A `struct kvm_s2_mmu` never moves once published; there is no fix-up of
  back pointers.
- Invalid marker: `VTTBR_CNP_BIT` set in `tlb_vttbr`, tested by
  `kvm_s2_mmu_valid()`. `kvm_init_nested_s2_mmu()` sets it, called from
  `kvm_init_stage2_mmu()` and from `kvm_free_stage2_pgd()`.
- `lookup_s2_mmu()` with guest stage 2 enabled: needs full VTTBR (CnP
  masked) and VTCR equal, on an entry that is also enabled.
- `lookup_s2_mmu()` with guest stage 2 disabled: needs only the VMID equal,
  on an entry that is also disabled.
- Recycling in `get_s2_mmu_nested()`: round-robin from `nested_mmus_next`,
  first entry with `refcnt == 0`, valid or not; `BUG_ON()` if none.
- `kvm_vcpu_put_hw_mmu()`: keeps the reference and `vcpu->arch.hw_mmu` when
  `vcpu->scheduled_out` is set and `IN_WFI` is clear.
- `kvm_vcpu_load_hw_mmu()`: does no lookup when `hw_mmu` is already set.
- `refcnt` therefore counts vCPUs whose `hw_mmu` points at the MMU,
  including preempted ones.
- `pending_unmap`: set only in `get_s2_mmu_nested()`, when the recycled
  entry was valid. No notifier path sets or reads it.
- Recycling does not unmap: the entry gets its new `tlb_vttbr`, `tlb_vtcr`
  and `nested_stage2_enabled` at once, with the old mappings still present.
- `check_nested_vcpu_requests()`, on `KVM_REQ_NESTED_S2_UNMAP` with
  `pending_unmap` set: unmaps the full range of `vcpu->arch.hw_mmu` with
  `may_block` true before guest entry, and clears `pending_unmap`.
- `kvm_nested_s2_unmap()`: passes its `may_block` argument straight to
  `kvm_stage2_unmap_range()` for each valid MMU; it defers nothing.
- `kvm_nested_s2_unmap()` and `kvm_nested_s2_wp()`: also call
  `kvm_invalidate_vncr_ipa_all()`. `kvm_nested_s2_flush()` does not.
- All three return at once when `nested_mmus_size` is 0, so the first two
  then skip that call.
- `kvm_age_gfn()` and `kvm_test_age_gfn()` in `arch/arm64/kvm/mmu.c`: act
  on `kvm->arch.mmu` only; shadow MMUs are not aged.
- `kvm_arch_flush_shadow_all()`: calls `kvm_free_stage2_pgd()` on each
  shadow, skipping with `WARN_ON()` any with non-zero `refcnt`, then
  `kvm_uninit_stage2_mmu()`. It does not free the structs or the array.
- `kvm_destroy_nested()`, from `kvm_arch_destroy_vm()`: frees the chunks
  and the pointer array.

**Trap forwarding tables**

- Names absent from this tree: sr_forward_xarray, forward_traps,
  kvm_check_forward_trap, check_cgt, BEHAVE_FORWARD_ANY. The tree has
  `sr_forward_xa`, `__forward_traps()`, `compute_trap_behaviour()` and
  `BEHAVE_FORWARD_RW`.
- `struct trap_bits`: holds `index`, `behaviour`, `value`, `mask` only.
  Complex conditions are callbacks in `ccc[]`.
- `union trap_config`: `sri` is the index into `sys_reg_descs[]` or
  `sys_insn_descs[]` plus one; `fgf` is the fine-grained filter. `line` is
  a field of `struct encoding_to_trap_config`.
- `encoding_to_cgt[]`, `encoding_to_fgt[]`, `non_0x18_fgt[]`: `__initconst`;
  after init only `sr_forward_xa` holds the encoding data.
- `kvm_sys_reg_table_init()`: called from `kvm_arm_init()` on every host;
  an error return makes KVM fail to initialise.
- Init checks by outcome:

| Check | Where | Outcome |
|---|---|---|
| MBZ bit, duplicate CGT, invalid or duplicate FGT | `populate_nv_trap_config()` | `-EINVAL` |
| FGT bit is generated RES0/RES1 in the read register and, if the group has one, in the write register | `aggregate_fgt()` | `-EINVAL` |
| FGT bit has both polarities | `check_fgt_masks()` | `-EINVAL` |
| recursive combination | `populate_nv_trap_config()` | `-EINVAL` |
| descriptor index too large or duplicate | `populate_sysreg_config()` | `-EINVAL` |
| masks do not cover all 64 bits | `check_fgt_masks()` | `kvm_info()`, `res0` recomputed |
| feature map does not cover the register | `check_feature_map()` | `kvm_err()` only |

- `populate_nv_trap_config()`: stores `encoding_to_fgt[]` entries in the
  xarray only when the host has `ARM64_HAS_FGT`; `aggregate_fgt()` runs
  either way.
- `check_fgt_bit()`: does not test the VM's FEAT_FGT or any enable bit in
  `HCR_EL2` or `HCRX_EL2`. It reads the guest register through
  `__vcpu_sys_reg()`, and for negative polarity also requires the bit not
  to be RES0.
- `HCRX_FGTnXS`: the only filter; it drops the FGT check when the guest
  set `HCRX_EL2_FGTnXS`.
- Missing entry, by kind:

| What is missing | Result |
|---|---|
| encoding not in `sr_forward_xa` at all | UNDEF, or FEAT_IDST handling in the feature ID space; message unless IMPDEF range |
| descriptor exists, no CGT or FGT entry | KVM handles it; the guest hypervisor's trap is ignored, no warning |
| CGT or FGT entry, no descriptor (`tc.sri == 0`) | forwarded if the guest traps it, else as in the first row |
| FGT register bit in neither `encoding_to_fgt[]` nor `non_0x18_fgt[]` | `check_fgt_masks()` makes it RES0; `get_reg_fixed_bits()` then makes it RES0 in the guest's register |

- Traps with an EC other than `ESR_ELx_EC_SYS64` do not use the tables, for
  example:
  - `forward_smc_trap()` and `forward_debug_exception()` in
    `arch/arm64/kvm/emulate-nested.c`: forward when `is_nested_ctxt()` and
    the bit is set in `HCR_EL2` or `MDCR_EL2`.
  - `handle_hvc()`: for any NV vCPU, in either context, forwards, or
    injects UNDEF if `HCR_HCD` is set.
  - `handle_svc()`: forwards unconditionally.
  - `kvm_handle_eret()`: forwards whenever `is_hyp_ctxt()` is false, except
    an ERETAx on a vCPU without ptrauth, which goes to
    `kvm_handle_ptrauth()` and gets UNDEF.
  - FP, SVE and WFx: helpers in `arch/arm64/include/asm/kvm_emulate.h`.

**Sanitising virtual EL2 registers**

- Sanitised range: every `enum vcpu_sysreg` entry from
  `__SANITISED_REG_START__` to `NR_SYS_REGS`. It is not only VNCR-backed
  registers.
- Non-VNCR entries in the range: `SCTLR_EL2`, `TCR2_EL2`, `SCTLR2_EL2`,
  `MDCR_EL2`, `CNTHCTL_EL2`, `ZCR_EL2`, `HCR_EL2`.
- `TCR_EL2`, `CPTR_EL2`, `SPSR_EL2`: before the marker, never masked.
- Non-zero masks exist only for registers with a `set_sysreg_masks()` call
  in `kvm_init_nv_sysregs()`; every other register in range passes
  unchanged, for example `TCR2_EL1`.
- `NVHCR_EL2`: gets a zero mask unless `kvm_has_nv3()`.
- `ICH_HFGRTR_EL2`, `ICH_HFGWTR_EL2`, `ICH_HFGITR_EL2`: have feature maps
  in `arch/arm64/kvm/config.c` but no `set_sysreg_masks()` call.
- `__vcpu_sys_reg()`: applies the masks on read.
- `__vcpu_assign_sys_reg()` and `__vcpu_rmw_sys_reg()`: apply them on
  write.
- All three test `vcpu_has_nv()` and `r >= __SANITISED_REG_START__` first.
- `vcpu_read_sys_reg()` and `vcpu_write_sys_reg()`: also mask the value
  read from or written to the CPU register when `locate_register()`
  reports `SR_LOC_LOADED`.
- `ctxt_sys_reg()` and `__ctxt_sys_reg()`: raw, no masks.
- Stored values are not guaranteed sanitised: the guest hypervisor writes
  the VNCR page directly, and hyp save code stores through
  `ctxt_sys_reg()`. A read through `__vcpu_sys_reg()` is masked whatever
  was stored.
- `struct kvm_sysreg_masks`: an array `mask[]` of `struct resx`, indexed by
  `sr - __SANITISED_REG_START__`.
- `kvm->arch.sysreg_masks`: NULL until the first `kvm_init_nv_sysregs()`
  call, and always NULL for a VM without NV; `__kvm_get_sysreg_resx()` then
  returns zero masks.
- `get_reg_fixed_bits()`: returns `struct resx` by value;
  `set_sysreg_masks()` takes one.
- `kvm_get_sysreg_resx()`: the lookup. `kvm_get_sysreg_res0()` is a static
  wrapper in `arch/arm64/kvm/emulate-nested.c`.

## Model gaps

### Other mistakes models make

- Models take GICv5 support to be absent, or limited to GICv3 guests on a
  GICv5 host. `vgic_is_v5()`, a macro in `include/kvm/arm_vgic.h`, is tested
  outside the vgic too, for example in `arch/arm64/kvm/arch_timer.c` and in
  `__hyp_vgic_restore_state()` in `arch/arm64/kvm/hyp/nvhe/switch.c`.
- Models take `vcpu_el2_e2h_is_set()` to read only the guest's `HCR_EL2`. It
  is always true without `ARM64_HAS_HCR_NV1`; see
  `arch/arm64/include/asm/kvm_emulate.h`.
- Models take an injected external abort to be always pended as a synchronous
  exception. `inject_abt64()` in `arch/arm64/kvm/inject_fault.c` calls
  `pend_serror_exception()` instead of `pend_sync_exception()` when
  `effective_sctlr2_ease()` is true.
- Models take GICv4 direct injection to be used whenever the host has it, and
  GICv2 emulation to be offered whenever the hardware allows. `vgic_v3_probe()`
  sets `has_gicv4` from `kvm-arm.vgic_v4_enable`, which defaults to off. It
  does not register the GICv2 device when the mode is `KVM_MODE_PROTECTED`.
- Models take the host never to take back a guest page by force.
  `is_spurious_el1_translation_fault()` in `arch/arm64/mm/fault.c` calls
  `pkvm_force_reclaim_guest_page()`.
- Models take a CFI failure at EL2 to go unreported. The host reports it in
  `kvm_nvhe_report_cfi_failure()` in `arch/arm64/kvm/handle_exit.c`, called
  from `nvhe_hyp_panic_handler()` under `CONFIG_CFI`.
- Models take the nVHE hypervisor to have no tracing. The host side is
  `arch/arm64/kvm/hyp_trace.c`, built under `CONFIG_NVHE_EL2_TRACING`.
  `__tracing_load` and the other tracing hypercalls sit in the range that is
  always available.
- Models take guest debug state to be chosen through a debug pointer in the
  vCPU. `kvm_vcpu_load_debug()` sets `vcpu->arch.debug_owner` at load, and
  pKVM copies debug state by that owner in `flush_debug_state()` and
  `sync_debug_state()`.
- Models take `KVM_ARM_VCPU_PMU_V3` to be the only PMU feature bit.
  `KVM_ARM_VCPU_PMU_V3_STRICT` is bit 9 and `KVM_VCPU_MAX_FEATURES` is 10.
  With it set, `kvm_setup_vcpu()` creates no default PMU.
- Models take host exit handling to cover only aborts from lower exception
  levels. `arm_exit_handlers[]` routes `ESR_ELx_EC_DABT_CUR` to
  `kvm_handle_vncr_abort()`, for faults on a guest hypervisor's VNCR page.
