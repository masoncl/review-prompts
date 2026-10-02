- Scope: the functions in `drivers/irqchip/irq-gic-v5.c`;
  `tools/testing/selftests/kvm/include/arm64/gic_v5.h` has its own functions
  named `gicv5_cpu_enable_interrupts()`, `gicv5_cpu_disable_interrupts()` and
  `gicv5_ppi_priority_init()`, which these bullets do not describe.
- `gicv5_cpu_disable_interrupts()`: the `SYS_ICC_CR0_EL1` write that clears
  EN is followed by `isb()`.
- `gicv5_cpu_enable_interrupts()`: the `SYS_ICC_PCR_EL1` write and the
  `SYS_ICC_CR0_EL1` write that sets EN are its last two writes, with no
  `isb()` after them; the body of `gicv5_starting_cpu()` adds none.
- `gicv5_ppi_priority_init()`: ends with one `isb()`, after all 16 priority
  writes.
- `SYS_ICC_PPI_ENABLER0_EL1` and `SYS_ICC_PPI_ENABLER1_EL1` clears: the
  first `isb()` after them is the one that ends `gicv5_ppi_priority_init()`.
- `SYS_ICC_CR0_EL1` in both functions: read, change `ICC_CR0_EL1_EN_MASK`
  only, write back; the other fields keep their value.
- `SYS_ICC_PCR_EL1`: written whole, not read-modify-write.
- `gicv5_cpu_disable_interrupts()` undoes EN only; PPI enables, PPI
  priorities and `SYS_ICC_PCR_EL1` keep what enable wrote.
- `gicv5_cpu_disable_interrupts()`: its one caller is the `out_int` label of
  `gicv5_init_common()`.
- `out_int` is reached when `gicv5_starting_cpu()` itself fails, as well as
  from later failures, so disable can run when
  `gicv5_cpu_enable_interrupts()` never ran.
- **Potentially unsafe usage**: adding an ICC system register write with no
  `isb()` after it.
  - Unsafe: when later code relies on the write having taken effect and no
    `isb()` runs in between; `gicv5_cpu_enable_interrupts()` has no `isb()`
    after its `gicv5_ppi_priority_init()` call.
  - Safe: before the `gicv5_ppi_priority_init()` call, where the `isb()` that
    ends that function follows it, as for the two enable-register clears.
  - Safe: with its own `isb()` after the write, as in
    `gicv5_cpu_disable_interrupts()` and `gicv5_ppi_irq_mask()`.
