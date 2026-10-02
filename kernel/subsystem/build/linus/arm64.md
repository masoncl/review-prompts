# ARM64 Architecture Code

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

| Job | File in this tree | Not in this tree / easy to miss |
|---|---|---|
| FP/SIMD, SVE, SME low-level save and restore | `arch/arm64/include/asm/fpsimd.h`: `static inline` functions with inline asm, e.g. `fpsimd_save_state()`, `sve_save_state()`, `sme_save_state()` | There is no entry-fpsimd.S and no fpsimdmacros.h. `arch/arm64/kvm/hyp/` has no fpsimd.S either; KVM calls the same FPSIMD and SVE inlines |
| FP/SIMD, SVE, SME state | `arch/arm64/kernel/fpsimd.c` | There is no sve_set_vector_length(); `vec_set_vector_length()` does that job |
| Exception entry in C | `arch/arm64/kernel/entry-common.c` holds the arm64 wrappers, e.g. `arm64_enter_from_user_mode()`, `arm64_exit_to_kernel_mode()` | `enter_from_user_mode()` and the `irqentry_` helpers they call are generic: `include/linux/irq-entry-common.h`, `kernel/entry/common.c`. `arch/arm64/Kconfig` selects `GENERIC_IRQ_ENTRY`, not `GENERIC_ENTRY` or `GENERIC_SYSCALL`. Arch hooks: `arch/arm64/include/asm/entry-common.h` |
| MTE swap tag storage | `arch/arm64/mm/mteswap.c` | Holds swap save/restore; synchronous tag check faults are handled by `do_tag_check_fault()` in `arch/arm64/mm/fault.c` |
| TLB invalidation | `arch/arm64/include/asm/tlbflush.h` | Out of line: under `CONFIG_ARM64_ERRATUM_4193714` and with `ARM64_WORKAROUND_4193714`, `__tlbi_sync_s1ish()` reaches `sme_do_dvmsync()` in `arch/arm64/kernel/fpsimd.c` |
| Early position-independent boot code | `arch/arm64/kernel/pi/` | `arch/arm64/kernel/pi/relacheck.c` is a host program, not kernel code. Symbols get a `__pi_` prefix from objcopy in `arch/arm64/kernel/pi/Makefile`: `arch/arm64/kernel/head.S` calls `__pi_early_map_kernel`, defined as `early_map_kernel()`. `PI_EXPORT_SYM()` in `arch/arm64/kernel/image-vars.h` makes a kernel symbol visible to PI code, for example `swapper_pg_dir` |
| Instruction patching header | `arch/arm64/include/asm/text-patching.h` | |

## Exception entry

**C entry and exit sequence**

- `arch/arm64/Kconfig` selects `GENERIC_IRQ_ENTRY` only, not `GENERIC_ENTRY`:
  the helpers are arm64's own, built from pieces of
  `include/linux/irq-entry-common.h`.
- arm64 calls neither `irqentry_enter()` nor `irqentry_exit()`.

| Case | arm64 helper | Built on |
|---|---|---|
| from kernel | `arm64_enter_from_kernel_mode()` | `irqentry_enter_from_kernel_mode()` |
| to kernel | `arm64_exit_to_kernel_mode()` | picks by `regs_irqs_disabled(regs)` |
| to kernel, may preempt | `arm64_exit_to_kernel_mode_preempt()` | `irqentry_exit_to_kernel_mode_preempt()` |
| to kernel, last step | `__arm64_exit_to_kernel_mode()` | `irqentry_exit_to_kernel_mode_after_preempt()` |
| to user | `arm64_exit_to_user_mode()` | `irqentry_exit_to_user_mode_prepare()`, `exit_to_user_mode()` |
| NMI | none | `irqentry_nmi_enter()`, `irqentry_nmi_exit()` |
| EL1 debug | `arm64_enter_el1_dbg()`, `arm64_exit_el1_dbg()` | open-coded |

- arm64_enter_nmi and arm64_exit_nmi do not exist; `__el1_pnmi()` and
  `el1h_64_error_handler()`, for example, call the generic NMI pair directly.
- exit_to_user_mode_prepare and exit_to_user_mode_prepare_legacy are defined
  nowhere; arm64 has no `do_notify_resume()`; pending work runs in
  `exit_to_user_mode_loop()` in `kernel/entry/common.c`.
- `local_daif_mask()`: done inside `__arm64_exit_to_kernel_mode()` and
  `arm64_exit_to_user_mode()`; a handler such as `el1_abort()` goes from
  `do_mem_abort()` straight into the exit helper.
- `irqentry_nmi_exit()` does not mask; `__el1_pnmi()` calls
  `local_daif_mask()` before it.
- Preemption on return to kernel: also after synchronous exceptions, since
  `arm64_exit_to_kernel_mode()` takes the preempt variant when the
  interrupted context had IRQs enabled.
- `__el1_irq()` calls `arm64_exit_to_kernel_mode_preempt()` directly.
- `instrumentation_begin()`: not used anywhere under `arch/arm64`; `noinstr`
  handlers call instrumentable `do_*()` functions directly between the
  helpers.
- **Potentially unsafe usage**: clearing DAIF bits before the enter helper.
  - Unsafe: clearing I or F on an entry from EL0 before
    `enter_from_user_mode()`; a nested IRQ reaches
    `irqentry_enter_from_kernel_mode()`, which calls `ct_irq_enter()` only
    for the idle task or `arch_in_rcu_eqs()`.
  - Safe: clearing only D and A with a raw `write_sysreg()`, as
    `el1_interrupt()` does with `DAIF_PROCCTX_NOIRQ`; debug and SError
    entries use `arm64_enter_el1_dbg()` and `irqentry_nmi_enter()`, which
    call `ct_nmi_enter()`.

**User-mode path obligations**

- `arm64_enter_from_user_mode()`: `enter_from_user_mode()`, then
  `rseq_note_user_irq_entry()`, `mte_disable_tco_entry()`,
  `sme_enter_from_user_mode()`.
- `arm64_syscall_enter_from_user_mode()`: the same without
  `rseq_note_user_irq_entry()`; it unmasks nothing and does no syscall work.
- `el0_svc()` unmasks with `local_daif_restore(DAIF_PROCCTX)` after
  `fpsimd_syscall_enter()`.
- `sme_enter_from_user_mode()` and `sme_exit_to_user_mode()`: called by both
  enter and both exit helpers; they act only with
  `ARM64_WORKAROUND_4193714` and `TIF_SME`; see
  `arch/arm64/include/asm/fpsimd.h`.
- Syscall exit: `arm64_syscall_exit_to_user_mode()`, which calls
  `syscall_exit_to_user_mode_prepare()`; arm64 does not call
  `syscall_exit_to_user_mode()`.
- `ret_from_fork` also exits through `arm64_syscall_exit_to_user_mode()`,
  via `asm_exit_to_user_mode()`.
- `fpsimd_syscall_enter()`: static in `arch/arm64/kernel/entry-common.c`,
  called from `el0_svc()` only; `el0_svc_compat()` does not call it.
- `fpsimd_syscall_enter()` leaves streaming mode with `sme_smstop_sm()` and
  keeps ZA; with `TIF_SVE` it calls `sve_flush_live()`.
- `arm64_syscall_exit_to_user_mode()` ends with `exit_to_user_mode()`, so
  `fpsimd_syscall_exit()`, which `el0_svc()` calls after it, runs after
  `exit_to_user_mode()`.
- rseq fixup: there is no rseq_handle_notify_resume; `TIF_RSEQ` is
  `TIF_NOTIFY_RESUME` on arm64, and `resume_user_mode_work()` calls
  `rseq_handle_slowpath()`.
- `rseq_exit_to_user_mode_restart()`: a stub returning `false` without
  `CONFIG_GENERIC_ENTRY`, which arm64 does not select.
- rseq on exit: `rseq_irqentry_exit_to_user_mode()` or
  `rseq_syscall_exit_to_user_mode()`, from the two prepare functions;
  neither does a fixup. The first clears `current->rseq.event.events`, the
  second does so only under `CONFIG_LOCKDEP`.
- **Unsafe usage**: `arm64_syscall_enter_from_user_mode()` or
  `fpsimd_syscall_enter()` on an EL0 path that is not an SVC.
  - Unsafe: `user_irq` stays clear, and for an `rseq_v2()` task
    `rseq_sched_switch_event()` acts only on `user_irq` or `ids_changed`
    and `rseq_signal_deliver()` only on `user_irq`; live SVE and streaming
    state is discarded.
  - Safe: `arm64_enter_from_user_mode()` for every other EL0 exception, as
    `el0_da()` and `el0_interrupt()` do.

**Assembly entry state**

- `kernel_ventry` for EL0: only recovers x30 from `tpidrro_el0` (64-bit) or
  zeroes it (32-bit), and only when entered through `tramp_ventry`;
  Spectre-BHB mitigation is in `tramp_ventry`.
- `kernel_entry` writes no PAN, UAO, BTI or MTE tag-check control; its only
  PSTATE write is `SET_PSTATE_DIT(1)`, for `\el == 0` under `ARM64_HAS_DIT`.
- Also EL0 only, for example: `NO_SYSCALL` stored at `S_SYSCALLNO`, and
  `FRAME_META_TYPE_FINAL` instead of `FRAME_META_TYPE_PT_REGS`.
- Shadow call stack on EL0 entry: `scs_load_current_base`, not
  `scs_load_current`; x18 restarts at the task's SCS base.
- SW PAN from EL0: `__swpan_entry_el0` always runs
  `__uaccess_ttbr0_disable`.
- SW PAN from EL1: `__swpan_entry_el1` disables TTBR0 only if it was
  enabled, and records which in `PSR_PAN_BIT` of the saved SPSR.
- State installed only for `\el == 0` stays current for EL1 entries because
  `cpu_switch_to()` switches it: `sp_el0`, the kernel PAC key
  (`ptrauth_keys_install_kernel`) and x18.
- Per-task kernel state added to the EL0 branch needs the same at context
  switch.
- `__sdei_asm_handler`: does not use `kernel_entry`; it reloads `sp_el0`
  from `__entry_task` and switches stacks, and performs none of the other
  EL0 entry steps.
- Writes sharing the one `isb`: `SYS_APIAKEYLO_EL1` and `SYS_APIAKEYHI_EL1`
  from `__ptrauth_keys_install_kernel_nosync`, the `SCTLR_ELx_ENIA` write
  to `sctlr_el1`, and `SYS_GCR_EL1` from `mte_set_kernel_gcr`; that `isb`
  is patched in only under `ARM64_MTE` or `ARM64_HAS_ADDRESS_AUTH`.
- `disable_step_tsk` and `__uaccess_ttbr0_disable` carry their own `isb`.
- The EL1 path of `kernel_entry` has no `isb` outside `__swpan_entry_el1`;
  a new write needed for EL1 entries must synchronise itself.

**Stack overflow detection**

- `THREAD_ALIGN`: `2 * THREAD_SIZE` unconditionally, in
  `arch/arm64/include/asm/memory.h`.
- The check has no `#ifdef` and no `.if \el`; `arch/arm64/Kconfig` selects
  `VMAP_STACK` unconditionally.
- It is in every `kernel_ventry`, including the copies in
  `__bp_harden_el1_vectors`.
- The property is alignment and size, not the allocator: the init task
  stack is placed by `RW_DATA(..., THREAD_ALIGN)` in
  `arch/arm64/kernel/vmlinux.lds.S`.
- `IRQ_STACK_SIZE` and `SDEI_STACK_SIZE` both equal `THREAD_SIZE`.
- Bit `THREAD_SHIFT` of SP set: `kernel_ventry` first moves SP to the top of
  `overflow_stack` and range-tests the old SP against
  `OVERFLOW_STACK_SIZE`.
- Old SP in range: SP and x0 are restored and the normal handler runs.
- Old SP out of range: `__bad_stack`, then `handle_bad_stack()`.
- `overflow_stack` is only `__aligned(16)`, so the bit is arbitrary there.
  SP below the overflow stack is caught only if the bit happens to be set;
  `__bad_stack` then restarts from the top of the overflow stack.
- `panic_bad_stack()`: calls `nmi_panic()`, then `cpu_park_loop()`.
- **Potentially unsafe usage**: SP on a stack whose base is not
  `THREAD_ALIGN`-aligned, or that is larger than `THREAD_SIZE`.
  - Unsafe: while an exception can enter through `kernel_ventry`; a valid SP
    can have bit `THREAD_SHIFT` set and end in `__bad_stack`, or an overflow
    can leave it clear.
  - Safe: allocated with `arch_alloc_vmap_stack()` and at most
    `THREAD_SIZE`, as `init_irq_stacks()` does.
  - Safe: `overflow_stack`, which `kernel_ventry` range-tests itself.
  - Safe: `early_init_stack`, defined in `arch/arm64/kernel/vmlinux.lds.S`
    and used by `primary_entry` and `__primary_switch` in
    `arch/arm64/kernel/head.S` before `__primary_switched` writes
    `vbar_el1`.

**Kernel stacks**

- Range test: `stackinfo_on_stack()` in
  `arch/arm64/include/asm/stacktrace/common.h`, on a `struct stack_info`
  from a `stackinfo_get_irq()`-style getter in
  `arch/arm64/include/asm/stacktrace.h`.
- `stackinfo_on_stack()` returns `false` for `stackinfo_get_unknown()`,
  which the SDEI getters become without `CONFIG_ARM_SDE_INTERFACE`.
- Named wrappers: only `on_irq_stack()`, `on_task_stack()` and
  `on_thread_stack()`. There is no on_overflow_stack, on_sdei_stack or
  on_accessible_stack.
- Getters for the IRQ, overflow and SDEI stacks read this CPU's pointer;
  `kunwind_stack_walk()` in `arch/arm64/kernel/stacktrace.c` uses them only
  under `STACKINFO_CPU()` and `STACKINFO_SDEI()`.
- EFI runtime stack: one global stack, `efi_rt_stack_top`, allocated by
  `arm64_efi_rt_init()` in `arch/arm64/kernel/efi.c` with
  `arch_alloc_vmap_stack(THREAD_SIZE, ...)`.
- EFI runtime stack: getter `stackinfo_get_efi()` under `CONFIG_EFI`;
  `current_in_efi()` in `arch/arm64/include/asm/efi.h` says the task is on
  it.
- EFI runtime stack: no shadow call stack; `__efi_rt_asm_wrapper` saves x18
  and, under `CONFIG_SHADOW_CALL_STACK`, restores it if firmware changed it.
- IRQ stack: allocated only by `arch_alloc_vmap_stack()`, in
  `init_irq_stacks()`.
- `overflow_stack`: defined unconditionally in `arch/arm64/kernel/traps.c`.
- SDEI stacks: allocated in `sdei_arch_get_entry_point()`, called from
  `sdei_probe()` in `drivers/firmware/arm_sdei.c`, not from `init_IRQ()`.
- SDEI shadow call stacks: `sdei_shadow_call_stack_normal_ptr` and
  `sdei_shadow_call_stack_critical_ptr`, allocated by `init_sdei_scs()`
  only when `scs_is_enabled()`.

**Switching stacks**

- `call_on_irq_stack()` masks all of DAIF with `save_and_disable_daif`, in
  two windows.
- First window: from entry up to `restore_irq` just before `blr x1`.
- Second window: from the return of `func` up to `restore_irq` before `ret`.
- `func` runs with the caller's DAIF.
- Old SP: not stored; it is recovered from x29, which points at the frame
  record pushed on the old stack.
- Old x18: stored by `scs_save` in the task's `thread_info` and reloaded by
  `scs_load_current`, not kept in the frame record.
- Each call starts at `irq_stack_ptr + IRQ_STACK_SIZE` and at the base of
  `irq_shadow_call_stack_ptr`.
- **Unsafe usage**: taking an IRQ or FIQ between loading x18 with another
  shadow stack and moving SP off the task stack.
  - Unsafe: `do_interrupt_handler()` sees `on_thread_stack()` true and calls
    `call_on_irq_stack()`, whose `scs_save` overwrites the task's saved SCS
    pointer with the foreign x18.
  - Safe: all of DAIF masked across both moves, as `call_on_irq_stack()`
    and `cpu_switch_to()` do with `save_and_disable_daif`.
- **Unsafe usage**: calling `call_on_irq_stack()` while already on the IRQ
  stack, or from preemptible context.
  - Unsafe: SP and x18 are reset to the start of the per-CPU stacks, over
    frames still in use.
  - Safe: `do_interrupt_handler()`, which tests `on_thread_stack()` first
    and runs with IRQs masked.
  - Safe: `do_softirq_own_stack()`; `do_softirq()` and `__irq_exit_rcu()`
    reach it only when `in_interrupt()` is false, with IRQs disabled.

**Kernel BRK routing**

- Path: `el1_brk64()` in `arch/arm64/kernel/entry-common.c` calls
  `do_el1_brk64()` in `arch/arm64/kernel/debug-monitors.c`, which calls
  the static `call_el1_break_hook()`.
- `call_el1_break_hook()`: an if-chain on `esr_brk_comment()`, most
  branches gated by `IS_ENABLED()`; it calls handlers named like
  `bug_brk_handler()` and `kasan_brk_handler()` directly.
- No match, or a handler returning anything but `DBG_HOOK_HANDLED`:
  `die("Oops - BRK", ...)`.
- There is no early BRK path: early_brk64 is only a leftover prototype in
  `arch/arm64/include/asm/traps.h`, with no definition and no caller.
- Handler prototypes sit outside the `#ifdef` of their option, as in
  `arch/arm64/include/asm/kprobes.h`, so the `IS_ENABLED()` branch compiles
  with the option off.
- `do_el1_brk64()` does not advance `regs->pc`; a handler that resumes
  after the BRK calls `arm64_skip_faulting_instruction()` itself, as
  `bug_brk_handler()` does.
- Annotations vary: `call_el1_break_hook()` and the kgdb handlers have
  `NOKPROBE_SYMBOL()`, the kprobes handlers are `__kprobes`, the handlers
  in `arch/arm64/kernel/traps.c` have neither.
