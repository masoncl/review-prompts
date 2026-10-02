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
