- Generic `COND_SYSCALL()`: defined in `kernel/sys_ni.c` as
  `cond_syscall(sys_##name)`; `cond_syscall()` in `include/linux/linkage.h` is
  an assembler weak alias to `sys_ni_syscall()`, with no function body.
- Wrapper architectures (`CONFIG_ARCH_HAS_SYSCALL_WRAPPER`): x86, arm64, riscv,
  s390, and powerpc only `if !SPU_BASE && !COMPAT`.
- What the wrapper's macro must provide: a symbol under the exact name the
  architecture's table macro builds, once for each ABI built in.

| Architecture | Symbol from `COND_SYSCALL(name)` | Kind |
|---|---|---|
| x86 | __x64_sys_name, __ia32_sys_name | `__weak` function, `const struct pt_regs *` |
| arm64 | __arm64_sys_name | `__weak` function, `const struct pt_regs *` |
| riscv | __riscv_sys_name | `__weak` function, `const struct pt_regs *` |
| powerpc | sys_name (no prefix) | `__weak` function, `const struct pt_regs *` |
| s390 | __s390x_sys_name | alias through `cond_syscall()` |

- `__COND_SYSCALL()`: exists on x86 only, in
  `arch/x86/include/asm/syscall_wrapper.h`.
- `COND_SYSCALL_COMPAT()`: x86 defines it only under `CONFIG_COMPAT`; s390 and
  powerpc define none, so the generic alias of compat_sys_name is used there.
- A call listed in every table but defined by some architectures only needs
  the line: `map_shadow_stack` is defined under `arch/x86`, `arch/arm64` and
  `arch/riscv`, and `COND_SYSCALL(map_shadow_stack)` lets the others link.
- No line needed: where the table entry names `sys_ni_syscall` itself, as
  powerpc does for `map_shadow_stack`.
- A number with no selected line: `scripts/syscalltbl.sh` fills it with
  `sys_ni_syscall`; on x86 the `default:` case of `x64_sys_call()` and
  `ia32_sys_call()` returns `-ENOSYS`.
