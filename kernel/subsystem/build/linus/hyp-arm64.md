# ARM64 Hyp (EL2) Subsystem Details

## Main structures

### Objects and how they relate

- Protected mode only: `pkvm_pgtable`, `host_mmu`, `hyp_vmemmap`, `vm_table`,
  `hpool` and `host_s2_pool` are set up from `__pkvm_init()`, which
  `arch/arm64/kvm/arm.c` calls only under `is_protected_kvm_enabled()`.
  Without it the hyp stage-1 is the host-owned `hyp_pgtable` in
  `arch/arm64/kvm/mmu.c`, and `handle___kvm_vcpu_run()` runs the host's
  `struct kvm_vcpu` directly.
- `struct pkvm_hyp_vm` / `struct pkvm_hyp_vcpu`: with pKVM enabled every VM,
  protected or not, gets its `struct pkvm_hyp_vm` at its first vCPU run, and
  each vCPU its `struct pkvm_hyp_vcpu` at that vCPU's own first run;
  `handle___kvm_vcpu_run()` returns `-EINVAL` unless the loaded hyp vCPU
  matches the host vCPU passed in.
- Protected VM memory is donated (`__pkvm_host_donate_guest()`, host loses
  access); non-protected VM memory is shared (`__pkvm_host_share_guest()`,
  host keeps access). Each hypercall handler rejects the other kind of VM.
- `struct hyp_page` records a state, not the other party. For a page whose
  host state is `PKVM_NOPAGE`, hyp text excepted, the owner is in the host
  stage-2 invalid PTE: type `KVM_HOST_INVALID_PTE_TYPE_DONATION`, an
  `enum pkvm_component_id`, and for a guest its handle and gfn; see
  `host_stage2_set_owner_metadata_locked()`.
- Host state `PKVM_PAGE_SHARED_OWNED` has three meanings: shared with hyp
  (hyp state is `PKVM_PAGE_SHARED_BORROWED`), shared with non-protected
  guests (`host_share_guest_count` is non-zero), or shared over FF-A
  (`__pkvm_host_share_ffa()`, no counterpart recorded).
- Host-side `struct kvm_pgtable` of a guest under pKVM is not a page table:
  its page-table fields share a union with `pkvm_mappings`, and only
  `pkvm_mappings` (interval tree of `struct pkvm_mapping`) and `mmu` are
  set. `KVM_PGT_FN()` in `arch/arm64/kvm/mmu.c` routes stage-2 calls to the
  `pkvm_pgtable_stage2_map()` family in `arch/arm64/kvm/pkvm.c`.
- `struct kvm_nvhe_init_params` stays live after init: `__deactivate_traps()`
  in `arch/arm64/kvm/hyp/nvhe/switch.c` reloads `hcr_el2` from it each time
  `__kvm_vcpu_run()` returns to the host,
  `arch/arm64/kvm/hyp/nvhe/psci-relay.c` passes it to CPU_ON and suspend
  entry, and `__pkvm_prot_finalize()` writes `vttbr`, `vtcr` and `hcr_el2`
  into it.
- `struct kvm_cpu_context`: a third per-CPU instance, `kvm_hyp_ctxt`, exists
  beside the host one in `struct kvm_host_data` and the one in each vCPU.
- Lock order: `vm_table_lock`, then `host_mmu.lock`, then `pkvm_pgd_lock` or
  the VM `lock`; `enum pkvm_component_id` lists host, hyp, guest in that
  order.
- EL2 tracing: `struct hyp_trace_buffer` in `arch/arm64/kvm/hyp/nvhe/trace.c`,
  built under `CONFIG_NVHE_EL2_TRACING`, loaded from a host-supplied
  `struct hyp_trace_desc` by `__tracing_load()`.
- There is no `struct` named kvm_hyp_req, kvm_iommu or hyp_arm_smmu, and no
  IOMMU code under `arch/arm64/kvm/`.
- There is no __kvm_call_hyp(); the host issues hypercalls with
  `kvm_call_hyp_nvhe()` in `arch/arm64/include/asm/kvm_host.h`.
- There is no pkvm_handle_psci(); `kvm_host_psci_handler()` serves host
  SMCs, and protected-guest HVCs go to `kvm_handle_pvm_hvc64()`, which
  returns anything it does not list to the host.

## Where to look

**Core files**

| Job | File in this tree |
|---|---|
| EL2 page allocator | `arch/arm64/kvm/hyp/nvhe/page_alloc.c`; `arch/arm64/kvm/hyp/nvhe/early_alloc.c` serves `__pkvm_init()` until `__pkvm_init_finalise()` calls `hyp_pool_init()` |
| EL2 vectors | `arch/arm64/kvm/hyp/hyp-entry.S` (`__kvm_hyp_vector`, guest running, both builds); `arch/arm64/kvm/hyp/nvhe/host.S` (`__kvm_hyp_host_vector`, host running); `arch/arm64/kvm/hyp/nvhe/hyp-init.S` (`__kvm_hyp_init`, before init) |
| Code shared with the VHE build | the `../` entries of `obj-y` in `arch/arm64/kvm/hyp/vhe/Makefile`, plus headers in `arch/arm64/kvm/hyp/include/hyp/`; the list includes `vgic-v2-cpuif-proxy.c` and `vgic-v5-sr.c` |
| Not shared, same name in `nvhe/` and `vhe/` | `switch.c`, `sysreg-sr.c`, `timer-sr.c`, `debug-sr.c`, `tlb.c`; there is no top-level `sysreg-sr.c`, `timer-sr.c`, `debug-sr.c` or fpsimd.S under `arch/arm64/kvm/hyp/` |
| Page-table walker | `arch/arm64/kvm/hyp/pgtable.c`: built into the nVHE object and, by `arch/arm64/kvm/hyp/Makefile`, as a plain kernel object; `arch/arm64/kvm/hyp/vhe/Makefile` does not build it |
| All other jobs asked | Models have these right: `hyp-main.c`, `mem_protect.c`, `pkvm.c`, `mm.c`, `setup.c`, `ffa.c`, `psci-relay.c`, `sys_regs.c`, `switch.c` in `arch/arm64/kvm/hyp/nvhe/`; host glue `arch/arm64/kvm/pkvm.c` |

**Entry points**

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

**The nVHE object**

- Section prefix: added by the partial link `ld -r -T hyp.lds` that makes
  `kvm_nvhe.tmp.o`; `cmd_hypcopy` only passes `--prefix-symbols=__kvm_nvhe_`.
- `arch/arm64/kvm/hyp/nvhe/hyp.lds.S`: prefixes only the input sections it
  lists; any other section, for example `__kvm_ex_table`, keeps its name.
- Section not listed in `hyp.lds.S`: `emit_rela_section()` in
  `arch/arm64/kvm/hyp/nvhe/gen-hyprel.c` skips it, so its pointers get no
  EL2 fix-up.
- `__ro_after_init` data in nVHE code: `HYPERVISOR_RODATA_SECTIONS` in
  `arch/arm64/kernel/vmlinux.lds.S` places it in `.hyp.rodata`, which is
  mapped `PAGE_HYP_RO` at EL2.
- Kernel symbol used at EL2: the only mechanism is `KVM_NVHE_ALIAS()` in
  `arch/arm64/kernel/image-vars.h`; there is no hyp-image.S or kvm_nvhe.h.
- Kernel code used at EL2: compiled a second time into the object, as
  `lib-objs` and `../../../kernel/smccc-call.o` in
  `arch/arm64/kvm/hyp/nvhe/Makefile`; `KVM_NVHE_ALIAS_HYP()` lines in
  `image-vars.h` alias plain names such as `memcpy` to the `__pi_` names.
- `KVM_NVHE_ALIAS()` only makes the link succeed; EL2 can dereference the
  symbol only if its page is in the EL2 stage-1, which `init_hyp_mode()` in
  `arch/arm64/kvm/arm.c` builds and, under pKVM, `recreate_hyp_mappings()`
  in `arch/arm64/kvm/hyp/nvhe/setup.c` rebuilds from its own list.
- `host_hcall[]` order: free, `HANDLE_FUNC()` is a designated initialiser.
- `kvm_call_hyp()` and `kvm_call_hyp_ret()`: call `f` directly when
  `has_vhe()`, so `f` needs a VHE definition too; an nVHE-only function
  must be called with `kvm_call_hyp_nvhe()`.
- Relocation source: the static RELA entries of `kvm_nvhe.tmp.o`; the object
  is not linked as PIE.
- hyp_symbol_addr is not in this tree; EL2 code takes the address of a
  symbol directly.
- `gen-hyprel`: emits a fix-up for `R_AARCH64_ABS64` only; an unlisted
  relocation type in a `.hyp` section or any `SHT_REL` section fails the
  build.
- `kvm_apply_hyp_relocations()`: `__init`, called once from
  `hyp_mode_check()` in `arch/arm64/kernel/smp.c`, after
  `kvm_compute_layout()`, only when `!is_kernel_in_hyp_mode()`.
- Every listed slot is rewritten whatever it points to, so a statically
  initialised pointer in hyp data holds a hyp VA afterwards, also when the
  host reads it.

**Debug options and tests**

| Job | Option in this tree | Kconfig |
|---|---|---|
| EL2 assertions, selftest | `CONFIG_NVHE_EL2_DEBUG` | prompt, default n |
| Relax host stage-2 on panic | `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC` | prompt, default n, inside `if NVHE_EL2_DEBUG` |
| pKVM stack traces | `CONFIG_PKVM_STACKTRACE` | default y, depends on `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC` |
| EL2 tracing | `CONFIG_NVHE_EL2_TRACING` | no prompt, default y inside `if NVHE_EL2_DEBUG`, depends on `TRACING && FTRACE` |

- CONFIG_PROTECTED_NVHE_STACKTRACE, CONFIG_PKVM_SELFTESTS and
  CONFIG_PKVM_TRACING are not in this tree.
- BUG file and line, and `%pB` symbol names: printed when
  `nvhe_hyp_panic_host_s2_disabled()` in `arch/arm64/kvm/handle_exit.c` is
  true, which under pKVM needs `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`.
- Checks that exist only under `CONFIG_NVHE_EL2_DEBUG`: two,
  `hyp_assert_lock_held()` in `arch/arm64/kvm/hyp/include/nvhe/spinlock.h`
  and `assert_host_shared_guest()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `assert_host_shared_guest()` callers: `__pkvm_host_relax_perms_guest()`,
  `__pkvm_host_wrprotect_guest()`, `__pkvm_host_test_clear_young_guest()`,
  `__pkvm_host_mkyoung_guest()`; in a normal build these do not check that
  the range is shared by the host.
- Other page-state checks and the `WARN_ON()` calls in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` outside
  `assert_host_shared_guest()` and the selftest: built in all
  configurations.
- `pkvm_ownership_selftest()`: no option of its own and no hypercall; it is
  the last step of `__pkvm_init_finalise()` in
  `arch/arm64/kvm/hyp/nvhe/setup.c`, reached only if every earlier step
  returned 0.
- Selftest timing: inside the `__pkvm_init` hypercall issued by
  `do_pkvm_init()` in `arch/arm64/kvm/arm.c`, before `finalize_pkvm()`.
- `pkvm_selftest_pages()` in `arch/arm64/include/asm/kvm_pkvm.h`: 32 under
  `CONFIG_NVHE_EL2_DEBUG`, else 0; `kvm_hyp_reserve()` adds it to the
  reserved hyp memory and `divide_memory_pool()` carves it out.
- Tracing hypercalls: in `host_hcall[]` in every configuration; without
  `CONFIG_NVHE_EL2_TRACING` the functions they call, for example
  `__tracing_load()`, are stubs in
  `arch/arm64/kvm/hyp/include/nvhe/trace.h`, most returning `-ENODEV`.
- Host side of tracing: `arch/arm64/kvm/hyp_trace.c`, registered by
  `kvm_hyp_trace_init()`.

## KVM modes and pKVM init

**KVM modes on arm64**

- `enum kvm_mode` in `arch/arm64/include/asm/kvm_host.h`: four values,
  `KVM_MODE_DEFAULT`, `KVM_MODE_PROTECTED`, `KVM_MODE_NV`, `KVM_MODE_NONE`.
- VHE, nVHE and hVHE: not values of `enum kvm_mode`; `has_vhe()` and
  `has_hvhe()` tell them apart.
- `has_vhe()` in hyp objects: a compile-time constant, true in VHE hyp code and
  false in nVHE hyp code; it reads the cap only in kernel-proper code.
- `has_vhe()` false in nVHE hyp code although that code runs at EL2:
  `has_vhe()` tells whether the kernel runs at EL2, not whether the calling
  code does.
- Hyp code that needs to know it is at EL2: `is_hyp_code()`,
  `is_nvhe_hyp_code()`, `is_vhe_hyp_code()` in
  `arch/arm64/include/asm/cpufeature.h`, all compile-time.
- `is_kernel_in_hyp_mode()`: kernel-proper only; it has a `BUILD_BUG_ON()` that
  fails the build in a hyp object.
- `is_protected_kvm_enabled()` and `has_hvhe()` in VHE hyp code: constant
  false.
- All three predicates outside hyp objects: go through `cpus_have_final_cap()`,
  which calls `BUG()` before `setup_system_features()` has run; earlier code
  uses `kvm_get_mode()` and `is_kernel_in_hyp_mode()`.

**Mode selection at boot**

- Aliases for `kvm-arm.mode`: in `aliases[]` in
  `arch/arm64/kernel/pi/idreg-override.c`; there is no
  arch/arm64/kernel/idreg-override.c.
- `kvm_arm.mode=protected` alias: expands to `arm64_sw.hvhe=1`.
- hVHE: `early_kvm_mode_cfg()` has no value for it; `arm64_sw.hvhe=1` selects
  it, given directly or through the `protected` alias.
- `hvhe_filter()`: accepts `arm64_sw.hvhe=1` only when the CPU booted at EL2 and
  has VHE.
- `__finalise_el2` in `arch/arm64/kernel/hyp-stub.S`: with the hvhe override
  set it refuses the upgrade to VHE, so the kernel stays at EL1 and
  `early_kvm_mode_cfg()` then accepts `protected` on a VHE-capable CPU.
- `is_kvm_protected_mode()` in `arch/arm64/kernel/cpufeature.c`: tests only
  `kvm_get_mode() == KVM_MODE_PROTECTED`; the exception-level test that the
  cap relies on is in `early_kvm_mode_cfg()`.
- Requests `early_kvm_mode_cfg()` refuses, in the order it tests them; every
  refusal leaves `kvm_mode` unchanged, none resets it to `KVM_MODE_DEFAULT`:

| Request | Condition | Result |
|---|---|---|
| NULL | always | `-EINVAL` |
| any but `none` | `!is_hyp_mode_available()` | `pr_warn_once()`, returns 0 |
| `protected` | `is_kernel_in_hyp_mode()` | `pr_warn_once()`, returns 0 |
| `nvhe` | `is_kernel_in_hyp_mode()` | `WARN_ON()`, `-EINVAL` |
| `nested` | `!is_kernel_in_hyp_mode()` | `WARN_ON()`, `-EINVAL` |
| unknown | none of the rows above matched | `-EINVAL` |

- `protected`: after `is_hyp_mode_available()`, `is_kernel_in_hyp_mode()` is
  its only test; there is no CPU feature test, no override test and no
  configuration test.

**Init state predicates**

| Predicate | Kind | Becomes true |
|---|---|---|
| `is_protected_kvm_enabled()` | cap `ARM64_KVM_PROTECTED_MODE` | in `setup_system_features()`, from `smp_cpus_done()` |
| `is_kvm_arm_initialised()` | plain `static bool kvm_arm_initialised` | last statement before `return 0` of a successful `kvm_arm_init()` |
| `kvm_protected_mode_initialized` | static key | in `pkvm_drop_host_privileges()`, before the per-CPU calls |
| `is_pkvm_initialized()` | `IS_ENABLED(CONFIG_KVM)` and the key | with the key; it tests nothing else |

- `kvm_arm_initialised`: not a static key; `is_kvm_arm_initialised()` is an
  out-of-line function in `arch/arm64/kvm/arm.c`.
- Key true: finalisation has started, not that every CPU has stage 2 on.
- At EL2: code tests the key directly; `KVM_NVHE_ALIAS()` in
  `arch/arm64/kernel/image-vars.h` gives the nVHE object the host's key.
- EL2 users of the key: `handle_host_hcall()`, `__load_host_stage2()` and,
  only with `CONFIG_NVHE_EL2_DEBUG`, `hyp_assert_lock_held()`.
- `is_pkvm_initialized()` and `is_kvm_arm_initialised()`: not used under
  `arch/arm64/kvm/hyp/`; `is_protected_kvm_enabled()` is.
- Between `__pkvm_init()` and the key flip: the key is false but the host no
  longer owns the hyp stage 1; `kvm_host_owns_hyp_mappings()` in
  `arch/arm64/kvm/mmu.c` detects it with
  `!hyp_pgtable && is_protected_kvm_enabled()`.
- Failed `kvm_arm_init()` in protected mode: `is_protected_kvm_enabled()` stays
  true, `is_kvm_arm_initialised()` stays false, and `finalize_pkvm()` returns 0
  without flipping the key.
- **Potentially unsafe usage**: issuing a hypercall numbered at or above
  `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` guarded only by
  `is_protected_kvm_enabled()`.
  - Unsafe: in code that can run while the key is off, that is before
    `pkvm_drop_host_privileges()` or after `kvm_arm_init()` failed; where EL2
    is installed `handle_host_hcall()` returns `SMCCC_RET_NOT_SUPPORTED`, and
    `kvm_call_hyp_nvhe()` warns and yields `-EOPNOTSUPP`.
  - Safe: in code reached only through a VM, as `kvm_arch_init_vm()` calling
    `pkvm_init_host_vm()`; `kvm_init()` runs at device_initcall and the key is
    flipped at device_initcall_sync.
  - Safe: testing the key first, as `is_spurious_el1_translation_fault()` in
    `arch/arm64/mm/fault.c` does: it calls `pkvm_force_reclaim_guest_page()`
    only after `is_pkvm_stage2_abort()` tested `is_pkvm_initialized()`.

**Init sequence**

- `kvm_hyp_reserve()`: called from `bootmem_init()` in `arch/arm64/mm/init.c`,
  not from `arm64_memblock_init()`; `setup_arch()` has already run
  `parse_early_param()`, so `kvm_get_mode()` is valid.
- `kvm_hyp_reserve()` and `divide_memory_pool()`: the first sums six page-count
  helpers, the second carves the same six at EL2; a new pool user must be added
  to both.
- `kvm_arm_init()`: `module_init()`; `CONFIG_KVM` is bool on arm64, so it is
  always a device_initcall.
- `finalize_pkvm()`: `device_initcall_sync()`, not a late initcall.
- `init_hyp_mode()` in protected mode: before `kvm_hyp_init_protection()` it
  also runs `init_pkvm_host_sve_state()` and
  `pkvm_check_sme_dvmsync_fw_call()`; each can fail the init, the latter with
  `-ENODEV` when the CPU has `ARM64_WORKAROUND_4193714` and firmware lacks
  the call.
- `init_hyp_mode()` in protected mode: installs EL2 only on the calling CPU,
  in `do_pkvm_init()` through `cpu_hyp_init_context()`.
- Other CPUs: get EL2 in `init_subsystems()` through `cpu_hyp_init()`, after
  `__pkvm_init()`; they enter with the `pgd_pa` that `update_nvhe_init_params()`
  rewrote.
- Stub hypercalls in protected mode: `__host_hvc` in
  `arch/arm64/kvm/hyp/nvhe/host.S` does not divert them, so
  `handle_host_hcall()` refuses them once `__kvm_hyp_host_vector` is installed
  on a CPU; until finalisation the host keeps unrestricted memory access and
  the init-only hypercalls.
- Hyp vmemmap: backed by `hyp_back_vmemmap()` in `recreate_hyp_mappings()`,
  inside `__pkvm_init()` and before the page-table switch.
- `__pkvm_init_finalise()`: starts with `hyp_pool_init()`; it also calls
  `pkvm_check_host_ownership()` and `pkvm_ownership_selftest()`, the latter an
  empty stub without `CONFIG_NVHE_EL2_DEBUG`.
- `finalize_init_hyp_mode()`: runs after `kvm_init()` has succeeded,
  immediately before `kvm_arm_initialised = true`.

**De-privilege point**