- Masked ranges in `arch/arm64/include/asm/brk-imm.h`: `KASAN_BRK_MASK`,
  `UBSAN_BRK_MASK` and `CFI_BRK_IMM_MASK` each claim a block above their
  base; the kgdb range 0x400 - 0x7ff is reserved by the comment only.
- BRKs taken in nVHE hyp code do not reach `call_el1_break_hook()`;
  `nvhe_hyp_panic_handler()` in `arch/arm64/kvm/handle_exit.c` decodes the
  immediate itself.
- `tools/arch/arm64/include/asm/brk-imm.h` is a second copy of the header.

## Exception masks

**Exception mask helpers**

- `local_daif_mask()`: sets D, A, I, F first, then under
  `system_uses_irq_prio_masking()` writes
  `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` to PMR.
- `local_daif_mask()` entry check: WARNs only when PMR already equals
  `GIC_PRIO_IRQOFF | GIC_PRIO_PSR_I_SET`, and only under
  `system_has_prio_mask_debugging()`.
- `local_daif_mask()` with IRQs already masked by PMR: accepted;
  `arm64_exit_to_user_mode()` calls it after `local_irq_disable()`.
- `local_daif_restore()` with I set in `flags`, priority masking on:

| `flags` | PMR written | DAIF written |
|---|---|---|
| I set, A clear | `GIC_PRIO_IRQOFF` | `flags` with I and F cleared |
| I set, A set | `GIC_PRIO_IRQON \| GIC_PRIO_PSR_I_SET` | `flags` unchanged |

- `local_daif_restore()` under priority masking: never leaves DAIF.I set with
  DAIF.A clear.
- `local_daif_save()` then `local_daif_restore()` under priority masking,
  entered with DAIF = I|F and PMR = `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET`:
  returns with DAIF I and F clear and PMR = `GIC_PRIO_IRQOFF`, the state
  `gic_unmask_pnmis()` sets.
- `local_daif_inherit()`: writes `regs->pmr` to PMR whenever
  `system_uses_irq_prio_masking()`, whatever the interrupted context's IRQ
  state; only `trace_hardirqs_on()` depends on `regs_irqs_disabled()`.
- `local_daif_inherit()`: has no WARN of its own and does not call
  `local_daif_restore()`.
- `local_daif_inherit()` callers: only the EL1 synchronous handlers in
  `arch/arm64/kernel/entry-common.c`, straight after
  `arm64_enter_from_kernel_mode()`; there is no enter_from_kernel_mode() here.
- **Unsafe usage**: calling `local_daif_restore()` with DAIF.I or DAIF.F
  clear.
  - Unsafe: under priority masking the PMR write lands while DAIF.I is still
    clear; the WARN at the top of `local_daif_restore()` checks this, under
    `system_has_prio_mask_debugging()` only.
  - Safe: after `local_daif_save()` or `local_daif_mask()`, as `cpu_suspend()`
    in `arch/arm64/kernel/suspend.c` does.
  - Safe: straight after exception entry, as `el0_da()` does.
  - Safe: with DAIF still masked from boot, as `secondary_start_kernel()`
    does.
- **Unsafe usage**: passing a `local_irq_save()` or `arch_local_save_flags()`
  value to `local_daif_restore()`.
  - Unsafe: under priority masking the value is a PMR priority, and
    `local_daif_restore()` decodes `PSR_I_BIT` and `PSR_A_BIT` from it.
  - Safe: a value from `local_daif_save()` or `local_daif_save_flags()`, as
    `__cpu_replace_ttbr1()` in `arch/arm64/mm/mmu.c` does.
  - Safe: a `DAIF_PROCCTX`, `DAIF_PROCCTX_NOIRQ` or `DAIF_ERRCTX` constant, as
    `el1h_64_error_handler()` does.

**Masks while a handler runs**

| Handler | How DAIF is set | Masked while the body runs | Can interrupt it |
|---|---|---|---|
| EL1 IRQ/FIQ, IRQ path: `__el1_irq()` | raw `write_sysreg(DAIF_PROCCTX_NOIRQ, daif)` in `el1_interrupt()` | I, F | debug, SError; pseudo-NMI once `gic_unmask_pnmis()` has run |
| EL1 pseudo-NMI: `__el1_pnmi()` | same write in `el1_interrupt()` | I, F | debug, SError |
| EL1 SError: `el1h_64_error_handler()` | `local_daif_restore(DAIF_ERRCTX)` | A, I, F | debug |
| EL1 debug: `el1_breakpt()`, `el1_softstp()`, `el1_watchpt()`, `el1_brk64()` | not written | D, A, I, F | nothing |
| EL0 debug: `el0_breakpt()`, `el0_watchpt()` | `local_daif_restore(DAIF_PROCCTX)` after the handler body | D, A, I, F | nothing |
| EL0 debug: `el0_softstp()`, `el0_brk64()`, `el0_bkpt32()` | `local_daif_restore(DAIF_PROCCTX)` before the handler body | none | everything |
| EL0 SError: `__el0_error_handler_common()` | `local_daif_restore(DAIF_ERRCTX)`, then `DAIF_PROCCTX` after `do_serror()` | A, I, F during `do_serror()` | debug during `do_serror()` |

- el1_dbg(): not in this tree; the four EL1 debug handlers in the table call
  `arm64_enter_el1_dbg()`.
- gic_arch_enable_irqs(): not in this tree; `gic_unmask_pnmis()` in
  `arch/arm64/include/asm/arch_gicv3.h` writes `GIC_PRIO_IRQOFF` and clears
  DAIF I and F.
- `el1_interrupt()` under priority masking: does not write PMR before the
  handler runs; it stays at the `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` that
  `kernel_entry` wrote until the irqchip driver changes it.
- `gic_unmask_pnmis()`: called by `__gic_handle_irq_from_irqson()` in
  `drivers/irqchip/irq-gic-v3.c` before the regular IRQ is handled; it does
  nothing without `gic_prio_masking_enabled()`.
- `el1_interrupt()` fixed mask: clears D and A whatever the interrupted
  context had, on the pseudo-NMI path too.
- `el0_softstp()`: runs `try_step_suspended_breakpoints()` fully masked, then
  unmasks before `do_el0_softstep()`.
- `arm64_exit_to_kernel_mode()`: calls `local_irq_disable()` first when
  `regs_irqs_disabled()` is false; there is no exit_to_kernel_mode() here.
- `__el1_pnmi()` and `el1h_64_error_handler()`: call `local_daif_mask()`
  themselves, before `irqentry_nmi_exit()`.
- `arch/arm64/mm/fault.c`: contains no `interrupts_enabled()` test and no
  `local_irq_enable()`; nothing in it unmasks what `el1_abort()` inherited.

**Interrupt priority masking**

- Values: `GIC_PRIO_IRQON` is `GICV3_PRIO_UNMASKED` (0xe0), `GIC_PRIO_IRQOFF`
  is `GICV3_PRIO_IRQ` (0xc0), `GIC_PRIO_PSR_I_SET` is `GICV3_PRIO_PSR_I_SET`
  (0x10); see `include/linux/irqchip/arm-gic-v3-prio.h`, which also has
  `GICV3_PRIO_NMI` (0x80).
- `arch_local_save_flags()` under priority masking: returns the raw PMR;
  nothing ORs in `GIC_PRIO_PSR_I_SET` at save time.
- `GIC_PRIO_PSR_I_SET` in a flags value or in `regs->pmr`: present only
  because a writer put it in PMR, for example `kernel_entry` in
  `arch/arm64/kernel/entry.S` or `local_daif_mask()`.
- `arch_local_irq_save()` under priority masking: writes nothing when PMR is
  not `GIC_PRIO_IRQON`; it returns the current PMR and leaves it. See
  `__pmr_local_irq_save()`.
- `arch_local_irq_enable()` and `arch_local_irq_disable()` under priority
  masking, with PMR neither `GIC_PRIO_IRQON` nor `GIC_PRIO_IRQOFF`:
  `WARN_ON_ONCE()` under `CONFIG_ARM64_DEBUG_PRIORITY_MASKING`; the PMR write
  still happens and DAIF is not touched.
- `arch_irqs_disabled()` under priority masking: reads only PMR, never DAIF;
  see `__pmr_irqs_disabled()`.
- `local_daif_save_flags()` in `arch/arm64/include/asm/daifflags.h`: the
  helper that reads both DAIF and PMR.
- `regs_irqs_disabled()`: tests `PSR_I_BIT` in `regs->pstate` under both
  schemes, and additionally `regs->pmr != GIC_PRIO_IRQON` under priority
  masking.
- `flags & PSR_I_BIT` on a PMR-format flags value: always true, because 0xe0,
  0xc0 and 0xf0 all contain 0x80; the test reads "masked" even when PMR is
  `GIC_PRIO_IRQON`.
- **Potentially unsafe usage**: reading `regs->pmr` directly.
  - Unsafe: without `system_uses_irq_prio_masking()`; `kernel_entry` branches
    over the store to `S_PMR`, so the field was not written at entry.
  - Safe: behind `system_uses_irq_prio_masking()`, as
    `irqs_priority_unmasked()` in `arch/arm64/include/asm/ptrace.h` and
    `local_daif_inherit()` do.

**Priority mask synchronisation**

- `ARM64_HAS_GIC_PRIO_RELAXED_SYNC`: set by `has_gic_prio_relaxed_sync()` in
  `arch/arm64/kernel/cpufeature.c` when `ARM64_HAS_GIC_PRIO_MASKING` is set and
  `ICC_CTLR_EL1_PMHE_MASK` is clear in `ICC_CTLR_EL1`.
- `pmr_sync()` with `CONFIG_ARM64_PSEUDO_NMI=y` and priority masking off: the
  capability is never set, so the `dsb sy` stays; `pmr_sync()` itself does not
  test `system_uses_irq_prio_masking()`.
- VHE `__kvm_vcpu_run()` in `arch/arm64/kvm/hyp/vhe/switch.c`: calls
  `pmr_sync()` with no `system_uses_irq_prio_masking()` guard.
- `kernel_exit` in `arch/arm64/kernel/entry.S`: does not use `pmr_sync()`; it
  open-codes `dsb sy` under
  `alternative_if_not ARM64_HAS_GIC_PRIO_RELAXED_SYNC`, after restoring PMR
  from `S_PMR`.
- `__pmr_local_irq_restore()` and `kernel_exit`: sync after every write,
  including when the restored value masks; a sync after a masking write is not
  an error.
- Writes of `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` with DAIF.I set: synced
  before guest entry in both `__kvm_vcpu_run()` variants (nVHE writes PMR
  itself, VHE relies on `local_daif_mask()`); not synced in
  `local_daif_mask()` or `kernel_entry`.
- `arm_cpuidle_save_irq_context()` in `arch/arm64/include/asm/cpuidle.h`: writes
  `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` with no `pmr_sync()`; `cpu_do_idle()`
  in `arch/arm64/kernel/idle.c` issues `dsb(sy)` before `wfi()`.
- nVHE `__kvm_vcpu_run()` after guest exit: writes `GIC_PRIO_IRQOFF` with no
  sync.
- `local_daif_inherit()`: not an example of a masking write; the `regs->pmr` it
  writes can be `GIC_PRIO_IRQON`.
- `gic_has_relaxed_pmr_sync()`: `drivers/irqchip/irq-gic-v3.c` prints "relaxed"
  or "forced" from it at boot.

## Syndromes

**ESR fields and ISS2**

- `ESR_ELx_ISS2_MASK`: bits 55:32, extracted with `ESR_ELx_ISS2()`.
- ISS2 field macros (`ESR_ELx_TnD`, `ESR_ELx_TagAccess`, `ESR_ELx_GCS`,
  `ESR_ELx_Overlay`, `ESR_ELx_DirtyBit`, `ESR_ELx_Xs_MASK`,
  `ESR_ELx_HDBSSF`): bit positions inside ISS2, not inside the register.
  Apply them to `ESR_ELx_ISS2(esr)`, as `is_gcs_fault()` in
  `arch/arm64/mm/fault.c` does.
- `ESR_ELx_GCS` applied to the raw value tests bit 8, which is `ESR_ELx_CM`.
- ISS2 reaches user space: `thread.fault_code` is `unsigned long` and `esr` in
  `struct esr_context` is `__u64`; `struct pt_regs` holds no syndrome.
- `ESR_ELx_Xs_MASK` (ISS2): `data_abort_decode()` in `arch/arm64/mm/fault.c`,
  its only reader, treats it as valid only when `ESR_ELx_ISV` is set, together
  with `ESR_ELx_SAS`, `ESR_ELx_SSE`, `ESR_ELx_SRT_MASK`, `ESR_ELx_SF` and
  `ESR_ELx_AR`.
- `ESR_ELx_Overlay`, `ESR_ELx_DirtyBit`, `ESR_ELx_TnD`, `ESR_ELx_TagAccess`:
  nothing in the tree gates them on another bit or on the FSC;
  `data_abort_decode()` prints them unconditionally.
- Bits 12:11 have two meanings selected by the FSC. `ESR_ELx_SET_MASK` names
  them; `kvm_handle_guest_sea()` in `arch/arm64/kvm/mmu.c` reports them only
  under `kvm_has_ras()`. `io_mem_abort()` in `arch/arm64/kvm/mmio.c` reads the
  same bits as the load/store type with a raw `GENMASK(12, 11)`, after the
  `ESR_ELx_ISV` test and only for the FSC ranges in its `switch`.
- `ESR_ELx_FnV`: `__fault_safe_to_translate()` in
  `arch/arm64/kvm/hyp/include/hyp/fault.h` honours it only when the FSC equals
  `ESR_ELx_FSC_EXTABT`; `do_sea()` and `kvm_handle_guest_sea()` test it for
  every FSC that reaches them.
- `ESR_ELx_VNCR`: listed in `arch/arm64/include/asm/esr.h` with the fields
  shared by both abort kinds, but `host_owns_sea()` reads it only after
  `!kvm_vcpu_trap_is_iabt()`, and `kvm_handle_vncr_abort()` is the handler for
  `ESR_ELx_EC_DABT_CUR`.

**Reading ISS fields**

- `do_mem_abort()`: does not test the EC before it indexes `fault_info[]` by
  `ESR_ELx_FSC`. The EC is established by the `switch` in the sync handlers of
  `arch/arm64/kernel/entry-common.c`, for example `el0t_64_sync_handler()`.
- Helpers that test the EC themselves: `esr_is_data_abort()`,
  `esr_is_cfi_brk()`.
- Helpers that test no EC: `esr_brk_comment()`, `esr_is_ubsan_brk()`, and the
  FSC helpers such as `esr_fsc_is_translation_fault()`.
- `kvm_vcpu_dabt_get_as()`, `kvm_vcpu_dabt_get_rd()`, `kvm_vcpu_dabt_issext()`,
  `kvm_vcpu_dabt_issf()`, `kvm_vcpu_dabt_iswrite()`: test neither the EC nor
  `ESR_ELx_ISV`; that is left to the caller.
- Bit 24 has four names: `ESR_ELx_ISV` (data abort), `ESR_ELx_CV` (trapped
  conditional instruction), `ESR_ELx_IDS` (SError),
  `ESR_ELx_MOPS_ISS_MEM_INST` (MOPS).
- **Potentially unsafe usage**: applying a field macro or an EC-less helper to
  a syndrome whose class the function has not tested.
  - Unsafe: when the function can be reached with a class in which the bits
    are another field; a data abort with `ESR_ELx_ISV` set reads as
    `ESR_ELx_CV` set.
  - Safe: the function tests the class first, as `kvm_condition_valid32()`
    does before `kvm_vcpu_get_condition()`, and `nvhe_hyp_panic_handler()`
    does before `esr_is_ubsan_brk()`.
  - Safe: every caller has tested the class. `cp15_cond_valid()` reads
    `ESR_ELx_CV` before the `switch` in `do_el0_cp15()`;
    `el0t_32_sync_handler()` reaches it only for `ESR_ELx_EC_CP15_32` and
    `ESR_ELx_EC_CP15_64`. `call_el1_break_hook()` is reached only under
    `ESR_ELx_EC_BRK64`.
- **Potentially unsafe usage**: reading a qualified field without its
  qualifier.
  - Unsafe: when no caller has tested the qualifier; the field is then
    whatever the hardware left there.
  - Safe: `ESR_ELx_ISV` before `ESR_ELx_SAS`, `ESR_ELx_SSE`,
    `ESR_ELx_SRT_MASK` and `ESR_ELx_SF`, as `io_mem_abort()` and
    `kvm_hyp_handle_dabt_low()` do.
  - Safe: `kvm_handle_mmio_return()` reads them without a test, because
    `vcpu->mmio_needed` is set only by `io_mem_abort()` after its ISV test.
  - Safe: `ESR_ELx_S1PTW`, then instruction abort, then `ESR_ELx_WNR`, as
    `kvm_is_write_fault()` does.
  - Safe: a permission fault before `ESR_ELx_FSC_LEVEL`, as
    `kvm_vcpu_trap_get_perm_fault_granule()` enforces with `BUG_ON()`.
  - Safe: `ESR_ELx_FP_EXC_TFV` before the FP exception bits, as
    `do_fpsimd_exc()` does.
- **Potentially unsafe usage**: classifying a fault with
  `(fsc & ESR_ELx_FSC_TYPE)`.
  - Unsafe: for translation and address size faults;
    `ESR_ELx_FSC_FAULT_L(-1)` is 0x2B and `ESR_ELx_FSC_ADDRSZ_L(-1)` is 0x29,
    which the mask does not reduce to `ESR_ELx_FSC_FAULT` or
    `ESR_ELx_FSC_ADDRSZ`.
  - Safe: for permission and access flag faults, which
    `esr_fsc_is_permission_fault()` and `esr_fsc_is_access_flag_fault()`
    define for levels 0 to 3 only, as `par_check_s1_perm_fault()` in
    `arch/arm64/kvm/at.c` does.
- Same ISS bits read under two classes, for example:
  - `do_watchpoint()` in `arch/arm64/kernel/hw_breakpoint.c`: `ESR_ELx_WNR`
    under the watchpoint classes.
  - `do_fpsimd_exc()`: `ESR_ELx_FP_EXC_TFV` under `ESR_ELx_EC_FP_EXC32` and
    `ESR_ELx_EC_FP_EXC64`.
  - `arm64_ras_serror_get_severity()` in `arch/arm64/include/asm/traps.h`:
    `ESR_ELx_FSC` under SError, where 0x11 is `ESR_ELx_FSC_SERROR`; in a data
    abort the same value is `ESR_ELx_FSC_MTE`.

