- Document scope: the GICv5 section of `Documentation/arch/arm64/booting.rst`
  has one condition, "entered at EL1 and EL2 is present", plus the line that
  the DT or ACPI tables must describe a GICv5.
- No EL3 item and no requirement on IRS or ITS state is in that section.
- Registers named by the document: `ICH_HFGRTR_EL2`, `ICH_HFGWTR_EL2` and
  `ICH_HFGITR_EL2`; every bit it lists must be 0b1.
- Bit 3 of `ICH_HFGRTR_EL2`: the document lists it as ICC_HAPR_EL1;
  `arch/arm64/tools/sysreg` declares it `Res1`, the tree has no field macro
  for it, and `__init_el2_gicv5` does not set it.
- Every other bit the document lists is in the masks `__init_el2_gicv5`
  writes.
- `__init_el2_gicv5` also writes `ICH_VCTLR_EL2_En` to `SYS_ICH_VCTLR_EL2`;
  the document has no matching item.
- `__init_el2_gicv5` feature test: reads `SYS_ID_AA64PFR2_EL1` from hardware;
  it does not use `check_override`.
- `__init_el2_gicv5` writes: whole-register values, not read-modify-write, so
  any bit not in the mask is written as 0.
- GICv3 compatibility: `__init_el2_gicv5` does nothing for it;
  `__init_el2_gicv3` is a separate macro keyed on `ID_AA64PFR0_EL1.GIC`.
- First EL1 access to a GICv5 register: `test_has_gicv5_legacy()` in
  `arch/arm64/kernel/cpufeature.c` reads `SYS_ICC_IDR0_EL1` from
  `setup_boot_cpu_features()`, before `init_IRQ()`.
- That read happens on the boot CPU when it reports GCIE, whether or not the
  firmware tables describe a GICv5.