- `pkvm_drop_host_privileges()`: enables `kvm_protected_mode_initialized`
  first, then runs `on_each_cpu()`; the key is not enabled afterwards by
  `finalize_pkvm()`.
- Repeat guard in `__pkvm_prot_finalize()`: `params->hcr_el2 & HCR_VM` already
  set in this CPU's `kvm_init_params` returns `-EPERM`; there is no finalized
  flag and no `-EBUSY`.
- `handle_host_hcall()`: cannot block a repeat by id, since
  `__pkvm_prot_finalize` is the first id it still accepts with the key on.
- `__pkvm_prot_finalize()`: besides `HCR_VM` it sets `HCR_FWB` in
  `params->hcr_el2` when the CPU has `ARM64_HAS_STAGE2_FWB`.
- `kvm_init_params` after finalisation: `psci_cpu_on()`, `psci_cpu_suspend()`
  and `psci_system_suspend()` in `arch/arm64/kvm/hyp/nvhe/psci-relay.c` pass it
  to `___kvm_hyp_init`, which reloads HCR_EL2, VTTBR_EL2 and VTCR_EL2 from it.
- `__pkvm_prot_finalize()`: acts on the calling CPU only; it changes that
  CPU's `kvm_init_params` and loads HCR_EL2 and the host stage 2 there.
- Host callers of `__pkvm_prot_finalize`: one, `_kvm_host_prot_finalize()`,
  which is `__init`; `on_each_cpu()` reaches only CPUs online at that time.
- `psci_cpu_on()`: refuses a CPU that `find_cpu_id()` does not find in
  `hyp_cpu_logical_map`, which `init_cpu_logical_map()` fills from the CPUs
  online during `kvm_arm_init()`.

## The EL2 environment

**Execution context and concurrency**

- `handle_trap()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`: has no SVE or FP
  case; an `ESR_ELx_EC_SYS64` trap goes to `handle_host_mte()`, which injects
  an UNDEF into the host or returns false, and `handle_trap()` then falls
  through to `BUG()`.
- SError: unmasked for one `isb` in `__guest_exit`
  (`arch/arm64/kvm/hyp/entry.S`), only without `ARM64_HAS_RAS_EXTN` and when
  ISR_EL1.A is set.
- That window is inside the `handle_trap()` call chain: `handle_host_hcall()`
  -> `handle___kvm_vcpu_run()` -> `__kvm_vcpu_run()` -> `__guest_enter`, with
  the guest vector installed.
- IRQ and FIQ masking is relied on by `__vgic_v3_get_gic_config()` in
  `arch/arm64/kvm/hyp/vgic-v3-sr.c`: on nVHE it sets `HCR_AMO | HCR_FMO |
  HCR_IMO` without touching DAIF.
- Per-CPU data is not always private to its CPU: `psci_cpu_on()` in
  `arch/arm64/kvm/hyp/nvhe/psci-relay.c` writes the target CPU's
  `cpu_on_args` through `per_cpu_ptr()`, serialised by
  `try_acquire_boot_args()`.
- There is no __hyp_per_cpu symbol; `__hyp_per_cpu_offset()` is in
  `arch/arm64/kvm/hyp/nvhe/hyp-smp.c`.
- Host memory can change under a read from another CPU: hyp copies a field
  once, for example the `READ_ONCE()` reads of `host_vcpu` and `host_kvm`
  fields in `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- Kernel tracepoints are absent, but `handle_trap()` calls
  `trace_hyp_enter()` and `trace_hyp_exit()`: hyp's own events from
  `HYP_EVENT()` in `arch/arm64/kvm/hyp/include/nvhe/trace.h`, empty inlines
  without `CONFIG_NVHE_EL2_TRACING`.
- `CONFIG_UBSAN_KVM_EL2`: builds nVHE objects with UBSAN in trap mode; a hit
  is a `brk` that ends in `hyp_panic()`.

**Vectors and the panic route**

- `invalid_host_el2_vect` in `arch/arm64/kvm/hyp/nvhe/host.S`: makes no
  loaded-vCPU test and never goes to `__guest_exit_panic`; it branches
  straight to `hyp_panic`.
- Stack overflow test in `invalid_host_el2_vect`: on the `NVHE_STACK_SHIFT`
  bit of SP; on overflow it switches to `overflow_stack` and branches to
  `hyp_panic_bad_stack()`, which only calls `hyp_panic()`.
- There is no __hyp_panic and no __kvm_vector_install here; the panic targets
  are `hyp_panic` and `__guest_exit_panic`, and `__activate_traps()` writes
  the per-CPU `kvm_hyp_vector` to VBAR_EL2.
- `__kvm_hyp_init` in `arch/arm64/kvm/hyp/nvhe/hyp-init.S` is another table,
  installed by `hyp_install_host_vector()` in `arch/arm64/kvm/arm.c`; every
  EL2 slot is `ventry .`, so an EL2 exception under it spins and never reaches
  `hyp_panic()`.
- Guest table, `el2_sync` and `el2_error`: both call
  `kvm_unexpected_el2_exception()`; with no fixup it stores ELR_EL2 in
  `kvm_hyp_ctxt` and returns to `__guest_exit_restore_elr_and_panic`, which
  reloads ELR_EL2 and falls into `__guest_exit_panic`.
- `el2_sync` tests SPSR_EL2.IL first: if set it leaves through `__guest_exit`
  with `ARM_EXCEPTION_IL` and does not panic.
- Two different "vCPU loaded" tests: `__guest_exit_panic` reads `kvm_hyp_ctxt`
  through `get_loaded_vcpu`, set only between `__guest_enter` and
  `__guest_exit`; `hyp_panic()` reads `host_ctxt->__hyp_running_vcpu`, set for
  the whole of `__kvm_vcpu_run()`.
- `hyp_panic()` in `arch/arm64/kvm/hyp/nvhe/switch.c`: does not call
  `__debug_switch_to_host()`; with `__hyp_running_vcpu` set its only restore
  calls are `__timer_disable_traps()`, `__deactivate_traps()`,
  `__load_host_stage2()` and `__sysreg_restore_state_nvhe()`.
- `__hyp_do_panic` called from `hyp_panic()`, so with a non-NULL `host_ctxt`:
  joins `__host_exit` at `__host_enter_for_panic`, which is after the kernel
  ptrauth key restore done at `__host_enter_restore_full`; host x0-x7 are
  replaced by the panic arguments.
- `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`, not `CONFIG_NVHE_EL2_DEBUG`, makes
  `__hyp_do_panic` clear `HCR_VM` and do `tlbi vmalls12e1`.

**EL2 exception fixup table**

- `__kvm_unexpected_el2_exception()` in
  `arch/arm64/kvm/hyp/include/hyp/switch.h`: does not read ESR_EL2; any
  synchronous exception or SError whose ELR_EL2 equals an entry's instruction
  address is recovered.
- Table entries are `struct kvm_exception_table_entry`, not
  `struct exception_table_entry`; the table is unsorted and scanned linearly.
- Marking: `_kvm_extable` in assembly, `__KVM_EXTABLE()` in inline asm; both
  are in `arch/arm64/include/asm/kvm_asm.h`.
- Users in this tree: only `__kvm_at()` and the SError window in `__guest_exit`
  (`abort_guest_exit_start`, `abort_guest_exit_end`); there is no
  ___kvm_hyp_call and no __kvm_get_mdcr_el2.
- Fixup code runs after the EL2 exception has overwritten ELR_EL2, SPSR_EL2
  and ESR_EL2; it must restore what later code reads, as `__kvm_at()` does for
  SPSR and ELR and the `9997` fixup in `arch/arm64/kvm/hyp/entry.S` does for
  all three.
- A marked instruction is not recovered while `__kvm_hyp_host_vector` is
  installed: `__kvm_at()` is also reached there, through `__get_fault_info()`
  from `handle_host_mem_abort()`, and a fault on it panics.

**BUG and WARN at EL2**

- `WARN_ON()` has no nVHE definition: nVHE code gets the generic one in
  `include/asm-generic/bug.h`, with `__WARN_FLAGS()` from
  `arch/arm64/include/asm/bug.h`; there is no __hyp_bug mechanism.
- `nvhe_hyp_panic_handler()` in `arch/arm64/kvm/handle_exit.c`: does not call
  `report_bug()` and never resumes; it uses `find_bug()` and
  `bug_get_file_line()` for the message, then `panic()`.
- File and line lookup: done only when `nvhe_hyp_panic_host_s2_disabled()` is
  true, that is without protected KVM or with
  `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`; otherwise only the address is printed.
- `CONFIG_BUG` off: `WARN_ON()` only evaluates its condition and execution
  continues, so the `return` after it is the only handling; `BUG()` is still a
  `brk`.
- Files built for both hyp and the kernel, for example
  `arch/arm64/kvm/hyp/pgtable.c` (`pgtable.o` in `arch/arm64/kvm/hyp/Makefile`
  and in `hyp-obj-y`): in the kernel build `WARN_ON()` warns and continues, so
  `if (WARN_ON(x)) return ...;` there needs a correct return value.

**Asserting versus returning an error**

- **Potentially unsafe usage**: `WARN_ON()` or `BUG_ON()` on the result of a
  call or on a state test.
  - Unsafe: when a host or guest argument, a page state or a memory shortfall
    can make the condition true and nothing earlier under the same lock hold
    has excluded it; the `brk` ends in `hyp_panic()` and
    `nvhe_hyp_panic_handler()` panics the host.
  - Safe: when earlier checks under the same locks make failure impossible,
    as in `__pkvm_host_share_hyp()`: `__host_check_page_state_range()` has
    passed for `PKVM_PAGE_OWNED`, so `__host_set_page_state_range()` skips
    `host_stage2_idmap_locked()`, its only call that can fail.
  - Safe: when the asserted step allocates and the memory was checked first,
    as `__guest_check_pgtable_memcache()` returns `-ENOMEM` before
    `WARN_ON(kvm_pgtable_stage2_map(...))` in `__pkvm_host_donate_guest()`,
    which passes the fixed `KVM_PGTABLE_PROT_RWX`.
- Returned, not asserted, while nothing has been changed yet:
  `__pkvm_host_share_ffa()` returns the result of
  `__host_set_page_state_range()`, and `__pkvm_host_unshare_guest()` returns a
  `kvm_pgtable_stage2_unmap()` error before it touches page state.
- Range arguments: rejected by `pfn_range_is_valid()` (`-EINVAL`) before any
  lock is taken, and by `check_range_allowed_memory()` (`-EINVAL` or
  `-EPERM`) before any host page state is read.
- There is no host_request_owned_transition() here; the host-side check is
  `__host_check_page_state_range()`.
- `host_stage2_adjust_range()`: returns `-EEXIST` for a valid PTE, `-EPERM`
  for an annotated one, and `-EINVAL` after `WARN_ON(1)`.
- `kvm_pgtable_stage2_map()` on a guest table and the other asserted commit
  steps are wrapped in `WARN_ON()`, not `BUG_ON()`.
- Debug-only assertions: `assert_host_shared_guest()` returns at once and
  `hyp_assert_lock_held()` is an empty stub without `CONFIG_NVHE_EL2_DEBUG`,
  so neither protects a production build.

## Locks

**Hypervisor spinlock**

- `hyp_assert_lock_held()` with `CONFIG_NVHE_EL2_DEBUG`: checks only once the
  static key `kvm_protected_mode_initialized` is enabled.
- `kvm_protected_mode_initialized`: enabled only in
  `pkvm_drop_host_privileges()` in `arch/arm64/kvm/pkvm.c`, which
  `finalize_pkvm()` reaches only when `is_protected_kvm_enabled()`.
- Non-protected nVHE: the key is never enabled, so the asserts in
  `arch/arm64/kvm/hyp/nvhe/trace.c` check nothing there.
- `__pkvm_init_finalise()` in `arch/arm64/kvm/hyp/nvhe/setup.c`: runs before
  the key is enabled, so `hyp_assert_lock_held()` checks nothing in
  `fix_host_ownership()`, which holds no lock, or in
  `pkvm_ownership_selftest()`.
- `union hyp_spinlock` field order: selected by `__AARCH64EB__`, not by
  `CONFIG_CPU_BIG_ENDIAN`.

**Locks and what they protect**

| State | Lock | Easy to miss |
|---|---|---|
| FF-A `host_buffers`, `hyp_buffers`, `ffa_desc_buf` | `host_buffers.lock` in `arch/arm64/kvm/hyp/nvhe/ffa.c` | `hyp_buffers.lock` is initialised and never taken |
| FF-A `hyp_ffa_version`, `has_version_negotiated` (writes) | `version_lock` in `arch/arm64/kvm/hyp/nvhe/ffa.c` | taken only in `do_ffa_version()` |
| Block fixmap slot `hyp_fixblock_slot` | `hyp_fixblock_lock` in `arch/arm64/kvm/hyp/nvhe/mm.c` | exists only `#if PAGE_SHIFT < 16` |
| Trace buffer load, unload, enable, reset, reader swap | `trace_buffer.lock` in `arch/arm64/kvm/hyp/nvhe/trace.c` | built only with `CONFIG_NVHE_EL2_TRACING`, which sits inside `if NVHE_EL2_DEBUG` |

- FF-A buffers and FF-A version: two locks, not one.
- `hyp_ffa_version` reads in the memory handlers: under `host_buffers.lock`
  or no lock, never `version_lock`.
- `hyp_ffa_version` stability: `do_ffa_version()` stops writing it once
  `has_version_negotiated` is set, and `kvm_host_ffa_handler()` rejects every
  other call until then.
- `hyp_fixblock_lock`: taken in `hyp_fixblock_map()` and still held on
  return; `hyp_fixblock_unmap()` releases it.
- `PAGE_SHIFT >= 16`: `hyp_fixblock_map()` falls back to the per-CPU
  `hyp_fixmap_map()` and takes no lock.
- Trace event writes: `tracing_reserve_entry()` and `tracing_commit_entry()`
  take no lock; they use the per-CPU `status` word in
  `kernel/trace/simple_ring_buffer.c`.
- `__hyp_check_page_state_range()`: has no `hyp_assert_lock_held()`;
  `__host_check_page_state_range()` and `__guest_check_page_state_range()`
  assert their lock.
- **Potentially unsafe usage**: writing hyp page state with `set_hyp_state()`
  without holding `host_mmu.lock`.
  - Unsafe: while another CPU can write host state under `host_mmu.lock`;
    `__host_state` and `__hyp_state_comp` are adjacent bit-fields in
    `struct hyp_page`, so one write can undo the other.
  - Safe: holding `host_mmu.lock` and `pkvm_pgd_lock` together, as every
    caller of `__hyp_set_page_state_range()` does, for example
    `__pkvm_host_donate_hyp()`.
  - Safe: with no lock inside the `__pkvm_init` hypercall, as
    `fix_host_ownership_walker()` does; `kvm_arm_init()` runs
    `init_hyp_mode()` before `init_subsystems()` gives the other CPUs EL2
    through `cpu_hyp_init()`.
- `pkvm_pgd_lock`: also covers the private-VA cursor `__io_map_next`, not
  `__io_map_base`; `__pkvm_alloc_private_va_range()` asserts it.
- `refcount` in `struct hyp_page`: under the pool lock only through
  `hyp_alloc_pages()`, `hyp_get_page()` and `hyp_put_page()`.
- `vm_table_lock`: also covers writes of `is_dying`, `loaded_hyp_vcpu` in
  `struct pkvm_hyp_vcpu`, and vCPU registration in `__pkvm_init_vcpu()`.
