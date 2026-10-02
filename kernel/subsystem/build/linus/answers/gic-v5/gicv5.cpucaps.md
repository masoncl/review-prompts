- Types, in `arm64_features[]`:

  | Capability | Type | Matcher |
  |---|---|---|
  | `ARM64_HAS_GICV5_CPUIF` | `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE` | `has_cpuid_feature()` |
  | `ARM64_HAS_GICV5_LEGACY` | `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE` | `test_has_gicv5_legacy()` |

- `ARM64_HAS_GICV5_CPUIF` mismatch on a secondary, in either direction: the
  type has `ARM64_CPUCAP_PANIC_ON_CONFLICT`, so `verify_local_cpu_caps()`
  calls `cpu_panic_kernel()` and the kernel panics; the CPU is not just
  refused.
- `ARM64_HAS_GICV5_LEGACY` on a late CPU: one that lacks it when the system
  has it goes to `cpu_die_early()`; one that has it when the system lacks it
  is allowed.
- `cpus_have_cap(ARM64_HAS_GICV5_LEGACY)` before `setup_system_features()`:
  can read true and later false; `update_cpu_capabilities()` sets the bit on
  the boot CPU and clears it when an early secondary lacks it.
- `cpus_have_cap(ARM64_HAS_GICV5_CPUIF)`: final once
  `setup_boot_cpu_features()` has run, which is before `init_IRQ()`.
- `cpus_have_final_boot_cap()`: valid for `ARM64_HAS_GICV5_CPUIF` after
  `setup_boot_cpu_features()`; no GICv5 code uses it.
- `cpus_have_final_boot_cap(ARM64_HAS_GICV5_LEGACY)`: after
  `setup_boot_cpu_features()` it reads false until `apply_alternatives_all()`,
  because only `SCOPE_BOOT_CPU` capabilities enter `boot_cpucaps`.
- `cpus_have_final_cap()`: tests the same capability bit whatever the scope,
  so it is valid for the local-scope `ARM64_HAS_GICV5_LEGACY`.
- There is no system_supports_gicv5() here; the irqchip driver's test is
  `gicv5_cpuif_has_gcie()` in `drivers/irqchip/irq-gic-v5.c`, which calls
  `this_cpu_has_cap()`.
- `this_cpu_has_cap(ARM64_HAS_GICV5_CPUIF)`: reads the calling CPU's
  `ID_AA64PFR2_EL1` from hardware, not the sanitised value.
- **Unsafe usage**: calling `cpus_have_final_cap()` on either capability
  before `setup_system_features()`, which runs from `smp_cpus_done()`; it
  hits `BUG()`. Irqchip probe and the boot CPU's first
  `gicv5_starting_cpu()` run before that.
  - Safe: `this_cpu_has_cap()` with IRQs off, as `gicv5_starting_cpu()` does
    through `gicv5_cpuif_has_gcie()`; `this_cpu_has_cap()` has no
    finalisation test.
  - Safe: `cpus_have_final_cap()` from KVM init, as `vgic_v5_probe()` does;
    it is reached from `kvm_arm_init()`, a `module_init()` call, after
    `smp_cpus_done()`.
  - Safe: `cpus_have_cap()` inside an alternative callback keyed on
    `ARM64_ALWAYS_SYSTEM`, as `kvm_patch_ich_vtr_el2()` does;
    `setup_system_capabilities()` runs `update_cpu_capabilities()` before
    `apply_alternatives_all()`.
- **Unsafe usage**: calling `this_cpu_has_cap()` from preemptible context; it
  hits `WARN_ON(preemptible())` and returns false without running the
  matcher. Affinity pinning or `migrate_disable()` does not satisfy the test.
  - Safe: with IRQs or preemption disabled, as in `gicv5_starting_cpu()`,
    which runs during `init_IRQ()` and as the `CPUHP_AP_IRQ_GIC_STARTING`
    callback.
  - Safe: from the matcher of a local-scope capability, as
    `can_trap_icv_dir_el1()` does for `ARM64_HAS_GICV5_LEGACY`;
    `setup_boot_cpu_features()` and `check_local_cpu_capabilities()` run
    those matchers with IRQs off on the CPU being probed. A system-scope
    matcher runs from `setup_system_capabilities()`, which is preemptible.
