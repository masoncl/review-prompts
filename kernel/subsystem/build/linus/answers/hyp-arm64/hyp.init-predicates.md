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