- `vm_table_lock` asserts: for example `get_vm_by_handle()`; one is outside
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`, in `kvm_init_pvm_id_regs()`
  (`arch/arm64/kvm/hyp/nvhe/sys_regs.c`).

**Lock ordering**

- Where the order is written: the one-line comment above
  `enum pkvm_component_id` in
  `arch/arm64/kvm/hyp/include/nvhe/mem_protect.h`; there is no comment beside
  the wrappers in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `enum pkvm_component_id`: exactly `PKVM_ID_HOST`, `PKVM_ID_HYP`,
  `PKVM_ID_GUEST`; there is no FF-A value.
- Order enforcement: none; `host_lock_component()`, `hyp_lock_component()`
  and `guest_lock_component()` call `hyp_spin_lock()` with no order check.
- `__pkvm_host_force_reclaim_page_guest()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`: takes `vm_table_lock`, then host,
  then guest, and releases in reverse.
- `vm_table_lock` in that function: held to the end because the VM comes
  from `get_vm_by_handle()` through `host_stage2_decode_gfn_meta()` and no
  reference is taken on it.
- `__pkvm_init_vcpu()`: holds `vm_table_lock` while `hyp_pin_shared_mem()`
  takes host then hyp.
- Nesting sites: those two functions are the only ones that take a component
  lock under `vm_table_lock`.
- `__pkvm_init_vm()`: does not hold `vm_table_lock` around
  `kvm_guest_prepare_stage2()`; `insert_vm_table_entry()` takes it
  afterwards.
- There is no __pkvm_teardown_vm() here; `__pkvm_start_teardown_vm()` and
  `__pkvm_finalize_teardown_vm()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c` do that.
- `__pkvm_finalize_teardown_vm()`: drops `vm_table_lock` before
  `reclaim_pgtable_pages()` takes the guest lock.

## Threat model and host inputs

**Protection goals**

- vCPU register state of a protected VM: not protected from the host in this
  tree. `flush_hyp_vcpu()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c` copies the
  host's `arch.ctxt` into the hyp vCPU before every run and `sync_hyp_vcpu()`
  copies it back; `Documentation/virt/kvm/arm/pkvm.rst` lists "CPU state
  isolation" as Unimplemented.
- DMA: nothing under `arch/arm64/kvm/` programs an IOMMU;
  `Documentation/virt/kvm/arm/pkvm.rst` lists "DMA isolation using an IOMMU"
  as Unimplemented.
- pVM memory: a page is protected only once it is donated, which happens
  lazily on a guest stage-2 fault (`pkvm_pgtable_stage2_map()` in
  `arch/arm64/kvm/pkvm.c` calling `__pkvm_host_donate_guest`).
- Host access to a donated pVM page: the host can destroy the page but not
  read it. `__pkvm_host_force_reclaim_page_guest()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` zeroes it with `hyp_poison_page()`,
  marks the guest PTE `KVM_GUEST_INVALID_PTE_TYPE_POISONED` and returns the
  page to the host.
- SMCs that are neither PSCI nor FF-A: `handle_host_smc()` passes them to EL3
  with the host's x0-x17 unchanged, through `default_host_smc_handler()`.
  Apart from the two refusals at the top of `handle_host_smc()` (non-zero SMC
  immediate, upper 32 bits of the id set), no code filters them; the comment
  in `kvm_host_ffa_handler()` gives the assumption that firmware exposes no
  access to arbitrary non-secure memory.
- `Documentation/virt/kvm/arm/pkvm.rst`: says nothing about side channels,
  availability, physical attacks or EL3. It lists the isolation mechanisms
  and their status.

**Isolation implemented so far**

- Status per mechanism, as `Documentation/virt/kvm/arm/pkvm.rst` gives it:

| Mechanism | Status |
|---|---|
| CPU memory isolation | anonymous memory and metadata pages |
| CPU state isolation | Unimplemented |
| DMA isolation using an IOMMU | Unimplemented |
| Proxying of Trustzone services | FF-A and PSCI calls from the host |
| Protected VM firmware (pvmfw) | Unimplemented |

- Device assignment and attestation: not mentioned in
  `Documentation/virt/kvm/arm/pkvm.rst`.
- Guest-initiated share and unshare: implemented. `kvm_handle_pvm_hvc64()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` reaches `__pkvm_guest_share_host()` and
  `__pkvm_guest_unshare_host()`.
- Teardown reclaim: implemented, `__pkvm_host_reclaim_page_guest()`; from the
  host it is reached only through `__pkvm_reclaim_dying_guest_page()`, once
  `__pkvm_start_teardown_vm()` has set `is_dying`.
- Taint: `pkvm_init_host_vm()` in `arch/arm64/kvm/pkvm.c` itself calls
  `add_taint(TAINT_USER, LOCKDEP_STILL_OK)` when `type` has
  `KVM_VM_TYPE_ARM_PROTECTED`.
- Taint timing: at `KVM_CREATE_VM` (`kvm_arch_init_vm()`), right after the
  `__pkvm_reserve_vm` hypercall succeeds, before the hyp VM exists; the hyp VM
  is built later by `pkvm_create_hyp_vm()`.
- Non-protected VM under pKVM: also goes through `pkvm_init_host_vm()` and
  reserves a handle, without taint.
- `KVM_VM_TYPE_ARM_PROTECTED` without protected mode: `kvm_arch_init_vm()`
  returns `-EINVAL`, no taint.

**Host-controlled inputs**

- Registers versus memory: models have this right; hypercall registers are
  saved per CPU by `__host_exit`, host-owned and shared memory can be
  rewritten by another CPU at any point of a hypercall.
- `flush_hyp_vcpu()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`: re-reads the
  host `struct kvm_vcpu` on every run. Besides the register context it takes
  `mdcr_el2`, `iflags` and `vsesr_el2` unmasked, for protected vCPUs too;
  from `hcr_el2` it takes only `HCR_TWI`, `HCR_TWE` and `HCR_VSE`.
- `handle_host_hcall()`: after `kvm_protected_mode_initialized`, of the ids
  in `host_hcall[]` it rejects only those below
  `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`. Every later entry of `host_hcall[]` stays
  callable by the host, in any order, on any CPU.
- `pkvm_load_hyp_vcpu()`: stops two CPUs from loading one hyp vCPU. It does
  not stop another CPU from writing the host `struct kvm_vcpu` behind it.
- Frozen at de-privilege, not host-changeable afterwards: values the host
  wrote into hyp data, rodata, bss and per-CPU sections before init, for
  example `kvm_init_params`, `hyp_memory[]` and `kvm_host_psci_config`.
  `fix_host_ownership()` in `arch/arm64/kvm/hyp/nvhe/setup.c` makes those
  pages hyp-owned.

**Reading host memory**

- Requirement 1, the page is readable at EL2: it is pinned with
  `hyp_pin_shared_mem()` or was donated first. See "Pinning shared host
  memory" for why a shared, unpinned page is not enough.
- Requirement 2, one fetch: copy the field into a local or into
  `hyp_vcpu->vcpu`, validate or clamp the copy, use only the copy.
- `flush_hyp_vcpu()`: only the `hcr_el2` read uses `READ_ONCE()`; the other
  fields are plain assignments into `hyp_vcpu->vcpu`.
- `vcpu_idx`: `init_pkvm_hyp_vcpu()` reads it once with `READ_ONCE()`; the
  range check is in `register_hyp_vcpu()`, on the hyp copy.
- Snapshot of a whole object: `refill_memcache()` in
  `arch/arm64/kvm/hyp/nvhe/mm.c` copies the host `struct kvm_hyp_memcache`
  into a local; `__do_ffa_mem_xfer()` copies the host TX buffer into
  `hyp_buffers.tx` and parses that.
- Donate instead of copy: `__tracing_load()` in
  `arch/arm64/kvm/hyp/nvhe/trace.c`, in protected mode, donates the
  descriptor with `__pkvm_host_donate_hyp()` (through `__admit_host_mem()`),
  validates it in place, then gives it back.
- **Unsafe usage**: in protected mode, applying `kern_hyp_va()` to a pointer
  taken from a hypercall argument or from host memory after de-privilege, and
  dereferencing it without a pin or a donation.
  - Unsafe: the access faults at EL2 when the page is not mapped there.
  - Safe: pin first and keep the pin for the whole use, as
    `init_pkvm_hyp_vcpu()` and `__pkvm_init_vm()` do; `hyp_unpin_shared_mem()`
    is what unmaps.
  - Safe: compare the argument with an already pinned pointer and use that,
    as `__get_host_hyp_vcpus()` does with `hyp_vcpu->host_vcpu`.
  - Safe: donate the page before the first read, as `admit_host_page()` does
    before `pop_hyp_memcache()` reads the link stored in the page.
  - Safe: when `is_protected_kvm_enabled()` is false; `kvm_share_hyp()` then
    maps through `create_hyp_mappings()` and `__pin_shared_page()` skips the
    pin.
- **Potentially unsafe usage**: reading the same field of host memory twice.
  - Unsafe: when the first read is checked and the second is used as an
    index, a length or a pointer at EL2.
  - Safe: one `READ_ONCE()` into a local that is clamped to a hyp-owned limit
    before use, as `pkvm_vcpu_init_sve()` does with `kvm_host_sve_max_vl`.
  - Safe: when neither read is trusted. `pkvm_refill_memcache()` reads
    `nr_pages` twice, and each page is still validated by
    `__pkvm_host_donate_hyp()` in `admit_host_page()`.

**Host-writable system registers**

- HCR_EL2 for the host: taken from per-CPU `kvm_init_params.hcr_el2`, not from
  a constant. `cpu_prepare_hyp_mode()` in `arch/arm64/kvm/arm.c` seeds it with
  `HCR_HOST_NVHE_PROTECTED_FLAGS` (which adds `HCR_TSC`), then `HCR_ATA` or
  `HCR_TID5`, then `HCR_E2H` with `ARM64_KVM_HVHE`.
- EL2 registers are not all free of host-chosen values:
  - CNTVOFF_EL2: `handle___kvm_timer_set_cntvoff()` writes hypercall
    register 1 to it unchecked, and the call stays allowed after init.
  - MDCR_EL2 during a guest run: `__activate_traps()` writes
    `vcpu->arch.mdcr_el2`, which `flush_hyp_vcpu()` copied from the host.
  - HCR_EL2 during a guest run: bits `HCR_TWI`, `HCR_TWE` and `HCR_VSE` of
    the hyp vCPU's `arch.hcr_el2` come from the host; the rest from
    `pkvm_vcpu_init_traps()`.
  - VSESR_EL2: `___activate_traps()` can write the host-supplied
    `vsesr_el2` when `HCR_VSE` is set and the CPU has `ARM64_HAS_RAS_EXTN`.
- Host-written EL1 and EL0 registers that EL2 code reads, for example:
  `inject_host_exception()` reads SCTLR_EL1 and VBAR_EL1 to build the
  injected exception; `enter_vmid_context()` reads TCR_EL1 under
  `ARM64_WORKAROUND_SPECULATIVE_AT`; `handle___kvm_vcpu_run()`, under pKVM
  and when `system_supports_sme()`, reads SVCR and refuses to run if it is
  non-zero.

**Pinning shared host memory**

- Arguments: hyp virtual addresses; callers convert first with
  `kern_hyp_va()` or `hyp_phys_to_virt()`.
- Alignment: the range is rounded outward to page boundaries; nothing checks
  that it was aligned.
- Checks, under `host_mmu.lock` then `pkvm_pgd_lock`, for every page: the
  range lies in one memory region that is not `MEMBLOCK_NOMAP`
  (`check_range_allowed_memory()`), host state is `PKVM_PAGE_SHARED_OWNED`,
  hyp state is `PKVM_PAGE_SHARED_BORROWED`.
- Error value: `-EINVAL` when the range crosses a region boundary, otherwise
  `-EPERM`; `init_pkvm_hyp_vcpu()` reports a failed pin of the host
  `struct kvm_vcpu` as `-EBUSY`.
- Mapping: `__pkvm_host_share_hyp()` only changes page state. The pin that
  takes `refcount` from 0 to 1 creates the EL2 mapping, and the unpin that
  takes it from 1 to 0 removes it with `kvm_pgtable_hyp_unmap()`.
- Guaranteed while pinned: the page is mapped at EL2, and
  `__pkvm_host_unshare_hyp()` fails with `-EBUSY`
  (`__hyp_check_page_count_range()`).
- `refcount` in `struct hyp_page`: a `u16`; `hyp_page_ref_inc()` hits
  `BUG_ON()` at `USHRT_MAX`, it does not wrap.
- Life of a hyp VM: the host `struct kvm`, pinned in `__pkvm_init_vm()`
  itself and unpinned in `__pkvm_finalize_teardown_vm()`. There is no
  unpin_host_kvm() and no __pkvm_teardown_vm() in this tree.
- Life of a hyp vCPU: the host `struct kvm_vcpu`, and the SVE state buffer
  when the hyp copy has `KVM_ARM_VCPU_SVE` (`pkvm_vcpu_init_sve()`). No
  `struct user_fpsimd_state` area is pinned.
- vCPU pins: dropped only by `unpin_host_vcpus()` at VM teardown, or on the
  error path of `__pkvm_init_vcpu()`; there is no per-vCPU destroy.
- Relying on the `struct kvm` pin: the timer `vm_offset` pointers that
  `init_pkvm_hyp_vcpu()` sets for non-protected vCPUs, and `teardown_mc` and
  `stage2_teardown_mc`, which teardown writes through `hyp_vm->host_kvm`.

## Host hypercalls and SMCs

**Hypercall dispatch**

- Table guard: `BUILD_BUG_ON(ARRAY_SIZE(host_hcall) !=
  __KVM_HOST_SMCCC_FUNC_MAX)`, first statement of `handle_host_hcall()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`.
- What the guard catches: a missing `HANDLE_FUNC()` line for the last entry
  before `__KVM_HOST_SMCCC_FUNC_MAX`, because the array is then too short.
- What the guard misses: a missing `HANDLE_FUNC()` line for any earlier entry.
  The slot is NULL, the array size is unchanged, the build passes, and the call
  fails at run time with `SMCCC_RET_NOT_SUPPORTED`.
- `HANDLE_FUNC(x)`: stores `handle_##x`; there is no kvm_host_hcall_ prefix.
- `array_index_nospec()`: not called by `handle_host_hcall()`; the index is used
  straight after the range test.
- Range test: `id < hcall_min || id >= hcall_max`; both bounds depend on the
  phase, see "Hypercall availability by phase".
- Invalid id: the `inval:` path writes `cpu_reg(host_ctxt, 0)` only; x1-x3 are
  not zeroed.
- Host side of an invalid id: `kvm_call_hyp_nvhe()` in
  `arch/arm64/include/asm/kvm_host.h` warns and yields `-EOPNOTSUPP` in place of
  `res.a1`.
- Stub hypercalls: `__host_hvc` in `arch/arm64/kvm/hyp/nvhe/host.S` diverts
  x0 below `HVC_STUB_HCALL_NR` to `__kvm_handle_stub_hvc` only without
  `ARM64_KVM_PROTECTED_MODE`.
- Stub ids in protected mode, once `__kvm_hyp_host_vector` is installed: every
  host HVC reaches `handle_host_hcall()`, and a stub id gets
  `SMCCC_RET_NOT_SUPPORTED`.

**Hypercall return registers**

- x0 timing: `handle_host_hcall()` writes `SMCCC_RET_SUCCESS` before it calls
  the handler, not after.
- Why before: `handle___pkvm_init()` does not return on success;
  `__pkvm_init_finalise()` in `arch/arm64/kvm/hyp/nvhe/setup.c` writes x1 and
  calls `__host_enter()` itself, so x0 must already hold the status.
- Handler that writes no result: x1 is not zeroed, the host gets back the x1
  it passed (its first argument); `kvm_call_hyp()` discards it.

**Hypercall availability by phase**

- Three bands, bounded by `hcall_min` and `hcall_max` in `handle_host_hcall()`:

| Band | Entries | Key clear | Key set |
|---|---|---|---|
| early | `__pkvm_init` up to the entry before `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` | allowed | rejected |
| common | from `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` up to the entry before `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` | allowed | allowed |
| pKVM-only | from `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` up to the entry before `__KVM_HOST_SMCCC_FUNC_MAX` | rejected | allowed |

- Key: the static key `kvm_protected_mode_initialized`, not
  `is_protected_kvm_enabled()`.
- Key clear: `hcall_max = __KVM_HOST_SMCCC_FUNC_PKVM_ONLY`; key set:
  `hcall_min = __KVM_HOST_SMCCC_FUNC_MIN_PKVM`.
- Non-protected nVHE: only `pkvm_drop_host_privileges()` in
  `arch/arm64/kvm/pkvm.c` enables the key, so the pKVM-only band is rejected for
  good.
- Marker names: there is no MAX_NO_PKVM marker; the three are
  `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`, `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` and
  `__KVM_HOST_SMCCC_FUNC_MAX`.
- `MARKER()` in `arch/arm64/include/asm/kvm_asm.h`: a marker uses up no number;
  it has the value of the entry written after it.
- New entry: it joins the band of the marker it is written after; an entry
  written directly after a marker becomes that band's first value.
- Only exception: `__pkvm_prot_finalize`, listed under the comment "unavailable
  once pKVM has finalised" yet written after `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`,
  so it stays callable.
- Reason, from the comment in `handle_host_hcall()`: the key must be enabled
  before finalisation, and finalisation runs per CPU.
- VM and vCPU lifecycle calls: all in the pKVM-only band, none placed against
  the rule.

**Hypercall arguments**

- `kern_hyp_va()`: arithmetic only; it does not check that the result is mapped
  at EL2 or belongs to the host.
- EL2 mapping of host memory: created by `hyp_pin_shared_mem()` on the first pin
  and by `__pkvm_host_donate_hyp()`, both in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `hyp_pin_shared_mem()`: fails unless the host has shared every page in the
  range; this is the check that rejects a bad pointer.
- Pinned page: stays host-writable; besides the mapping, the pin only makes
  `__pkvm_host_unshare_hyp()` fail while it is held.
- Donated page: owned by hyp, so repeated reads are stable until
  `__pkvm_hyp_donate_host()`.
- `DECLARE_REG()`: also declares an unused `int` named `___check_reg_` plus
  the register number, so two declarations of one register in a scope fail to
  build.

**Host SMC handling**

- Refused before any handler runs, in `handle_host_smc()`:
  - a non-zero SMC immediate (`esr & ESR_ELx_xVC_IMM_MASK`);
  - a function id with any of the upper 32 bits set after
    `ARM_SMCCC_CALL_HINTS` is cleared.
- Refused call: x0 becomes `SMCCC_RET_NOT_SUPPORTED`, nothing reaches EL3, and
  `kvm_skip_host_instr()` still runs.
- Why the upper bits are tested: `kvm_host_psci_handler()` and
  `kvm_host_ffa_handler()` take the id as `u32`.
- Hypervisor-reserved range: `handle_host_smc()` has no check for one.
- Hints: cleared in a local copy only; a call forwarded by
  `default_host_smc_handler()` or `psci_forward()` carries the host's
  original x0.
- `kvm_host_psci_handler()`: from PSCI 0.2 on it claims all 32 function numbers
  of both bases (`is_psci_0_2_call()`); an id it does not know gets
  `PSCI_RET_NOT_SUPPORTED` and is not forwarded.
- PSCI SYSTEM_OFF and SYSTEM_RESET: forwarded unchanged by `psci_forward()`;
  only CPU_ON, CPU_SUSPEND and SYSTEM_SUSPEND get a hyp entry point.
- `kvm_host_ffa_handler()`: until a version is negotiated, every FF-A call
  except `FFA_VERSION` gets `FFA_RET_INVALID_PARAMETERS`.
- Unclaimed call: `default_host_smc_handler()` forwards it whatever its owner
  field; no filter limits it to standard ids.
- Reason for forwarding: stated in the comment in `kvm_host_ffa_handler()` in
  `arch/arm64/kvm/hyp/nvhe/ffa.c`; devices rely on custom firmware calls and
  EL3 has to be trusted anyway.

## Memory from the host

**Hyp memcaches**

- Per-vCPU memcache: `pkvm_memcache` in `struct kvm_vcpu_arch`. It exists
  twice: the host's `vcpu->arch.pkvm_memcache` and EL2's
  `hyp_vcpu->vcpu.arch.pkvm_memcache`.
- No field is named `stage2_mc`; that name is only a local variable in
  `__pkvm_finalize_teardown_vm()`.
- `get_mmu_memcache()` in `arch/arm64/kvm/mmu.c`: selects `pkvm_memcache` for
  every VM when `is_protected_kvm_enabled()`, protected or not.
- Helpers: there is no __push_hyp_memcache() or __pop_hyp_memcache(); the
  inline helpers in `arch/arm64/include/asm/kvm_host.h` are
  `push_hyp_memcache()`, `pop_hyp_memcache()`, `__topup_hyp_memcache()` and
  `__free_hyp_memcache()`.
- Per-VM memcaches: `teardown_mc` and `stage2_teardown_mc`, both in
  `struct kvm_protected_vm` (host `kvm->arch.pkvm`). There is no hyp_donations.
- `struct pkvm_hyp_vm` has no memcache member of its own, and EL2 does not use
  the `teardown_mc` and `stage2_teardown_mc` copies in
  `hyp_vm->kvm.arch.pkvm`; EL2 writes the host's headers through
  `hyp_vm->host_kvm` in `__pkvm_finalize_teardown_vm()`.
- There is no __pkvm_teardown_vm() and no reclaim_hyp_memcache(); teardown is
  `__pkvm_start_teardown_vm()` then `__pkvm_finalize_teardown_vm()`.

| Memcache | Filled by | Drained by |
|---|---|---|
| host `vcpu->arch.pkvm_memcache` | host, `topup_hyp_memcache()` | EL2, `refill_memcache()`; rest freed by host, `free_hyp_memcache()` in `kvm_arch_vcpu_destroy()` |
| hyp `hyp_vcpu->vcpu.arch.pkvm_memcache` | EL2, `refill_memcache()` | `guest_s2_zalloc_page()`; rest popped at teardown |
| `teardown_mc` | EL2, `teardown_donated_memory()`: pages of each `struct pkvm_hyp_vcpu` and of `struct pkvm_hyp_vm` | host, `free_hyp_memcache()` |
| `stage2_teardown_mc` | EL2: PGD and stage-2 table pages (`reclaim_pgtable_pages()`), unused hyp vCPU memcache pages | host, `free_hyp_memcache()` |

- `stage2_teardown_mc` and the host vCPU memcache carry
  `HYP_MEMCACHE_ACCOUNT_STAGE2`: `hyp_mc_free_fn()` then calls
  `kvm_account_pgtable_pages()` with -1 per page. A page pushed on
  `teardown_mc` is freed without that.
- Pages popped from the hyp vCPU memcache never return to a memcache while the
  VM lives: a freed table page goes to `hyp_vm->pool` through `hyp_put_page()`.
- `guest_s2_zalloc_page()`: tries `current_vm->pool` first and pops the memcache
  only when the pool is empty.

**Taking pages from memcaches**

- Snapshot: `refill_memcache()` in `arch/arm64/kvm/hyp/nvhe/mm.c` copies
  `*host_mc` into the local `tmp`, works on `&tmp`, and writes `tmp` back.
  `flush_hyp_vcpu()` does not touch `pkvm_memcache`.
- `READ_ONCE()` is not used: `admit_host_page()` reads `nr_pages` and `head`,
  and `pop_hyp_memcache()` reads both again.
- **Potentially unsafe usage**: donating `mc->head` and then calling
  `pop_hyp_memcache()` on the same header.
  - Unsafe: when the header is in host memory; the host can change `head`
    between the two reads, and the pop dereferences a page that was not donated.
  - Safe: when the header is a hyp-private copy, as `refill_memcache()` passes
    `&tmp` to `admit_host_page()`.
  - Safe: `pop_hyp_memcache()` on the hyp vCPU's `pkvm_memcache`, as in
    `guest_s2_zalloc_page()`; its pages were donated by `admit_host_page()`.
  - Safe: `push_hyp_memcache()` on a header in host memory, as
    `teardown_donated_memory()` does; push stores `head` and never
    dereferences it.
- `min_pages`: `pkvm_refill_memcache()` passes the host's
  `host_vcpu->arch.pkvm_memcache.nr_pages`, read apart from the snapshot. It is
  only the loop bound; the hyp memcache has no capacity limit.
- Alignment of `head`: not checked. `hyp_phys_to_pfn()` and the `PAGE_MASK` in
  `pop_hyp_memcache()` both drop the low bits, so both name the same page.
- Failed donation: `refill_memcache()` returns `-ENOMEM` whatever the donation
  error was. Pages already admitted stay in the hyp memcache.
- Host memcache address: taken from `hyp_vcpu->host_vcpu`, which
  `init_pkvm_hyp_vcpu()` pinned with `hyp_pin_shared_mem()`; it is not a
  hypercall argument.
- Hyp vCPU memcache: no lock protects it. `pkvm_refill_memcache()` callers take
  the vCPU from `pkvm_get_loaded_hyp_vcpu()`; teardown pops it only after
  `get_pkvm_unref_hyp_vm_locked()` saw a zero page count.
