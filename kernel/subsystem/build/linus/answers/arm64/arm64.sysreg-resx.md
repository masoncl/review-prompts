- `Raz`: adds to none of the three masks; `kvm_init_nv_sysregs()` in
  `arch/arm64/kvm/nested.c` adds `GENMASK_ULL(8, 4)` by hand for `ZCR_EL2`.
- `Prefix P`: the block gets its own `P_R_RES0`, `P_R_RES1`, `P_R_UNKN`; the
  unprefixed masks restart from `UL(0)` after `EndPrefix`.
- `Res1` lines: the whole description file has three; `SCTLR_EL1_RES1`,
  `SCTLR_EL2_RES1` and `CPACR_EL1_RES1`, for example, are `(UL(0))`.
- Names absent from this tree: there is no NEEDS_FEAT_FIXED, FIXED_VALUE or
  compute_res0_bits; `FORCE_RES0()`, `FORCE_RES1()` and `compute_resx_bits()`
  in `arch/arm64/kvm/config.c` do those jobs, and the result type is
  `struct resx` (`res0`, `res1`).
- Marking in a `struct reg_bits_to_feat_map` entry, as evaluated by
  `compute_resx_bits()`:

| Entry | Bits when the feature is absent |
|---|---|
| `NEEDS_FEAT(bits, feat)` | RES0 |
| `NEEDS_FEAT_FLAG()` with `AS_RES1` | RES1 |
| with `RES1_WHEN_E2H0` | RES1 if the VM has `FEAT_E2H0`, else RES0 |
| with `RES1_WHEN_E2H1` | RES1 if the VM lacks `FEAT_E2H0`, else RES0 |
| with `REQUIRES_E2H1` | the feature also counts as absent when the VM has `FEAT_E2H0` |
| `FORCE_RES0(bits)`, `FORCE_RES1(bits)` | reserved always; no feature is tested |

- Generated masks inside the maps: each non-FGT map ends with
  `FORCE_RES0(R_RES0)` and `FORCE_RES1(R_RES1)`.
- `DECLARE_FEAT_MAP(n, r, m, f)`: `f` is the feature of the whole register;
  when absent, every bit of `~(r##_RES0 | r##_RES1)` becomes RES0.
- `struct fgt_masks`: has `res1` as well as `res0`; `FGT_MASKS()` in
  `arch/arm64/kvm/emulate-nested.c` seeds both from the generated masks.