**Syndromes built in software**

- `inject_abt64()` and `inject_undef64()` in `arch/arm64/kvm/inject_fault.c`:
  OR in `ESR_ELx_IL` unconditionally; neither calls
  `kvm_vcpu_trap_il_is32bit()`, including when `inject_abt64()` reports a
  fault taken from AArch32 EL0.
- `kvm_vcpu_trap_il_is32bit()`: no injection path calls it.
- `inject_abt32()`, `inject_undef32()`: build no ESR-format value, so there is
  no IL to set.
- `kvm_inject_nested_sea()`, `kvm_inject_nested_serror()`, and the emulated
  path of `kvm_inject_serror_esr()`: set `ESR_ELx_IL` unconditionally.
- Fake trapped syndromes written to `vcpu->arch.fault.esr_el2`
  (`__pkvm_memshare_page_req()`, `kvm_hyp_handle_impdef()`): also set
  `ESR_ELx_IL`.
- **Unsafe usage**: building a syndrome to inject into a guest from an EC
  constant such as `ESR_ELx_EC_UNKNOWN` without `ESR_ELx_IL`.
  - Safe: OR in `ESR_ELx_IL` unconditionally, as `inject_undef64()`,
    `kvm_inject_nested_sve_trap()` and `kvm_inject_nested_excl_atomic()` do.
- **Unsafe usage**: rewriting a syndrome that is injected or reported whole,
  EC included, with a mask that drops `ESR_ELx_IL`.
  - Safe: clear and replace only the field that changes, as
    `kvm_inject_size_fault()` and `handle_vncr_perm()` do for `ESR_ELx_FSC`,
    and `host_inject_mem_abort()` does for the EC.
  - Safe: an allow-list that names `ESR_ELx_IL`, as `set_thread_esr()`,
    `kvm_emulate_nested_eret()` and `kvm_handle_guest_sea()` use.
- `set_thread_esr()`: is in `arch/arm64/mm/fault.c`; it never sets
  `ESR_ELx_IL`. The IL user space sees is the hardware value: stored
  unmodified for a TTBR0 address, kept by the mask otherwise.

**ERET trap and FPAC syndromes**

- `ESR_ELx_ERET_ISS_ERET` is 0x2 and `ESR_ELx_ERET_ISS_ERETA` is 0x1; test
  them with `esr_iss_is_eretax()` and `esr_iss_is_eretab()`.
- FPAC syndrome: the trapped value is masked with
  `ESR_ELx_ERET_ISS_ERETA | ESR_ELx_IL`, then `ESR_ELx_EC_FPAC` is inserted.
  IL is kept from the trapped syndrome; ISS bit 1 and ISS2 are dropped.
- Injection needs both `kvm_has_pauth(vcpu->kvm, FPACCOMBINE)` and
  `PSR_IL_BIT` clear in the SPSR returned by
  `kvm_check_illegal_exception_return()`.
- `kvm_auth_eretax()` in `arch/arm64/kvm/pauth.c`: returns true without
  authenticating when the key's enable bit (`SCTLR_EL1_EnIA` or
  `SCTLR_EL1_EnIB`) is clear in the guest's SCTLR_EL2; the ELR is then used
  as it is and no FPAC is possible.
- Mangled ELR on failure: `corrupt_addr()` writes the error code only when the
  guest lacks PAuth2; with PAuth2 the value is `ptr ^ (pac & mask)`.
- When FPAC is injected, `kvm_emulate_nested_eret()` returns before the
  PC/PSTATE switch; the exception return is not performed.
- `kvm_handle_eret()` in `arch/arm64/kvm/handle_exit.c` gates the emulation:
  - ERETAx without `vcpu_has_ptrauth()`: goes to `kvm_handle_ptrauth()`, which
    injects UNDEF.
  - not `is_hyp_ctxt()`: the trap is forwarded with the unmodified syndrome.
- `kvm_hyp_handle_eret()` in `arch/arm64/kvm/hyp/vhe/switch.c`: returns false
  when `kvm_auth_eretax()` fails, so `kvm_emulate_nested_eret()` runs the
  authentication a second time.

## System register definitions

**Accessor macros**

- `REG_TCR2_EL1` and the other generated `REG_` names with the plain forms:
  the generator emits each as the generic `S<op0>_<op1>_C<crn>_C<crm>_<op2>`
  spelling, which the assembler takes without knowing the register, so
  `read_sysreg()`, `write_sysreg()`, `sysreg_clear_set()` and bare `mrs`/`msr`
  in `.S` files work with it; see `sysreg_clear_set(REG_TCR2_EL1, ...)` in
  `arch/arm64/kernel/cpufeature.c` and `arch/arm64/kernel/hyp-stub.S`.
- `write_sysreg_hcr()`: exists for `CONFIG_AMPERE_ERRATUM_AC04_CPU_23`
  (capability `ARM64_WORKAROUND_AMPERE_AC04_CPU_23`), not for a Cortex
  erratum.
- `write_sysreg_hcr()` with the workaround selected: emits
  `dsb nsh; msr hcr_el2; isb`.
- `write_sysreg_hcr()` selection: a C `if`, true when the config is enabled
  and either `system_capabilities_finalized()` is false or the capability is
  set.
- `write_sysreg_hcr()` otherwise: a bare `msr hcr_el2` with no barrier; the
  caller still supplies any `isb` it needs.
- `sysreg_clear_set_hcr()`: the read-modify-write form; it skips the write,
  and with it both barriers, when the value is unchanged.
- `msr_hcr_el2` (assembly macro in `arch/arm64/include/asm/sysreg.h`): the
  `dsb nsh` depends on the config symbol alone, with no capability test; the
  trailing `isb` is emitted in every configuration.

**XZR and no-operand instructions**

| Form | Where Rt = 31 comes from | Example |
|---|---|---|
| `write_sysreg_s(0, enc)`, `gic_insn(0, insn)` | text `xzr`, no asm operand, taken when `__builtin_constant_p(__val) && __val == 0` | `gicv5_handle_irq()` in `drivers/irqchip/irq-gic-v5.c` |
| `asm volatile(__msr_s(enc, "xzr"))` | text `xzr`, unconditional | `sme_smstart_sm()` in `arch/arm64/include/asm/fpsimd.h` |
| `__tlbi(op)`, which selects `__TLBI_0` | the assembler, from `tlbi <op>` with an empty operand list | `arch/arm64/include/asm/tlbflush.h` |
| fixed word through `__emit_inst()` | 31 written into the constant | `__SYS_BARRIER_INSN()`, `BRB_IALL_INSN`, `SET_PSTATE()` |
| `msr_s` with `xzr` in assembly, for example `msr_s SYS_LORC_EL1, xzr` | text `xzr` | `arch/arm64/include/asm/el2_setup.h` |

- `write_sysreg_s()` in `arch/arm64/include/asm/sysreg.h`: does not use
  `"rZ"`; its non-zero branch binds the value with plain `"r"`.
- `__TLBI_0` and `__TLBI_1`: contain only `ARM64_ASM_PREAMBLE` and the
  mnemonic, no alternative; `__TLBI_1` binds its argument with `"rZ"` and
  `%x0`.
- `gic_insn(v, insn)`: is `write_sysreg_s(v, GICV5_OP_GIC_##insn)`; there is
  no sys_s macro in this tree.
- Barrier words: the names are `SB_BARRIER_INSN`, `GSB_SYS_BARRIER_INSN` and
  `GSB_ACK_BARRIER_INSN`.
- `mrs_s`/`msr_s` register argument: must print as `x0`..`x30`, `w0`..`w30`,
  `xzr` or `wzr`; `__DEFINE_ASM_GPR_NUMS` in
  `arch/arm64/include/asm/gpr-num.h` defines a `.L__gpr_num_` symbol for
  those names only, so the asm operand needs a register constraint, or
  `"rZ"` printed with `%x0` as `write_sysreg_elx()` has.
- **Potentially unsafe usage**: `write_sysreg_s(v, enc)` or `gic_insn(v, insn)`
  for an instruction whose register field must be 31.
  - Unsafe: when `v` is not a zero that `__builtin_constant_p()` sees as
    constant at the macro expansion; the `else` branch binds it with `"r"`,
    Rt is a general register, and the build reports nothing.
  - Safe: a literal `0`, as `gicv5_handle_irq()` passes in
    `gic_insn(0, CDEOI)`; the test in `write_sysreg_s()` then emits `xzr`.
  - Safe: a run-time value for an instruction that takes a register operand,
    as `gicv5_hwirq_eoi()` passes in `gic_insn(cddi, CDDI)`.
- **Potentially unsafe usage**: relying on `"rZ"` with `%x0` to produce XZR.
  - Unsafe: when the instruction requires Rt = 31; `"rZ"` also permits a
    general register that holds zero; `write_sysreg_s()` tests the constant
    itself and prints `xzr` instead.
  - Safe: when any register is acceptable, as in `write_sysreg()`,
    `write_sysreg_hcr()`, `write_sysreg_elx()` and `__TLBI_1`.

**Register description file:** `R` is the block name, `F` the field name, `P` a
prefix.

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

**Reserved-bit masks**

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

**Consumers of generated masks**

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

## Context synchronisation

**Register writes needing an ISB**

- `update_sctlr_el1()`: writes with `sysreg_clear_set()`; the `isb()` after it
  runs even when `sysreg_clear_set()` skipped the write.
- `set_sctlr_el1`: an assembler macro in `arch/arm64/include/asm/assembler.h`,
  used by `__enable_mmu` and `enter_vhe`; `update_sctlr_el1()` does not use it.
- `__mte_enable_kernel()`: `isb()` directly after the `sysreg_clear_set()` of
  `SCTLR_EL1_TCF_MASK`; `mte_enable_kernel_store_only()` has the same shape.
- `cpu_enable_pan()`: no `isb()` in the body; it clears `SCTLR_EL1_SPAN` with
  `sysreg_clear_set()` and then runs `set_pstate_pan(1)`.
- `init_el2_state` macros with no `isb` of their own, for example
  `__init_el2_fgt` and `__init_el2_hstr`: covered by a later `isb`, not by the
  `eret`.
  - `init_el2` in `arch/arm64/kernel/head.S`: `isb` after `msr vbar_el2`,
    which follows `init_el2_state`.
  - `___kvm_hyp_init` in `arch/arm64/kvm/hyp/nvhe/hyp-init.S`: `isb` after
    `msr tcr_el2`, which follows both calls of `__kvm_init_el2_state`.
  - Comment above `init_kernel_el()`: ERET is not relied on, because
    `SCTLR_ELx_EOS` may be clear.
- There is no __init_el2_hcr here; `init_el2_hcr` in
  `arch/arm64/include/asm/el2_setup.h` writes through the `msr_hcr_el2`
  assembler macro, which always ends in `isb`.
- Caller of `sysreg_clear_set_hcr()` that needs the barrier: adds `isb()`, as
  `__vgic_v3_get_gic_config()` does.
- Writes left without an `isb()`, and the reason the tree gives:

| Code | Write | Reason |
|---|---|---|
| `cpu_enable_mpam()` | `SYS_MPAM0_EL1` | comment: left to the ERET to EL0; the `SYS_MPAM1_EL1` write before it gets `isb()` |
| `permission_overlay_switch()` | `SYS_POR_EL0` | comment: a spurious overlay fault is tolerated |
| `mte_check_tfsr_el1()` | `SYS_TFSR_EL1` | comment: no indirect read follows the direct write |
| `cpu_enable_mte()` | `SCTLR_ELx_ATA`, `SCTLR_EL1_ATA0` | `mte_cpu_setup()` ends in `local_flush_tlb_all()`, which has `isb()`, before `mte_clear_page_tags()` runs |

**Writes that need no barrier**

| Write | Where | What shows it |
|---|---|---|
| `ZCR_ELx_LEN_MASK` of `SYS_ZCR_EL1`, `SMCR_ELx_LEN_MASK` of `SYS_SMCR_EL1` | `vec_probe_vqs()`, through `write_vl()` | comment `/* self-syncing */`; `sve_get_vl()` or `sme_get_vl()` runs next |
| same two fields, and `SYS_SVCR` | `task_fpsimd_load()` | code only, no comment: `sme_load_state()` and `sve_load_state()` follow and take the length from `sme_get_vl()` and `sve_get_vl()` |
| `SYS_ICC_PMR_EL1` | `local_daif_restore()`, masking branch | comment: "writes to PMR are self-synchronizing"; no barrier follows `gic_write_pmr()` |
| `daif` | `local_daif_restore()` | same comment, quoting the ARM ARM on PSTATE writes |
| PSTATE.SSBS | `spectre_v4_enable_hw_mitigation()` | comment: "SSBS is self-synchronizing" |

- There is no sve_set_vq(), sme_set_vq(), sve_load_vq or fpsimdmacros.h here;
  `task_fpsimd_load()` calls `sysreg_clear_set_s()` itself.
- `pmr_sync()` in `local_daif_restore()`: only in the unmasking branch.
- `pmr_sync()`: `dsb sy`, patched to NOPs by
  `ARM64_HAS_GIC_PRIO_RELAXED_SYNC`; empty without `CONFIG_ARM64_PSEUDO_NMI`.
  There is no gic_pmr_sync static key.
- `spectre_v4_enable_hw_mitigation()`: `spec_bar()` follows
  `set_pstate_ssbs(0)` under `CONFIG_ARM64_ERRATUM_3194386`.

**Initial SCTLR values**

| Value | EIS and EOS | How |
|---|---|---|
| `INIT_SCTLR_EL1_MMU_ON` | set | named: `SCTLR_EL1_EIS`, `SCTLR_EL1_EOS` |
| `INIT_SCTLR_EL1_MMU_OFF` | set | named: `SCTLR_EL1_EIS`, `SCTLR_EL1_EOS` |
| `INIT_SCTLR_EL2_MMU_ON` | set | named: `SCTLR_ELx_EIS`, `SCTLR_ELx_EOS` |
| `INIT_SCTLR_EL2_MMU_OFF` | clear | holds only `SCTLR_EL2_RES1` and `ENDIAN_SET_EL2` |

- `SCTLR_EL2_RES1`: generated by `arch/arm64/tools/gen-sysreg.awk` from
  `arch/arm64/tools/sysreg`; it starts at `UL(0)` and gains bits only from
  `Res1` lines.
- `SCTLR_EL2` block in `arch/arm64/tools/sysreg`: no `Res1` line; EIS and EOS
  are `Field` lines, so the mask contributes neither bit.
- `INIT_SCTLR_EL1_MMU_ON` and `INIT_SCTLR_EL1_MMU_OFF`: do not use
  `SCTLR_EL1_RES1`.
- `tools/arch/arm64/include/asm/sysreg.h`: its copy of
  `INIT_SCTLR_EL2_MMU_ON` lacks the two bits; the kernel builds from
  `arch/arm64/include/asm/sysreg.h`.
- `INIT_SCTLR_EL2_MMU_OFF` is installed by `__init_el2_sctlr`, by `init_el2`
  in `arch/arm64/kernel/head.S`, and by the reset path of
  `__kvm_handle_stub_hvc`.
- nVHE hyp: `___kvm_hyp_init` installs `INIT_SCTLR_EL2_MMU_ON`, so both bits
  are set there.
- `kvm_hyp_handle_fpsimd()` in `arch/arm64/kvm/hyp/include/hyp/switch.h`:
  has no `isb()` after `__activate_cptr_traps()`; on return to the guest the
  write is left to the `eret` in `__guest_enter`.
- **Unsafe usage**: under `INIT_SCTLR_EL2_MMU_OFF`, leaving a system register
  write to be synchronised by `eret` or by exception entry.
  - Unsafe: on a CPU with `FEAT_ExS`, where the clear bits mean that neither
    event is context synchronising.
  - Safe: an `isb` after the writes, as `___kvm_hyp_init` has after
    `msr tcr_el2`, before it installs `INIT_SCTLR_EL2_MMU_ON`; the comment
    above `init_kernel_el()` states the requirement.
  - Safe: under the other three values, which name both bits, as
    `kvm_hyp_handle_fpsimd()` runs under `INIT_SCTLR_EL2_MMU_ON` or
    `INIT_SCTLR_EL1_MMU_ON`.

**Reading a register back**

- `gic_has_group0()` in `drivers/irqchip/irq-gic-v3.c`: `gic_write_pmr()` then
  `gic_read_pmr()`, no barrier; on a zero read-back it returns `false`, no
  access to Group 0.
- `gic_has_group0()` does not find the number of priority bits;
  `gic_get_pribits()` reads that from `ICC_CTLR_EL1`.
- `__arm_spe_pmu_dev_probe()` in `drivers/perf/arm_spe_pmu.c`: writes
  `U64_MAX` to `SYS_PMSEVFR_EL1` and reads it back, no barrier; bits that read
  0 are unsupported filter bits, stored in `pmsevfr_res0`.
- `init_el2_hcr` in `arch/arm64/include/asm/el2_setup.h`: no `HCR_EL2`
  read-back. It tests the E2H0 field of `SYS_ID_AA64MMFR4_EL1`, else writes
  `far_el1`, `isb`, writes `far_el2`, `isb`, and reads `far_el1` to see
  whether the two names alias.
- `vec_probe_vqs()`: does not find the length by reading `SYS_ZCR_EL1` or
  `SYS_SMCR_EL1` back; it reads the resulting length with `sve_get_vl()` or
  `sme_get_vl()`, which depends on the write being self-synchronising.
- `sve_setup()`: does no probing; `vec_probe_vqs()` is called by
  `vec_init_vq_map()`, `vec_update_vq_map()` and `vec_verify_vq_map()`.
- Read-backs of `ICC_SRE_EL1` and `ICC_SRE_EL2` that test whether a write to
  the SRE bit took effect have an `isb` between write and read:
  `__init_el2_gicv3`, `gic_enable_sre()` through `gic_write_sre()`, and
  `__vgic_v3_get_gic_config()`.

## CPU capabilities

**Testing a capability**

