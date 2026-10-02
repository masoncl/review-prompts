| Pass | Reached from | Caps patched |
|---|---|---|
| `apply_boot_alternatives()` | `smp_prepare_boot_cpu()` -> `setup_boot_cpu_features()` -> `setup_boot_cpu_capabilities()` | `boot_cpucaps` |
| `apply_alternatives_all()` | `smp_cpus_done()` -> `setup_system_features()` -> `setup_system_capabilities()` | complement of `boot_cpucaps` |
| `apply_alternatives_vdso()` | `apply_alternatives_all()`, before `stop_machine()` | all set caps |
| `apply_alternatives_module()` | `module_finalize()` | all set caps |

- Callback alternatives: there is no ARM64_CB_PATCH; an entry carries a real
  cap plus `ARM64_CB_BIT` and is patched in that cap's pass, for example
  `ARM64_ALWAYS_SYSTEM` in the system pass.
- `boot_cpucaps`: only caps whose type has `SCOPE_BOOT_CPU` and that matched
  on the boot CPU.
- Local-scope caps found on the boot CPU, such as errata: set in
  `system_cpucaps` from `setup_boot_cpu_capabilities()`, but patched only by
  `apply_alternatives_all()`; until then `cpus_have_cap()` is true and the
  alternative sequences are still the default.
- Early assembly may contain alternatives: `__cpu_setup()` has
  `alternative_if ARM64_HAS_VA52`; the boot CPU runs the default sequence,
  secondaries and `cpu_resume` run the patched one.
- `__apply_alternatives()`: not `noinstr`; `patch_alternative()`,
  `clean_dcache_range_nopatch()` and `alt_cb_patch_nops()` are.
- System pass: the CPU with `smp_processor_id()` 0 patches; the others spin on
  `all_alternatives_applied` in `__apply_alternatives_multi_stop()`.
- `alternative_is_applied()`: tests `applied_alternatives`, which the kernel
  image and vDSO passes update and module patching does not;
  `cpu_copy_el2regs()` uses it.
- **Potentially unsafe usage**: testing a cap through
  `alternative_has_cap_unlikely()`, `alternative_has_cap_likely()` or a helper
  built on them, on a path that can run before the pass that patches that
  cap.
  - Unsafe: when the path needs the real answer; the test reads false, or
    hits `BUG()` through `cpus_have_final_cap()`.
  - Safe: `cpus_have_cap()`, which reads `system_cpucaps`, as
    `enable_cpu_capabilities()` and `__apply_alternatives()` do.
  - Safe: a boot-scope cap tested after `setup_boot_cpu_features()`, as
    `smp_prepare_boot_cpu()` tests `system_uses_irq_prio_masking()`;
    `apply_boot_alternatives()` has patched `boot_cpucaps` by then.
  - Safe: when false before the pass is the intended answer, as
    `check_local_cpu_capabilities()` uses `system_capabilities_finalized()`
    to choose between updating and verifying.
