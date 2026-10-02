- Name: `HAS_BBML3` in `arch/arm64/tools/cpucaps`, so `ARM64_HAS_BBML3`;
  described as "BBM Level 3".
- There is no HAS_BBML2_NOABORT, system_supports_bbml2_noabort(),
  cpu_supports_bbml2_noabort() or has_bbml2_noabort() in this tree;
  `system_supports_bbml3()`, `cpu_supports_bbml3()` and `has_bbml3()` do
  those jobs.
- `cpu_supports_bbml3()` in `arch/arm64/kernel/cpufeature.c`: true when
  `ID_AA64MMFR2_EL1.BBM` is at least `ID_AA64MMFR2_EL1_BBM_3`, or when the
  MIDR is in `supports_bbml3_list`; either is enough.
- `cpu_supports_bbml3()` reads the register with
  `__read_sysreg_by_encoding()`, not the sanitised value; there is no
  command-line option to turn the capability off.
- Type: `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE`, not
  `ARM64_CPUCAP_SYSTEM_FEATURE`; the capability stays set only if every
  early CPU matches.
- Secondary CPU at boot that lacks it: `update_cpu_capabilities()` clears the
  capability; the CPU stays online.
- `linear_map_maybe_split_to_ptes()`: called from `setup_system_features()`;
  runs when `linear_map_requires_bbml3` is set and `system_supports_bbml3()`
  is false.
- `linear_map_split_to_ptes()`: leaves the kernel image alias from
  `lm_alias(_stext)` to `lm_alias(__init_begin)` unsplit.
- Late CPU that lacks it, system has it: `verify_local_cpu_caps()` calls
  `cpu_die_early()`; no panic.
- Late CPU that has it, system lacks it: allowed
  (`ARM64_CPUCAP_PERMITTED_FOR_LATE_CPU`); the capability stays off.
- `split_kernel_leaf_mapping()` first test: returns 0 when
  `linear_map_requires_bbml3` is false or `is_kfence_address()` holds for
  `start`.
- `split_kernel_leaf_mapping()` without `system_supports_bbml3()`:

| State | Result |
|---|---|
| capabilities finalised | returns 0, no split |
| not finalised, `page_alloc_available` false | `WARN_ON()`, `-EBUSY` |
| not finalised, more than one CPU online | `WARN_ON()`, `-EBUSY` |
| not finalised, one CPU online, allocator up | splits |

- `linear_map_requires_bbml3`: set once in `map_mem()` as
  `!force_pte_mapping() && can_set_direct_map()`.
- `arch_add_memory()`: applies `force_pte_mapping()` to hot-added memory too.