- `cpus_have_final_cap()`: `BUG()` until `system_capabilities_finalized()`,
  then `alternative_has_cap_unlikely()`; there is no static key per
  capability in this tree.
- `system_capabilities_finalized()`: becomes true when
  `apply_alternatives_all()` patches `ARM64_ALWAYS_SYSTEM`, not when the
  system caps are detected.
- `.cpu_enable` callbacks at boot: run from `enable_cpu_capabilities()` before
  the matching alternatives pass, so `cpus_have_final_cap()` there hits
  `BUG()`; on a late CPU the same callback runs after the pass.
- `cpus_have_final_boot_cap()`: `BUG()` until `boot_capabilities_finalized()`;
  it checks only `ARM64_ALWAYS_BOOT`, not the scope of the cap passed in.
- `cpus_have_final_boot_cap()` on a cap that is not boot-scope: returns false
  with no `BUG()` between the boot pass and the system pass.
- `system_supports_bti_kernel()`: uses `cpus_have_final_boot_cap(ARM64_BTI)`,
  valid because `CONFIG_ARM64_BTI_KERNEL` makes `ARM64_BTI` a
  `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE`.
- `system_supports_sve()`: calls `alternative_has_cap_unlikely(ARM64_SVE)`
  directly, so it reads false before the system pass and never `BUG()`s.
- Helpers in `arch/arm64/include/asm/cpufeature.h` are not uniform: some
  `BUG()` early instead of reading false, for example `system_supports_bti()`
  and `system_supports_lpa2()` (`cpus_have_final_cap()`), and
  `system_supports_address_auth()` (`cpus_have_final_boot_cap()`).
- `this_cpu_has_cap()`: does not call `cpucap_is_possible()`; it returns false
  when `cpucap_ptrs` has no entry for the cap.
- `this_cpu_has_cap()` before `setup_boot_cpu_features()`: false for every
  cap, because `init_cpucap_indirect_list()` has not filled `cpucap_ptrs`.
- `cpus_have_cap()`: applies `cpucap_is_possible()` only when the argument is
  a compile-time constant.

**Capability scopes and types**

| Type | Scope | Late CPU may have it, system not | Late CPU may lack it, system has | Conflict |
|---|---|---|---|---|
| `ARM64_CPUCAP_LOCAL_CPU_ERRATUM` | local | no | yes | CPU dies |
| `ARM64_CPUCAP_SYSTEM_FEATURE` | system | yes | no | CPU dies |
| `ARM64_CPUCAP_WEAK_LOCAL_CPU_FEATURE` | local | yes | yes | none |
| `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE` | local, all early CPUs | yes | no | CPU dies |
| `ARM64_CPUCAP_BOOT_RESTRICTED_CPU_LOCAL_FEATURE` | local | no | yes | CPU dies |
| `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE` | boot | no | no | panic |
| `ARM64_CPUCAP_BOOT_CPU_FEATURE` | boot | yes | no | CPU dies |

- `ARM64_CPUCAP_BOOT_RESTRICTED_CPU_LOCAL_FEATURE`: same bits as
  `ARM64_CPUCAP_LOCAL_CPU_ERRATUM`.
- `ARM64_CPUCAP_PANIC_ON_CONFLICT`: set only by
  `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE`.
- `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE`: adds
  `ARM64_CPUCAP_MATCH_ALL_EARLY_CPUS`; `update_cpu_capabilities()` sets the
  cap only while probing the boot CPU and clears it when an early secondary
  does not match, so `cpus_have_cap()` can go from true to false before
  finalisation.
- There is no ARM64_CPUCAP_BOOT_CPU_ERRATUM; `arm64_errata` entries use
  `ARM64_CPUCAP_LOCAL_CPU_ERRATUM` (set by the `ERRATA_MIDR_RANGE()` family),
  and a few use `ARM64_CPUCAP_WEAK_LOCAL_CPU_FEATURE` or
  `ARM64_CPUCAP_SYSTEM_FEATURE`.
- Which CPU is late: see `check_local_cpu_capabilities()`; every secondary is
  verified against boot-scope caps, and against the other scopes only once
  `system_capabilities_finalized()` is true.
- Secondary before finalisation: not verified for local-scope caps; it runs
  `update_cpu_capabilities(SCOPE_LOCAL_CPU)` and can set them.
- Conflict: `verify_local_cpu_caps()` prints "Detected conflict for
  capability", then calls `cpu_panic_kernel()` or `cpu_die_early()`.
- `cpu_die_early()`: marks the CPU not present; under `CONFIG_HOTPLUG_CPU` it
  sets `CPU_KILL_ME` and calls `__cpu_try_die()`; if that returns, or without
  the option, it sets `CPU_STUCK_IN_KERNEL` and parks; the cap is unchanged.
- `cpu_panic_kernel()`: the secondary sets `CPU_PANIC_KERNEL` and parks; the
  CPU in `__cpu_up()` calls `panic()`.
- No conflict and the system has the cap: `.cpu_enable` runs on the new CPU
  whether or not that CPU matches.

**ID register sanitisation**

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

**Adding a feature or erratum**

- `arch/arm64/tools/cpucaps`: the file is not sorted;
  `arch/arm64/tools/gen-cpucaps.awk` numbers names in file order, and
  `update_cpu_capabilities()` probes in number order, so order matters where
  one cap's `.matches` reads another, as the `BUILD_BUG_ON()` in
  `can_use_gic_priorities()` checks.
- `arch/arm64/tools/gen-cpucaps.awk`: fails the build only for a line that is
  neither blank, nor a `#` comment, nor made of upper case, digits,
  underscore and lower-case v.
- Generated header: `asm/cpucap-defs.h`; `cpucap_is_possible()` is
  hand-written in `arch/arm64/include/asm/cpucaps.h`.
- `KERNEL_HWCAP_` constants: generated into `asm/kernel-hwcap.h` by
  `arch/arm64/tools/gen-kernel-hwcaps.sh` from
  `arch/arm64/include/uapi/asm/hwcap.h`; the constant needs only the uapi
  define, not a hand-written `KERNEL_HWCAP_` line.
- Table entry without `.matches`: `init_cpucap_indirect_list_from_array()`
  treats it as the end of the table, so every later entry is silently
  dropped.
- Name in `arch/arm64/tools/cpucaps` with no table entry: builds and boots;
  the cap is never set and `this_cpu_has_cap()` returns false.
- `.type` scope of a MIDR-based erratum: checked at boot; the matchers such as
  `is_affected_midr_range_list()` `WARN_ON()` a scope other than
  `SCOPE_LOCAL_CPU`. The late-CPU bits are checked by nothing.
- Feature with `has_cpuid_feature()`: the register must be in
  `__read_sysreg_by_encoding()`, else `BUG()`; at boot for a scope other than
  `SCOPE_SYSTEM`, and for `SCOPE_SYSTEM` only when `verify_local_cpu_caps()`
  checks a late CPU or `this_cpu_has_cap()` is called.
- `#ifdef` around the table entry and the `cpucap_is_possible()` case: nothing
  checks that they name the same option; with the entry built and the case
  false, `cpus_have_cap()` on a constant reads false while the bit is set, as
  for `ARM64_HAS_TLB_RANGE` without `CONFIG_ARM64_TLB_RANGE`.
- `arm64_errata` guards: not always a `CONFIG_ARM64_ERRATUM_` option; some
  entries use a shared hidden option such as
  `CONFIG_ARM64_WORKAROUND_REPEAT_TLBI_SYNC`, and some have no guard.
- `ERRATA_MIDR_RANGE()` and its relatives in `arch/arm64/kernel/cpu_errata.c`
  set `.type` and `.matches`; an entry written by hand must set both.

**Alternatives patching**

- Replacement location: `.subsection 1` of the section that holds the
  original; arm64 does not use an `.altinstr_replacement` section.
- `get_alt_insn()` rewrites: immediate branches (`aarch64_insn_is_branch_imm()`)
  whose target is outside the replacement, and `adrp`.
- `get_alt_insn()` hits `BUG()` for the rest of
  `aarch64_insn_uses_literal()`: `adr`, `ldr` literal, `ldrsw` literal and
  `prfm` literal. The `BUG()` fires only at patch time on a system that has
  the cap.
- Rewritten branch range: not checked; `aarch64_insn_encode_immediate()` masks
  the new offset, so a short-range branch that no longer reaches is encoded
  wrong silently.
- Length mismatch: caught at assembly by the `.org` directives, and by
  `BUG_ON()` in `__apply_alternatives()`; the "<= orig_len" comment on
  `alt_len` in `struct alt_instr` does not hold.
- `ALTERNATIVE_CB()` entry: `alt_len` must be 0 (`BUG_ON()`), and `alt_offset`
  holds the callback.
- Callback in a module's alternatives: must satisfy `core_kernel_text()`,
  else `apply_alternatives_module()` returns `-ENOEXEC` and the load fails.
- `__init` callback: fails that test once `system_state` reaches
  `SYSTEM_FREEING_INITMEM`, so a module loaded after that cannot use it.
- `noinstr` on a callback: not enforced; in-tree callbacks are a mix, for
  example `kvm_update_va_mask()` is `__init`, `kvm_patch_vector_branch()` is
  plain, `alt_cb_patch_nops()` is `noinstr`.
- Callback used by nVHE hyp code: needs a `KVM_NVHE_ALIAS()` line in
  `arch/arm64/kernel/image-vars.h`.
- Callback used from a module: must be exported, as `alt_cb_patch_nops()` is.
- vDSO: `alternative_has_cap_likely()` uses plain `ALTERNATIVE()` under
  `BUILD_VDSO` instead of the callback.
- `updptr` for the kernel image: `lm_alias()` of `origptr`; for a module it
  equals `origptr`.

**Points of alternative patching**

| Pass | Reached from | Caps patched |
|---|---|---|
| `apply_boot_alternatives()` | `smp_prepare_boot_cpu()` -> `setup_boot_cpu_features()` -> `setup_boot_cpu_capabilities()` | `boot_cpucaps` |
| `apply_alternatives_all()` | `smp_cpus_done()` -> `setup_system_features()` -> `setup_system_capabilities()` | complement of `boot_cpucaps` |
| `apply_alternatives_vdso()` | `apply_alternatives_all()`, before `stop_machine()` | all set caps |
| `apply_alternatives_module()` | `module_finalize()` | all set caps |

- Callback alternatives: there is no ARM64_CB_PATCH; an entry carries a real
  cap plus `ARM64_CB_BIT` and is patched in that cap's pass, for example
  `ARM64_ALWAYS_SYSTEM` in the system pass.
- `boot_cpucaps`: only caps whose type has `SCOPE_BOOT_CPU` and that matched
  on the boot CPU.
- Local-scope caps found on the boot CPU, such as errata: set in
  `system_cpucaps` from `setup_boot_cpu_capabilities()`, but patched only by
  `apply_alternatives_all()`; until then `cpus_have_cap()` is true and the
  alternative sequences are still the default.
- Early assembly may contain alternatives: `__cpu_setup()` has
  `alternative_if ARM64_HAS_VA52`; the boot CPU runs the default sequence,
  secondaries and `cpu_resume` run the patched one.
- `__apply_alternatives()`: not `noinstr`; `patch_alternative()`,
  `clean_dcache_range_nopatch()` and `alt_cb_patch_nops()` are.
- System pass: the CPU with `smp_processor_id()` 0 patches; the others spin on
  `all_alternatives_applied` in `__apply_alternatives_multi_stop()`.
- `alternative_is_applied()`: tests `applied_alternatives`, which the kernel
  image and vDSO passes update and module patching does not;
  `cpu_copy_el2regs()` uses it.
- **Potentially unsafe usage**: testing a cap through
  `alternative_has_cap_unlikely()`, `alternative_has_cap_likely()` or a helper
  built on them, on a path that can run before the pass that patches that
  cap.
  - Unsafe: when the path needs the real answer; the test reads false, or
    hits `BUG()` through `cpus_have_final_cap()`.
  - Safe: `cpus_have_cap()`, which reads `system_cpucaps`, as
    `enable_cpu_capabilities()` and `__apply_alternatives()` do.
  - Safe: a boot-scope cap tested after `setup_boot_cpu_features()`, as
    `smp_prepare_boot_cpu()` tests `system_uses_irq_prio_masking()`;
    `apply_boot_alternatives()` has patched `boot_cpucaps` by then.
  - Safe: when false before the pass is the intended answer, as
    `check_local_cpu_capabilities()` uses `system_capabilities_finalized()`
    to choose between updating and verifying.

**Early EL2 setup**

- `init_el2_state` users: `init_kernel_el` in `arch/arm64/kernel/head.S` and
  `__kvm_init_el2_state` in `arch/arm64/kvm/hyp/nvhe/hyp-init.S`;
  `arch/arm64/kernel/hyp-stub.S` does not run it.
- `init_kernel_el` callers: `primary_entry`, `secondary_holding_pen`,
  `secondary_entry` and `cpu_resume`.
- `__kvm_init_el2_state`: runs `init_el2_state` then `finalise_el2_state`;
  called from `__kvm_hyp_init_cpu`, and from `___kvm_hyp_init` only when
  `HCR_E2H` is set.
- `sctlr_el2`: set inside `init_el2_state` by `__init_el2_sctlr`, not left to
  the caller.
- `hcr_el2`: set by the caller before the macro, with `init_el2_hcr` in
  `init_kernel_el` and `__kvm_hyp_init_cpu`, and with `msr_hcr_el2` in
  `___kvm_hyp_init`; `__check_hvhe` in `__init_el2_timers` and
  `__init_el2_cptr` reads the `HCR_E2H` bit it leaves.
- `init_el2_state` can run with `HCR_E2H` set (a VHE-only CPU, or the hVHE
  replay), so a register whose layout depends on it needs `__check_hvhe`.
- Left to `init_kernel_el` outside the macro: `elr_el2` before it, and after
  it `vbar_el2`, `spsr_el2`, and `sctlr_el1` or `SYS_SCTLR_EL12`.
- Left to `finalise_el2_state`, which honours ID overrides through
  `check_override`:

| Feature | Registers |
|---|---|
| MPAM | `SYS_MPAM2_EL2`, `SYS_MPAMHCR_EL2` |
| GCS | `SYS_GCSCR_EL1`, `SYS_GCSCRE0_EL1` |
| SVE | `CPTR_EL2_TZ` or `CPACR_EL1_ZEN`, `SYS_ZCR_EL2` |
| SME | `CPTR_EL2_TSM` or `CPACR_EL1_SMEN`, `SCTLR_ELx_ENTP2`, `SYS_SMCR_EL2`, `SYS_SMPRIMAP_EL2` |