- `guest_s2_zalloc_page()`: sets only `refcount` in `struct hyp_page`, not
  `order`. `__hyp_attach_page()` forces order 0 for a page outside the pool
  range.

**Memory donated for hyp objects**

- `map_donated_memory()` failure: returns `NULL` for any cause;
  `__pkvm_init_vm()` and `__pkvm_init_vcpu()` report `-ENOMEM`.
- VM size: `pkvm_get_hyp_vm_size()` of `READ_ONCE(host_kvm->created_vcpus)`.
  The same value is stored in `hyp_vm->kvm.created_vcpus` and bounds `vcpus[]`.
- Clearing on map: `map_donated_memory()` clears `size` bytes; the donation
  covers `PAGE_ALIGN(size)`. The tail of the last page keeps host content.
- PGD: taken with `map_donated_memory_noclear()`. `hyp_pool_init()` in
  `kvm_guest_prepare_stage2()` zeroes it, through `__hyp_attach_page()`.
- Hand-back paths:

| Path | Function | Clears | Goes to |
|---|---|---|---|
| init error | `unmap_donated_memory()` | `size` bytes | host frees with `free_pages_exact()` |
| VM, vCPU at teardown | `teardown_donated_memory()` | `PAGE_ALIGN(size)`, before the link is written | `teardown_mc` |
| PGD, stage-2 tables at teardown | `reclaim_pgtable_pages()` | no; pool pages are already zero | `stage2_teardown_mc` |
| unused hyp vCPU memcache pages | `unmap_donated_memory_noclear()` | no | `stage2_teardown_mc` |

- `__pkvm_hyp_donate_host()`: returns `-EBUSY` if any page has a non-zero
  `refcount` in `struct hyp_page` (`__hyp_check_page_count_range()`).
  `__unmap_donated_memory()` wraps the call in `WARN_ON()`.
- `reclaim_pgtable_pages()`: sets `page->refcount = 0` before each donation for
  that reason.
- Host after teardown: `free_hyp_memcache()` frees page by page with
  `free_page()`. `__pkvm_create_hyp_vm()` and `__pkvm_create_hyp_vcpu()`
  allocate with `alloc_pages_exact()` so each page can be freed alone.
- **Potentially unsafe usage**: handing memory back to the host without
  clearing it.
  - Unsafe: when EL2 wrote hyp or guest state into the pages and nothing has
    zeroed them since.
  - Safe: after `teardown_donated_memory()` has cleared the object; it then
    calls `unmap_donated_memory_noclear()`.
  - Safe: pages drained from `hyp_vm->pool`, as in `reclaim_pgtable_pages()`;
    `__hyp_attach_page()` zeroed them when they were freed.
  - Safe: pages still in the hyp vCPU memcache, as in
    `__pkvm_finalize_teardown_vm()`; EL2 wrote only the link into them.

**Hyp structure sizes**

- Generated header: `hyp_constants.h`, made by `arch/arm64/kvm/Makefile` and
  included by `arch/arm64/kvm/pkvm.c`.
- Host VM size: computed inline in `__pkvm_create_hyp_vm()`.
  `pkvm_get_hyp_vm_size()` is a static EL2 function in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`; the host cannot call it.
- No size crosses the hypercall: `__pkvm_init_vm()` and `__pkvm_init_vcpu()`
  get the host VA of the area with no size, and donate `PAGE_ALIGN()` of
  EL2's own size from it.
- If EL2's size exceeds the host's allocation, EL2 takes whatever host-owned
  pages follow it, or the donation fails; nothing compares the two sizes.
- `struct pkvm_hyp_vm` embeds `struct kvm`, `struct pkvm_hyp_vcpu` embeds
  `struct kvm_vcpu`: a field added to either, or to `struct kvm_arch` or
  `struct kvm_vcpu_arch`, grows the donation too.
- **Unsafe usage**: a member under `#ifdef __KVM_NVHE_HYPERVISOR__` in either
  structure or in a structure they embed.
  - Unsafe: `arch/arm64/kvm/hyp/hyp-constants.c` is built by
    `arch/arm64/kvm/Makefile` without `-D__KVM_NVHE_HYPERVISOR__`, EL2 code is
    built with it (`arch/arm64/kvm/hyp/nvhe/Makefile`), so the host constant
    and EL2's `sizeof()` differ.
  - Safe: a member whose presence depends only on a `CONFIG_` symbol, as
    `debugfs_nv_dentry` in `struct kvm_arch` under
    `CONFIG_PTDUMP_STAGE2_DEBUGFS`; both builds see the same layout.
- New field at EL2: starts as zero (`map_donated_memory()`). The hyp copy is
  separate from the host's; a host value arrives only where EL2 copies it, for
  example `init_pkvm_hyp_vcpu()`, `pkvm_init_features_from_host()` or
  `flush_hyp_vcpu()`.
- New field that owns a resource: release it in
  `__pkvm_finalize_teardown_vm()` before `teardown_donated_memory()` clears the
  object. There is no __pkvm_teardown_vm().
- Alignment: both sides round the size with `PAGE_ALIGN()`;
  `map_donated_memory_noclear()` returns `NULL` unless the address is
  page-aligned.

## Hyp VMs and vCPUs

**Hyp copies and back pointers**

- EL2 copy holding host pointers: `hyp_vcpu->vcpu.arch.sve_state` points at
  the host's pinned SVE buffer; for a non-protected vCPU the timer
  `offset.vm_offset` pointers point into `hyp_vm->host_kvm`. See
  `pkvm_vcpu_init_sve()` and `init_pkvm_hyp_vcpu()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- `__get_host_hyp_vcpus()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`: turns a
  host vCPU pointer from a register into the pair (host vCPU, hyp vCPU).
  Under pKVM it returns NULL for both unless the loaded hyp vCPU's
  `host_vcpu` equals the pointer.
- `hyp_vcpu` NULL with a non-NULL host vCPU: pKVM is off, and the handler
  runs on the host's `struct kvm_vcpu` directly, as `handle___kvm_vcpu_run()`
  does.
- `container_of(vcpu, struct pkvm_hyp_vcpu, vcpu)`: valid only when `vcpu`
  is the embedded copy; `pkvm_memshare_call()` uses it on the vCPU that
  `__kvm_vcpu_run()` was given.
- Copies between host and hyp vCPU: not only `flush_hyp_vcpu()` and
  `sync_hyp_vcpu()`. For example `handle___pkvm_vcpu_load()` copies `fgt`
  for a non-protected vCPU, `handle___pkvm_vcpu_put()` and
  `handle___pkvm_vcpu_sync_state()` call `sync_hyp_vcpu_state()`, and
  `pkvm_refill_memcache()` reads the host memcache.
- `READ_ONCE()` on host fields: not uniform. Most of `flush_hyp_vcpu()` and
  of `pkvm_init_features_from_host()` use plain assignment; `READ_ONCE()` is
  on, for example, `created_vcpus`, `arch.pkvm.handle`, `vcpu_idx`,
  `sve_max_vl`.
- `hyp_vm->host_kvm` and `hyp_vcpu->host_vcpu`: stored as hyp VAs;
  `handle___pkvm_init_vm()` and `handle___pkvm_init_vcpu()` apply
  `kern_hyp_va()` before the call.

**VM handles and table**

- `get_vm_by_handle()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`: returns NULL for
  a slot holding `RESERVED_ENTRY`, as well as for an out-of-range index.
- Dying VM: `get_vm_by_handle()` returns it; callers that care test
  `hyp_vm->kvm.arch.pkvm.is_dying` themselves.
- NULL result, by caller: `__pkvm_init_vcpu()` returns `-ENOENT`; teardown,
  reclaim and the handle-based handlers that return a value, for example
  `handle___pkvm_host_unshare_guest()`, return `-EINVAL`;
  `host_stage2_decode_gfn_meta()` returns `-EAGAIN`; `pkvm_load_hyp_vcpu()`
  returns NULL.
- Handle: chosen by `allocate_vm_table_entry()` (first NULL slot) in
  `__pkvm_reserve_vm()`, which stores `RESERVED_ENTRY` there.
- VMID: `idx + 1`, set with `atomic64_set()` in `init_pkvm_hyp_vm()`, not in
  `insert_vm_table_entry()`; there is no VMID allocator at EL2.
- `__insert_vm_table_entry()`: returns `-EINVAL` unless the slot holds
  `RESERVED_ENTRY`.

**References to a hyp VM**

- Count: `refcount` of the `struct hyp_page` for `hyp_virt_to_page(hyp_vm)`;
  `struct pkvm_hyp_vm` has no count field.
- Refusal: `get_pkvm_unref_hyp_vm_locked()` returns NULL while
  `hyp_page_count(hyp_vm)` is not zero, and `__pkvm_start_teardown_vm()` and
  `__pkvm_finalize_teardown_vm()` then return `-EINVAL`, not `-EBUSY`.
- `WARN_ON()`: none at EL2 for this; the host wraps both hypercalls in
  `WARN_ON()` in `arch/arm64/kvm/pkvm.c`.

| Takes a reference | Used by |
|---|---|
| `pkvm_load_hyp_vcpu()` | load; dropped by `pkvm_put_hyp_vcpu()` |
| `get_pkvm_hyp_vm()` | `__pkvm_reclaim_dying_guest_page()` |
| `get_np_pkvm_hyp_vm()` | unshare, wrprotect, test-clear-young, `handle___pkvm_tlb_flush_vmid()` |

- No reference by handle: the donate, share, relax-perms and mkyoung
  handlers use the loaded vCPU, whose load holds the reference.
- `__pkvm_init_vcpu()` and `__pkvm_host_force_reclaim_page_guest()`: take no
  reference; they hold `vm_table_lock` for the whole use.
- **Unsafe usage**: returning between `get_pkvm_hyp_vm()` or
  `get_np_pkvm_hyp_vm()` and `put_pkvm_hyp_vm()`.
  - Safe: put on every path after a non-NULL get, as
    `handle___pkvm_host_unshare_guest()` does; otherwise
    `get_pkvm_unref_hyp_vm_locked()` fails teardown with `-EINVAL` for good.

**Creating a hyp VM**

- Handle: reserved earlier by `__pkvm_reserve_vm()`, called from
  `pkvm_init_host_vm()`; `__pkvm_init_vm()` reads it from
  `host_kvm->arch.pkvm.handle`, not from a register.
- Failed `__pkvm_init_vm()`: leaves the reservation; the host releases it
  with `__pkvm_unreserve_vm()` in `__pkvm_destroy_hyp_vm()`.
- PGD size and `mmu->vtcr`: from EL2's `host_mmu.arch.mmu.vtcr`, not from
  `host_kvm->arch.mmu.vtcr`.

| Step, in order | Failure | Undone |
|---|---|---|
| `hyp_pin_shared_mem()` of `host_kvm` | its error | nothing |
| `READ_ONCE()` of `created_vcpus`, below 1 | `-EINVAL` | unpin |
| `READ_ONCE()` of `arch.pkvm.handle`, below `HANDLE_OFFSET` | `-EINVAL` | unpin |
| `map_donated_memory()` of the VM | `-ENOMEM` | unpin |
| `map_donated_memory_noclear()` of the PGD | `-ENOMEM` | VM memory, unpin |
| `init_pkvm_hyp_vm()` | cannot fail | - |
| `kvm_guest_prepare_stage2()` | its error | both donations, unpin |
| `insert_vm_table_entry()` | `-EINVAL` | `kvm_guest_destroy_stage2()`, both donations, unpin |

- `init_pkvm_hyp_vm()`: reads `arch.pkvm.is_protected` with `READ_ONCE()`.
- `pkvm_init_features_from_host()`: reads `arch.flags` with `READ_ONCE()`;
  `arch.ctr_el0`, `arch.vgic.vgic_model`, `arch.vcpu_features` and
  `arch.midr_el1` with plain loads.
- Table entry: never removed by `__pkvm_init_vm()`; insertion is the last
  step, so no failure follows it.

**Host side of VM creation**

- `pkvm_create_hyp_vm()` in `arch/arm64/kvm/pkvm.c`: takes `kvm->slots_lock`,
  then `kvm->arch.config_lock`; the caller already holds `vcpu->mutex`.
- Skip test: `pkvm_hyp_vm_is_created()`, which reads
  `kvm->arch.pkvm.is_created`; `kvm->arch.pkvm.handle` is already set by
  `pkvm_init_host_vm()` at VM creation.
- `kvm->slots_lock`: `kvm_arch_prepare_memory_region()` in
  `arch/arm64/kvm/mmu.c` reads `is_created` under it and returns `-EPERM`
  for `KVM_MR_DELETE` or `KVM_MR_MOVE` on a protected VM that is created.

**Creating a hyp vCPU**

- Publication: `smp_store_release()` in `register_hyp_vcpu()`, paired with
  `smp_load_acquire()` in `pkvm_load_hyp_vcpu()`; both also run under
  `vm_table_lock`.
- Index bound: `hyp_vm->kvm.created_vcpus`, fixed when the hyp VM was
  created; `struct pkvm_hyp_vm` has no vCPU counter and nothing is
  incremented.
- Index: any free slot below the bound, not the next one; an occupied slot
  or an index at or above the bound returns `-EINVAL`.
- SVE pin: `pkvm_vcpu_init_sve()` pins the host buffer for any vCPU whose
  hyp copy has `KVM_ARM_VCPU_SVE`, whatever the VM kind.
- `init_pkvm_hyp_vcpu()` failure after the host vCPU is pinned: unpins the
  host vCPU only; the SVE pin is its last step.
- `register_hyp_vcpu()` failure: `__pkvm_init_vcpu()` calls
  `unpin_host_vcpu()` and `unpin_host_sve_state()`.

**Loading and putting a vCPU**

- `pkvm_load_hyp_vcpu()` returns NULL when: this CPU's `loaded_hyp_vcpu` is
  set (tested before the lock); the lookup returns NULL; the VM `is_dying`;
  `vcpu_idx` is at or above `hyp_vm->kvm.created_vcpus`; the slot is NULL;
  `hyp_vcpu->loaded_hyp_vcpu` is set.
- Load before the hyp VM exists: fails, since the slot holds
  `RESERVED_ENTRY`; the host's `kvm_arch_vcpu_load()` does not look at the
  result.
- No vCPU loaded, handlers that return a value: `-EINVAL`, for example
  `handle___pkvm_host_donate_guest()` and
  `handle___pkvm_vcpu_in_poison_fault()`.
- No vCPU loaded, handlers that return nothing: silent return, for example
  `handle___pkvm_vcpu_sync_state()` and, under pKVM,
  `handle___vgic_v3_save_aprs()`.
- `handle___pkvm_host_donate_guest()`: also `-EINVAL` when the loaded vCPU
  is not protected; share, relax-perms and mkyoung when it is protected.
- Memcache topup: no hypercall; `pkvm_refill_memcache()` runs inside the
  donate and share handlers.

**Putting a vCPU**

- `handle___pkvm_vcpu_put()`: has no `is_protected_kvm_enabled()` test; it
  acts on `pkvm_get_loaded_hyp_vcpu()` if that is not NULL.
- Non-protected vCPU: put calls `sync_hyp_vcpu_state()`, which copies
  registers to the host vCPU, unless the host vCPU has
  `PKVM_HOST_STATE_DIRTY` set.
- Host after put: `kvm_arch_vcpu_put()` sets `PKVM_HOST_STATE_DIRTY` for a
  non-protected VM, so the next `flush_hyp_vcpu()` copies host state in.
- `hyp_page_ref_dec()`: has `BUG_ON(!p->refcount)`, so a
  `pkvm_put_hyp_vcpu()` that finds the VM's count at zero is fatal at EL2. A
  second `__pkvm_vcpu_put` hypercall is not: `pkvm_get_loaded_hyp_vcpu()` is
  then NULL and `handle___pkvm_vcpu_put()` does nothing.
- **Unsafe usage**: calling `pkvm_put_hyp_vcpu()` with a vCPU that is not
  this CPU's loaded one.
  - Safe: pass `pkvm_get_loaded_hyp_vcpu()`, as `handle___pkvm_vcpu_put()`
    does; `pkvm_put_hyp_vcpu()` writes NULL to this CPU's `loaded_hyp_vcpu`
    whatever it is given.

**Tearing a VM down**

| Stage | Hypercall | Host call site |
|---|---|---|
| 1 | `__pkvm_start_teardown_vm` | `pkvm_pgtable_stage2_destroy_range()` |
| 2, protected | `__pkvm_reclaim_dying_guest_page` | `__pkvm_pgtable_stage2_reclaim()` |
| 2, non-protected | `__pkvm_host_unshare_guest` | `__pkvm_pgtable_stage2_unshare()` |
| 3 | `__pkvm_finalize_teardown_vm` | `__pkvm_destroy_hyp_vm()` |

- Stages 1 and 2: reached from `kvm_arch_flush_shadow_all()` through
  `kvm_free_stage2_pgd()`; stage 3 from `kvm_arch_destroy_vm()`.
- `__pkvm_start_teardown_vm()`: `-EINVAL` for an unknown handle, a non-zero
  count, or a VM already dying.
- `__pkvm_reclaim_dying_guest_page()`: `-EINVAL` for an unknown handle or a
  VM not dying.
- `__pkvm_finalize_teardown_vm()`: `-EINVAL` for an unknown handle, a
  non-zero count, or a VM not dying.
- `-EBUSY`: returned by none of the three. `-ENOENT`: never for the handle
  or the count; `__pkvm_reclaim_dying_guest_page()` can pass it on from
  `get_valid_guest_pte()` for a gfn with no valid entry.
- `is_dying`: a field of `struct kvm_protected_vm`; EL2 uses the copy in
  `hyp_vm->kvm.arch.pkvm`, the host keeps its own in `kvm->arch.pkvm`.
- `is_dying` is tested at EL2 in four places only: `pkvm_load_hyp_vcpu()` and
  `__pkvm_start_teardown_vm()` refuse; reclaim and finalize require it.
- Not tested by: `__pkvm_init_vcpu()`, `get_pkvm_hyp_vm()`,
  `get_np_pkvm_hyp_vm()`, so handle-based unshare still works on a dying VM.
- Share, donate, relax-perms, mkyoung: no `is_dying` test; they need a
  loaded vCPU, and none can be loaded once the VM is dying.
- VM reserved but never created: `__pkvm_destroy_hyp_vm()` calls
  `__pkvm_unreserve_vm` instead of finalize.

**Pages returned at teardown**

| Page kind | Way back to the host |
|---|---|
| Protected guest page | `__pkvm_host_reclaim_page_guest()`, per page |
| Non-protected guest page | `__pkvm_host_unshare_guest()`, per mapping |
| Stage-2 tables and PGD | `reclaim_pgtable_pages()` into `stage2_teardown_mc` |
| vCPU memcache pages | popped, pushed to `stage2_teardown_mc` |
| Hyp vCPU and hyp VM | `teardown_donated_memory()` into `teardown_mc` |

- `__pkvm_reclaim_dying_guest_page` arguments: handle and gfn only; EL2
  takes the physical address from the guest stage-2 entry in
  `get_valid_guest_pte()`.
- `__pkvm_host_reclaim_page_guest()`, guest state `PKVM_PAGE_OWNED`: page
  zeroed by `hyp_poison_page()`, then unmapped and given to the host.
- `__pkvm_host_reclaim_page_guest()`, guest state `PKVM_PAGE_SHARED_OWNED`:
  not zeroed, then unmapped and given to the host.
- `__pkvm_host_reclaim_page_guest()`, any other guest state,
  `PKVM_PAGE_SHARED_BORROWED` included: `-EPERM`.
- `-EHWPOISON` from `get_valid_guest_pte()`:
  `__pkvm_host_reclaim_page_guest()` turns it into 0, so the host drops its
  pin on a page that was force-reclaimed earlier.
- Host choice: `__pkvm_pgtable_stage2_reclaim()` in `arch/arm64/kvm/pkvm.c`
  walks `pgt->pkvm_mappings`; on success it unpins the page and frees the
  mapping, on failure it warns and keeps both.
- PGD: part of `hyp_vm->pool` since `kvm_guest_prepare_stage2()`; not
  returned by `teardown_donated_memory()`.
- There is no pkvm_pgtable_stage2_destroy here;
  `pkvm_pgtable_stage2_destroy_range()` does the per-range work.

**Features allowed for protected VMs**

- `kvm_pkvm_ext_allowed()`: static inline in
  `arch/arm64/include/asm/kvm_pkvm.h`; there is no kvm_pvm_ext_allowed.

| Capability | Result |
|---|---|
| ten listed in the first `case` group | true for every VM |
| `KVM_CAP_ARM_MTE` | false for every VM |
| `KVM_CAP_ARM_EAGER_SPLIT_CHUNK_SIZE`, `KVM_CAP_ARM_SUPPORTED_BLOCK_SIZES` | false for every VM |
| any other | true if `kvm` is NULL or the VM is not protected |

- `KVM_CAP_ARM_PMU_V3` and `KVM_CAP_ARM_SVE`: not in the listed group, so
  false for a protected VM.
- Protected VM features: the host's bitmap ANDed with `KVM_ARM_VCPU_PSCI_0_2`
  and the two `KVM_ARM_VCPU_PTRAUTH_ADDRESS`, `KVM_ARM_VCPU_PTRAUTH_GENERIC`
  bits; `KVM_ARM_VCPU_PMU_V3` and `KVM_ARM_VCPU_SVE` are dropped.
- Protected VM flags: start at 0 in `init_pkvm_hyp_vm()`;
  `KVM_ARCH_FLAG_MTE_ENABLED` is never copied.
- `KVM_ARCH_FLAG_GUEST_HAS_SVE`: assigned for both kinds of VM from EL2's
  resulting feature bitmap, not copied from the host flags.
- Non-protected VM flags: the host's `arch.flags` with
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED` cleared.
- Non-protected VM, `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS` set: only
  `midr_el1` is copied.
