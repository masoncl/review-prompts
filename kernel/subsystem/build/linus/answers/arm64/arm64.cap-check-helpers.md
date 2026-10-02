- `cpus_have_final_cap()`: `BUG()` until `system_capabilities_finalized()`,
  then `alternative_has_cap_unlikely()`; there is no static key per
  capability in this tree.
- `system_capabilities_finalized()`: becomes true when
  `apply_alternatives_all()` patches `ARM64_ALWAYS_SYSTEM`, not when the
  system caps are detected.
- `.cpu_enable` callbacks at boot: run from `enable_cpu_capabilities()` before
  the matching alternatives pass, so `cpus_have_final_cap()` there hits
  `BUG()`; on a late CPU the same callback runs after the pass.
- `cpus_have_final_boot_cap()`: `BUG()` until `boot_capabilities_finalized()`;
  it checks only `ARM64_ALWAYS_BOOT`, not the scope of the cap passed in.
- `cpus_have_final_boot_cap()` on a cap that is not boot-scope: returns false
  with no `BUG()` between the boot pass and the system pass.
- `system_supports_bti_kernel()`: uses `cpus_have_final_boot_cap(ARM64_BTI)`,
  valid because `CONFIG_ARM64_BTI_KERNEL` makes `ARM64_BTI` a
  `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE`.
- `system_supports_sve()`: calls `alternative_has_cap_unlikely(ARM64_SVE)`
  directly, so it reads false before the system pass and never `BUG()`s.
- Helpers in `arch/arm64/include/asm/cpufeature.h` are not uniform: some
  `BUG()` early instead of reading false, for example `system_supports_bti()`
  and `system_supports_lpa2()` (`cpus_have_final_cap()`), and
  `system_supports_address_auth()` (`cpus_have_final_boot_cap()`).
- `this_cpu_has_cap()`: does not call `cpucap_is_possible()`; it returns false
  when `cpucap_ptrs` has no entry for the cap.
- `this_cpu_has_cap()` before `setup_boot_cpu_features()`: false for every
  cap, because `init_cpucap_indirect_list()` has not filled `cpucap_ptrs`.
- `cpus_have_cap()`: applies `cpucap_is_possible()` only when the argument is
  a compile-time constant.