- `check_override` in the nVHE object: reads a symbol named after the
  register with the suffix `_el1_sys_val`, for example
  `id_aa64pfr0_el1_sys_val`, instead of the override; a new register there
  needs that variable in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`, set in
  `arch/arm64/kvm/arm.c`.
- `finalise_el2_state` runs on every `HVC_FINALISE_EL2`, before
  `__finalise_el2` decides whether to switch to VHE.
- `__finalise_el2` requires the EL2 MMU off: bit 0 of `sctlr_el2` set returns
  `HVC_STUB_ERR` and the kernel stays at EL1.
- `__finalise_el2` copies `sp_el1`, and through the `_EL12` aliases
  `SYS_CPACR_EL12`, `SYS_VBAR_EL12`, `SYS_TCR_EL12`, `SYS_TTBR0_EL12`,
  `SYS_TTBR1_EL12`, `SYS_MAIR_EL12`, then `REG_TCR2_EL12` if TCRX is present,
  and `REG_PIRE0_EL12` and `REG_PIR_EL12` only if both TCRX and S1PIE are.
- `enter_vhe` copies `SYS_SCTLR_EL12` and then writes
  `INIT_SCTLR_EL1_MMU_OFF` to it.
- `tpidr_el1`: not copied by `__finalise_el2`; `cpu_copy_el2regs()`, the
  `.cpu_enable` of `ARM64_HAS_VIRT_HOST_EXTN`, copies it to `tpidr_el2` while
  `alternative_is_applied()` is false for that cap.
- An EL1 register that `HCR_E2H` redirects to EL2 and that is programmed
  before `finalise_el2`, in `__cpu_setup()` or `__enable_mmu`, needs its own
  copy in `__finalise_el2`; otherwise the value stays in the EL1 register
  after the switch.
- `__finalise_el2` also undoes nVHE-only state: it clears
  `MDCR_EL2_E2PB_MASK` and `MDCR_EL2_E2TB_MASK`.
- There is no HCRX_HOST_FLAGS in this tree; the `SYS_HCRX_EL2` boot value is
  built in `__init_el2_hcrx`.

## Patching and cache maintenance

**Instruction patching functions**

| Function | Cache maintenance | Other CPUs resynchronise |
|---|---|---|
| `aarch64_insn_copy()` | `flush_icache_range()` over the whole range, after `patch_lock` is dropped | yes, IPI from `kick_all_cpus_sync()` |
| `aarch64_insn_set()` | same; both are `__text_poke()` | yes, same IPI |
| `aarch64_insn_patch_text()` | `aarch64_insn_patch_text_nosync()` per instruction, on the patching CPU | yes; the others spin, then `isb()` |
| `aarch64_insn_patch_text_nosync()` | `caches_clean_inval_pou()` over the one instruction | no |
| `aarch64_insn_write()` | none | no |

- `aarch64_insn_patch_text_cb()`: the last CPU to enter patches, not the
  first.
- `aarch64_insn_patch_text()`: the caller must hold the CPU hotplug read
  lock; `stop_machine_cpuslocked()` has `lockdep_assert_cpus_held()`.
- `aarch64_insn_copy()` and `aarch64_insn_set()`: need interrupts enabled
  and task context, because `kick_all_cpus_sync()` reaches
  `smp_call_function_many_cond()` in `kernel/smp.c`, which asserts both.
- `flush_icache_range()` under `in_dbg_master()`: returns after the cache
  maintenance, without the IPI.
- `aarch64_insn_copy()`: returns `NULL` only for a `dst` that is not 4-byte
  aligned; `text_poke_memcpy()` discards the result of
  `copy_to_kernel_nofault()`, so a fault is not reported.
- `aarch64_insn_set()`: writes `len / 4` words with `memset32()`, not
  through `copy_to_kernel_nofault()`.
- `patch_map()`: no configuration test; `is_image_text()` selects
  `__pa_symbol()`, every other address goes to `vmalloc_to_page()` with
  `BUG_ON(!page)`.
- `is_image_text()`: also covers the exit text while `system_state` is below
  `SYSTEM_RUNNING`.
- kprobes arm and disarm: `arch_arm_kprobe()` and `arch_disarm_kprobe()` call
  `aarch64_insn_patch_text()` with one instruction, so each is a
  `stop_machine_cpuslocked()` run.
- `arm_kprobe()` and `disarm_kprobe()` in `kernel/kprobes.c`: take
  `cpus_read_lock()` and `text_mutex` around those calls.
- `arch_prepare_ss_slot()`: the only kprobes user of
  `aarch64_insn_patch_text_nosync()`; it fills the single-step slot, not the
  probed address.

**Other CPUs and patched code**

- Instruction class: no function in `arch/arm64/kernel/patching.c` checks
  which instructions are swapped; there is no aarch64_insn_hotpatch_safe()
  here.
- `aarch64_insn_patch_text_nosync()`: tests only 4-byte alignment
  (`-EINVAL`) and accepts any 32-bit value; the caller chooses between it
  and `aarch64_insn_patch_text()`.
- **Potentially unsafe usage**: `aarch64_insn_patch_text_nosync()` with
  nothing after it that resynchronises the other CPUs.
  - Unsafe: when the caller then relies on no CPU still running the old
    instruction; the only `isb` is the one in `caches_clean_inval_pou()`, on
    the calling CPU, and another CPU may keep executing what it already
    fetched.
  - Safe: followed by `kick_all_cpus_sync()`, as
    `arch_jump_label_transform_apply()` does; `flush_icache_range()` in
    `arch/arm64/include/asm/cacheflush.h` defines the same IPI as the
    resynchronisation step.
  - Safe: the text written cannot be reached until a later exception, as in
    `arch_prepare_ss_slot()`, which fills the slot before
    `arch_arm_kprobe()` writes the BRK; the slot is entered only from
    `setup_singlestep()` in the BRK handler.
  - Safe: `aarch64_insn_patch_text()`, where every other CPU does `isb()`
    in `aarch64_insn_patch_text_cb()` before it leaves.
- Jump label: arm64 defines `HAVE_JUMP_LABEL_BATCH` and has no definition of
  `arch_jump_label_transform()`.
- `arch_jump_label_transform_queue()`: queues nothing; it patches at once
  with `aarch64_insn_patch_text_nosync()`, ignores the result and returns
  `true`.
- `arch_jump_label_transform_apply()`: not a no-op; it is the one
  `kick_all_cpus_sync()` per `__jump_label_update()` in
  `kernel/jump_label.c`.
- `__apply_alternatives()`: calls no routine from `arch/arm64/mm/cache.S`,
  since that code is itself patched; it uses `clean_dcache_range_nopatch()`
  per entry, then one `dsb(ish)`, `icache_inval_all_pou()`, `isb()`.
- `apply_alternatives_module()`: no `stop_machine()` and no cache
  maintenance; `__apply_alternatives()` skips both the clean and the I-cache
  invalidate when `is_module`.
- Module alternatives: the maintenance is `flush_module_icache()` in
  `kernel/module/main.c`, which runs after `post_relocation()` has called
  `module_finalize()`.

**Cache maintenance routines**

- `dcache_clean_poc_nosync()` and `dcache_inval_poc_nosync()`: defined in
  `arch/arm64/mm/cache.S`, missing from the comment in
  `arch/arm64/include/asm/cacheflush.h`; they issue the same operations to
  PoC as the forms without the suffix, without the closing `dsb sy`.
- `arch_sync_dma_for_device()`: calls `dcache_clean_poc_nosync()`, not
  `dcache_clean_poc()`.
- `arch_sync_dma_for_cpu()`: calls `dcache_inval_poc_nosync()`, not
  `dcache_inval_poc()`.
- `arch_sync_dma_flush()` in `arch/arm64/include/asm/cache.h`: the `dsb(sy)`
  that completes them; the DMA core calls it after the sync, for example
  `dma_direct_sync_single_for_device()` in `kernel/dma/direct.h`.
- `CONFIG_ARCH_HAS_BATCHED_DMA_SYNC`: selected by `arch/arm64/Kconfig`;
  without it `arch_sync_dma_flush()` is the empty stub in
  `include/linux/dma-map-ops.h`.
- **Potentially unsafe usage**: calling `dcache_clean_poc_nosync()` or
  `dcache_inval_poc_nosync()`.
  - Unsafe: when no `dsb(sy)` follows before the device or the CPU touches
    the buffer; the maintenance may not have completed.
  - Safe: when `arch_sync_dma_flush()` follows, as
    `dma_direct_sync_single_for_device()` issues it after
    `arch_sync_dma_for_device()`; elsewhere use `dcache_clean_poc()` or
    `dcache_inval_poc()`, which end in `dsb sy`.
- `arch_dma_prep_coherent()`: uses `dcache_clean_poc()`, a clean only, not
  `dcache_clean_inval_poc()`.
- Persistent memory: there is no invalidate-to-PoP routine;
  `arch_invalidate_pmem()` in `arch/arm64/mm/flush.c` uses
  `dcache_inval_poc()`.

## Page table entries

**Software and hardware PTE bits**

- `PTE_PRESENT_INVALID`: is `PTE_NG`, bit 11, and has that meaning only while
  `PTE_VALID` is clear; see `arch/arm64/include/asm/pgtable-prot.h`.
- `pte_write()`: tests `PTE_WRITE` alone; hardware dirty is
  `pte_write() && !pte_rdonly()`.
- Userfaultfd bits: `PTE_UFFD` (bit 58, present entries) and `PTE_SWP_UFFD`
  (bit 3, swap entries); there is no PTE_UFFD_WP or PTE_SWP_UFFD_WP here.
- Userfaultfd accessors: for example `pte_uffd()`, `pte_mkuffd()`,
  `pte_clear_uffd()`, `pte_swp_uffd()`; there is no pte_uffd_wp() in this
  tree.
- Without `CONFIG_HAVE_ARCH_USERFAULTFD_WP`: `PTE_UFFD` and `PTE_SWP_UFFD` are
  both 0 and arm64 defines no accessors; the stubs in
  `include/asm-generic/pgtable_uffd.h` are used.
- Table above `__check_safe_pte_update()`: gives the dirty/writable encoding,
  not a list of safe transitions.
- Present-invalid is not the same as PROT_NONE: `pte_protnone()` also requires
  `!pte_user()` and `!pte_user_exec()`.
- Present-invalid kernel entries exist: `set_memory_valid()` and
  `set_direct_map_invalid_noflush()` in `arch/arm64/mm/pageattr.c` set
  `PTE_PRESENT_INVALID` on linear-map entries, so `pte_present()` stays true
  for them.
- Making a kernel entry valid again: clear `PTE_PRESENT_INVALID`, then set
  `PTE_PRESENT_VALID_KERNEL`, which re-adds nG only through `PTE_MAYBE_NG`;
  see `pte_mkvalid_k()`.
- `set_pageattr_masks()` in `arch/arm64/mm/pageattr.c`: clears before it sets,
  because some callers pass the aliasing bits in both masks.

**Public and private PTE accessors**

- `mm_is_user()` in `arch/arm64/mm/contpte.c`: false for `init_mm` and the EFI
  mm; `__contpte_try_fold()` and `__contpte_try_unfold()` return there, so a
  public accessor never converts a kernel block.
- Public setters strip `PTE_CONT` from the value they are given, with
  `pte_mknoncont()`: `set_pte()`, `set_ptes()`, `ptep_set_access_flags()`.
- `ptep_get()`: has no mm test; on any valid entry with `PTE_CONT`, kernel
  ones included, it returns `contpte_ptep_get()`, the entry with access and
  dirty gathered from the block.
- `set_pte()`: cannot unfold (no mm, no address); it warns once if the entry
  it overwrites is valid with `PTE_CONT`.
- Without `CONFIG_ARM64_CONTPTE` the public names are `#define`s of the `__`
  forms, so a wrong choice changes nothing in such a build.
- Under `arch/arm64/mm/` the only public calls are `get_and_clear_ptes()` in
  `modify_prot_start_ptes()` and `set_ptes()` in `modify_prot_commit_ptes()`,
  both on a user mm.
- **Potentially unsafe usage**: a public accessor that writes an `init_mm` or
  EFI mm entry.
  - Unsafe: when the entry or the new value carries `PTE_CONT`; the bit is
    stripped from the value, nothing is unfolded, and one entry of a live
    block is rewritten on its own.
  - Safe: when neither carries `PTE_CONT`, as `set_pte_at()` in
    `vmap_pte_range()` in `mm/vmalloc.c`; contiguous sizes go to
    `set_huge_pte_at()` there. `mm_is_user()` and `pte_mknoncont()` in
    `set_ptes()` define the limit.

**Writing an entry**

- `__set_pte_complete()`: decides from the entry bits with
  `pte_valid_not_user()`, not from the address or the mm.
- `__set_ptes_anysz()`: the common store path for kernel and user entries, at
  PTE, PMD and PUD size.
- `__sync_cache_and_tags()`: called unconditionally, once, before the first
  store, for `nr * stride` pages; its own tests select user-executable and
  tagged user-accessible entries.
- `__set_pte_nosync()` without `__set_pte_complete()`: `init_pte()` in
  `arch/arm64/mm/mmu.c`; the barrier comes from `pte_clear_fixmap()` at the
  end of `alloc_init_cont_pte()`.
- Higher levels differ from the PTE rule:

  | Setter | Barriers queued when |
  |---|---|
  | `set_pmd()` | `pmd_valid()`, user entries included |
  | `set_pud()` | `pud_valid()`, user entries included |
  | `set_p4d()`, `set_pgd()` | always |
  | `set_pmd_at()`, `set_pud_at()` | `pte_valid_not_user()`, through `__set_ptes_anysz()` |

- `set_swapper_pgd()`: used by `set_pmd()`, `set_pud()`, `set_p4d()` and
  `set_pgd()` for entries in `swapper_pg_dir`; the barriers for the entry it
  stores are never deferred: it issues `dsb(ishst)` and `isb()` itself while
  `rodata_is_rw`, and otherwise gets them from `flush_tlb_kernel_range()` in
  `pgd_clear_fixmap()`.

**Deferred PTE barriers**

- `__switch_to()` in `arch/arm64/kernel/process.c`: issues `dsb(ish)`; it
  does not test or clear `TIF_LAZY_MMU_PENDING` and has no `isb()` of its own.
- Preempted task: the flag stays set in its thread flags; `dsb(ishst)` and
  `isb()` are issued when that task itself next flushes, possibly on another
  CPU.
- Interrupt handler: `is_lazy_mmu_mode_active()` in `include/linux/sched.h`
  is false under `in_interrupt()`, so its own stores get `emit_pte_barriers()`
  at once; the interrupted task's flag is untouched.
- Callers use `lazy_mmu_mode_enable()`, `lazy_mmu_mode_disable()`,
  `lazy_mmu_mode_pause()` and `lazy_mmu_mode_resume()` in
  `include/linux/pgtable.h`; generic and arm64 code reach the `arch_` hooks
  only through these.
- State: `enable_count` and `pause_count` in `current->lazy_mmu_state`;
  `arch_enter_lazy_mmu_mode()` is empty on arm64.
- `lazy_mmu_mode_disable()`: emits pending barriers at every nesting level,
  not only the outermost; so does the first `lazy_mmu_mode_pause()`.
- In interrupt context all four calls do nothing; while paused,
  `lazy_mmu_mode_enable()` and `lazy_mmu_mode_disable()` do nothing and a
  nested pause or resume only changes `pause_count`.
- Sleeping inside a section is allowed on arm64: `split_kernel_leaf_mapping()`
  in `arch/arm64/mm/mmu.c` holds a mutex and allocates inside one.
- **Unsafe usage**: accessing a kernel address whose valid entry was written
  in the current lazy MMU section, before the pending barriers are emitted.
  - Unsafe: the access can take a translation fault; `__do_kernel_fault()`
    recovers through `is_spurious_el1_translation_fault()`, with a
    rate-limited warning.
  - Safe: access after `lazy_mmu_mode_disable()`, as callers of
    `vmap_pte_range()` do.
  - Safe: store inside `lazy_mmu_mode_pause()` / `lazy_mmu_mode_resume()`, as
    `kasan_populate_vmalloc_pte()` in `mm/kasan/shadow.c`; the store then gets
    immediate barriers.
  - Safe: arm64's `ptep_try_set()`, defined under `CONFIG_ARM64_CONTPTE`,
    which calls `emit_pte_barriers()` directly and ignores the mode; without
    the option the generic stub in `include/linux/pgtable.h` stores nothing.

**Levels and folding**

- `pgtable_l4_enabled()` and `pgtable_l5_enabled()`: return
  `vabits_actual == VA_BITS` until `ARM64_ALWAYS_BOOT` is patched in, then
  test the `ARM64_HAS_VA52` capability.
- `vabits_actual`: not a variable; with `VA_BITS > 48` it is a macro that
  reads T1SZ through `read_tcr()`, see `arch/arm64/include/asm/memory.h`.
- `pgtable_l4_enabled()` with `CONFIG_PGTABLE_LEVELS > 3`: constant true when
  `CONFIG_PGTABLE_LEVELS > 4` or without `CONFIG_ARM64_LPA2`; one kernel folds
  at most one level at run time.
- Which level: P4D with 4K pages (5 levels configured), PUD with 16K pages
  (4 levels configured).
- Decision point: `early_map_kernel()` in `arch/arm64/kernel/pi/map_kernel.c`;
  with `CONFIG_ARM64_LPA2` and `!cpu_has_lpa2()` it uses `VA_BITS_MIN` and
  starts one level lower.
- `cpu_has_lpa2()`: tests the stage 1 granule field only, with command-line
  overrides applied; `has_lpa2()` also tests stage 2, for `ARM64_HAS_LPA2`,
  which KVM uses.
- `arm64.nolva`: alias of `id_aa64mmfr2.varange=0`; `mmfr2_varange_filter()`
  then also hides LPA2, so the level is folded.
- `lpa2_is_enabled()`: `TCR_EL1_DS` is set only together with the 52-bit
  T1SZ, in `__cpu_setup` under `ARM64_HAS_VA52` and in `early_map_kernel()`
  through `remap_idmap_for_lpa2()`; true means no level is folded at run time.
- `lpa2_is_enabled()` false on a `CONFIG_ARM64_LPA2` kernel: the one foldable
  level is folded.
- PUD folded: `p4d_none()` and `p4d_bad()` return false, and `p4d_clear()`
  does nothing; P4D folded: the same for `pgd_none()`, `pgd_bad()` and
  `pgd_clear()`.

**Contpte folding and unfolding**

- `__flush_tlb_range()`: `contpte_convert()` passes `PAGE_SIZE`, level 3 and
  `TLBF_NOWALKCACHE`.
- `contpte_try_fold()`: has one caller, `set_ptes()` with `nr == 1`;
  write-protect paths never fold.
- Fold tests: the inline tests `pte_valid()`, not `PTE_USER`;
  `__contpte_try_fold()` then tests `mm_is_user(mm)` and that one folio covers
  the whole block, before it compares entries.
- `contpte_set_ptes()` (`set_ptes()` with `nr > 1`): writes `PTE_CONT`
  directly on every naturally aligned full block of a user mm, with no clear
  and no invalidation; it has no folio or special test of its own.
- Never unfold, act on the whole block instead:
  `contpte_test_and_clear_young_ptes()`, `contpte_clear_flush_young_ptes()`,
  `contpte_clear_young_dirty_ptes()`.

**Reading entries without the lock**

- `contpte_ptep_get_lockless()`: reads the target entry first, not the first
  entry of the block, and returns it as read if it is not valid with
  `PTE_CONT`.
- Block scan: stops as soon as both dirty and young are found; entries after
  that point are neither read nor checked by `contpte_is_consistent()`.
- `ptep_get()`: expects the page table lock; `contpte_ptep_get()` gathers
  bits with no consistency check and no retry.
- Without `CONFIG_ARM64_CONTPTE`: there is no arm64 `ptep_get_lockless()`; the
  generic one in `include/linux/pgtable.h` is a plain `ptep_get()`.
- `pud_offset_lockless()` with the PUD folded: ignores the value `p4d` and
  returns `p4d_to_folded_pud(p4dp, addr)`, computed from the pointer.
- `p4d_offset_lockless()` with the P4D folded: the same, through
  `pgd_to_folded_p4d(pgdp, addr)`.
- `p4d_offset_lockless_folded()`: used in every build with
  `CONFIG_PGTABLE_LEVELS <= 4`; returns `p4d_offset(pgdp, addr)` from the
  original pointer.
- After `p4d_offset_lockless_folded()`: the caller loads the same live entry
  a second time, as the P4D entry; each level still loads it once.
- **Potentially unsafe usage**: passing the address of a local copy of the
  upper entry as `p4dp` or `pgdp` to an offset helper.
  - Unsafe: with the level folded at run time; `p4d_to_folded_pud()` and
    `pgd_to_folded_p4d()` align the pointer down to a page and index it, and
    their `VM_BUG_ON()` checks the pointer against `addr`.
  - Safe: pass the pointer into the live table together with the value read
    from it, as `gup_fast_pud_range()` and `gup_fast_p4d_range()` in
    `mm/gup.c` do.
  - Safe: with `CONFIG_PGTABLE_LEVELS <= 3`, where arm64 defines no
    `pud_offset_lockless()` and the generic one in `include/linux/pgtable.h`
    passes `&(p4d)` to `pud_offset()` in
    `include/asm-generic/pgtable-nopud.h`, which returns the pointer as it is.

## TLB invalidation

**Invalidation functions**

- Rows that differ from the older API; all are in
  `arch/arm64/include/asm/tlbflush.h` except `tlb_flush()` in
  `arch/arm64/include/asm/tlb.h`:

