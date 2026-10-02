- `WARN_ON()` has no nVHE definition: nVHE code gets the generic one in
  `include/asm-generic/bug.h`, with `__WARN_FLAGS()` from
  `arch/arm64/include/asm/bug.h`; there is no __hyp_bug mechanism.
- `nvhe_hyp_panic_handler()` in `arch/arm64/kvm/handle_exit.c`: does not call
  `report_bug()` and never resumes; it uses `find_bug()` and
  `bug_get_file_line()` for the message, then `panic()`.
- File and line lookup: done only when `nvhe_hyp_panic_host_s2_disabled()` is
  true, that is without protected KVM or with
  `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`; otherwise only the address is printed.
- `CONFIG_BUG` off: `WARN_ON()` only evaluates its condition and execution
  continues, so the `return` after it is the only handling; `BUG()` is still a
  `brk`.
- Files built for both hyp and the kernel, for example
  `arch/arm64/kvm/hyp/pgtable.c` (`pgtable.o` in `arch/arm64/kvm/hyp/Makefile`
  and in `hyp-obj-y`): in the kernel build `WARN_ON()` warns and continues, so
  `if (WARN_ON(x)) return ...;` there needs a correct return value.
