All are in `arch/arm64/kvm/sys_regs.c`; `ID_DESC()` and
`ID_DESC_DEFAULT_CALLBACKS` are the shared body of the first five rows, not
kinds of their own.

| Macro | Guest reads | Userspace write | `val` |
|---|---|---|---|
| `ID_SANITISED(name)` | stored value | only the `.reset` value | 0 |
| `ID_WRITABLE(name, mask)` | stored value | fields in mask | mask |
| `ID_FILTERED(sysreg, name, mask)` | stored value | the setter named `set_` plus name, for example `set_id_aa64pfr0_el1()`, then as `ID_WRITABLE()` | mask |
| `AA32_ID_WRITABLE(name)` | stored value; zero without 32-bit EL0 | low 32 bits; without 32-bit EL0 any value returns 0 and is dropped | `GENMASK(31, 0)` |
| `ID_HIDDEN(name)`, `ID_UNALLOCATED(crm, op2)` | zero | only 0 | 0 |
| `IMPLEMENTATION_ID(reg, mask)` | stored value with `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS`, else the running CPU's | `set_imp_id_reg()` | mask |

- There is no AA32_ID_SANITISED() here; `AA32_ID_WRITABLE()` does that job.
- `aa32_id_visibility()`: tests `kvm_supports_32bit_el0()`, and returns
  `REG_RAZ | REG_USER_WI` when it is false.
- RAZ registers whose `.reset` is `kvm_read_sanitised_id_reg()`: zero comes
  from the stored value, since that `.reset` returns 0; `access_id_reg()`
  does not test `REG_RAZ`.
- `ID_DFR0_EL1`: declared without a macro, with `set_id_dfr0_el1()`,
  `read_sanitised_id_dfr0_el1()` and `aa32_id_visibility()`.
- `set_imp_id_reg()`: a write of the stored value returns 0; another value
  needs the flag (`-EINVAL`), a VM that has not run (`-EBUSY`) and no bit
  outside the mask (`-EINVAL`); it does not call `arm64_check_features()`.
- `ID_SANITISED()` and the other non-RAZ kinds built on `ID_DESC()`: the
  register needs an entry in `arm64_ftr_regs`, or `read_sanitised_ftr_reg()`
  warns and returns 0.