- `arch.vgic.vgic_model`: copied from the host for both kinds, like
  `ctr_el0`.
- There is no fixed_config.h or PVM_ID_AA64PFR0_ALLOW here; protected ID
  registers come from `kvm_init_pvm_id_regs()` in
  `arch/arm64/kvm/hyp/nvhe/sys_regs.c`.
- `kvm_pkvm_ioctl_allowed()`: maps a VM ioctl to a capability with
  `kvm_get_cap_for_kvm_ioctl()` and applies the same list.

## EL2 addresses

**EL2 address space layout**

- Hyp image sections (`__hyp_text_start`, `__hyp_rodata_start`,
  `__hyp_data_start`, `__hyp_bss_start`): part of the linear map, not a
  region of their own. `__hyp_pa()` and `hyp_virt_to_phys()` are valid on a
  hyp symbol; `hyp_create_idmap()` uses that on `__hyp_idmap_text_start`.
- There is no hyp_symbol_addr() and no hyp_create_pcpu_fixmap() here;
  `hyp_create_fixmap()` in `arch/arm64/kvm/hyp/nvhe/mm.c` makes the fixmap
  slots.
- vmemmap: not allocated from the private range. `hyp_create_idmap()` fixes
  `__hyp_vmemmap`, and that address is the upper limit of the private range.
- `__io_map_base`: written once, in `hyp_create_idmap()`. `__io_map_next` is
  the allocation cursor. `pkvm_check_host_ownership()` relies on
  `__io_map_base` staying at the start of the quarter.
- Private range, by who owns the hyp stage-1:

| Owner | Base | Grows | Allocator | Fails with `-ENOMEM` when |
|---|---|---|---|---|
| EL2 (pKVM) | `__io_map_base` | up | `pkvm_alloc_private_va_range()` | end passes `__hyp_vmemmap` |
| host | `io_map_base = hyp_idmap_start` in `kvm_mmu_init()` | down | `hyp_alloc_private_va_range()` in `arch/arm64/kvm/mmu.c` | `BIT(VA_BITS - 1)` flips |

- `hyp_create_idmap()`, `hyp_back_vmemmap()`, `hyp_create_fixmap()`: called
  only on the `__pkvm_init()` path in `arch/arm64/kvm/hyp/nvhe/setup.c`.
- Without pKVM: `__hyp_vmemmap` is never set, so no `struct hyp_page`
  conversion is valid; the host maps the idmap in `kvm_map_idmap_text()`.
- `__hyp_va()` and `hyp_phys_to_virt()`: return an address for any PA. The
  address can be dereferenced only if the hyp stage-1 (`pkvm_pgtable` under
  pKVM) maps that page.
- Unmapped linear VA used as a handle: `__apply_guest_page()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` gets one for a guest page and turns
  it back into a PA with `__hyp_pa()`.

**Host pointer conversion**

- `__kern_hyp_va()`: five instructions, `and`, `ror`, `add`, `add ... lsl 12`,
  `ror`. `kvm_update_va_mask()` has `BUG_ON(nr_inst != 5)`.
- Assembly: there is no kern_hyp_va assembler macro here. The `__ASSEMBLER__`
  part of `arch/arm64/include/asm/kvm_mmu.h` has only `hyp_pa` and
  `hyp_kimg_va`.
- Region bit of the tag: bit `hyp_va_bits - 1`, the complement of that bit in
  `__pa_symbol(__hyp_idmap_text_start)`. `hyp_va_bits` is `kvm_hyp_va_bits()`,
  `max(IDMAP_VA_BITS, vabits_actual)`, not `vabits_actual`.
- Random tag bits: only with `CONFIG_RANDOMIZE_BASE` and
  `tag_lsb != hyp_va_bits - 1`; they fill
  `GENMASK_ULL(hyp_va_bits - 2, tag_lsb)`.
- Call site: `hyp_mode_check()` in `arch/arm64/kernel/smp.c` calls
  `kvm_compute_layout()`, then `kvm_apply_hyp_relocations()`.
- Condition: both run only if `IS_ENABLED(CONFIG_KVM)` and
  `!is_kernel_in_hyp_mode()`. Under VHE neither runs, and `va_mask`,
  `tag_val` stay zero.
- Order: `smp_cpus_done()` calls `hyp_mode_check()` before
  `setup_system_features()`, which reaches `apply_alternatives_all()`.
- Zero tag: when `tag_val` is 0, `kvm_update_va_mask()` keeps the `and` and
  writes NOPs over the other four instructions.
- VHE hyp objects: the asm is inside `#ifndef __KVM_VHE_HYPERVISOR__`, so
  `__kern_hyp_va()` compiles to nothing there. Elsewhere under VHE the five
  instructions are patched to NOPs.
- `__early_kern_hyp_va()` in `arch/arm64/kvm/va_layout.c`: the same
  computation in C. `init_hyp_physvirt_offset()`,
  `kvm_apply_hyp_relocations()` and `kvm_patch_vector_branch()` use it.
- `compute_instruction()` and `__early_kern_hyp_va()` must give the same
  result; `hyp_physvirt_offset` is derived from the C form.

**Converting a pointer twice**

- Unchanged: an address whose bits from `tag_lsb` up already equal `tag_val`.
  That is every hyp linear-map address, hyp image symbols included.
- Changed: an address whose bits from `tag_lsb` up differ from `tag_val`. The
  idmap always differs, because the region bit is the complement of the
  idmap's.
- `__kvm_vcpu_run()` in `arch/arm64/kvm/hyp/nvhe/switch.c`: does
  `kern_hyp_va(vcpu->arch.hw_mmu)`. It does not convert `mmu->arch`.
- `hw_mmu` under pKVM: `init_pkvm_hyp_vcpu()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` sets it to `&hyp_vm->kvm.arch.mmu`, already
  a hyp VA. `pkvm_load_hyp_vcpu()` does not set it.
- `timer_get_offset()` in `include/kvm/arm_arch_timer.h`: applies
  `KERN_HYP_VA()` to `vm_offset`, which `init_pkvm_hyp_vcpu()` points into
  `hyp_vm->host_kvm` for a non-protected vCPU, already converted in
  `handle___pkvm_init_vm()`.
- `kern_hyp_va(vcpu->kvm)`: for a hyp vCPU `vcpu.kvm` is `&hyp_vm->kvm`. Users
  are, for example, `vcpu_has_sve()` and `arch/arm64/kvm/hyp/vgic-v3-sr.c`.
  `arch/arm64/kvm/hyp/nvhe/tlb.c` does not call `kern_hyp_va()`.
- `kern_hyp_va(vcpu->arch.sve_state)`: `pkvm_vcpu_init_sve()` stores the
  converted pointer, and the SVE save and restore paths convert it again.

**Fixmap slots**

- `hyp_fixmap_map()`: returns the slot address plus `offset_in_page(phys)`.
  The PA need not be page-aligned; `__tracing_enable_event()` in
  `arch/arm64/kvm/hyp/nvhe/events.c` passes the PA of a field.
- `fixmap_map_slot()`: makes no test of the old PTE. A map over a live mapping
  retargets the slot with no invalidation and no error.
- `fixmap_map_slot()`: writes the PTE, then `dsb(ishst)`. No TLBI, no `isb()`.
- `fixmap_clear_slot()`: clears `KVM_PTE_VALID`, then `dsb(ishst)`,
  `__tlbi_level(vale2is, addr, level)`, `__tlbi_sync_s1ish_hyp()`, `isb()`.
- `__tlbi_sync_s1ish_hyp()` in `arch/arm64/include/asm/tlbflush.h`: `dsb(ish)`
  plus a repeated TLBI under `ARM64_WORKAROUND_REPEAT_TLBI_SYNC`. A bare
  `dsb(ish)` in its place loses the workaround.
- Attributes: `fixmap_map_slot()` changes only the address bits and
  `KVM_PTE_VALID`. Every mapping has the `PAGE_HYP` attributes that
  `hyp_create_fixmap()` gave the slot, whatever the page is elsewhere.
- Writing a read-only page: `__tracing_enable_event()` uses the fixmap to
  write to hyp rodata, which the linear map has as `PAGE_HYP_RO`.

**Using the fixmap**

- Locks: `hyp_fixmap_map()` takes none, asserts none and checks nothing about
  the PA. What keeps the page in its state is the caller's business.
- `hyp_poison_page()`: both callers hold the host and the guest component
  lock. `__tracing_enable_event()` holds no lock; its page is hyp rodata.
- In-tree pairs: `hyp_poison_page()` and `__apply_guest_page()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`, and `__tracing_enable_event()`.
  `fix_host_ownership_walker()` does not use the fixmap.
- **Unsafe usage**: calling `hyp_fixmap_map()` before `hyp_create_fixmap()`
  has run.
  - Unsafe: in non-protected nVHE, or before `__pkvm_init_finalise()`. The
    slot's `ptep` is NULL and `fixmap_map_slot()` dereferences it.
  - Safe: `hyp_poison_page()`. Its hypercalls are above
    `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`, which `handle_host_hcall()` rejects
    until `kvm_protected_mode_initialized` is set;
    `pkvm_ownership_selftest()` runs after `hyp_create_fixmap()` in
    `__pkvm_init_finalise()`.
  - Safe: `__tracing_enable_event()`, although its hypercall is below
    `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`. Its only host caller,
    `hyp_trace_enable_event()` in `arch/arm64/kvm/hyp_trace.c`, issues it
    only when `is_protected_kvm_enabled()`, and is registered from
    `init_subsystems()`, after `init_hyp_mode()` has run `__pkvm_init`.
- **Potentially unsafe usage**: accessing `PAGE_SIZE` bytes from the returned
  pointer.
  - Unsafe: when the PA is not page-aligned. The pointer includes the offset,
    and the slot maps one page, so the access runs past the slot.
  - Safe: when the PA is page-aligned, as in `hyp_poison_page()`.
    `__pkvm_host_force_reclaim_page_guest()` masks with `PAGE_MASK`;
    `get_valid_guest_pte()` returns `kvm_pte_to_phys()` of a last-level PTE.
- **Unsafe usage**: holding a `hyp_fixblock_map()` mapping and a
  `hyp_fixmap_map()` mapping at once.
  - Unsafe: without `HAS_FIXBLOCK` (`PAGE_SHIFT >= 16`), `hyp_fixblock_map()`
    is `hyp_fixmap_map()` on the same per-CPU slot. The second map retargets
    the first.
  - Safe: one mapping at a time, as in the loop of `__apply_guest_page()`.
- **Potentially unsafe usage**: ending a `hyp_fixblock_map()` with
  `hyp_fixmap_unmap()`.
  - Unsafe: when the map returned `PMD_SIZE`, that is with `HAS_FIXBLOCK`.
    `hyp_fixblock_map()` then returns holding `hyp_fixblock_lock`, which only
    `hyp_fixblock_unmap()` releases; the next `hyp_fixblock_map()` on any CPU
    spins.
  - Safe: when the map returned `PAGE_SIZE`, that is without `HAS_FIXBLOCK`,
    where `hyp_fixblock_map()` took no lock and `hyp_fixblock_unmap()` is
    `hyp_fixmap_unmap()`. `__apply_guest_page()` tests the returned
    `map_size` against `PMD_SIZE` to pick `hyp_fixblock_unmap()` or
    `hyp_fixmap_unmap()`.

## The page allocator

**Per-page metadata**

- `struct hyp_page` has no `flags` field: ownership is the bit-fields
  `__host_state` and `__hyp_state_comp`, used through `get_host_state()`,
  `set_host_state()`, `get_hyp_state()`, `set_hyp_state()`.
- Guest state: not in `struct hyp_page`; it is in PTE software bits, read
  with `pkvm_getstate()`.
- Hyp stage-1 lock: `pkvm_pgd_lock` in `arch/arm64/kvm/hyp/nvhe/mm.c`;
  there is no pkvm_pgtable_lock.
- `set_hyp_state()` after init: reached only through
  `__hyp_set_page_state_range()`, and each of its callers holds
  `host_mmu.lock` as well as `pkvm_pgd_lock`.
- `__host_state` and `__hyp_state_comp`: adjacent 4-bit bit-fields; host
  state writers such as `__pkvm_host_share_ffa()` hold only `host_mmu.lock`.
- `host_share_guest_count`: written in `__pkvm_host_share_guest()` and
  `__pkvm_host_unshare_guest()` with `host_mmu.lock` and the VM's `lock`
  both held; `host_mmu.lock` is the one shared by all VMs.
- `refcount` of a page that is in no pool: not under a pool lock; see
  "Pool locking".
- Size: 8 bytes, enforced by
  `BUILD_BUG_ON(sizeof(struct hyp_page) != sizeof(u64))` inside
  `hyp_phys_to_page()` in `arch/arm64/kvm/hyp/include/nvhe/memory.h`;
  there is no assert next to the struct.
- `STRUCT_HYP_PAGE_SIZE`: generated from
  `arch/arm64/kvm/hyp/hyp-constants.c`.
- `hyp_back_vmemmap()`: in `arch/arm64/kvm/hyp/nvhe/mm.c`; its argument is
  the physical address of the backing memory, not a page count.
- Backing memory: `vmemmap_base`, taken with `hyp_early_alloc_contig()` in
  `divide_memory_pool()`; `recreate_hyp_mappings()` passes it on.
- Backed entries: only the vmemmap pages that cover a `hyp_memory[]` region;
  `hyp_phys_to_page()` makes no range check, so the pointer for any other
  address may be unmapped.
- Guard before dereference: for example `check_range_allowed_memory()` in
  `__host_check_page_state_range()`, `addr_is_memory()` in
  `host_stage2_adjust_range()`.
- There is no hyp_pfn_to_page(); `hyp_phys_to_page()` and
  `hyp_virt_to_page()` are the lookups.

**Page pools**

| Pool | Backs | Pages come from |
|---|---|---|
| `hpool`, static in `arch/arm64/kvm/hyp/nvhe/setup.c` | hyp stage-1 table pages of `pkvm_pgtable`, nothing else | `hyp_pgt_base`, `hyp_s1_pgtable_pages()` pages; pages the early allocator already used are `reserved_pages` |
| `host_s2_pool`, static in `arch/arm64/kvm/hyp/nvhe/mem_protect.c` | host stage-2 table pages of `host_mmu.pgt` | `host_s2_pgt_base`, `host_s2_pgtable_pages()` pages |
| `pool` in `struct pkvm_hyp_vm` | that VM's stage-2 table pages, for protected and non-protected VMs | the PGD donated in `__pkvm_init_vm()`; later, memcache pages freed into it |

- There is no hyp_s1_pool, and `struct host_mmu` has no pool member.
- VM and vCPU structures: host-donated memory from `map_donated_memory()`
  in `arch/arm64/kvm/hyp/nvhe/pkvm.c`, not from `hpool`.
- Guest callbacks such as `guest_s2_get_page()`: find the pool through the
  per-CPU `current_vm`, which is set only between `guest_lock_component()`
  and `guest_unlock_component()`.
- Host stage-2 callers pass `&host_s2_pool` as the memcache argument of
  `kvm_pgtable_stage2_map()`; `host_s2_zalloc_page()` allocates from that
  argument.
