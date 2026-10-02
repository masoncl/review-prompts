| Job | Option in this tree | Kconfig |
|---|---|---|
| EL2 assertions, selftest | `CONFIG_NVHE_EL2_DEBUG` | prompt, default n |
| Relax host stage-2 on panic | `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC` | prompt, default n, inside `if NVHE_EL2_DEBUG` |
| pKVM stack traces | `CONFIG_PKVM_STACKTRACE` | default y, depends on `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC` |
| EL2 tracing | `CONFIG_NVHE_EL2_TRACING` | no prompt, default y inside `if NVHE_EL2_DEBUG`, depends on `TRACING && FTRACE` |

- CONFIG_PROTECTED_NVHE_STACKTRACE, CONFIG_PKVM_SELFTESTS and
  CONFIG_PKVM_TRACING are not in this tree.
- BUG file and line, and `%pB` symbol names: printed when
  `nvhe_hyp_panic_host_s2_disabled()` in `arch/arm64/kvm/handle_exit.c` is
  true, which under pKVM needs `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`.
- Checks that exist only under `CONFIG_NVHE_EL2_DEBUG`: two,
  `hyp_assert_lock_held()` in `arch/arm64/kvm/hyp/include/nvhe/spinlock.h`
  and `assert_host_shared_guest()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `assert_host_shared_guest()` callers: `__pkvm_host_relax_perms_guest()`,
  `__pkvm_host_wrprotect_guest()`, `__pkvm_host_test_clear_young_guest()`,
  `__pkvm_host_mkyoung_guest()`; in a normal build these do not check that
  the range is shared by the host.
- Other page-state checks and the `WARN_ON()` calls in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` outside
  `assert_host_shared_guest()` and the selftest: built in all
  configurations.
- `pkvm_ownership_selftest()`: no option of its own and no hypercall; it is
  the last step of `__pkvm_init_finalise()` in
  `arch/arm64/kvm/hyp/nvhe/setup.c`, reached only if every earlier step
  returned 0.
- Selftest timing: inside the `__pkvm_init` hypercall issued by
  `do_pkvm_init()` in `arch/arm64/kvm/arm.c`, before `finalize_pkvm()`.
- `pkvm_selftest_pages()` in `arch/arm64/include/asm/kvm_pkvm.h`: 32 under
  `CONFIG_NVHE_EL2_DEBUG`, else 0; `kvm_hyp_reserve()` adds it to the
  reserved hyp memory and `divide_memory_pool()` carves it out.
- Tracing hypercalls: in `host_hcall[]` in every configuration; without
  `CONFIG_NVHE_EL2_TRACING` the functions they call, for example
  `__tracing_load()`, are stubs in
  `arch/arm64/kvm/hyp/include/nvhe/trace.h`, most returning `-ENODEV`.
- Host side of tracing: `arch/arm64/kvm/hyp_trace.c`, registered by
  `kvm_hyp_trace_init()`.