| Function | Scope | Walk cache dropped | Waits |
|---|---|---|---|
| `flush_tlb_page()` | one user page, all CPUs | no, leaf only | yes |
| `__flush_tlb_page()` | one user page, level 3 | never | unless `TLBF_NOSYNC` |
| `__flush_tlb_range()` | user range, caller's stride and level | unless `TLBF_NOWALKCACHE` | unless `TLBF_NOSYNC` |
| `__flush_tlb_kernel_pgtable()` | one kernel address, all CPUs | yes | yes, plus `isb()` |
| `local_flush_tlb_all()` | everything, this CPU only | yes | `dsb(nsh)` plus `isb()` |
| `arch_tlbbatch_add_pending()` | user range, level 3 | no | no |
| `arch_tlbbatch_flush()` | no TLBI except the `__repeat_tlbi_sync()` repeat | n/a | yes |
| `tlb_flush()` | the mmu_gather range | if `tlb->freed_tables` or `tlb->unshared_tables` | yes |

- `__flush_tlb_range()`: signature is `(vma, start, end, stride, tlb_level,
  flags)`; it takes no `bool` last-level argument.
- Not defined anywhere in this tree: __flush_tlb_range_nosync(),
  __flush_tlb_page_nosync(), flush_tlb_page_nosync(),
  local_flush_tlb_page_nonotify(), local_flush_tlb_contpte(),
  flush_tlb_pgtable().
- `local_flush_tlb_page()` and `flush_tlb_kernel_page()`: defined by other
  architectures only; arm64 defines neither.
- No-wait, local and no-notify variants: `__flush_tlb_range()` or
  `__flush_tlb_page()` with `TLBF_NOSYNC`, `TLBF_NOBROADCAST`,
  `TLBF_NONOTIFY`; see "Invalidation flags".
- `tlb_flush()` with `tlb->fullmm`: issues `flush_tlb_mm()` only if
  `tlb->freed_tables`, otherwise no invalidation at all.
- `flush_tlb_kernel_range()` leftovers: walk-cache entries for the
  intermediate levels; `__flush_tlb_kernel_pgtable()` drops them for one
  address, and code in `arch/arm64/mm/mmu.c` calls it after clearing a table
  entry and before freeing the table, for example `pmd_free_pte_page()`.

**Invalidation flags**

- Flags type: `tlbf_t`, a `__bitwise` type in
  `arch/arm64/include/asm/tlbflush.h`; `__flush_tlb_range()` and
  `__flush_tlb_page()` both end in `__do_flush_tlb_range()`, which interprets
  the flags.

| Flag | Changes | A caller |
|---|---|---|
| `TLBF_NONE` | broadcast, drops walk cache, notifies, waits | `flush_tlb_range()` |
| `TLBF_NOWALKCACHE` | leaf-only op (`vale1is` instead of `vae1is`) | `contpte_convert()` |
| `TLBF_NOSYNC` | no completing barrier | `__ptep_clear_flush_young()`, `arch_tlbbatch_add_pending()` |
| `TLBF_NONOTIFY` | no `mmu_notifier_arch_invalidate_secondary_tlbs()` call | `flush_tlb_fix_spurious_fault()` |
| `TLBF_NOBROADCAST` | local op `vale1`, `dsb(nshst)` before, `dsb(nsh)` after | `__ptep_set_access_flags_anysz()` in `arch/arm64/mm/fault.c` |

- `__flush_tlb_page()`: ORs in `TLBF_NOWALKCACHE` itself and uses level 3.
- Refused combination: `TLBF_NOBROADCAST` without `TLBF_NOWALKCACHE` hits
  `BUG()` at run time in `__do_flush_tlb_range()`; there is no build-time
  check.
- `__flush_tlb_page()` cannot reach that `BUG()`, since it always adds
  `TLBF_NOWALKCACHE`.
- Limit excess in `__do_flush_tlb_range()`: it calls `flush_tlb_mm()` and
  returns before any flag is tested, so the flush is broadcast, drops the
  walk cache, waits and notifies whatever flags were passed.
- `TLBF_NOBROADCAST` without `TLBF_NOSYNC`: completion is a bare
  `dsb(nsh)`, not `__tlbi_sync_s1ish()`.
- `TLBF_NOBROADCAST` without `TLBF_NONOTIFY`: the notifier is still called,
  as in `__ptep_set_access_flags_anysz()`.
- **Potentially unsafe usage**: `TLBF_NOSYNC`.
  - Unsafe: when the entry was unmapped or made stricter and nothing later
    completes the invalidation before the caller relies on it.
  - Safe: `arch_tlbbatch_add_pending()`; `arch_tlbbatch_flush()` later runs
    `__tlbi_sync_s1ish_batch()`.
  - Safe: `__ptep_clear_flush_young()`; `__ptep_test_and_clear_young()`
    clears only the access flag, so a stale entry maps the same page.
- **Potentially unsafe usage**: `TLBF_NOBROADCAST`.
  - Unsafe: when the change unmaps or reduces permission; other CPUs keep
    the old entry.
  - Safe: when the change only makes the entry more permissive and a later
    fault on it goes through `handle_pte_fault()`, as for
    `__ptep_set_access_flags()`; a CPU with a stale entry takes a write
    fault and `fix_spurious_fault()` in `mm/memory.c` calls
    `flush_tlb_fix_spurious_fault()`.

**Barriers around invalidation**

- `__tlbi()`: one asm statement, no erratum repeat inside it.
- Erratum repeat: `__repeat_tlbi_sync()` issues one extra TLBI and a second
  `dsb(ish)`, once per sync helper, not once per TLBI.
- Capability name: `ARM64_WORKAROUND_REPEAT_TLBI_SYNC`; there is no
  ARM64_WORKAROUND_REPEAT_TLBI in this tree.
- Helpers, all in `arch/arm64/include/asm/tlbflush.h`, each starting with
  `dsb(ish)`:

| Helper | Repeat op | Extra step | Used for |
|---|---|---|---|
| `__tlbi_sync_s1ish(mm)` | `vale1is`, operand 0 | `sme_dvmsync(mm)` | user mappings of one mm |
| `__tlbi_sync_s1ish_batch()` | `vale1is`, operand 0 | `sme_dvmsync_batch()` | `arch_tlbbatch_flush()` |
| `__tlbi_sync_s1ish_kernel()` | `vale1is`, operand 0 | none | kernel mappings, `flush_tlb_all()` |
| `__tlbi_sync_s1ish_hyp()` | `vale2is`, operand 0 | none | KVM hyp code |

- SME step: compiled in under `CONFIG_ARM64_ERRATUM_4193714` and active with
  `ARM64_WORKAROUND_4193714`; an empty stub without the option.
- `sme_do_dvmsync()` in `arch/arm64/kernel/fpsimd.c`: sends a waiting IPI
  with `smp_call_function_many()` to `mm_cpumask(mm)`, or to
  `sme_active_cpus` for the batch form; returns at once if the mask is empty.
- IPI consequence: when the mask is not empty,
  `smp_call_function_many_cond()` in `kernel/smp.c` asserts that interrupts
  are enabled (`lockdep_assert_irqs_enabled()`), which then applies to
  callers of the user and batch sync helpers.
- Local completion: `local_flush_tlb_all()` and the `TLBF_NOBROADCAST` path
  use a bare `dsb(nsh)`, with no repeat and no SME step.
- **Potentially unsafe usage**: completing a broadcast TLBI with a bare
  `dsb(ish)`.
  - Unsafe: when that `dsb(ish)` is the last barrier before the caller
    relies on the invalidation; the `__repeat_tlbi_sync()` repeat and, for
    a user mm, `sme_dvmsync()` are skipped.
  - Safe: as an intermediate barrier between a stage-2 and a stage-1
    invalidation in a sequence that ends in `__tlbi_sync_s1ish_hyp()`, as
    `__kvm_tlb_flush_vmid_ipa()` in `arch/arm64/kvm/hyp/vhe/tlb.c` does.
  - Safe: ending in the matching helper, as `flush_tlb_mm()` does with
    `__tlbi_sync_s1ish()`.

**Invalidation operands**

- `__TLBI_VADDR()` and `__tlbi_user()`: `#undef`ed at the end of
  `arch/arm64/include/asm/tlbflush.h`, so unusable outside it.
- No __TLBI_VADDR_RANGE() or __tlbi_user_level() here; `__tlbi_range()`
  builds the range operand with `FIELD_PREP()` and the `TLBIR_ASID_MASK`
  family of masks.
- Ops are `tlbi_op` functions, not macro arguments;
  `__flush_s1_tlb_range_op()` and `__flush_s2_tlb_range_op()` paste `r##op`,
  so an op needs an r-prefixed twin, for example `vale1is()` and
  `rvale1is()`.
- KPTI second op: done inside the user op functions such as `vae1is()`;
  `vaale1is()`, the hyp ops and the stage-2 ops issue one TLBI only.
- `__tlbi_level_asid()` hint: written for any `level <= 3`, level 0
  included, when the CPU has `ARM64_HAS_ARMv8_4_TTL`.
- Unknown level: `TLBI_TTL_UNKNOWN`, which is `INT_MAX`; 0 does not mean
  unknown.
- `__tlbi_range()` hint: does not test `ARM64_HAS_ARMv8_4_TTL`; the two-bit
  field holds levels 1 to 3, and level 0 or above 3 is written as 0.
- `__flush_tlb_range_op()` order: single ops until 64K aligned (LPA2 only),
  range ops from scale 3 downwards, one single op last for an odd page.
- Limit: `__flush_tlb_range_limit_excess()`, used by both
  `__do_flush_tlb_range()` and `flush_tlb_kernel_range()`.
- Limit with range ops: `pages > MAX_TLBI_RANGE_PAGES`.
- Limit without range ops: `pages >= (MAX_DVM_OPS * stride) >> PAGE_SHIFT`;
  the constant is `MAX_DVM_OPS`, there is no MAX_TLBI_OPS definition.
- **Unsafe usage**: `pages * PAGE_SIZE` not a multiple of `stride` in
  `__flush_tlb_range_op()`.
  - Unsafe: the single-op path adds `stride` and the loop runs while
    `addr != end`, so it steps past `end`.
  - Safe: go through `__flush_tlb_range()`, which rounds both ends to
    `stride`; `__do_flush_tlb_range()` and `__flush_tlb_range_op()` do not
    round.
  - Safe: `flush_tlb_kernel_range()` rounds to `PAGE_SIZE` itself.
- **Unsafe usage**: calling `__flush_tlb_range_op()` with more than
  `MAX_TLBI_RANGE_PAGES` pages on a CPU with range ops.
  - Unsafe: `__TLBI_RANGE_NUM()` does not clamp to 31 and `FIELD_PREP()`
    masks the excess silently, while `addr` advances by the full count.
  - Safe: test `__flush_tlb_range_limit_excess()` first, as
    `flush_tlb_kernel_range()` does.
  - Safe: split the range, as `kvm_tlb_flush_vmid_range()` in
    `arch/arm64/kvm/hyp/pgtable.c` does with `min(pages,
    MAX_TLBI_RANGE_PAGES)`.
- **Unsafe usage**: a fixed level hint for a range that may hold entries of
  another level or table entries.
  - Unsafe: the hinted invalidation may skip those entries.
  - Safe: `TLBI_TTL_UNKNOWN`, as `flush_tlb_range()` passes.
  - Safe: a level derived from the mapping size, as
    `__flush_hugetlb_tlb_range()` in `arch/arm64/include/asm/hugetlb.h`
    does from `stride`.
  - Safe: the `TLBI_TTL_UNKNOWN` that `tlb_get_level()` returns when
    `tlb->freed_tables` is set or other than exactly one cleared level is
    recorded.

## Break-before-make

**Replacing a live entry**

- `contpte_convert()` in `arch/arm64/mm/contpte.c`: always clears all
  `CONT_PTES` entries with `__ptep_get_and_clear()`; the `__flush_tlb_range()`
  before `__set_ptes()` is skipped when `system_supports_bbml3()`.
- `__ptep_set_access_flags()`: inline wrapper in
  `arch/arm64/include/asm/pgtable.h`; the `cmpxchg_relaxed()` loop is in
  `__ptep_set_access_flags_anysz()` in `arch/arm64/mm/fault.c`, shared with
  `pmdp_set_access_flags()` and `huge_ptep_set_access_flags()`.
- `__ptep_set_access_flags_anysz()`: does not call `pgattr_change_is_safe()`;
  it masks `entry` to `PTE_RDONLY | PTE_AF | PTE_WRITE | PTE_DIRTY` itself.
- `__ptep_set_access_flags_anysz()` with `dirty`: flushes the local CPU only
  (`TLBF_NOWALKCACHE | TLBF_NOBROADCAST`); remote stale entries are left to a
  later fault, where `fix_spurious_fault()` in `mm/memory.c` calls
  `flush_tlb_fix_spurious_fault()` or `flush_tlb_fix_spurious_fault_pmd()`,
  from `handle_pte_fault()` and `__handle_mm_fault()`.
- Kernel splits: `split_pud()`, `split_pmd()`, `split_contpmd()` and
  `split_contpte()` in `arch/arm64/mm/mmu.c` overwrite the live entry with
  `set_pmd()`, `__set_pte()`, `__pud_populate()` or `__pmd_populate()`: no
  invalid step, no TLBI. There is no __set_pmd() or __set_pud().
- `stage2_try_break_pte()` in `arch/arm64/kvm/hyp/pgtable.c`: leaves the TLBI
  out when the walk has `KVM_PGTABLE_WALK_SKIP_BBM_TLBI`.
- `ARM64_WORKAROUND_2645198`: on affected CPUs the clear of a user-executable
  entry is followed by a TLBI before the new entry is written; see
  `huge_ptep_modify_prot_start()` in `arch/arm64/mm/hugetlbpage.c`.
- **Potentially unsafe usage**: writing a valid entry of another size (block
  to table, `PTE_CONT` set or cleared) over a valid entry with no invalid
  step.
  - Unsafe: while a CPU that lacks the capability can walk the table.
  - Safe: `split_kernel_leaf_mapping()` splits only when
    `system_supports_bbml3()`, or before capabilities are finalised with one
    CPU online and `page_alloc_available`; `linear_map_requires_bbml3` is
    only set when the boot CPU passed `cpu_supports_bbml3()`.
  - Safe: `linear_map_split_to_ptes()`: every other CPU waits in
    `wait_linear_map_split_to_ptes` on the idmap; the boot CPU calls
    `flush_tlb_kernel_range()` before it releases them.
  - Safe: `arch_kfence_init_pool()`: reaches `range_split_to_ptes()` only
    when `force_pte_mapping()` and `kfence_early_init` are both false, under
    `pgtable_split_lock`; with `kfence_early_init` false,
    `force_pte_mapping()` is false only when BBML3 is supported.
- **Potentially unsafe usage**: a plain store of a valid entry over a valid
  entry in a live user mm.
  - Unsafe: when the new value drops an access or dirty state that hardware
    may set meanwhile; the cases are the first two warnings of
    `__check_safe_pte_update()`, listed under "Changes allowed without
    break-before-make".
  - Safe: a `cmpxchg_relaxed()` loop on the entry, as in
    `__ptep_set_access_flags_anysz()` and `___ptep_set_wrprotect()`.
  - Safe: `__ptep_get_and_clear()` first, fold dirty and young into the new
    value, then set, as `contpte_convert()` does.
- **Potentially unsafe usage**: changing permissions in place on entries that
  have `PTE_CONT`.
  - Unsafe: when only part of the contiguous block is changed.
  - Safe: the whole block; `contpte_wrprotect_ptes()` first unfolds any
    partly covered block with `contpte_try_unfold_partial()`.
  - Safe: `contpte_ptep_set_access_flags()`: updates all `CONT_PTES` entries
    when the write bit is unchanged, and unfolds first when it changes.

**Changes allowed without break-before-make**

- `pgattr_change_is_safe()` mask: `PTE_PXN | PTE_RDONLY | PTE_WRITE | PTE_NG |
  PTE_SWBITS_MASK`, nothing else.
- `pgattr_change_is_safe()` tests before the mask: true when old or new is
  not valid; false for a pfn change and for a change that clears `PTE_NG`.
- Not in the mask, so a change is rejected: for example `PTE_USER`,
  `PTE_UXN`, `PTE_GP`, `PTE_AF`, `PTE_CONT`.
- `PTE_CONT`: there is no test for it; only a change of the bit is rejected,
  by the mask comparison.
- `MT_NORMAL` and `MT_NORMAL_TAGGED`: `PTE_ATTRINDX_MASK` is added to the mask
  when old and new are each one of the two, in either direction; there is no
  MTE test.
- `BUG_ON(!pgattr_change_is_safe())`: in `init_pte()`, `init_pmd()` and
  `alloc_init_pud()` only; `alloc_init_cont_pmd()` has none.
- `pmd_set_huge()` and `pud_set_huge()`: return 0 and leave the entry
  unchanged when `pgattr_change_is_safe()` fails.
- `init_pmd()` and `alloc_init_pud()` on such a refusal: `WARN_ON()` fires;
  the `BUG_ON()` after it compares the old value with the unchanged entry.
- `alloc_init_cont_pte()` and `alloc_init_cont_pmd()`: do not add `PTE_CONT`
  when `pte_range_has_valid_noncont()` or `pmd_range_has_valid_noncont()`
  finds a valid entry without it.
- `__check_safe_pte_update()`: called from `__set_ptes_anysz()` before each
  store, not from `__set_pte_complete()`.
- `__check_safe_pte_update()` tests nothing unless `CONFIG_DEBUG_VM` is on,
  old and new are both valid, and the mm is `current->active_mm` or has
  `mm_users` above 1.
- `__check_safe_pte_update()` issues three `VM_WARN_ONCE()`; the store still
  happens:

| Condition | Message |
|---|---|
| new entry not young, whatever the old was | "racy access flag clearing" |
| old entry writable and new entry not dirty | "racy dirty state clearing" |
| `!pgattr_change_is_safe()` | "unsafe attribute change" |

- Unchecked writers: `__set_pte()`, `set_pmd()` and `set_pud()` call neither
  check; the `pageattr_ops` walkers in `arch/arm64/mm/pageattr.c` and the
  split helpers use them.