- With `CONFIG_NVHE_EL2_DEBUG`: `selftest_vm` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` has a fourth pool, seeded from
  `selftest_base` by `init_selftest_vm()`.
- With `CONFIG_NVHE_EL2_DEBUG`: `pkvm_ownership_selftest()` takes one page
  from `host_s2_pool` that is not a table page.

**Page allocator interface**

- Reference count: set by `hyp_set_page_refcounted()`, not incremented; it
  does `BUG_ON(p->refcount)`, so a free page with a non-zero count is fatal.
- Tail pages of an order > 0 block: `refcount` stays 0 and `order` stays
  `HYP_NO_ORDER` until `hyp_split_page()`.
- Zeroing: done at free time in `__hyp_attach_page()`, for
  `PAGE_SIZE << order` bytes; `hyp_alloc_pages()` has no `memset()`.
- Callers rely on that zeroing: `hyp_zalloc_hyp_page()` and
  `host_s2_zalloc_page()` return the result of `hyp_alloc_pages()`
  unchanged.
- Free-list node inside the page: cleared by `page_remove_from_list()`, so
  the page is all zero when returned.
- `hyp_pool_init()`: pages below `reserved_pages` are not attached by it, so
  they are not zeroed until their first final `hyp_put_page()`.

**Pool locking**

- `get_page` and `put_page` callbacks of the three pools
  (`hpool_get_page()`, `hpool_put_page()`, `host_s2_get_page()`,
  `host_s2_put_page()`, `guest_s2_get_page()`, `guest_s2_put_page()`): call
  `hyp_get_page()` or `hyp_put_page()`, so they take the pool lock.
- `get_page` and `put_page` of `hyp_early_alloc_mm_ops`
  (`arch/arm64/kvm/hyp/nvhe/early_alloc.c`): empty functions; no count is
  changed and no lock is taken.
- Helpers that rely on the caller: `hyp_page_ref_inc()`,
  `hyp_page_ref_dec()`, `hyp_page_ref_dec_and_test()` and
  `hyp_set_page_refcounted()` in
  `arch/arm64/kvm/hyp/include/nvhe/memory.h`, and `hyp_split_page()`.
- Refcount changes without the pool lock; search for `refcount` and the
  helpers above under `arch/arm64/kvm/hyp/nvhe` for the sites:

| Where | Page | What protects the count |
|---|---|---|
| `hyp_pin_shared_mem()`, `hyp_unpin_shared_mem()` | host page shared with hyp, in no pool | `host_mmu.lock` and `pkvm_pgd_lock` |
| `get_pkvm_hyp_vm()`, `put_pkvm_hyp_vm()`, `pkvm_load_hyp_vcpu()`, `pkvm_put_hyp_vcpu()` | page holding the donated `struct pkvm_hyp_vm`, in no pool | `vm_table_lock` |
| `guest_s2_zalloc_page()`, `refcount = 1` | page just popped from the memcache | not yet linked into a table; caller holds the VM's `lock` |
| `reclaim_pgtable_pages()`, `refcount = 0` | page just allocated from the VM pool | sole owner; VM already removed from `vm_table` |
| `hyp_split_page()` | tails of a block just allocated | sole owner |
| `hyp_pool_init()` | every page of the range | pool not yet in use |
| `pkvm_ownership_selftest()`, `init_selftest_vm()` | selftest pages, `CONFIG_NVHE_EL2_DEBUG` only | run from `__pkvm_init_finalise()` |

- Memcache page after `guest_s2_zalloc_page()`: later changes go through
  `guest_s2_get_page()` and `guest_s2_put_page()`, under the VM pool's lock.
- `__hyp_check_page_count_range()`: reads `refcount` under `host_mmu.lock`
  and `pkvm_pgd_lock`; `__pkvm_host_unshare_hyp()` and
  `__pkvm_hyp_donate_host()` return `-EBUSY` when it is non-zero.
- `get_pkvm_unref_hyp_vm_locked()`: reads the VM page's count with
  `hyp_page_count()` under `vm_table_lock`.

**Using the page allocator**

- Pool argument: `hyp_get_page()` and `hyp_put_page()` use the pool passed
  in; nothing derives it from the address and `struct hyp_page` records no
  pool.
- `hyp_page_to_pool()` in `arch/arm64/kvm/hyp/include/nvhe/memory.h`:
  unused, and names a `pool` field that `struct hyp_page` does not have.
- Address argument: any hyp linear-map VA inside the page;
  `arch/arm64/kvm/hyp/pgtable.c` passes `ctx->ptep`.
- `NULL` test: `guest_s2_zalloc_page()` tests the result itself;
  `hyp_zalloc_hyp_page()` and `host_s2_zalloc_page()` do not, and the test
  is in their caller in `arch/arm64/kvm/hyp/pgtable.c`.
- Guest pool callbacks: valid only under `guest_lock_component()`, which
  sets `current_vm`; `kvm_guest_prepare_stage2()` takes it around
  `__kvm_pgtable_stage2_init()` for that reason.
- There is no host_get_page() or host_put_page() at EL2; the host stage-2
  callbacks are `host_s2_get_page()` and `host_s2_put_page()`.
- **Unsafe usage**: `hyp_get_page()` or `hyp_put_page()` on a tail page of
  an order > 0 block that was not split.
  - Unsafe: tails have `refcount` 0, so the put hits `BUG_ON(!p->refcount)`
    in `hyp_page_ref_dec()`.
  - Safe: call `hyp_split_page()` on the head right after allocation, as
    `guest_s2_zalloc_pages_exact()` does; `guest_s2_free_pages_exact()` then
    puts each page.
- **Potentially unsafe usage**: `hyp_put_page()` into a pool whose
  `range_start`..`range_end` does not contain the page.
  - Unsafe: for a block larger than one page; `__hyp_attach_page()` forces
    order 0, so only the first page is zeroed and enters the pool.
  - Safe: for a single hyp-owned page with `refcount` 1, as the memcache
    page from `guest_s2_zalloc_page()` later freed by `guest_s2_put_page()`;
    `__hyp_attach_page()` inserts it at order 0 without coalescing.

## Page ownership state

**Page states**

- `enum pkvm_page_state` is in `arch/arm64/kvm/hyp/include/nvhe/memory.h`.
- The two-bit mask is `PKVM_PAGE_STATE_VMEMMAP_MASK`; there is no
  PKVM_PAGE_STATE_MASK and no PKVM_MODULE_OWNED_PAGE in this tree.

| Value | Host and hyp (`struct hyp_page`) | Guest (stage-2 PTE) |
|---|---|---|
| `PKVM_PAGE_OWNED`, `PKVM_PAGE_SHARED_OWNED`, `PKVM_PAGE_SHARED_BORROWED` | stored | stored in SW0/SW1 of a valid PTE |
| `PKVM_NOPAGE` | stored | inferred: invalid PTE that is not poisoned |
| `PKVM_POISON` (`BIT(2)`) | not used | inferred: invalid PTE of type `KVM_GUEST_INVALID_PTE_TYPE_POISONED` |

- `PKVM_POISON`: the host forcibly reclaimed the page from the guest; only
  `guest_get_page_state()` returns it.
- `PKVM_POISON` does not fit `PKVM_PAGE_STATE_PROT_MASK` or
  `PKVM_PAGE_STATE_VMEMMAP_MASK`; no caller passes it to `pkvm_mkstate()`,
  `set_host_state()` or `set_hyp_state()`.

**State storage and testing**

- All-zero `struct hyp_page`: host sees `PKVM_PAGE_OWNED`, hyp sees
  `PKVM_NOPAGE`, because `get_hyp_state()` XORs `__hyp_state_comp` with
  `PKVM_PAGE_STATE_VMEMMAP_MASK`.
- Hyp stage-1 PTEs: SW bits are not kept in step with the hyp state;
  `pkvm_mkstate()` is called only for guest stage-2 maps, and
  `fix_host_ownership_walker()` in `arch/arm64/kvm/hyp/nvhe/setup.c` is the
  only reader of hyp SW bits.
- Non-memory addresses: have no ownership record at all;
  `host_stage2_set_owner_metadata_locked()` and the `PKVM_ID_HOST` case of
  `host_stage2_set_owner_locked()` return `-EPERM` for them.
- `guest_get_page_state()`: tests `guest_pte_is_poisoned()` before validity, so
  a poisoned entry is `PKVM_POISON`, not `PKVM_NOPAGE`, and fails a
  `__guest_check_page_state_range()` for `PKVM_NOPAGE` with `-EPERM`.
- `__hyp_check_page_state_range()`: has no memory check and no lock assertion
  of its own.
- **Potentially unsafe usage**: `hyp_phys_to_page()`, `get_host_state()`,
  `get_hyp_state()` or `for_each_hyp_page()` on a physical address.
  - Unsafe: when nothing earlier showed the address lies in a `hyp_memory`
    region; `hyp_back_vmemmap()` backs the vmemmap only for those regions.
  - Safe: after `check_range_allowed_memory()`, as
    `__host_check_page_state_range()` and `__pkvm_host_share_guest()` do.
  - Safe: after `addr_is_memory()`, as `host_stage2_get_guest_info()` and
    `check_page_ownership()` in `arch/arm64/kvm/hyp/nvhe/mm.c` do.
  - Safe: `__hyp_check_page_state_range()` after
    `__host_check_page_state_range()` passed on the same range, as in
    `__pkvm_host_donate_hyp()`.
  - Safe: on an address taken from hyp's own allocation, as
    `reclaim_pgtable_pages()` passes to `__pkvm_hyp_donate_host()`, which has
    no hypercall handler.
  - Safe: on memory that `__pkvm_host_donate_hyp()` accepted earlier, as
    `__unmap_donated_memory()` passes to `__pkvm_hyp_donate_host()`.
- **Potentially unsafe usage**: `pkvm_getstate()` directly on a guest PTE.
  - Unsafe: when the PTE may be invalid; an empty or poisoned entry has zero
    SW bits and decodes as `PKVM_PAGE_OWNED`.
  - Safe: after `get_valid_guest_pte()` succeeded, as
    `__pkvm_guest_share_host()` does; it rejects poisoned, invalid and
    non-last-level entries.
  - Safe: through `guest_get_page_state()`.

**Host stage-2 invalid entries**

- There is no kvm_pgtable_stage2_set_owner(), kvm_init_invalid_leaf_owner(),
  KVM_INVALID_PTE_OWNER_MASK or pkvm_host_invalid_pte_type here;
  `kvm_pgtable_stage2_annotate()` in `arch/arm64/kvm/hyp/pgtable.c` writes the
  entry, and the types are `enum kvm_invalid_pte_type` in
  `arch/arm64/include/asm/kvm_pgtable.h`.

| PTE bits | Field | Mask |
|---|---|---|
| 63:60 | type | `KVM_INVALID_PTE_TYPE_MASK` |
| 59:4 | extra metadata | `KVM_HOST_DONATION_PTE_EXTRA_MASK` |
| 3:1 | owner (`enum pkvm_component_id`) | `KVM_HOST_DONATION_PTE_OWNER_MASK` |
| 0 | valid, clear | `KVM_PTE_VALID` |

- Owner and extra masks: defined in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`,
  not in a header.

| Type | Where it appears | Meaning |
|---|---|---|
| `KVM_INVALID_PTE_TYPE_LOCKED` | any stage-2, transient | break-before-make in progress |
| `KVM_HOST_INVALID_PTE_TYPE_DONATION` | host stage-2 | page owned by hyp or a guest |
| `KVM_GUEST_INVALID_PTE_TYPE_POISONED` | guest stage-2 | page forcibly reclaimed by the host |

- `kvm_pgtable_stage2_annotate()`: returns `-EINVAL` for type 0, for
  `KVM_INVALID_PTE_TYPE_LOCKED`, and for an annotation that touches bit 0 or
  bits 63:60.
- `host_stage2_set_owner_metadata_locked()`: returns `-EINVAL` for
  `PKVM_ID_HOST`; on success always sets the host state to `PKVM_NOPAGE`.
- `host_stage2_set_owner_locked()`: accepts only `PKVM_ID_HYP` (annotation with
  zero metadata) and `PKVM_ID_HOST`; `PKVM_ID_GUEST` gets `-EINVAL`.
- `host_stage2_set_owner_locked()` with `PKVM_ID_HOST`: installs a valid
  `PKVM_HOST_MEM_PROT` idmap in place of the annotation and sets
  `PKVM_PAGE_OWNED`; it does not leave a zero entry.
- Guest-owned page: extra metadata from `host_stage2_encode_gfn_meta()`; VM
  handle in metadata bits 15:0 (`KVM_HOST_PTE_OWNER_GUEST_HANDLE_MASK`), gfn in
  bits 55:16 (`KVM_HOST_PTE_OWNER_GUEST_GFN_MASK`).
- `host_stage2_decode_gfn_meta()`: `-EINVAL` for a valid PTE or another type,
  `-EPERM` when the owner is not `PKVM_ID_GUEST`, `-EAGAIN` when
  `get_vm_by_handle()` no longer finds the VM.
- Only `__pkvm_host_force_reclaim_page_guest()` decodes the metadata, through
  `host_stage2_get_guest_info()`; `__pkvm_host_reclaim_page_guest()` takes the
  VM and gfn from its caller.
- Guest page shared back to the host: `__pkvm_guest_share_host()` replaces the
  annotation with a valid mapping, so owner and gfn are in the host stage-2
  only while the host state is `PKVM_NOPAGE`;
  `__pkvm_guest_unshare_host()` writes the annotation again.

**Host stage-2 map**

- Before the first fault the table also holds valid mappings: for each hyp
  text page `fix_host_ownership_walker()` in
  `arch/arm64/kvm/hyp/nvhe/setup.c` installs a page-level
  `KVM_PGTABLE_PROT_R` idmap and sets the host state to `PKVM_NOPAGE`.
- Hyp text is therefore the one case of host state `PKVM_NOPAGE` with a valid
  host PTE instead of an annotation; `check_page_ownership()` in
  `arch/arm64/kvm/hyp/nvhe/mm.c` accepts it when the PTE is not writable.
- `fix_host_ownership()`: walks the hyp linear map of every `hyp_memory`
  region and the per-CPU stacks in the private VA range.
- `KVM_HOST_S2_FLAGS`: `KVM_PGTABLE_S2_AS_S1 | KVM_PGTABLE_S2_IDMAP`; there is
  no KVM_PGTABLE_S2_NOFWB in this tree.
- MMIO is not mapped as device memory at stage-2: `PKVM_HOST_MMIO_PROT` lacks
  `KVM_PGTABLE_PROT_DEVICE`, and with `KVM_PGTABLE_S2_AS_S1`
  `KVM_S2_MEMATTR()` gives `PAGE_S2_MEMATTR(AS_S1)` for every host leaf; MMIO
  differs from memory only in having no execute permission.
- `host_stage2_force_pte_cb()`: MMIO mapped with `PKVM_HOST_MMIO_PROT` is not
  forced to pages and may be a block.
- `host_stage2_force_pte_cb()` on a range that is not wholly inside one
  `hyp_memory` region: compares against `PKVM_HOST_MMIO_PROT`, so
  `PKVM_HOST_MEM_PROT` is forced to pages there.
- Shared and borrowed host pages: mapped with plain `PKVM_HOST_MEM_PROT`, no
  SW bits, state only in `struct hyp_page`; the callback does not force them
  and a `PKVM_PAGE_SHARED_OWNED` page may sit inside a block.
- Annotations: do not consult the callback; `kvm_pgtable_stage2_annotate()`
  sets `force_pte` itself.
- The only prot other than `PKVM_HOST_MEM_PROT` and `PKVM_HOST_MMIO_PROT`
  passed to `host_stage2_idmap_locked()` in this tree is
  `KVM_PGTABLE_PROT_R` for hyp text.

**Host stage-2 faults**

- Faulting address: `FIELD_GET(HPFAR_EL2_FIPA, fault.hpfar_el2) << 12`;
  `HPFAR_MASK` is not used here, and the page offset from `FAR_EL2` is not
  merged in.
- `__get_fault_info()` returns `false` (AT on `FAR_EL2` failed):
  `handle_host_mem_abort()` returns without mapping and the host retries.
- `__get_fault_info()` returns `true` with `HPFAR_EL2_NS` clear, which
  happens when `__fault_safe_to_translate()` is false: `BUG_ON()`.
- `ARM64_WORKAROUND_834220`: `__hpfar_valid()` is false for translation
  faults, so the address comes from `__translate_far_to_hpfar()`.

| `host_stage2_idmap()` result | Handling |
|---|---|
| `0` | return to host |
| `-EEXIST` (leaf already valid) | return to host |
| `-EPERM` (annotated entry) | `host_inject_mem_abort()`, then return |
| anything else, `-EAGAIN` and `-ENOMEM` included | `BUG()` |

- `-EAGAIN` from the map walker never reaches the switch:
  `__host_stage2_idmap()` passes `KVM_PGTABLE_WALK_IGNORE_EAGAIN`.
- There is no __inject_host_exception(); `host_inject_mem_abort()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` calls `inject_host_exception()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`.
- Injected `ESR_EL1`: the `ESR_EL2` value with `ESR_ELx_S1PTW` set and, unless
  the fault came from `PSR_MODE_EL0t`, the EC repainted to
  `ESR_ELx_EC_DABT_CUR` or `ESR_ELx_EC_IABT_CUR`; the FSC is unchanged, so it
  is not a synchronous external abort.
- `inject_host_exception()`: writes `FAR_EL1` only when the FSC is a
  translation fault.
- `is_pkvm_stage2_abort()` in `arch/arm64/mm/fault.c`: tests only
  `is_pkvm_initialized()` and `ESR_ELx_S1PTW`; it does not test the FSC.
- User-mode fault: `do_page_fault()` sends `SIGSEGV` with `SEGV_ACCERR` before
  any VMA lookup.

## Ownership transitions

**Share, donate and reclaim functions**

- There is no struct pkvm_mem_transition, check_share(), check_unshare(),
  check_donation() or __do_share() here; each transition function in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` open-codes its checks, most with
  `__host_check_page_state_range()`, `__hyp_check_page_state_range()` and
  `__guest_check_page_state_range()`.

| Function | Initiator | Before | After |
|---|---|---|---|
| `__pkvm_host_share_ffa()` | host | host `PKVM_PAGE_OWNED` | host `PKVM_PAGE_SHARED_OWNED`; no second side |
| `__pkvm_host_unshare_ffa()` | host | host `PKVM_PAGE_SHARED_OWNED` | host `PKVM_PAGE_OWNED` |
| `__pkvm_host_share_guest()` | host | guest `PKVM_NOPAGE`; each host page `PKVM_PAGE_OWNED`, or `PKVM_PAGE_SHARED_OWNED` with `host_share_guest_count` non-zero and below `U32_MAX` | host `PKVM_PAGE_SHARED_OWNED`, count + 1; guest `PKVM_PAGE_SHARED_BORROWED` |
| `__pkvm_host_unshare_guest()` | host | guest leaf `PKVM_PAGE_SHARED_BORROWED`; host `PKVM_PAGE_SHARED_OWNED`, count non-zero | guest unmapped; count - 1, host `PKVM_PAGE_OWNED` only at 0 |
| `__pkvm_guest_share_host()` | guest | guest `PKVM_PAGE_OWNED`; host `PKVM_NOPAGE` | guest `PKVM_PAGE_SHARED_OWNED`; host `PKVM_PAGE_SHARED_BORROWED` |
| `__pkvm_guest_unshare_host()` | guest | guest `PKVM_PAGE_SHARED_OWNED`; host `PKVM_PAGE_SHARED_BORROWED` | guest `PKVM_PAGE_OWNED`; host `PKVM_NOPAGE`, guest annotation |
| `__pkvm_host_reclaim_page_guest()` | host | guest `PKVM_PAGE_OWNED` (host `PKVM_NOPAGE`) or guest `PKVM_PAGE_SHARED_OWNED` (host `PKVM_PAGE_SHARED_BORROWED`) | guest unmapped; host `PKVM_PAGE_OWNED` |
| `__pkvm_host_force_reclaim_page_guest()` | host | host `PKVM_NOPAGE` with guest annotation; guest `PKVM_PAGE_OWNED` | guest `PKVM_POISON`; host `PKVM_PAGE_OWNED` |

- Host `PKVM_PAGE_SHARED_OWNED` with count 0 (shared with hyp or FF-A):
  `__pkvm_host_share_guest()` returns `-EPERM`.
- Guest-initiated functions: need a valid last-level PTE at the IPA; see
  `get_valid_guest_pte()` for `-ENOENT`, `-E2BIG` and `-EHWPOISON`.
- `__pkvm_guest_share_host()` returning `-ENOENT`: `pkvm_memshare_call()`
  exits to the host as a fake data abort so the page gets faulted in.
- VM kind is enforced by the handlers in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`, not in the transition: share and
  unshare with a guest reject protected VMs,
  `handle___pkvm_host_donate_guest()` rejects non-protected ones.

**Order of checks and updates**

- `__pkvm_host_share_hyp()`: the hyp-side check is unconditional. Of the
  page-state checks, only `assert_host_shared_guest()` is a no-op without
  `CONFIG_NVHE_EL2_DEBUG`.
- `__guest_check_pgtable_memcache()`: explicit check before a guest
  stage-2 map; `-ENOMEM` when `pkvm_memcache.nr_pages` is below
  `kvm_mmu_cache_min_pages()`.
- `__guest_check_pgtable_memcache()` runs after the state checks and before
  the first update, in `__pkvm_host_donate_guest()` and
  `__pkvm_host_share_guest()`.
- `__pkvm_guest_share_host()` and `__pkvm_guest_unshare_host()`: no
  memcache check; `get_valid_guest_pte()` limits them to an existing
  last-level leaf (`-E2BIG` otherwise).
- Checked before the locks in `__pkvm_host_share_guest()`: `prot` within
  `KVM_PGTABLE_PROT_RWX`, `pfn_range_is_valid()`,
  `__guest_check_transition_size()`, `check_range_allowed_memory()`.
- Checked, not asserted, and always the first update of its function:
  - `kvm_pgtable_stage2_unmap()` in `__pkvm_host_unshare_guest()`
  - `kvm_pgtable_stage2_annotate()` in
    `__pkvm_host_force_reclaim_page_guest()`
  - `__host_set_page_state_range()` in `__pkvm_host_share_ffa()` and
    `__pkvm_host_unshare_ffa()`
- `kvm_pgtable_stage2_unmap()` on a guest table is asserted only in
  `__pkvm_host_reclaim_page_guest()`.
- `host_stage2_set_owner_metadata_locked()`: asserted with `WARN_ON()` in
  `__pkvm_host_donate_guest()` and `__pkvm_guest_unshare_host()`.
- `__pkvm_host_reclaim_page_guest()`: the host-side state check is itself
  asserted with `WARN_ON()`, after the guest state has been checked.
