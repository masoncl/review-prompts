| Form | Where Rt = 31 comes from | Example |
|---|---|---|
| `write_sysreg_s(0, enc)`, `gic_insn(0, insn)` | text `xzr`, no asm operand, taken when `__builtin_constant_p(__val) && __val == 0` | `gicv5_handle_irq()` in `drivers/irqchip/irq-gic-v5.c` |
| `asm volatile(__msr_s(enc, "xzr"))` | text `xzr`, unconditional | `sme_smstart_sm()` in `arch/arm64/include/asm/fpsimd.h` |
| `__tlbi(op)`, which selects `__TLBI_0` | the assembler, from `tlbi <op>` with an empty operand list | `arch/arm64/include/asm/tlbflush.h` |
| fixed word through `__emit_inst()` | 31 written into the constant | `__SYS_BARRIER_INSN()`, `BRB_IALL_INSN`, `SET_PSTATE()` |
| `msr_s` with `xzr` in assembly, for example `msr_s SYS_LORC_EL1, xzr` | text `xzr` | `arch/arm64/include/asm/el2_setup.h` |

- `write_sysreg_s()` in `arch/arm64/include/asm/sysreg.h`: does not use
  `"rZ"`; its non-zero branch binds the value with plain `"r"`.
- `__TLBI_0` and `__TLBI_1`: contain only `ARM64_ASM_PREAMBLE` and the
  mnemonic, no alternative; `__TLBI_1` binds its argument with `"rZ"` and
  `%x0`.
- `gic_insn(v, insn)`: is `write_sysreg_s(v, GICV5_OP_GIC_##insn)`; there is
  no sys_s macro in this tree.
- Barrier words: the names are `SB_BARRIER_INSN`, `GSB_SYS_BARRIER_INSN` and
  `GSB_ACK_BARRIER_INSN`.
- `mrs_s`/`msr_s` register argument: must print as `x0`..`x30`, `w0`..`w30`,
  `xzr` or `wzr`; `__DEFINE_ASM_GPR_NUMS` in
  `arch/arm64/include/asm/gpr-num.h` defines a `.L__gpr_num_` symbol for
  those names only, so the asm operand needs a register constraint, or
  `"rZ"` printed with `%x0` as `write_sysreg_elx()` has.
- **Potentially unsafe usage**: `write_sysreg_s(v, enc)` or `gic_insn(v, insn)`
  for an instruction whose register field must be 31.
  - Unsafe: when `v` is not a zero that `__builtin_constant_p()` sees as
    constant at the macro expansion; the `else` branch binds it with `"r"`,
    Rt is a general register, and the build reports nothing.
  - Safe: a literal `0`, as `gicv5_handle_irq()` passes in
    `gic_insn(0, CDEOI)`; the test in `write_sysreg_s()` then emits `xzr`.
  - Safe: a run-time value for an instruction that takes a register operand,
    as `gicv5_hwirq_eoi()` passes in `gic_insn(cddi, CDDI)`.
- **Potentially unsafe usage**: relying on `"rZ"` with `%x0` to produce XZR.
  - Unsafe: when the instruction requires Rt = 31; `"rZ"` also permits a
    general register that holds zero; `write_sysreg_s()` tests the constant
    itself and prints `xzr` instead.
  - Safe: when any register is acceptable, as in `write_sysreg()`,
    `write_sysreg_hcr()`, `write_sysreg_elx()` and `__TLBI_1`.
