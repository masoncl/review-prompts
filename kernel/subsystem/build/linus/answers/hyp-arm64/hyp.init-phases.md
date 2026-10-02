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
