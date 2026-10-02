- User-space `mrs`: served by `do_emulate_mrs()` -> `emulate_sys_reg()` ->
  `arm64_ftr_reg_user_value()`, not by `read_sanitised_ftr_reg()`; there is no
  emulate_mrs() here.
- `read_sanitised_ftr_reg()` on a register missing from `arm64_ftr_regs`:
  `WARN_ON()` in `get_arm64_ftr_reg()` and returns 0; it does not `BUG_ON()`.
- `arm64_ftr_regs` out of order: `BUG_ON()` at boot in `sort_ftr_regs()`,
  which only `WARN()`s for overlapping or oversized fields.
- Caps whose scope is not `SCOPE_SYSTEM`: `read_scoped_sysreg()` reads the raw
  register with `__read_sysreg_by_encoding()`, so a field with no
  `struct arm64_ftr_bits` entry still matches there and reads 0 only for
  `SCOPE_SYSTEM`.
- `__read_sysreg_by_encoding()`: has its own register switch; a register
  missing from it hits `BUG()`, so a register read through it, for example
  by `has_cpuid_feature()`, needs a `read_sysreg_case()` line as well as the
  `ARM64_FTR_REG()` entry; `SYS_MPAMIDR_EL1` and `SYS_GMID_EL1` have no line.
- Hwcaps: `has_user_cpuid_feature()` returns false unless the field is in
  `user_mask`, so a hwcap matched by it on a `FTR_HIDDEN` field is never set.
- Overrides in `init_cpu_ftr_reg()`: applied per listed field, kept only if
  `arm64_ftr_safe_value()` picks the override; otherwise the field is cleared
  from the `struct arm64_ftr_override` ("ignoring override").
- Overrides on other CPUs and local reads: `__read_sysreg_by_encoding()`
  applies whatever `mask` and `val` remain to the raw value.
- Override of a field with no `struct arm64_ftr_bits` entry: never reaches
  `sys_val`, because `init_cpu_ftr_reg()` walks only listed fields.
- Code that reads the raw register before or outside sanitisation sees no
  override unless it applies it itself: for example
  `arm64_apply_feature_override()` in C, as `cpu_has_bti()` does, or
  `check_override` in assembly.
- Fields the command line can name: only those in the `struct ftr_set_desc`
  tables reached from `regs` in `arch/arm64/kernel/pi/idreg-override.c`;
  `aliases` maps options such as `arm64.nosve` onto them; a filter can set
  other fields, as `pfr0_sve_filter()` does for `id_aa64zfr0_override`.
- Making a register overridable from the command line needs, together: a
  `struct arm64_ftr_override`, `ARM64_FTR_REG_OVERRIDE()` in `arm64_ftr_regs`,
  `PI_EXPORT_SYM()` in `arch/arm64/kernel/image-vars.h`, and a descriptor in
  `regs`.
- Override value: `parse_hexdigit()` accepts one hex digit; `match_options()`
  treats a field as 4 bits wide unless the descriptor sets `width`.
- Parsing time: `init_feature_override()` runs from `early_map_kernel()`,
  after `init_kernel_el` has already run on the boot CPU.
