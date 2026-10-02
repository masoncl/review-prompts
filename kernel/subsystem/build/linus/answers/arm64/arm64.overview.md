- Capability bitmaps: there is no cpu_hwcaps; the bitmaps are
  `system_cpucaps` and `boot_cpucaps` in `arch/arm64/kernel/cpufeature.c`.
- `cpucap_ptrs[]`: one `struct arm64_cpu_capabilities` per cpucap number,
  filled from `arm64_features[]` and `arm64_errata[]`; a duplicate number
  is dropped with a `WARN()`.
- `struct arm64_cpu_capabilities` match input depends on scope:
  `read_scoped_sysreg()` reads the sanitised `struct arm64_ftr_reg` only for
  `SCOPE_SYSTEM`; for other scopes it reads the register of the CPU it runs on.
- ELF hwcaps: not bits of `system_cpucaps`. They are separate
  `struct arm64_cpu_capabilities` tables, `arm64_elf_hwcaps[]` and
  `compat_elf_hwcaps[]`, matched by `setup_elf_hwcaps()` into `elf_hwcap`, or
  into `compat_elf_hwcap` and `compat_elf_hwcap2` for compat entries.
- `struct arm64_ftr_reg` mismatch on a secondary, in bits of `strict_mask`:
  `update_cpu_features()` warns and sets `TAINT_CPU_OUT_OF_SPEC`; the CPU
  still comes up.
- Late CPU rejection: done by `verify_local_cpu_capabilities()`, against
  cpucaps, hwcaps, SVE/SME vector lengths, VMID/IPA width and MPAM; the CPU
  ends in `cpu_die_early()`.
- `cpu_panic_kernel()`: reached only from `check_early_cpu_features()`, which
  every secondary runs.
- `struct arm64_ftr_override`: command-line override of ID register fields,
  merged into `sys_val` by `init_cpu_ftr_reg()`; parsed in
  `arch/arm64/kernel/pi/idreg-override.c`.
- Userspace view of an ID register: `arm64_ftr_reg_user_value()`, which
  replaces fields not marked `FTR_VISIBLE`; it is not `sys_val`.
- `mm_context_t`: holds no pointer-auth keys and no MTE state; for POE it
  holds only `pkey_allocation_map`.
- Per-thread, in `struct thread_struct`: `keys_user`, `keys_kernel`,
  `mte_ctrl`, `por_el0`, `sctlr_user`, and the GCS fields.
- With SW PAN: `update_saved_ttbr0()` stores the value in `ttbr0` of
  `struct thread_info`, and `__uaccess_ttbr0_enable()` installs it.
- `init_pg_dir`: visible only to the code in `arch/arm64/kernel/pi/`, which
  is built with every symbol prefixed `__pi_`; `map_kernel()` there maps the
  kernel image and copies the root into `swapper_pg_dir`.
- Fixmap: set up by `early_fixmap_init()` in `arch/arm64/mm/fixmap.c`, not in
  `arch/arm64/mm/mmu.c`.
- `struct pt_regs` `stackframe`: a `struct frame_record_meta`, that is a
  zeroed `struct frame_record` plus a `type`.
- `kernel_entry` sets `type` to `FRAME_META_TYPE_FINAL` on entry from EL0 and
  `FRAME_META_TYPE_PT_REGS` on entry from EL1; the unwinder ends at the first
  and steps through `pt_regs` `pc` at the second.
- `struct kunwind_state` in `arch/arm64/kernel/stacktrace.c`: the kernel
  unwinder's state; it wraps `struct unwind_state`, which is the part shared
  with the hyp unwinders in `arch/arm64/kvm/stacktrace.c` and
  `arch/arm64/kvm/hyp/nvhe/stacktrace.c`.
- `arch_stack_walk_reliable()`: fails the whole unwind at a
  `KUNWIND_SOURCE_REGS_PC` step, so any exception boundary makes it
  unreliable.
- `struct undef_hook` and `register_undef_hook()`: `arch/arm` only; on arm64
  `do_el0_undef()` in `arch/arm64/kernel/traps.c` calls
  `try_emulate_mrs()` and `try_emulate_armv8_deprecated()` directly.
- `struct sys64_hook` in `arch/arm64/kernel/traps.c`: the host's table for
  trapped EL0 system instructions; `struct sys_reg_desc` is KVM-only.
- `struct exception_table_entry`: `fixup_exception()` has one caller,
  `__do_kernel_fault()` in `arch/arm64/mm/fault.c`, and it is skipped for EL1
  instruction aborts; `do_el1_undef()` does no extable lookup.
- `struct secondary_data`: carries `task` to the secondary and `status` back;
  it has no stack field.
- `struct cpu_fp_state` (per-CPU `fpsimd_last_state`): pointers to the storage
  of whichever context is bound to this CPU's FP registers; that may be a
  vCPU's, bound by `kvm_arch_vcpu_ctxsync_fp()`, not `current`'s.
- Kernel-mode FPSIMD is a third owner of the registers: `TIF_KERNEL_FPSTATE`
  with `thread.kernel_fpsimd_state`, a buffer the caller passes to
  `kernel_neon_begin()` and `kernel_neon_end()`.
- `fpsimd_thread_switch()`: saves the outgoing task's kernel-mode state when
  it has `TIF_KERNEL_FPSTATE`, its user state otherwise; it loads only an
  incoming task's kernel-mode state, and otherwise just updates
  `TIF_FOREIGN_FPSTATE`.
- `struct kvm_host_data`: per-CPU; holds the host's `struct kvm_cpu_context`
  (`host_ctxt`) and `fp_owner`, which says whether host, guest or nobody owns
  the FP registers; accessed with `host_data_ptr()`.
- `struct pkvm_hyp_vm` and `struct pkvm_hyp_vcpu`
  (`arch/arm64/kvm/hyp/include/nvhe/pkvm.h`): the hypervisor's own copies of
  `struct kvm` and `struct kvm_vcpu` in protected mode; the host's instances
  are reached through `host_kvm` and `host_vcpu` and are untrusted.