- **Unsafe usage**: in a transition function in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`, changing state on either side
  before the last check that can return an error; no transition function
  has an undo path.
  - Safe: check the whole range, then update it in a second pass, as
    `__pkvm_host_share_guest()` does.
  - Safe: make the one fallible update first and return its error, as
    `__pkvm_host_unshare_guest()` does with `kvm_pgtable_stage2_unmap()`.
  - Safe: after the last returning check, wrap every update in
    `WARN_ON()`, as `__pkvm_host_donate_guest()` does.

**Validating physical ranges**

- There is no addr_is_allowed_memory() in this tree.

| Helper | Checks | Leaves unchecked |
|---|---|---|
| `pfn_range_is_valid()` | range lies below `BIT(kvm_phys_shift() - PAGE_SHIFT)` of the host stage-2, without overflow | `nr_pages` of 0 passes; whether it is memory |
| `check_range_allowed_memory()` | start and `end - 1` in one `struct kvm_mem_range`; a memblock region; not `MEMBLOCK_NOMAP` | who owns the pages, including hyp-owned ones |
| `range_is_memory()` | start is memory and `end - 1` is in the same region | `MEMBLOCK_NOMAP` |
| `addr_is_memory()` | one address is in a memblock region | `MEMBLOCK_NOMAP` |

- `check_range_allowed_memory()`: `-EINVAL` when the range leaves its
  region, `-EPERM` when it is not memory or is `MEMBLOCK_NOMAP`.
- `pfn_range_is_valid()`: called by the functions that take `nr_pages`
  with a pfn. `__pkvm_host_share_hyp()`, `__pkvm_host_unshare_hyp()` and
  `__pkvm_host_donate_guest()` do not call it.
- Those three rely on `check_range_allowed_memory()` inside
  `__host_check_page_state_range()`.
- `check_range_allowed_memory()` also runs, under `WARN_ON()`, on the
  address read from a guest PTE: `get_valid_guest_pte()` and
  `__check_host_shared_guest()`.
- `range_is_memory()`: gates `host_stage2_set_owner_locked()` (for
  `PKVM_ID_HOST`) and `host_stage2_set_owner_metadata_locked()` with
  `-EPERM`; `host_stage2_force_pte_cb()` uses it to pick the expected prot.
- `__pkvm_hyp_donate_host()`: `__hyp_check_page_state_range()` runs before
  any memory check; the function has no hypercall handler, EL2 code
  supplies the pfn.

**Mapping sizes for guests**

- Donation to a protected guest: one page only.
  `__pkvm_host_donate_guest()` takes no page count and uses `PAGE_SIZE`.
- `pkvm_pgtable_stage2_map()` in `arch/arm64/kvm/pkvm.c`, protected VM:
  rejects any size but `PAGE_SIZE` and any prot but
  `KVM_PGTABLE_PROT_RWX`, with `WARN_ON_ONCE()` and `-EINVAL`.
- `pkvm_pgtable_stage2_map()`, non-protected VM: accepts `PAGE_SIZE` or
  `PMD_SIZE`.
- `pkvm_mem_abort()` in `arch/arm64/kvm/mmu.c`: always asks for
  `PAGE_SIZE`.
- EL2 size check: `__guest_check_transition_size()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `__guest_check_transition_size()` gets the real `phys` only from
  `__pkvm_host_share_guest()`. `__pkvm_host_unshare_guest()`,
  `__pkvm_host_wrprotect_guest()` and
  `__pkvm_host_test_clear_young_guest()` pass 0, so only the IPA alignment
  is tested there.
- `__pkvm_host_relax_perms_guest()` and `__pkvm_host_mkyoung_guest()`:
  take no size; they pass 0 to `assert_host_shared_guest()`, which accepts
  a leaf of any level.
- Host cap at PMD level: `fault_supports_stage2_huge_mapping()` in
  `arch/arm64/kvm/mmu.c` returns false under `is_protected_kvm_enabled()`
  for any size but `PAGE_SIZE` and `PMD_SIZE`.
- EL2 computes the block as `kvm_granule_size(KVM_PGTABLE_LAST_LEVEL - 1)`;
  the host tests `PMD_SIZE`.

**Forced reclaim and poisoned entries**

- Host decision point: `is_spurious_el1_translation_fault()` in
  `arch/arm64/mm/fault.c`, reached from `__do_kernel_fault()`; it calls
  `pkvm_force_reclaim_guest_page()` in `arch/arm64/kvm/pkvm.c`.
- The host reclaims only when all of these hold:
  - the abort carries `ESR_ELx_S1PTW`, set by `host_inject_mem_abort()`
  - it is an EL1 data abort reported as a translation fault
  - `fixup_exception()` found no fixup; it runs first
  - `AT S1E1R` on the address succeeds, which gives the physical address
- `pkvm_force_reclaim_guest_page()`: 0 and `-EAGAIN` both count as handled
  and the access is retried; any other result ends in
  `die_kernel_fault()`, for which `__do_kernel_fault()` picks the message
  "access to hypervisor-protected memory" when `is_pkvm_stage2_abort()` is
  true and no earlier branch (permission fault, address below `PAGE_SIZE`)
  matched.
- `__pkvm_host_force_reclaim_page_guest()` returns `-EAGAIN` when the
  page's host state is no longer `PKVM_NOPAGE`, or the VM handle is gone.
- `__pkvm_host_force_reclaim_page_guest()` returns `-EPERM` when the
  annotation's owner is not `PKVM_ID_GUEST`, or the guest's state for the
  page is not `PKVM_PAGE_OWNED`.
- Order of updates:
  1. `kvm_pgtable_stage2_annotate()` writes
     `KVM_GUEST_INVALID_PTE_TYPE_POISONED` into the guest entry, with no
     memcache; its error is returned.
  2. `hyp_poison_page()` clears the page.
  3. `host_stage2_set_owner_locked()` with `PKVM_ID_HOST`, asserted.
- Guest's next access: EL2 injects nothing; the stage-2 fault exits to the
  host and reaches `pkvm_mem_abort()`.
- `pkvm_pgtable_stage2_map()`: finds the `struct pkvm_mapping` still in
  the tree and issues the `__pkvm_vcpu_in_poison_fault` hypercall; any
  non-zero result becomes `-EFAULT`, zero becomes `-EAGAIN`.
- `kvm_handle_guest_abort()` returns that `-EFAULT`, which ends `KVM_RUN`.
- `__pkvm_vcpu_in_poison_fault()`: reads the faulting IPA from the vCPU's
  fault registers at EL2, not from the host.
- After a forced reclaim the host keeps its `struct pkvm_mapping` and its
  pin on the page until teardown.

**Clearing reclaimed pages**

- `hyp_poison_page()`: two callers only,
  `__pkvm_host_force_reclaim_page_guest()` and
  `__pkvm_host_reclaim_page_guest()`; it clears with `memset()`.
- A page the host shared with a guest (guest `PKVM_PAGE_SHARED_BORROWED`):
  `__pkvm_host_reclaim_page_guest()` returns `-EPERM`; it leaves through
  `__pkvm_host_unshare_guest()`, which clears nothing.
- `__pkvm_hyp_donate_host()`: does no clearing and no cache maintenance; a
  caller that needs either does it before the call.
- Hypervisor pages, in `arch/arm64/kvm/hyp/nvhe/pkvm.c`:

| Helper | Clears | Cache maintenance |
|---|---|---|
| `unmap_donated_memory()` | `memset()` over `size` | `kvm_flush_dcache_to_poc()` |
| `unmap_donated_memory_noclear()` | no | `kvm_flush_dcache_to_poc()` |
| `teardown_donated_memory()` | `memset()` over `PAGE_ALIGN(size)` | `kvm_flush_dcache_to_poc()` |

- The flush for all three is in `__unmap_donated_memory()`, just before
  `__pkvm_hyp_donate_host()`.
- `teardown_donated_memory()`: after the `memset()` it pushes each page on
  the teardown memcache with `push_hyp_memcache()`, then flushes and
  donates.

## Entering a guest

**The run hypercall**

- Pointer check under pKVM: `__get_host_hyp_vcpus()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c` requires a loaded hyp vCPU whose
  `host_vcpu` equals `kern_hyp_va()` of x1; otherwise both pointers are NULL
  and the run returns `-EINVAL`.
- x1 under pKVM: compared, never dereferenced; host state is reached through
  `hyp_vcpu->host_vcpu`.
- Refusals in `handle___kvm_vcpu_run()`: exactly two, both `-EINVAL`: the
  pointer check above, then (pKVM only) `system_supports_sme()` with non-zero
  `SYS_SVCR`, tested before `flush_hyp_vcpu()`.
- `handle___kvm_vcpu_run()`: has no test of `is_dying` and none of pending
  requests.
- `handle___pkvm_vcpu_load()`: writes no return register, so a refused load
  is not reported; with no hyp vCPU loaded the next run returns `-EINVAL`.
- `handle___vgic_v3_save_aprs()` and `handle___vgic_v3_restore_vmcr_aprs()`:
  `get_host_hyp_vcpus_from_vgic_v3_cpu_if()` applies the same check after
  `container_of()` on the passed `struct vgic_v3_cpu_if`.

**Per-entry flush and sync**

| State | Protected | Non-protected |
|---|---|---|
| `arch.ctxt` on entry | whole struct assigned from host | `__copy_vcpu_state()`, only if host has `PKVM_HOST_STATE_DIRTY` |
| `arch.ctxt` on exit | whole struct assigned to host | only `regs.pc` and `regs.pstate` |

- Everything else in `flush_hyp_vcpu()` and `sync_hyp_vcpu()`: same for both
  kinds.
- vgic on entry, `flush_hyp_vgic_state()`: `vgic_hcr`, `used_lrs` clamped to
  `hyp_gicv3_nr_lr`, and that many `vgic_lr[]`; `vgic_sre` is set to a
  constant, not taken from the host.
- vgic on exit, `sync_hyp_vgic_state()`: `vgic_hcr`, `vgic_vmcr`, and
  `vgic_lr[]` up to the hyp `used_lrs`.
- `arch.ctxt.__hyp_running_vcpu`: set to NULL after the copy;
  `arch/arm64/kvm/hyp/include/hyp/sysreg-sr.h` treats a non-NULL value as
  "this is the host context".
- `flush_debug_state()` with host-owned debug: also copies
  `external_mdscr_el1`, which the world switch loads as MDSCR_EL1.
- `arch.pid`: copied on entry; read by `arch/arm64/kvm/hyp/include/nvhe/trace.h`.
- `fpsimd_sve_sync()`: does nothing unless `guest_owns_fp_regs()`.

**Full register state copy**

- `PKVM_HOST_STATE_DIRTY` and `handle___pkvm_vcpu_sync_state()`: both exist in
  this tree.
- `PKVM_HOST_STATE_DIRTY`: bit 4 of `iflags` in the host's vCPU, defined in
  `arch/arm64/include/asm/kvm_host.h`; set means the host's register copy is
  current and must be flushed to the hyp vCPU.
- Scope: non-protected vCPUs under pKVM only; the host sets it only when
  `!kvm_vm_is_protected()`, EL2 tests it only on the non-protected branch.
- Protected vCPU: whole `arch.ctxt` goes each way on every entry and exit;
  there are no per-exit-class handlers that expose selected registers.
- Host to hyp: `flush_hyp_vcpu()`, when the flag is set.
- Hyp to host: `handle___pkvm_vcpu_sync_state()`, and
  `handle___pkvm_vcpu_put()` when the flag is clear.
- `handle___pkvm_vcpu_sync_state()`: only copies; it does not touch the flag,
  and returns silently with no loaded vCPU or a protected one.
- Host setters, complete list:
  - `kvm_arch_vcpu_run_pid_change()`: set before the hyp vCPU is created.
  - `kvm_arch_vcpu_put()`: set after the `__pkvm_vcpu_put` hypercall.
  - `handle_exit_pkvm_state()` in `arch/arm64/kvm/handle_exit.c`: on
    `ARM_EXCEPTION_TRAP`, `ARM_EXCEPTION_EL1_SERROR` or a pending SError it
    makes the sync hypercall and sets the flag; on any other exit it clears it.
- Register ioctls: make no sync hypercall; they run with the vCPU put
  (`vcpu_load()` is called only in `kvm_arch_vcpu_ioctl_run()`), when the
  host's copy is current.
- `__copy_vcpu_state()`: copies `regs`, the four `spsr_` fields, `fp_regs` and
  `sys_regs[]` from index 1, skipping `CNTVOFF_EL2`, `CNTV_CVAL_EL0`,
  `CNTV_CTL_EL0`, `CNTP_CVAL_EL0`, `CNTP_CTL_EL0`; not
  `__hyp_running_vcpu` or `vncr_array`.
- Flag clear, vCPU loaded (for example after an IRQ exit): the host's
  `arch.ctxt` is stale apart from `regs.pc` and `regs.pstate`; a host write
  to it is not flushed at the next entry and is overwritten at put.

**Load-time versus entry-time state**

| State | Protected | Non-protected | Where |
|---|---|---|---|
| `HCR_TWE`, `HCR_TWI` from x3 | at load | not at load | `handle___pkvm_vcpu_load()` |
| `arch.fgt` | never from host | at load, `memcpy()` from host vCPU | `handle___pkvm_vcpu_load()` |
| `vgic_vmcr`, `vgic_ap0r`, `vgic_ap1r` | at load | at load | `handle___vgic_v3_restore_vmcr_aprs()` |
| `vgic_vmcr`, APRs back to host | at put | at put | `handle___vgic_v3_save_aprs()` |
| register state back to host | every exit | at put, if `PKVM_HOST_STATE_DIRTY` clear; also on the `__pkvm_vcpu_sync_state` hypercall | `sync_hyp_vcpu()` for protected; `handle___pkvm_vcpu_put()` and `handle___pkvm_vcpu_sync_state()` for non-protected |

- State that `flush_hyp_vcpu()` takes from the host: copied on each entry,
  not at load; see "Per-entry flush and sync".
- `handle___pkvm_vcpu_load()`: has no `is_protected_kvm_enabled()` test; its
  id lies above `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`, so `handle_host_hcall()`
  rejects it until `kvm_protected_mode_initialized` is set.
- `arch.fgt`: not copied at init.
- `kvm_arch_vcpu_load()` in `arch/arm64/kvm/arm.c`: runs
  `kvm_vcpu_load_debug()`, `kvm_vcpu_load_fgt()` and the TWE/TWI update before
  the `__pkvm_vcpu_load` hypercall; state computed after the hypercall, such
  as `vcpu->arch.pid`, reaches EL2 only through `flush_hyp_vcpu()`.
- `__vgic_v3_restore_vmcr_aprs`: issued right after `__pkvm_vcpu_load`, so the
  pointer check in "The run hypercall" passes.

**HCR_EL2 for a hyp vCPU**

- At load, `handle___pkvm_vcpu_load()`: `HCR_TWE | HCR_TWI` from the x3
  argument, protected vCPUs only.
- On each entry, `flush_hyp_vcpu()`: `HCR_TWI | HCR_TWE | HCR_VSE` from
  `READ_ONCE(host_vcpu->arch.hcr_el2)`, both kinds.
- `HCR_VI`, `HCR_VF`: not taken from the host.
- `pkvm_vcpu_reset_hcr()`: sets `HCR_FWB` with `ARM64_HAS_STAGE2_FWB`, and
  `HCR_API | HCR_APK` when `vcpu_has_ptrauth()`; `pvm_init_traps_hcr()` sets
  neither.
- `HCR_TID4` in `pkvm_vcpu_reset_hcr()`: also requires the VM's `SYS_CTR_EL0`
  value to equal `read_cpuid(CTR_EL0)`; otherwise `HCR_TID2`.
- VM `ctr_el0`: copied from the host by `pkvm_init_features_from_host()` for
  protected VMs too, so the host picks between `HCR_TID4` and `HCR_TID2`.
- **Unsafe usage**: writing host-supplied bits into a protected hyp vCPU's
  `arch.hcr_el2` outside the two masks above, by assignment, or by an OR
  without a mask.
  - Safe: clear the mask in the hyp value, then OR in the register argument
    under the same mask, as `handle___pkvm_vcpu_load()` does with
    `HCR_TWE | HCR_TWI`.
  - Safe: the same with a single `READ_ONCE()` of `host_vcpu->arch.hcr_el2`,
    as `flush_hyp_vcpu()` does with `HCR_TWI | HCR_TWE | HCR_VSE`; the bits
    set by `pvm_init_traps_hcr()` are outside both masks.

**Other trap registers**

| Register | Protected | Non-protected | Overwritten from host |
|---|---|---|---|
| MDCR_EL2 | `pvm_init_traps_mdcr()` at init | 0 at init | every entry, both kinds, `flush_hyp_vcpu()` |
| HCRX_EL2 | `vcpu_set_hcrx()` on the hyp VM, at init | host's `hcrx_el2`, at init | never |
| FGT registers | no EL2 writer | host's `arch.fgt` | at each load, non-protected only |
| CPTR_EL2 | no stored value | no stored value | never |

- `arch.mdcr_el2` of a protected vCPU: the value from `pvm_init_traps_mdcr()`
  does not survive the first entry; `__activate_traps()` in
  `arch/arm64/kvm/hyp/nvhe/switch.c` writes the host's value.
- Host's `arch.mdcr_el2`: built by `kvm_arm_setup_mdcr_el2()` in
  `arch/arm64/kvm/debug.c`.
- `arch.fgt` of a protected hyp vCPU: stays as zeroed by
  `map_donated_memory()` in `__pkvm_init_vcpu()`;
  `__activate_traps_hfgxtr()` writes it to the registers as it is.
- Host's `arch.fgt`: built by `kvm_vcpu_load_fgt()` in
  `arch/arm64/kvm/config.c`.
- There is no pvm_init_traps_cptr() here; `__activate_cptr_traps()` in
  `arch/arm64/kvm/hyp/include/hyp/switch.h` builds CPTR_EL2 on each entry.
- `pkvm_vcpu_init_traps()`: for a non-protected vCPU it returns after the
  `hcrx_el2` copy, before `pkvm_check_pvm_cpu_features()`.

**Ordering in the world switch**

- Entry order: `__sysreg32_restore_state()`,
  `__sysreg_restore_state_nvhe(guest_ctxt)`, `__load_stage2()`,
  `__activate_traps()`; stage 2 and traps come after the guest EL1 sysregs.
- `ARM64_WORKAROUND_SPECULATIVE_AT`, entry: `__sysreg_restore_el1_state()`
  writes the guest TCR_EL1 with `TCR_EPD0_MASK | TCR_EPD1_MASK` and skips
  SCTLR_EL1; `__activate_traps()` restores SCTLR_EL1 then TCR_EL1 after
  stage 2 is on.
- `ARM64_WORKAROUND_SPECULATIVE_AT`, exit: `__deactivate_traps()` sets the EPD
  bits, then sets `SCTLR_ELx_M`; the host's SCTLR_EL1 and TCR_EL1 come back in
  `__sysreg_restore_el1_state()`.
- `host_ctxt->__hyp_running_vcpu`: set before
  `__sysreg_save_state_nvhe(host_ctxt)`; besides `hyp_panic()`, the helpers in
  `arch/arm64/kvm/hyp/include/hyp/sysreg-sr.h` use it to pick the host branch.
- `___deactivate_traps()`: runs first in `__deactivate_traps()`; it reads
  `HCR_VSE` back from the hardware HCR_EL2 before `write_sysreg_hcr()` loads
  the host value.
- `__fpsimd_save_fpexc32()`: runs after
  `__sysreg_restore_state_nvhe(host_ctxt)`, only if `guest_owns_fp_regs()`.
- `__debug_save_host_buffers_nvhe()`: also disables BRBE and switches
  TRFCR_EL1, before the `dsb(nsh)`.
- There is no kvm_adjust_pc() here; `__kvm_adjust_pc()` runs after the
  `dsb(nsh)` and before the guest sysreg restore.

**Exit handling at EL2**

- `fixup_guest_exit()`: in `arch/arm64/kvm/hyp/nvhe/switch.c`; true re-enters
  the guest, false returns to the host.
- `__fixup_guest_exit()`: in `arch/arm64/kvm/hyp/include/hyp/switch.h`; does
  not save ELR_EL2 into the vCPU PC.
- Guest PC: saved by `__sysreg_save_state_nvhe(guest_ctxt)` after the loop;
  `regs.pstate` is saved on every exit by `synchronize_vcpu_pstate()`.
- There is no early_exit_filter() here; the AArch32 test is inline in
  `fixup_guest_exit()`, before `__fixup_guest_exit()`, on every exit.
- `hyp_exit_handlers`: has no entry for `ESR_ELx_EC_PAC` or
  `ESR_ELx_EC_HVC64`.
- `pvm_exit_handlers` versus `hyp_exit_handlers`:
  - adds `ESR_ELx_EC_HVC64`, `kvm_handle_pvm_hvc64()`;
  - `ESR_ELx_EC_SYS64` is `kvm_handle_pvm_sys64()`;
  - `ESR_ELx_EC_SVE` is `kvm_handle_pvm_restricted()`;
  - has no `ESR_ELx_EC_CP15_32` entry;
  - the remaining entries are the same.
- There is no kvm_handle_pvm_fpsimd here; `ESR_ELx_EC_FP_ASIMD` uses
  `kvm_hyp_handle_fpsimd()` in both tables.
- `kvm_handle_pvm_sys64()`: calls `kvm_hyp_handle_sysreg()` first, then
  `kvm_handle_pvm_sysreg()`.
