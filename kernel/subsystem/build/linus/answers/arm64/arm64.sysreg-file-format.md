`R` is the block name, `F` the field name, `P` a prefix.

| Line | Macros emitted |
|---|---|
| `Sysreg R op0 op1 crn crm op2` | `REG_R` (generic `S..._C..._C..._...` name), `SYS_R` (`sys_reg()`), `SYS_R_Op0`, `SYS_R_Op1`, `SYS_R_CRn`, `SYS_R_CRm`, `SYS_R_Op2` |
| `SysregFields X` | none for the line; names inside start `X_` |
| `Field msb[:lsb] F` | `R_F`, `R_F_MASK` (both `GENMASK()`), `R_F_SHIFT`, `R_F_WIDTH` |
| `Enum msb[:lsb] F` | the four `Field` macros |
| `UnsignedEnum` / `SignedEnum` | the four, plus `R_F_SIGNED` as `false` / `true` |
| `0b... NAME` inside an enum | `R_F_NAME` as `UL(0b...)`, unshifted |
| `Res0`, `Res1`, `Unkn` | none per line; bits go to the block's mask |
| `Raz msb[:lsb]` | none; the bits count as described |
| `Fields X`, `Mapping X` | a comment; at `EndSysreg` `R_RES0`, `R_RES1`, `R_UNKN` defined as `(X_RES0)`, `(X_RES1)`, `(X_UNKN)`; no `R_F` names |
| `Prefix P` ... `EndPrefix` | every name in the block gets `P_` in front: `P_R_F`, `P_R_F_MASK`, ..., and `P_R_RES0`, `P_R_RES1`, `P_R_UNKN` at `EndPrefix` |
| `EndSysreg`, `EndSysregFields` | `R_RES0`, `R_RES1`, `R_UNKN` |

- Comment at the top of `arch/arm64/tools/sysreg`: does not list `Raz`,
  `SignedEnum`, `UnsignedEnum` or `Prefix`; the rules in
  `arch/arm64/tools/gen-sysreg.awk` are the authority.
- Field masks: `GENMASK()`; only the RES0, RES1 and UNKN masks use
  `GENMASK_ULL()`.
- `SYS_FIELD_VALUE(reg, field, val)`: the fourth helper, beside
  `SYS_FIELD_GET()`, `SYS_FIELD_PREP()` and `SYS_FIELD_PREP_ENUM()`; it pastes
  `reg##_##field##_##val`.
- Helpers and prefixes: all four paste `reg##_##field`, so for a register
  described with `Fields X` pass `X` as `reg`, and for a `Prefix` field pass
  the prefixed name; `arch/arm64/kvm/vgic/vgic-v5.c` uses
  `FEAT_GCIE_ICH_VMCR_EL2_EN` with `FIELD_GET()` directly.
- Helpers in assembly: not available, they are in the C-only part of
  `arch/arm64/include/asm/sysreg.h`; `.S` code uses `_SHIFT` and `_WIDTH`.
- `_SIGNED`: required by, for example, `__ARM64_CPUID_FIELDS()` in
  `arch/arm64/kernel/cpufeature.c`, `kvm_cmp_feat()` in
  `arch/arm64/include/asm/kvm_host.h` and `__NEEDS_FEAT_3()` in
  `arch/arm64/kvm/config.c`; a plain `Enum` field does not build there.
- `Prefix` coverage: the block must describe 63..0 by itself, and the
  unprefixed lines after `EndPrefix` must describe 63..0 again.
- `Prefix` position: must come before any unprefixed field line of the
  register.
- `Fields` / `Mapping`: must be the only unprefixed line of the block; the
  generator does not check that `X` is defined.
- Enum values: only a repeated value is rejected; completeness and width are
  not checked.