- `set_memory_x()` and `set_memory_nx()`: change `PTE_MAYBE_GP` (`PTE_GP` when
  `system_supports_bti_kernel()`), which is outside the mask, through those
  unchecked writers.

**BBM level capability**

- Name: `HAS_BBML3` in `arch/arm64/tools/cpucaps`, so `ARM64_HAS_BBML3`;
  described as "BBM Level 3".
- There is no HAS_BBML2_NOABORT, system_supports_bbml2_noabort(),
  cpu_supports_bbml2_noabort() or has_bbml2_noabort() in this tree;
  `system_supports_bbml3()`, `cpu_supports_bbml3()` and `has_bbml3()` do
  those jobs.
- `cpu_supports_bbml3()` in `arch/arm64/kernel/cpufeature.c`: true when
  `ID_AA64MMFR2_EL1.BBM` is at least `ID_AA64MMFR2_EL1_BBM_3`, or when the
  MIDR is in `supports_bbml3_list`; either is enough.
- `cpu_supports_bbml3()` reads the register with
  `__read_sysreg_by_encoding()`, not the sanitised value; there is no
  command-line option to turn the capability off.
- Type: `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE`, not
  `ARM64_CPUCAP_SYSTEM_FEATURE`; the capability stays set only if every
  early CPU matches.
- Secondary CPU at boot that lacks it: `update_cpu_capabilities()` clears the
  capability; the CPU stays online.
- `linear_map_maybe_split_to_ptes()`: called from `setup_system_features()`;
  runs when `linear_map_requires_bbml3` is set and `system_supports_bbml3()`
  is false.
- `linear_map_split_to_ptes()`: leaves the kernel image alias from
  `lm_alias(_stext)` to `lm_alias(__init_begin)` unsplit.
- Late CPU that lacks it, system has it: `verify_local_cpu_caps()` calls
  `cpu_die_early()`; no panic.
- Late CPU that has it, system lacks it: allowed
  (`ARM64_CPUCAP_PERMITTED_FOR_LATE_CPU`); the capability stays off.
- `split_kernel_leaf_mapping()` first test: returns 0 when
  `linear_map_requires_bbml3` is false or `is_kfence_address()` holds for
  `start`.
- `split_kernel_leaf_mapping()` without `system_supports_bbml3()`:

| State | Result |
|---|---|
| capabilities finalised | returns 0, no split |
| not finalised, `page_alloc_available` false | `WARN_ON()`, `-EBUSY` |
| not finalised, more than one CPU online | `WARN_ON()`, `-EBUSY` |
| not finalised, one CPU online, allocator up | splits |

- `linear_map_requires_bbml3`: set once in `map_mem()` as
  `!force_pte_mapping() && can_set_direct_map()`.
- `arch_add_memory()`: applies `force_pte_mapping()` to hot-added memory too.

**Changing kernel mappings**

- `change_memory_common()`: accepts only a range inside one area from
  `find_vm_area()` whose flags have `VM_ALLOC` and not `VM_ALLOW_HUGE_VMAP`;
  a linear-map address gets `-EINVAL`.
- `-EINVAL` from `change_memory_common()`: no warning, and tested before
  `numpages == 0`, so a zero-page call on a bad address fails too.
- Linear alias: changed only when `rodata_full` is set and `set_mask` or
  `clear_mask` equals `PTE_RDONLY` exactly; `can_set_direct_map()` is not
  consulted.
- `rodata_full`: defaults to `true`; cleared by `rodata=off` and
  `rodata=noalias` in `arch_parse_debug_rodata()`.
- `can_set_direct_map()`: has no BBM capability term.
- `set_memory_valid()`: no range check; goes straight to
  `__change_memory_common()`.
- Range update: `update_range_prot()` uses
  `walk_kernel_page_table_range_lockless()` with `pageattr_ops`; arm64 has no
  `change_page_range()`.
- `update_range_prot()`: calls `split_kernel_leaf_mapping()` on every call; a
  non-zero return gives `WARN_ON_ONCE()` and no walk.
- `split_kernel_leaf_mapping()` returning 0 does not mean the range is split;
  see "BBM level capability" for the early returns.
- Leaf only partly covered at walk time: `pageattr_pud_entry()` and
  `pageattr_pmd_entry()` hit `WARN_ON_ONCE()` and return `-EINVAL`; the leaf
  is not changed.
- `pageattr_pte_entry()`: has no `PTE_CONT` test; a contiguous run that was
  not split is changed one entry at a time.
- **Potentially unsafe usage**: changing linear-map permissions from atomic
  context.
  - Unsafe: when `linear_map_requires_bbml3` is set, `system_supports_bbml3()`
    holds and the address is outside the KFENCE pool;
    `split_kernel_leaf_mapping()` then takes the mutex `pgtable_split_lock`
    and can allocate with `GFP_PGTABLE_KERNEL`.
  - Safe: a KFENCE pool address, as in `kfence_protect_page()`;
    `is_kfence_address()` returns before the mutex, and the pool is
    PTE-mapped by `arm64_kfence_map_pool()`, by `arch_kfence_init_pool()`, or
    with the rest of the linear map when `force_pte_mapping()` is true.
  - Safe: with `debug_pagealloc_enabled()`, as in `__kernel_map_pages()`;
    `force_pte_mapping()` is then true, so `linear_map_requires_bbml3` is
    false and the function returns before the mutex.

## Tagged addresses and MTE

**Tag removal helpers**

- `untagged_addr()` and `__untagged_addr()`: both are macros in
  `arch/arm64/include/asm/memory.h`.
- `untagged_addr()` on a value with bit 55 set: returned unchanged, so a
  kernel pointer keeps its KASAN tag, whatever the top byte is.
- `__tag_reset()`: is `__untagged_addr()` only under `CONFIG_KASAN_SW_TAGS` or
  `CONFIG_KASAN_HW_TAGS`; otherwise it expands to `(addr)` and changes nothing.
- `__tag_reset()` on a kernel pointer, with either option on: sets the top byte
  to 0xff; this is what `kasan_reset_tag()` and `virt_addr_valid()` use.
- `access_ok()`: untags only if `CONFIG_ARM64_TAGGED_ADDR_ABI` is on and the
  caller has `PF_KTHREAD` or `TIF_TAGGED_ADDR`; otherwise a tagged pointer
  fails the range check.
- `__access_ok()`: the generic one in `include/asm-generic/access_ok.h`; it
  does not untag.
- `mm_untag_mask()`: arm64 defines it in
  `arch/arm64/include/asm/mmu_context.h`; it returns `-1UL >> 8` for every mm,
  whatever the task setting.
- `mm_untag_mask()` on arm64 takes no user address and untags nothing; it is
  only reported, as `untag_mask` in `fs/proc/array.c`.

**Arithmetic on user addresses**

- `find_vma()` in `mm/mmap.c`: passes `addr` straight to `mt_find()`; no VMA
  lookup helper untags.
- **Potentially unsafe usage**: a VMA lookup or range comparison on a
  user-supplied address without `untagged_addr()`.
  - Unsafe: when nothing earlier rejected or stripped a tag; the tagged value
    is above every VMA, so `find_vma()` returns `NULL`.
  - Safe: untag a copy first, as `do_mprotect_pkey()` in `mm/mprotect.c` and
    `arm64_notify_segfault()` in `arch/arm64/kernel/traps.c` do.
  - Safe: a tagged value was rejected when the address was registered, as
    `kvm_set_memory_region()` in `virt/kvm/kvm_main.c` does with
    `mem->userspace_addr != untagged_addr(mem->userspace_addr)`.
  - Safe: the address is left tagged so that the range check fails, as
    `validate_unaligned_range()` in `mm/userfaultfd.c` does against
    `mm->task_size`.
- Entry points that untag: search for `untagged_addr(`; the mm syscalls that
  untag do it in their own file, and `mm/mmap.c` has only the `munmap` one.
- `brk`: the syscall in `mm/mmap.c` does not untag.
- `mm/userfaultfd.c`: has no `untagged_addr()` call.
- `madvise`: untagged by `get_untagged_addr()`, called from
  `madvise_do_behavior()` in `mm/madvise.c`, not in `do_madvise()`.
- `get_untagged_addr()`: uses `untagged_addr()` when `mm` is `current->mm`,
  because only a per-VMA lock may be held and `untagged_addr_remote()` would
  trip its assertion.
- `untagged_addr_remote()`: the generic macro in `include/linux/uaccess.h`;
  it calls `mmap_assert_locked()` and does not take the lock.
- `__get_user_pages()` in `mm/gup.c`: untags `start` itself with
  `untagged_addr_remote()`; `get_user_page_vma_remote()` then calls
  `vma_lookup()` on the address as it was passed, and `__access_remote_vm()`
  in `mm/memory.c` untags before calling it.
- `do_mem_abort()` in `arch/arm64/mm/fault.c`: hands the tagged `far` to the
  handler; `do_page_fault()`, `do_translation_fault()` and `do_bad_area()` each
  untag a local copy.

**Page tag state flags**

- Hugetlb folios: use the same `PG_mte_tagged` and `PG_mte_lock` bits, in
  `folio->flags.f`; there are no HPG_ bits for MTE in
  `enum hugetlb_page_flags`.
- Per-page helpers on a hugetlb folio: `VM_WARN_ON_ONCE()`; the hugetlb folio
  helpers warn on any other folio.
- Hugetlb flags: cleared by `arch_clear_hugetlb_flags()` in
  `arch/arm64/include/asm/hugetlb.h`, called from `add_hugetlb_folio()` and
  `free_huge_folio()`; the MTE part runs only if `system_supports_mte()`.
- Non-hugetlb pages: no arm64 code clears either flag;
  `__free_pages_prepare()` in `mm/page_alloc.c` clears them with the rest of
  `PAGE_FLAGS_CHECK_AT_PREP`.
- `__split_folio_to_order()` in `mm/huge_memory.c`: gives the first page of
  each new folio the `PG_arch_2` and `PG_arch_3` of the original head,
  replacing that page's own bits.

**Tag initialisation at mapping time**

- `__sync_cache_and_tags()`: static inline in
  `arch/arm64/include/asm/pgtable.h`; its only caller is `__set_ptes_anysz()`,
  which passes `nr * stride` pages and calls it before the first store.
- `mte_sync_tags()` is called only if all four hold: `system_supports_mte()`,
  `pte_access_permitted_no_overlay(pte, false)`, `!pte_special(pte)`,
  `pte_tagged(pte)`.
- `pte_access_permitted_no_overlay()` with `write` false: tests `PTE_VALID`
  and `PTE_USER` only; unlike `pte_access_permitted()` it does not read
  `POR_EL0`.
- Ordering barrier: the `smp_wmb()` at the end of `mte_sync_tags()` in
  `arch/arm64/kernel/mte.c`, separate from the one in `set_page_mte_tagged()`.
- That `smp_wmb()`: runs on the hugetlb and the normal path, also when this
  caller lost `try_page_mte_tagging()` and wrote no tags.
- PTE store after it: `__set_pte_nosync()`, a `WRITE_ONCE()`;
  `__set_pte_complete()` emits no barrier for a user PTE.
- Hugetlb folio in `mte_sync_tags()`: `nr_pages` is ignored;
  `folio_nr_pages()` pages are cleared, starting at `pte_page(pte)`.

**Making a tagged page visible**

- `copy_highpage()` on a non-hugetlb source: ignores the result of
  `try_page_mte_tagging(to)`, has no warning there, and copies the tags
  whenever `page_mte_tagged(from)`.
- `memcmp_pages()`: reads no tags; with equal data and either page
  `page_mte_tagged()` it returns `addr1 != addr2`, so zero only for the same
  page.
- `tag_clear_highpages()`: takes `(page, numpages, clear_pages)`; there is no
  singular tag_clear_highpage in this tree.
- `tag_clear_highpages()` without `system_supports_mte()`: returns
  `clear_pages` unchanged; when that is `true`, `post_alloc_hook()` then
  zeroes the data itself.
- `tag_clear_highpages()` with MTE: returns `false`; uses
  `mte_zero_clear_page_tags()` if `clear_pages`, else `mte_clear_page_tags()`,
  which leaves the data alone.
- **Unsafe usage**: returning after `try_page_mte_tagging()` gave `true`
  without calling `set_page_mte_tagged()`.
  - Unsafe: every later caller of `try_page_mte_tagging()` on that page spins
    in `smp_cond_load_acquire()` with no timeout.
  - Safe: do every test that can bail out before taking the lock, as
    `mte_restore_tags()` in `arch/arm64/mm/mteswap.c` does with `xa_load()`.
- **Potentially unsafe usage**: writing a page's tags without calling
  `try_page_mte_tagging()` first.
  - Unsafe: while `PG_mte_lock` may still be clear; a later `mte_sync_tags()`
    wins the lock and zeroes the tags just written.
  - Safe: call it and ignore the result when overwriting is intended, as
    `copy_highpage()` and `kvm_vm_ioctl_mte_copy_tags()` do; once it returns,
    no other caller can win the lock.
  - Safe: the page already has `PG_mte_tagged`; `__access_remote_tags()` in
    `arch/arm64/kernel/mte.c` expects that and has a `WARN_ON_ONCE()` for it.
  - Safe: `empty_zero_page`, which `cpu_enable_mte()` clears once with
    `mte_clear_page_tags()`; its PTEs are made with `pte_mkspecial()`, for
    example in `do_anonymous_page()`, and `__sync_cache_and_tags()` calls
    `mte_sync_tags()` only for `!pte_special(pte)`.
- **Unsafe usage**: installing a tagged PTE for a swapped-in page before
  `arch_swap_restore()`.
  - Unsafe: `mte_sync_tags()` wins the lock and zeroes the tags;
    `mte_restore_tags()` then gets `false` and skips the restore.
  - Safe: restore first, as `do_swap_page()` does before `set_ptes()` and
    `shmem_swapin_folio()` does before `shmem_add_to_page_cache()`.

## FP, SVE and SME state

**Saved state format**

- `thread.fp_type` in `struct thread_struct`: says whether the saved vector
  state is in `thread.uw.fpsimd_state` or in `thread.sve_state`; `fp_type` in
  `struct cpu_fp_state` is a pointer to it (for a vCPU, to
  `vcpu->arch.fp_type`).
- `TIF_SVE` set with `thread.fp_type == FP_STATE_FPSIMD`: a valid state, left
  for example by a save made while `to_save` was `FP_STATE_FPSIMD`;
  `task_fpsimd_load()` then clears `TIF_SVE` and loads
  `thread.uw.fpsimd_state`, not `sve_state`.
- `TIF_SME` set: `thread.sve_state` and `thread.sme_state` must both be
  allocated; `fpsimd_save_user_state()` writes `sve_state` with no NULL test
  when the live SVCR has SM set; see `do_sme_acc()`.
- `FP_STATE_CURRENT` in `to_save`: what `fpsimd_bind_task_to_cpu()` sets for an
  ordinary task; `kvm_arch_vcpu_ctxsync_fp()` sets `FP_STATE_SVE` or
  `FP_STATE_FPSIMD` from `vcpu_has_sve()`.
- `to_save` in `struct cpu_fp_state`: set when a state is bound, and rewritten
  outside `arch/arm64/kernel/fpsimd.c` by `fpsimd_syscall_enter()` and
  `fpsimd_syscall_exit()` in `arch/arm64/kernel/entry-common.c`;
  `fpsimd_save_user_state()` only reads it.

**Lazy state tracking**

- `TIF_FOREIGN_FPSTATE` clear: the registers hold the state that this CPU's
  `fpsimd_last_state` describes; `fpsimd_save_user_state()` decides whether
  to save from the flag alone and saves through `fpsimd_last_state`, never
  through `current->thread`.
- Between `kvm_arch_vcpu_ctxsync_fp()` and `kvm_arch_vcpu_put_fp()`, when
  `guest_owns_fp_regs()`: the flag is clear on the host task while
  `fpsimd_last_state` describes the vCPU, so a softirq's `kernel_neon_begin()`
  saves guest registers into the vCPU.
- `kvm_arch_vcpu_load_fp()`: saves and flushes the host task's state at once
  with `fpsimd_save_and_flush_cpu_state()` and sets `fp_owner` to
  `FP_STATE_FREE`; the host state is not kept live. With `IN_NESTED_ERET` or
  `IN_NESTED_EXCEPTION` set it returns before both.
- `kvm_arch_vcpu_ctxsync_fp()`: when `guest_owns_fp_regs()`, binds the vCPU's
  state with `fpsimd_bind_state_to_cpu()` and clears `TIF_FOREIGN_FPSTATE`.
- `kvm_arch_vcpu_ctxflush_fp()`: runs before guest entry; if
  `TIF_FOREIGN_FPSTATE` is set it sets `fp_owner` to `FP_STATE_FREE`.
- `fpsimd_flush_task_state()`: sets `fpsimd_cpu` to `NR_CPUS` and sets
  `TIF_FOREIGN_FPSTATE` on the task it is given, current or not; it also sets
  `thread.kernel_fpsimd_state` to NULL.
- `fpsimd_flush_cpu_state()`: static to `arch/arm64/kernel/fpsimd.c`; besides
  clearing `fpsimd_last_state.st` it runs `sme_smstop()`, which
  `kvm_arch_vcpu_load_fp()` relies on.
- `fpsimd_update_current_state()`: only writes `thread.uw.fpsimd_state` and,
  for `FP_STATE_SVE`, calls `fpsimd_to_sve()`; it loads no register and
  changes no flag, so its callers save and flush first, as
  `restore_sigframe()` does.
- `struct cpu_fp_state` holds copies of the `sve_state` and `sme_state`
  pointers and of both VLs, taken at bind time; code that allocates a buffer
  while the state is live must rebind, as `do_sve_acc()` and `do_sme_acc()`
  do with `fpsimd_bind_task_to_cpu()`.

**FPSIMD context ownership**

- `get_cpu_fpsimd_context()` and `put_cpu_fpsimd_context()`: static to
  `arch/arm64/kernel/fpsimd.c`; code elsewhere uses wrappers such as
  `fpsimd_save_and_flush_current_state()`, or runs with IRQs disabled as
  `kvm_arch_vcpu_ctxsync_fp()` does.
