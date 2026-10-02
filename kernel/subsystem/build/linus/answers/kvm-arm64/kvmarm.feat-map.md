- There is no NEEDS_FEAT_FIXED() and no FIXED_VALUE flag here; fixed bits
  are `FORCE_RES0()` and `FORCE_RES1()`.
- Flags that pick RES1 over RES0 when the feature is absent: `AS_RES1`,
  `RES1_WHEN_E2H0`, `RES1_WHEN_E2H1`.
- `REQUIRES_E2H1`: the bits are also reserved when the VM has `FEAT_E2H0`.
- `NEEDS_FEAT()` with three arguments after the bits: `idreg_feat_match()`
  reads `kvm->arch.id_regs[]` directly, so the register must be one stored
  there; anything else needs the predicate form.
- Predicate form: one argument after the bits sets `CALL_FUNC`.
- `DECLARE_FEAT_MAP()` and `DECLARE_FEAT_MAP_FGT()`: wrap a table in a
  `struct reg_feat_map_desc` with a feature for the whole register.
- `get_reg_fixed_bits()`: returns `struct resx`; without the whole-register
  feature every non-RESx bit is RES0. There is no compute_res0_bits().
- `compute_fgu()`: ignores the whole-register feature and `NEVER_FGU`
  entries, ORs RES0 and RES1 results, and overwrites `fgu[group]`.
- Boot check: `check_feature_map()`, called by `kvm_sys_reg_table_init()`
  after `populate_nv_trap_config()`; it is a run-time check.
- `check_feat_map()`: the OR of the entries, leaving out `FORCE_RESx`
  entries that overlap the architectural RESx bits, must equal the non-RESx
  bits exactly, so it reports missing and surplus bits alike.
- Non-RESx bits: for an FGT register `mask | nmask` of its
  `struct fgt_masks`, built from `SR_FGT()` entries; otherwise the
  complement of the register's generated RES0 and RES1 masks, for example
  `~(HCRX_EL2_RES0 | HCRX_EL2_RES1)`.
- Failed check: one `kvm_err()` line; nothing fails.
- New table: nothing registers it; each user names the tables one by one,
  for example `check_feature_map()`, `get_reg_fixed_bits()` and
  `kvm_init_nv_sysregs()`, and for an FGT group `compute_fgu()` and
  `kvm_calculate_traps()`.