- `kvm_handle_pvm_sysreg()` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`: register
  not in `pvm_sys_reg_descs` gets UNDEF and re-entry; a descriptor with NULL
  `access` returns to the host; otherwise it is emulated at EL2.
- `kvm_handle_pvm_hvc64()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`: handles four
  KVM vendor calls at EL2 and returns any other function to the host; a
  memory-share call on an unmapped page goes to the host as a faked data
  abort.
- `VCPU_INITIALIZED` on AArch32: cleared in the hyp vCPU's `cflags`;
  `sync_hyp_vcpu()` does not copy `cflags`, and no code under
  `arch/arm64/kvm/hyp/` tests the flag.
- Host on `ARM_EXCEPTION_IL`: `handle_exit()` returns `-EINVAL` with
  `KVM_EXIT_FAIL_ENTRY`.

## Floating point

**Host FP state**

- Names: there is no fpsimd_kvm_prepare(), __fpsimd_save_state(),
  __sve_save_state() or __sve_restore_state() here; hyp code uses
  `fpsimd_save_state()`, `fpsimd_load_state()`, `sve_save_state()`,
  `sve_load_state()`, `fpsimd_save_common()` and `fpsimd_load_common()` from
  `arch/arm64/include/asm/fpsimd.h`, the same helpers the host kernel uses.
- Host SVE buffer: `sve_regs` in `struct kvm_host_data`, of the opaque type
  `struct arm64_sve_state`; there is no struct cpu_sve_state.
- Host values outside the buffer: ZCR_EL1 in `ctxt_sys_reg(hctxt, ZCR_EL1)`,
  FPMR in `ctxt_sys_reg(hctxt, FPMR)`, FPSR and FPCR in `host_ctxt.fp_regs`.
- `sve_save_state()` and `sve_load_state()`: take no vector length; they lay
  the buffer out from `sve_get_vl()`, so the ZCR_EL2 write just before the
  call decides the layout. There is no sve_ffr_offset() here.
- ZCR_EL2 for host state: `sve_vq_from_vl(kvm_host_sve_max_vl) - 1`, not
  `ZCR_ELx_LEN_MASK`; see `__hyp_sve_save_host()` and
  `__hyp_sve_restore_host()`.
- `sve_regs`: already a hyp VA once `finalize_init_hyp_mode()` in
  `arch/arm64/kvm/arm.c` has run, so hyp code dereferences it without
  `kern_hyp_va()`; sized by `pkvm_host_sve_state_size()`.
- Under pKVM the host still saves: `kvm_arch_vcpu_load()` calls
  `kvm_arch_vcpu_load_fp()` unconditionally; the EL2 save is in addition.
- `fpsimd_lazy_switch_to_host()`: saves and restores no FP or SVE register
  contents; it stores the guest's ZCR into the vCPU and rewrites ZCR.
- `fpsimd_lazy_switch_to_host()` ZCR values: with `has_vhe()`, ZCR_EL2 gets
  the vCPU's max; otherwise (nVHE and hVHE) ZCR_EL2 gets the host max and
  ZCR_EL1 the vCPU's max.
- Callers of the two lazy switch functions: `__kvm_vcpu_run_vhe()`, and the
  non-pKVM branch of `handle___kvm_vcpu_run()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`; nVHE `__kvm_vcpu_run()` calls neither.
- pKVM branch of `handle___kvm_vcpu_run()`: calls neither lazy switch
  function; `fpsimd_sve_flush()` and `fpsimd_sve_sync()` bracket the run.
- Protected and non-protected guests under pKVM: both run on
  `hyp_vcpu->vcpu`, and the host save and restore are the same for both.
- Protected VM: cannot have SVE (`kvm_pkvm_ext_allowed()` falls to its
  default case for `KVM_CAP_ARM_SVE`), so for the guest only FPSIMD state is
  ever loaded.
- Non-protected VM with SVE under pKVM: `sve_state` is host memory pinned by
  `pkvm_vcpu_init_sve()`, with the VL capped at `kvm_host_sve_max_vl`.

**Lazy FP and SVE switching**

- `host_data_ptr()` under pKVM: once `kvm_protected_mode_initialized` is set,
  host code resolves it to the `kvm_host_data` instance defined in
  `arch/arm64/kvm/hyp/vhe/switch.c`, while EL2 uses the nVHE instance, so the
  host and EL2 each have their own `fp_owner`.
- Writers of `fp_owner`: `FP_STATE_FREE` only from `arch/arm64/kvm/fpsimd.c`;
  `FP_STATE_HOST_OWNED` only from `fpsimd_sve_flush()` and
  `fpsimd_sve_sync()`; `FP_STATE_GUEST_OWNED` only from
  `kvm_hyp_handle_fpsimd()`.
- Under pKVM every run starts `FP_STATE_HOST_OWNED`, so the guest's first FP
  access in each `__kvm_vcpu_run()` call traps; state carried across entries
  with only a ZCR reprogram exists only without pKVM.
- `pvm_exit_handlers` in `arch/arm64/kvm/hyp/nvhe/switch.c`: routes
  `ESR_ELx_EC_SVE` to `kvm_handle_pvm_restricted()`, which injects an
  undefined exception; only `ESR_ELx_EC_FP_ASIMD` reaches the handler for a
  protected VM.
- `ESR_ELx_EC_SYS64` in the handler: reached only from
  `kvm_hyp_handle_zcr_el2()` in `arch/arm64/kvm/hyp/vhe/switch.c`, which
  discards the handler's return value and returns false itself.
- Trap clearing in the handler: `__deactivate_cptr_traps()` followed by
  `isb()`; there is no cpacr_clear_set() in this tree.
- Guest FPSIMD load: `fpsimd_load_state()`; there is no
  __fpsimd_restore_state() here.
- Last step of the handler: `__activate_cptr_traps()`, after `fp_owner` is
  set; it keeps SVE trapped for a vCPU without SVE and re-applies a guest
  hypervisor's traps.
- No `isb()` follows that last step; the ERET to the guest synchronises.

**Changing FP switching code**

- **Potentially unsafe usage**: touching FP, SVE or ZCR registers at EL2
  without `__deactivate_cptr_traps()` and `isb()` first.
  - Unsafe: while a trap that `__activate_cptr_traps()` set for that register
    may still be in effect, that is until the clearing write is followed by
    `isb()`; the EL2 access traps.
  - Safe: in `kvm_hyp_handle_fpsimd()`, which clears and synchronises before
    its first access.
  - Safe: in `fpsimd_sve_sync()`, which runs after `__deactivate_traps()` and
    issues its own `isb()`.
  - Safe: in `fpsimd_lazy_switch_to_host()` on VHE, where
    `__kvm_vcpu_run_vhe()` issues `isb()` after `__deactivate_traps()`.
  - Safe: in `fpsimd_lazy_switch_to_host()` on nVHE, which acts only when
    `guest_owns_fp_regs()` and touches ZCR only when `vcpu_has_sve()`;
    `__activate_cptr_traps()` leaves neither access trapped in that state.
- **Potentially unsafe usage**: calling `sve_save_state()` or
  `sve_load_state()` without writing ZCR first.
  - Unsafe: when the live VL differs from the VL the buffer was sized for;
    the helpers read `sve_get_vl()` and misplace or overrun the buffer.
  - Safe: host buffer after writing `sve_vq_from_vl(kvm_host_sve_max_vl) - 1`
    to ZCR_EL2, as `__hyp_sve_save_host()` does; `pkvm_host_sve_state_size()`
    defines the size.
  - Safe: guest buffer after setting ZCR_EL2 to `vcpu_sve_max_vq(vcpu) - 1`,
    as `__hyp_sve_restore_guest()` does; `vcpu_sve_state_size()` defines the
    size.
  - Safe: `fpsimd_save_user_state()`, which compares `sve_get_vl()` with the
    bound `sve_vl` before saving.
- **Potentially unsafe usage**: returning to the host with guest-owned SVE
  registers without `fpsimd_lazy_switch_to_host()`.
  - Unsafe: without pKVM, where the host later saves the guest's state;
    `fpsimd_save_user_state()` warns and sends SIGKILL when the live VL is not
    the vCPU's `sve_max_vl`.
  - Safe: under pKVM, where `fpsimd_sve_sync()` saves the guest state and sets
    `FP_STATE_HOST_OWNED` before returning, as `sync_hyp_vcpu()` does.
- **Unsafe usage**: calling `__activate_cptr_traps()` at the end of the
  handler before `fp_owner` is `FP_STATE_GUEST_OWNED`.
  - Safe: set the owner first, as `kvm_hyp_handle_fpsimd()` does;
    `__activate_cptr_traps()` sets the FP trap whenever `guest_owns_fp_regs()`
    is false.
- Host restore: `fpsimd_sve_sync()` is the only restore of what
  `kvm_hyp_save_fpsimd_host()` saved, and tests the same conditions
  (`system_supports_sve()`, `kvm_has_fpmr()`).
- Host save form: chosen by `system_supports_sve()`, a system-wide test; the
  guest load is chosen by `vcpu_has_sve()`.
- `FPEXC32_EL2`: `kvm_hyp_save_fpsimd_host()` and `fpsimd_sve_sync()` do not
  touch it; the guest's value is saved by `__fpsimd_save_fpexc32()` in
  `__kvm_vcpu_run()` when the guest owns the registers.
- SME without pKVM: `kvm_arch_vcpu_load_fp()` only warns on a non-zero
  `SYS_SVCR`.

## The FF-A proxy

**FF-A calls handled at EL2**

- `FFA_MAX_FUNC_NUM`: 0xFF, not 0x7F (`arch/arm64/kvm/hyp/include/nvhe/ffa.h`);
  `is_ffa_call()` does not test the 32-bit/64-bit convention bit.
- `handle_host_smc()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`, before
  `kvm_host_ffa_handler()` runs: clears `ARM_SMCCC_CALL_HINTS` from the id,
  answers `SMCCC_RET_NOT_SUPPORTED` for a non-zero SMC immediate or non-zero
  upper 32 bits of x0, and tries `kvm_host_psci_handler()` first.
- `ffa_call_supported()`: the `switch` compares the whole function id, so the
  32-bit and 64-bit forms of a call are separate entries; for example
  `FFA_MSG_SEND_DIRECT_RESP` is refused and `FFA_FN64_MSG_SEND_DIRECT_RESP`
  is not named.
- `FFA_RXTX_MAP` (32-bit): refused; `FFA_FN64_RXTX_MAP` is the handled form.
- `FFA_MEM_FRAG_TX`: handled by `do_ffa_mem_frag_tx()`; `FFA_MEM_FRAG_RX` is
  the refused one.
- `FFA_ID_GET`: passed through; EL2 has no `case` for it and only issues its
  own in `hyp_ffa_post_init()`.
- `FFA_MSG_SEND2`: not named in `ffa_call_supported()`.
- FF-A 1.2 group on the deny list: `FFA_MSG_SEND_DIRECT_REQ2`,
  `FFA_MSG_SEND_DIRECT_RESP2`, `FFA_CONSOLE_LOG`,
  `FFA_PARTITION_INFO_GET_REGS`; refused whatever version was agreed.
- `FFA_MSG_SEND_DIRECT_REQ2`: there is no do_ffa_direct_msg2() or other EL2
  handler for it here.
- `FFA_MEM_SHARE` and `FFA_MEM_LEND` (32-bit): handled, and re-issued to EL3
  as `FFA_FN64_MEM_SHARE` / `FFA_FN64_MEM_LEND`; `do_ffa_mem_xfer()` has a
  `BUILD_BUG_ON()` that allows only those two ids.

**FF-A version negotiation**

- `hyp_ffa_init()`: offers `FFA_VERSION_1_2` to EL3 and caps
  `hyp_ffa_version` at it.
- Higher or equal minor, not yet negotiated: not refused for its version; if
  `hyp_ffa_post_init()` succeeds the host gets `hyp_ffa_version` and
  negotiation is complete, otherwise it gets `FFA_RET_NOT_SUPPORTED`.
- Lower minor, not yet negotiated: `do_ffa_version()` forwards `FFA_VERSION`
  to EL3; only `FFA_RET_NOT_SUPPORTED` counts as refusal, and the value then
  stored is the host's request, not EL3's answer.
- `hyp_ffa_version`: lowered before `hyp_ffa_post_init()` runs and not
  restored when that fails; the flag stays clear and the host may call again.
- After negotiation: a lower minor gets `FFA_RET_NOT_SUPPORTED`; equal or
  higher gets `hyp_ffa_version`.
- `has_version_negotiated`: written only in `do_ffa_version()`; no other FF-A
  call sets it, they are refused by the gate in `kvm_host_ffa_handler()`.
- `has_version_negotiated` reads: plain read under `version_lock` in
  `do_ffa_version()`; the `smp_load_acquire()` is in
  `kvm_host_ffa_handler()`, with no lock.
- `do_ffa_version()` results: written straight into `a0` (version or
  `FFA_RET_NOT_SUPPORTED`), not through `ffa_to_smccc_error()`.
- `hyp_ffa_init()` returning 0 early (SMCCC older than 1.2, or EL3 answers
  `FFA_RET_NOT_SUPPORTED`): leaves `hyp_ffa_version` 0 and the flag clear;
  `kvm_host_ffa_handler()` has no "FF-A absent" test, so the gate still
  applies.
- **Potentially unsafe usage**: writing `hyp_ffa_version`.
  - Unsafe: once `has_version_negotiated` is set; `__do_ffa_mem_xfer()`,
    `do_ffa_mem_reclaim()` and `do_ffa_part_get()` read it without
    `version_lock`.
  - Safe: under `version_lock` while the flag is clear, before the
    `smp_store_release()`, as `do_ffa_version()` does.
  - Safe: in `hyp_ffa_init()`, while the flag is clear; it runs inside the
    `__pkvm_init` hypercall, before `init_subsystems()` installs EL2 on the
    other CPUs.

**Memory transfer descriptor checks**

- Fragmented transfers (`fraglen` below `len`): accepted; `fraglen > len` and
  `fraglen` above `KVM_FFA_MBOX_NR_PAGES * PAGE_SIZE` are refused, with
  `FFA_RET_INVALID_PARAMETERS`. The rest arrives through
  `do_ffa_mem_frag_tx()`.
- `addr_range_cnt` and `total_pg_cnt`: not read by `__do_ffa_mem_xfer()`; the
  range count comes from `fraglen` and `composite_off`.
- Minimum `fraglen`: `FFA_MEM_REGION_SZ(hyp_ffa_version)` plus
  `ffa_emad_size_get(hyp_ffa_version)`, both in `include/linux/arm_ffa.h`;
  smaller than the `sizeof` of the two structs below `FFA_VERSION_1_2`.
- `ep_mem_offset`: bounded; the result of `ffa_mem_desc_offset()` plus
  `ffa_emad_size_get()` must not exceed `fraglen`, tested in 64 bits before
  `composite_off` is read.
- Also refused with `FFA_RET_INVALID_PARAMETERS`: non-zero x3 or non-zero low
  32 bits of x4, `sender_id` other than `HOST_FFA_ID`, no `host_buffers.tx`.
- `len > ffa_desc_buf.len`: `FFA_RET_NO_MEMORY`; `do_ffa_mem_reclaim()` needs
  the whole descriptor to fit there later.
- `hyp_buffers.tx`: the copy that is checked is also the one EL3 reads; it is
  the buffer `ffa_map_hyp_buffers()` registered. EL3 never sees
  `host_buffers.tx`.
- Not checked in the copy: receiver id, permissions, `attributes`, `flags`,
  `tag`, `handle`. The proxy filters on page ownership.

**Host pages in a transfer**

- `__ffa_host_share_ranges()`: tests `PAGE_ALIGNED(sz | range->address)`, so
  the address as well as the size must be aligned to the kernel `PAGE_SIZE`.
- `__pkvm_host_share_ffa()` in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`: also
  fails for a range beyond the host IPA space (`pfn_range_is_valid()`), and
  for one that is not memory or is `MEMBLOCK_NOMAP`
  (`check_range_allowed_memory()`).
- `ffa_host_share_ranges()`: turns every such failure into `FFA_RET_DENIED`;
  the errno is dropped.
- A page named in two ranges of one descriptor: the second share finds it
  `PKVM_PAGE_SHARED_OWNED` and the whole call gets `FFA_RET_DENIED`.
- Lend and share: identical at EL2; `func_id` is used only as the id of the
  SMC.
- Fragmented first call (`fraglen != len`): succeeds only on
  `FFA_MEM_FRAG_RX` with `a3 == fraglen`; anything else goes to
  `err_unshare`.
- EL3 failure: `ret` stays 0, so EL3's registers reach the host unchanged
  after the unshare.
- Later fragment fails in `do_ffa_mem_frag_tx()`: only that fragment's ranges
  are rolled back; pages of earlier fragments stay
  `PKVM_PAGE_SHARED_OWNED`, because their descriptors are no longer held.
  The `ffa_mem_reclaim()` there tells EL3 to drop the handle; it does not
  touch host page state.

**FF-A feature queries**

- `FFA_FN64_RXTX_MAP` query: forwarded; EL3's minimum size reaches the host
  unchanged. `FFA_RXTX_MAP` query: `FFA_RET_NOT_SUPPORTED`.
- Answered at EL2 with `FFA_SUCCESS` and properties 0: only `FFA_MEM_SHARE`,
  `FFA_FN64_MEM_SHARE`, `FFA_MEM_LEND`, `FFA_FN64_MEM_LEND`. Every other id
  not on the deny list makes `do_ffa_features()` return false, and the query
  is forwarded.
- Calls EL2 handles itself, other than share and lend: their feature query is
  answered by EL3, so the answer does not reflect EL2's own limits; for
  example `do_ffa_rxtx_map()` accepts exactly
  `KVM_FFA_MBOX_NR_PAGES * PAGE_SIZE / FFA_PAGE_SIZE` pages.
- `ffa_call_supported()`: does not look at `hyp_ffa_version`; an id on the
  list is refused at every agreed version.
- New optional interface not implemented at EL2: models have this right; add
  a `case` to `ffa_call_supported()` in `arch/arm64/kvm/hyp/nvhe/ffa.c`.

## Model gaps

### Other mistakes models make

- Models take `guest_lock_component()` to be one of several places that take
  the `lock` of `struct pkvm_hyp_vm`. No other code takes that lock
  (`arch/arm64/kvm/hyp/nvhe/mem_protect.c`).
- Models know of no hypercall that must serve both a trusted and an
  untrusted host. The tracing hypercalls, for example `__tracing_load`, sit
  between `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` and
  `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` in `arch/arm64/include/asm/kvm_asm.h`,
  so `handle_host_hcall()` accepts them with and without pKVM.
- Models take EL2 to donate every host buffer it uses. `__admit_host_mem()`
  in `arch/arm64/kvm/hyp/nvhe/trace.c` skips the donation when
  `!is_protected_kvm_enabled()`.
- Models take a guest share request on an unmapped IPA to return an error to
  the guest. `__pkvm_memshare_page_req()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` rewinds ELR_EL2 by 4 before the exit to
  the host, so the guest executes the HVC again on its next entry.
- Models take `hyp_fixblock_map()` to return the slot base. It returns the
  slot address plus `offset_in_page(phys)`
  (`arch/arm64/kvm/hyp/nvhe/mm.c`).
- Models take HCR_EL2 to be written with `write_sysreg()`. C code under
  `arch/arm64/` uses only `write_sysreg_hcr()` or `sysreg_clear_set_hcr()`
  and assembly uses `msr_hcr_el2`; these carry the barriers for
  `CONFIG_AMPERE_ERRATUM_AC04_CPU_23`.
- Models list no key switch on entry from the host. With
  `CONFIG_ARM64_PTR_AUTH_KERNEL`, `ARM64_HAS_ADDRESS_AUTH` and
  `ARM64_KVM_PROTECTED_MODE`, `__host_exit` saves the host's
  pointer-authentication keys and loads EL2's own from `kvm_hyp_ctxt`;
  `pkvm_hyp_init_ptrauth()` in `arch/arm64/kvm/arm.c` generates them.
- Models take a host stage-2 unmap to need only the page-table update. With
  `ARM64_WORKAROUND_4193714`, `host_stage2_set_owner_metadata_locked()`
  also makes a firmware call through `pkvm_sme_dvmsync_fw_call()`.
- Models take UBSAN to be always off in the nVHE object.
  `nvhe_hyp_panic_handler()` in `arch/arm64/kvm/handle_exit.c` decodes
  UBSAN BRKs under `CONFIG_UBSAN_KVM_EL2` and, under `CONFIG_CFI`, CFI BRKs,
  and both are fatal.
