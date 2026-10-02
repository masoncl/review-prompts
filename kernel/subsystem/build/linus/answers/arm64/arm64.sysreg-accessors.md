- `REG_TCR2_EL1` and the other generated `REG_` names with the plain forms:
  the generator emits each as the generic `S<op0>_<op1>_C<crn>_C<crm>_<op2>`
  spelling, which the assembler takes without knowing the register, so
  `read_sysreg()`, `write_sysreg()`, `sysreg_clear_set()` and bare `mrs`/`msr`
  in `.S` files work with it; see `sysreg_clear_set(REG_TCR2_EL1, ...)` in
  `arch/arm64/kernel/cpufeature.c` and `arch/arm64/kernel/hyp-stub.S`.
- `write_sysreg_hcr()`: exists for `CONFIG_AMPERE_ERRATUM_AC04_CPU_23`
  (capability `ARM64_WORKAROUND_AMPERE_AC04_CPU_23`), not for a Cortex
  erratum.
- `write_sysreg_hcr()` with the workaround selected: emits
  `dsb nsh; msr hcr_el2; isb`.
- `write_sysreg_hcr()` selection: a C `if`, true when the config is enabled
  and either `system_capabilities_finalized()` is false or the capability is
  set.
- `write_sysreg_hcr()` otherwise: a bare `msr hcr_el2` with no barrier; the
  caller still supplies any `isb` it needs.
- `sysreg_clear_set_hcr()`: the read-modify-write form; it skips the write,
  and with it both barriers, when the value is unchanged.
- `msr_hcr_el2` (assembly macro in `arch/arm64/include/asm/sysreg.h`): the
  `dsb nsh` depends on the config symbol alone, with no capability test; the
  trailing `isb` is emitted in every configuration.