- Not `CONFIG_PREEMPT_RT`, IRQs disabled: `get_cpu_fpsimd_context()` does
  nothing; it calls `local_bh_disable()` only when `irqs_disabled()` is false.
- `put_cpu_fpsimd_context()`, not `CONFIG_PREEMPT_RT`: tests
  `irqs_disabled()` again, so the IRQ state must be the same at get and at
  put.
- There is no have_cpu_fpsimd_context() helper and no per-CPU busy flag in
  this tree.
- How callees state the assumption:

  | Function | Check |
  |---|---|
  | `fpsimd_save_user_state()`, `task_fpsimd_load()` | `WARN_ON(preemptible())` |
  | `fpsimd_bind_state_to_cpu()` | `WARN_ON(!in_softirq() && !irqs_disabled())` |
  | `fpsimd_thread_switch()` | `WARN_ON_ONCE(!irqs_disabled())` |
  | `fpsimd_bind_task_to_cpu()`, `fpsimd_flush_cpu_state()` | comment only |

- `fpsimd_save_and_flush_cpu_state()`: has `WARN_ON(preemptible())` but does
  not need the caller to hold the context; it disables IRQs itself with
  `local_irq_save()`.
- `WARN_ON(preemptible())`: passes under a plain `preempt_disable()`, where
  softirqs can still run on a non-RT kernel; it does not prove the context is
  held.
- **Potentially unsafe usage**: writing the saved FP state of `current`
  (`thread.uw.fpsimd_state`, `thread.sve_state`, `thread.fp_type`,
  `thread.svcr`) without the context held.
  - Unsafe: while `TIF_FOREIGN_FPSTATE` is clear and IRQs are enabled;
    `fpsimd_save_user_state()`, run from a softirq's `kernel_neon_begin()` or
    from `fpsimd_thread_switch()`, overwrites the edit from the registers.
  - Safe: after `fpsimd_save_and_flush_current_state()`, as
    `restore_sigframe()` and `compat_restore_vfp_context()` do;
    `fpsimd_save_user_state()` returns at once while `TIF_FOREIGN_FPSTATE` is
    set, and `fpsimd_thread_switch()` keeps it set while `fpsimd_cpu` is
    `NR_CPUS`.
  - Safe: with IRQs disabled, where `get_cpu_fpsimd_context()` itself takes
    nothing on a non-RT kernel; `kvm_arch_vcpu_ctxsync_fp()` rebinds and
    clears `TIF_FOREIGN_FPSTATE` that way and asserts `irqs_disabled()`.

**Kernel-mode SIMD**

- `kernel_neon_begin()` and `kernel_neon_end()`: each takes a
  `struct user_fpsimd_state *`; see `arch/arm64/include/asm/neon.h`.
- NULL argument: allowed only in task context that is not preemptible;
  `kernel_neon_begin()` has
  `WARN_ON((preemptible() || in_serving_softirq()) && !state)`;
  `kernel_fpu_begin()` in `arch/arm64/include/asm/fpu.h` passes NULL after
  `preempt_disable()`.
- Task-level buffer: recorded in `thread.kernel_fpsimd_state`; written only at
  context switch, by `fpsimd_save_kernel_state()`.
- Softirq caller's buffer on a non-RT kernel: receives the registers of the
  task-level section it interrupted, not its own; `kernel_neon_end()` reloads
  them from it. This is why a softirq caller needs a buffer.
- The buffer need not be initialised; `scoped_ksimd()` declares it
  `__uninitialized`.
- `kernel_neon_begin()` with `TIF_KERNEL_FPSTATE` already set: `BUG_ON()`
  unless serving a softirq on a non-RT kernel; the
  `WARN_ON(current->thread.kernel_fpsimd_state != NULL)` is reached only with
  the flag clear.
- `scoped_ksimd()`: declares a `struct user_fpsimd_state` on the stack and
  runs the following statement under guard class `ksimd`, which calls
  `kernel_neon_begin()` and `kernel_neon_end()` on that buffer.

**Preemption inside kernel-mode SIMD**

- Task context: the section stays preemptible and may migrate;
  `kernel_neon_begin()` calls `put_cpu_fpsimd_context()` before it returns.
- Softirq section on a non-RT kernel: sets no flag, so nothing would save its
  registers at a context switch; it relies on softirq context not being
  preempted.
- `kernel_neon_end()` with `TIF_KERNEL_FPSTATE` clear: returns at once; this
  is the softirq section that interrupted no task-level section.
- `may_use_simd()`: has no `irqs_disabled()` test and no per-CPU busy flag; it
  is true in task context with IRQs disabled.

**Vector state across system calls**

- `fpsimd_syscall_enter()`: changes no thread flag and no saved state;
  `TIF_SVE` and `TIF_FOREIGN_FPSTATE` are left as they are.
- `TIF_SVE` afterwards: stays set if the state stays live for the whole
  syscall; if the state is saved and reloaded, `task_fpsimd_load()` sees
  `FP_STATE_FPSIMD` and clears it, and the next SVE use traps to
  `do_sve_acc()`.
- Streaming mode: `sme_smstop_sm()` at entry whenever
  `system_supports_sme()`; the ZA enable and ZA contents are kept.
- `sme_smstop_sm()` changes only the live SVCR; `thread.svcr` of `current`
  is not updated until the next `fpsimd_save_user_state()`.
- `fpsimd_syscall_exit()`: only writes `FP_STATE_CURRENT` to
  `fpsimd_last_state.to_save`; it loads nothing. `el0_svc()` calls it after
  `arm64_syscall_exit_to_user_mode()`, which is where a pending reload runs.

**Changing the vector length**

- `change_live_vector_length()`: after saving the live state, keeps
  `thread.fp_type`, `TIF_SVE`, `TIF_SME` and the SM bit of `thread.svcr`; the
  state is not converted to `FP_STATE_FPSIMD`.
- Vector contents after the change: V0-V31, FPSR and FPCR are preserved; with
  `FP_STATE_SVE` the new `sve_state` holds the V registers zero-padded at
  `thread_get_cur_vl()`, so the upper Z bits, P and FFR are zero.
- `thread.sve_state`: replaced by a new zeroed buffer on every change, SVE or
  SME, sized by `__sve_state_size()` for the larger of the two VLs; it does
  not call `sve_free()`.
- SME VL change: clears only `SVCR_ZA_MASK` and replaces `sme_state` with a
  zeroed buffer, so ZA and ZT0 are lost; streaming mode is kept.
- SVE VL change: leaves `sme_state` and the ZA enable alone.
- The new buffers are allocated before anything is changed; `-ENOMEM` leaves
  the task as it was.
- Live state: `fpsimd_save_and_flush_current_state()` for `current`,
  `fpsimd_flush_task_state()` for another task, so the registers are reloaded
  from memory before the task next runs in userspace.
- VL picked by `find_supported_vector_length()` equal to the current VL:
  `change_live_vector_length()` is not called and nothing is flushed.
- Callers must be able to sleep: the buffers are allocated with `GFP_KERNEL`.
- The task must be `current` or not running; for another task nothing saves
  its registers. In-tree callers pass `current` (prctl) or a ptrace target.
- The VL in effect afterwards may differ from the request:
  `find_supported_vector_length()` picks a supported one, and with
  `PR_SVE_SET_VL_ONEXEC` the current VL is unchanged. `sve_set_common()`
  re-reads `task_get_vl()` and returns `-EIO` if register data was supplied
  for another VL.
- **Potentially unsafe usage**: writing `SVCR_SM_MASK` in a task's
  `thread.svcr`.
  - Unsafe: when the saved vector state is left as it was;
    `thread_get_cur_vl()` switches between the SVE and SME VL with that bit,
    and `preserve_sve_context()` copies `sve_state` at that VL whenever the
    bit is set, whatever `thread.fp_type` says.
  - Unsafe: while the task's state is live; `fpsimd_save_user_state()`
    overwrites `thread.svcr` from the SVCR register.
  - Safe: leaving streaming mode with `task_smstop_sm()` on a task whose state
    is saved and flushed, as `setup_return()` does.
  - Safe: replacing the whole vector state, as `sve_set_common()` and
    `restore_sve_fpsimd_context()` do: flush first, `sve_alloc()` with flush,
    set `thread.fp_type`, and when entering streaming mode `sme_alloc()` and
    `TIF_SME`.

**SME streaming mode and ZA**

- `task_smstop_sm()`: when SM is set in `thread.svcr`, zeroes the saved V
  registers, sets the saved FPSR to 0x0800009f, zeroes `thread.uw.fpmr` if
  `system_supports_fpmr()`, clears `SVCR_SM_MASK` and sets `thread.fp_type` to
  `FP_STATE_FPSIMD`.
- `task_smstop_sm()` leaves alone: `TIF_SVE`, `TIF_SME`, FPCR, the ZA enable,
  `sve_state`, `sme_state` and the registers.
- `task_smstop_sm()` acts on the saved state only; the task's state must not
  be live when it is called.
- Callers of `task_smstop_sm()`: `setup_return()` and
  `arch_dup_task_struct()`; ptrace does not use it, `sve_set_common()` clears
  the bit itself and rewrites the whole state.

**Signal frame records**

- `SVE_SIG_FLAG_SM`: not compared with the task's current SVCR; it selects the
  mode restored. Set: `sme_alloc()`, `SVCR_SM_MASK` and `TIF_SME` are set, VL
  must equal `task_get_sme_vl()`. Clear, with a payload: `SVCR_SM_MASK` is
  cleared and `TIF_SVE` set.
- SVE record with payload: after the copy into `sve_state`,
  `fpsimd_update_current_state()` overwrites the low 128 bits of every Z
  register with the V registers of the `fpsimd_context` record; FPSR and FPCR
  come from that record too.
- VL test: made before the header-only test, so a header-only record must also
  carry the task's current SVE VL; `preserve_sve_context()` writes the VL even
  when there is no payload.
- Size rejections in `restore_sve_fpsimd_context()`: both are `<`; a record
  larger than `SVE_SIG_CONTEXT_SIZE()` for the VL is accepted.
  `preserve_sve_context()` writes the size rounded up to 16.
- Record without `SVE_SIG_FLAG_SM`: the feature test is
  `system_supports_sve()` or `system_supports_sme()`; there is no test of
  `system_supports_sve()` alone.
- SVE record in a written frame: always present when SVE or SME is supported;
  it has a payload when `thread.fp_type == FP_STATE_SVE` or streaming mode is
  on, and `TIF_SVE` is not consulted.
- ZA record in a written frame: always present when SME is supported,
  header-only when ZA is off; the ZT record is present only with SME2 and ZA
  on.
- GCS record in a written frame: present when `system_supports_gcs()` and
  `current->thread.gcspr_el0` is non-zero.

## Faults and user access

**Page fault handling**

- `do_page_fault()` access chain, in order: `is_el0_instruction_abort()`,
  `is_gcs_fault()`, `is_write_abort()`, else read; `vm_flags` has no value
  before the chain.
- EL1 instruction abort: not matched by `is_el0_instruction_abort()`; it falls
  through to `is_write_abort()`, which tests no EC, and else to the read case;
  it gets no `FAULT_FLAG_INSTRUCTION`.
- Read case: `VM_READ | VM_WRITE`, plus `VM_EXEC` only when `ARM64_HAS_EPAN` is
  absent.
- There is no esr_is_gcs_fault() here; `is_gcs_fault()` in
  `arch/arm64/mm/fault.c` does that, and it matches EL0 and EL1 data aborts
  (`esr_is_data_abort()`).
- `is_el1_permission_fault()`: matches EL1 data aborts and EL1 instruction
  aborts.
- TTBR0 address with `is_el1_permission_fault()` true: dies at once only for an
  EL1 instruction abort or when `insn_may_access_user()` is false.
- `insn_may_access_user()` true: the fault goes on to the VMA lookup and
  `handle_mm_fault()`; `fixup_exception()` runs only if that path ends at
  `no_context`.
- `insn_may_access_user()` in `arch/arm64/mm/extable.c`: any entry type at
  `regs->pc` other than `EX_TYPE_UACCESS_CPY` passes,
  `EX_TYPE_KACCESS_ERR_ZERO` included.
- `EX_TYPE_UACCESS_CPY` entries: pass only when `ESR_ELx_WNR` matches
  `EX_DATA_UACCESS_WRITE`, so a fault on the kernel side of a user copy fails
  `insn_may_access_user()`; `ex_handler_uaccess_cpy()` refuses the fixup on
  the same test.
- `is_pkvm_stage2_abort()` (`ESR_ELx_S1PTW` with `is_pkvm_initialized()`):
  tested after the die-at-once test and before the VMA lookup; kernel mode
  goes to `no_context`, user mode gets `SEGV_ACCERR`.
- `do_mem_abort()` in kernel mode, handler returned non-zero (`do_bad()`):
  `die_kernel_fault()` with `inf->name`; `fixup_exception()` is not tried.
- `do_sea()` in kernel mode: `arm64_notify_die()` calls `die()`;
  `fixup_exception()` is not tried, even at a uaccess instruction.
- `fault_from_pkey()`: runs before `handle_mm_fault()`, after the
  `vma->vm_flags & vm_flags` test passes, on both lookup paths.
- `ESR_ELx_Overlay`: not read for the pkey decision; only `data_abort_decode()`
  prints it.
- `is_invalid_gcs_access()`: called in `do_page_fault()` after
  `lock_vma_under_rcu()` succeeds and before the `vm_flags` test.
- Faults without `FAULT_FLAG_USER`: jump to `lock_mmap` and never take the
  `lock_vma_under_rcu()` path.

**User access primitives**

- `__uaccess_mask_ptr()`: one `bic` that clears bit 55; no compare with
  `TASK_SIZE_MAX`, no conditional select, no speculation barrier, and the tag
  byte is kept.
- `__access_ok()` in `include/asm-generic/access_ok.h`: range test only;
  callers apply the mask after `access_ok()`, search `uaccess_mask_ptr`.
- `get_user` is defined as `__get_user`, and `put_user` as `__put_user`; both
  forms run `might_fault()`, `access_ok()` and the mask.
- `__raw_get_user(x, ptr, label)`: on a fault jumps to `label` and leaves `x`
  unassigned; `__get_user_error()` does the zeroing and sets `-EFAULT`.
- `__get_mem_asm()` with `CONFIG_CC_HAS_ASM_GOTO_OUTPUT`: for a user access
  the extable entry is `_ASM_EXTABLE_UACCESS()`, which names `wzr` for both
  registers, so the fixup only branches.
- **Potentially unsafe usage**: running anything but the access instructions
  between `uaccess_ttbr0_enable()` and `uaccess_ttbr0_disable()`.
  - Unsafe: when a caller expression or call inside the window reaches the
    scheduler directly; `check_and_switch_context()` in
    `arch/arm64/mm/context.c` skips `cpu_switch_mm()` when
    `system_uses_ttbr0_pan()`, so nothing reopens the window when the task
    runs again.
  - Safe: a fault, interrupt or preemption taken as an exception inside the
    window; `__swpan_entry_el1` in `arch/arm64/kernel/entry.S` closes TTBR0
    and records the state in `PSR_PAN_BIT` of the saved pstate, and
    `__swpan_exit_el1` reopens it.
  - Safe: evaluating `x` and `ptr` into temporaries before the enable, as
    `__raw_get_user()` and `__raw_put_user()` do.
- `uaccess_ttbr0_disable()`: tests only `system_uses_ttbr0_pan()` and keeps no
  nesting count; an accessor with its own window, such as
  `raw_copy_from_user()`, leaves an enclosing `user_access_begin()` window
  closed when it returns.
- `user_access_begin()`: `access_ok()` plus `uaccess_ttbr0_enable()`; it never
  changes PSTATE.PAN, so on hardware PAN it opens nothing.
- `__uaccess_ttbr0_enable()`: one `isb()`, after both the TTBR1_EL1 and the
  TTBR0_EL1 write.
- Futex ops with `ARM64_HAS_LSUI` (`CONFIG_ARM64_LSUI`): `__lsui_llsc_body()`
  in `arch/arm64/include/asm/lsui.h` picks the LSUI variants, which use only
  `uaccess_ttbr0_enable()`; the LL/SC variants use
  `uaccess_enable_privileged()`.
- `uaccess_enable_privileged()`: calls `mte_enable_tco()` first, which with
  `CONFIG_KASAN_HW_TAGS` and `ARM64_MTE` sets PSTATE.TCO (tag checks off);
  `uaccess_disable_privileged()` clears it.
- `mte_enable_tco()`: emits no instruction without `CONFIG_KASAN_HW_TAGS`;
  with it, a `nop` unless the CPU has `ARM64_MTE`.
- `uaccess_enable_privileged()` with software PAN: returns after
  `uaccess_ttbr0_enable()` and never reaches `__uaccess_disable_hw_pan()`.

## Model gaps

### Other mistakes models make

- Models take `fpsimd_flush_cpu_state()` to clear only the binding and set
  `TIF_FOREIGN_FPSTATE`. Its `sme_smstop()` leaves `PSTATE.SM` and
  `PSTATE.ZA` clear after `kernel_neon_begin()` and
  `fpsimd_save_and_flush_cpu_state()`, when SME is supported; see
  `arch/arm64/kernel/fpsimd.c`.
- Models take `__get_user()` and `__put_user()` to skip `access_ok()`.
  `__raw_get_user()` and `__raw_put_user()` in
  `arch/arm64/include/asm/uaccess.h` do neither `access_ok()` nor the mask.
- Models take exit to EL0 to save the shadow call stack pointer. `scs_save`
  (`arch/arm64/include/asm/scs.h`) is only in `cpu_switch_to()` and
  `call_on_irq_stack()`.
- Models take the order of `arch/arm64/tools/cpucaps` to be cosmetic.
  `arch/arm64/tools/gen-cpucaps.awk` numbers names in file order, and
  `cpu_enable_sme2()` and `cpu_enable_fa64()` have a `BUILD_BUG_ON()` on
  their number against `ARM64_SME`.
- Models take `do_notify_resume()` to be arm64's return-to-user work loop.
  The generic loop calls `arch_exit_to_user_mode_work()` in
  `arch/arm64/include/asm/entry-common.h` and `arch_do_signal_or_restart()`
  in `arch/arm64/kernel/signal.c`.
