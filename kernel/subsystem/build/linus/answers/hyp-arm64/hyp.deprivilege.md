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
