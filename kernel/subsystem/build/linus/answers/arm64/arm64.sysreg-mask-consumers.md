- `INIT_SCTLR_EL2_MMU_ON` in `arch/arm64/include/asm/sysreg.h`: ORs in
  `SCTLR_EL2_RES1` beside the bits it names, as `INIT_SCTLR_EL2_MMU_OFF`
  does.
- Assembly users: `INIT_SCTLR_EL2_MMU_OFF` in `__init_el2_sctlr`
  (`arch/arm64/include/asm/el2_setup.h`), `init_el2`
  (`arch/arm64/kernel/head.S`) and `arch/arm64/kvm/hyp/nvhe/hyp-init.S`;
  `INIT_SCTLR_EL2_MMU_ON` only in `hyp-init.S`; `arch/arm64/kernel/hyp-stub.S`
  uses neither.
- C users: search `_RES0\b|_RES1\b` under `arch/arm64/`; the kinds include
  guest reset values (`EL2_REG(SCTLR_EL2, ..., SCTLR_EL2_RES1)` in
  `arch/arm64/kvm/sys_regs.c`), register values (`VTCR_EL2_FLAGS`,
  `translate_sctlr_el2_to_sctlr_el1()`), writable masks
  (`ID_WRITABLE(..., ~ID_AA64ISAR0_EL1_RES0)`), `FGT_MASKS()` and
  `DECLARE_FEAT_MAP()`.
- Aliased masks: a register described with `Fields X` or `Mapping X` takes its
  masks from `X`, so an edit to `X` changes every such register.
- Hand-written lookalikes: for example `TCR_EL2_RES1`, `CPTR_NVHE_EL2_RES1`,
  `CPTR_NVHE_EL2_RES0`, `CPTR_VHE_EL2_RES0` in
  `arch/arm64/include/asm/kvm_arm.h` and `SYS_PAR_EL1_RES1` in
  `arch/arm64/include/asm/sysreg.h` are not generated; a description edit
  does not change them.
- Tools build: `tools/arch/arm64/tools/Makefile` generates from the same
  `arch/arm64/tools/sysreg`, but `tools/arch/arm64/include/asm/sysreg.h` is a
  separate hand copy of the header, and its `INIT_SCTLR_EL2_MMU_ON` differs.
- Editing a register declared with `DECLARE_FEAT_MAP()` in
  `arch/arm64/kvm/config.c`: a new `Field` needs a map entry, or
  `check_feat_map()` reports the bit; a `Field` turned into `Res0`/`Res1`
  must leave the map.
- Editing a fine-grained trap register: also check `encoding_to_fgt[]` in
  `arch/arm64/kvm/emulate-nested.c`; `aggregate_fgt()` rejects a table bit
  that the generated masks call reserved in the read register and, where the
  group has one, in the write register too.
- `check_feat_map()`: ORs the `bits` of the map entries, skipping
  `FORCE_RESx` entries that overlap the reserved set, and compares with the
  complement of that set; `kvm_err()` prints "Undefined %s behaviour" with
  the differing bits.
- `check_feat_map()` reports: a bit in no entry, and an entry without
  `FORCE_RESx` that names a bit of the reserved set; it does not detect a
  bit named by two entries.
- `check_feature_map()`: returns `void`, so KVM init continues; it checks only
  the descriptors listed in its body.
- Order in `kvm_sys_reg_table_init()`: `populate_nv_trap_config()` runs first,
  and for trap registers the reserved set given to `check_feat_map()` is
  `~(mask | nmask)` from the trap table, not the generated masks.
- `check_fgt_masks()` on masks that do not partition 64 bits: prints
  "Inconsistent masks" with `kvm_info()` and then overwrites `res0` with the
  complement of the other three, so the generated `R_RES0` is replaced and
  init continues.
- Among the failures that stop KVM init with `-EINVAL`: "bit has both
  polarities" from `check_fgt_masks()`, and "FGT bit is reserved" and
  "non_0x18_fgt[%d] is reserved" from `populate_nv_trap_config()`.
