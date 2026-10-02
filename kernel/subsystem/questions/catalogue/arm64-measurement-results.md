# What the arm64 measurement found

Three models were asked the 90 questions in `arm64-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C. Reader C
is the most current (it answered for kernels up to 7.1), reader A is a few
releases behind it, and reader B is older still and weakest; which models they
were does not matter here. The hand-written guide was never checked against
current sources, so differences between it and the built guide are expected and
are noted below. KVM, the hypervisor code and the GIC drivers have their own
guides and were not measured here.

## What all three readers got wrong

- **The FP/SIMD assembly file is gone.** All three listed
  arch/arm64/kernel/entry-fpsimd.S, and two added fpsimdmacros.h. Neither
  exists. `fpsimd_save_state()`, `sve_save_state()`, `sme_save_state()` and the
  load routines are inline assembly in `arch/arm64/include/asm/fpsimd.h`. The
  helpers sve_set_vq() and sme_set_vq() that readers A and C hung the
  "self-synchronising" comment on are gone too; `task_fpsimd_load()` writes the
  length with `sysreg_clear_set_s()` and no comment, and the only such comment
  is on `write_vl()` in `vec_probe_vqs()`.
- **The break-before-make capability is `ARM64_HAS_BBML3`.** Every reader used
  BBML2_NOABORT and system_supports_bbml2_noabort(). The tree has
  `system_supports_bbml3()` and `cpu_supports_bbml3()`, which accepts
  `ID_AA64MMFR2_EL1.BBM` of 3 or more and otherwise an allowlist of CPU
  models. Its type is `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE`; one reader
  guessed a system feature, one called the list a denylist. It covers changes
  of block size and of the contiguous bit only, not of output address or memory
  type.
- **The C entry code is built on the generic entry library.** All three gave
  enter_from_kernel_mode() and exit_to_kernel_mode(), calling irqentry_enter()
  and irqentry_exit(). The tree has `arm64_enter_from_kernel_mode()`, which
  calls `irqentry_enter_from_kernel_mode()`, then `mte_check_tfsr_entry()` and
  `mte_disable_tco_entry()`; the exit is split into a preemption step,
  `local_daif_mask()`, `mte_check_tfsr_exit()` and
  `irqentry_exit_to_kernel_mode_after_preempt()`. All missed
  `sme_enter_from_user_mode()`, `sme_exit_to_user_mode()` and
  `rseq_note_user_irq_entry()` on the user paths. arm64_enter_nmi() is gone;
  the callers use `irqentry_nmi_enter()`.
- **The FPAC syndrome built from a failed authenticated ERET** keeps
  `ESR_ELx_ERET_ISS_ERETA | ESR_ELx_IL`. Two readers said it keeps only the key
  bit, one said the ISS is zero. It is injected only with FPACCOMBINE and no
  pending illegal execution state; otherwise the mangled ELR is used.
- **Initial SCTLR values.** All three had `INIT_SCTLR_EL2_MMU_ON` getting the
  entry and return synchronisation bits from `SCTLR_EL2_RES1`. That mask is
  `UL(0)` because the `SCTLR_EL2` description has no `Res1` line; the macro
  names `SCTLR_ELx_EIS | SCTLR_ELx_EOS` itself, and `INIT_SCTLR_EL2_MMU_OFF`
  sets neither.
- **The SVE and SME buffers are typed.** All three said `void *`. They are the
  opaque `struct arm64_sve_state *` and `struct arm64_sme_state *`.
- **Consumers of generated masks.** None could name them. Besides the SCTLR
  init values they are `DECLARE_FEAT_MAP()` in `arch/arm64/kvm/config.c`, which
  uses the complement of RES0 and RES1 as the set of bits that need a feature
  entry, `FORCE_RES0()` and `FORCE_RES1()`, and `check_feature_map()`, which
  complains about any bit left uncovered.
- **Page fault details.** A kernel fault on a user address dies at once only
  when `is_el1_permission_fault()` is true and `insn_may_access_user()` finds
  no suitable exception table entry. `fault_from_pkey()` deliberately ignores
  the overlay bit of the syndrome and asks `arch_vma_access_permitted()`. A
  guarded control stack fault counts as a write.
- **Exception level setup.** `init_el2_state` does not set HCR_EL2 or the
  vector length registers; `init_el2_hcr` and `finalise_el2_state` do.
  `__finalise_el2` requires the EL2 MMU to be off, and the stub also accepts
  `HVC_GET_ICH_VTR_EL2`.

## What readers A and B got wrong as well

- **TLB invalidation interface.** Both said there is no flags argument and named
  __flush_tlb_range_nosync() and a last_level bool. `__flush_tlb_range()` and
  `__flush_tlb_page()` take a `tlbf_t`: `TLBF_NOWALKCACHE`, `TLBF_NOSYNC`,
  `TLBF_NONOTIFY`, `TLBF_NOBROADCAST`; broadcast off with the walk cache kept is
  a `BUG()`. The completing barrier is wrapped in `__tlbi_sync_s1ish()` and its
  `_batch`, `_kernel` and `_hyp` forms, which also carry the errata work: a
  dummy invalidate and second barrier under
  `ARM64_WORKAROUND_REPEAT_TLBI_SYNC` (both used an older capability name and
  put the repeat inside `__tlbi()`), and an IPI to CPUs running SME code under
  `ARM64_WORKAROUND_4193714`, which neither had heard of. The operation limit is
  `MAX_DVM_OPS`.
- **Stack overflow check.** Both tied it to CONFIG_VMAP_STACK and to EL1. It
  is in every `kernel_ventry`, unconditionally; it tests bit `THREAD_SHIFT` of
  SP, which works because stacks are aligned to twice their size; an exception
  taken while already on the overflow stack carries on.
- **Switching to the IRQ stack.** Reader A said `call_on_irq_stack()` masks
  nothing, reader B that it masks IRQs for the whole call. It masks all of
  DAIF around each of the two switches and restores the caller's mask before
  calling the handler.
- **BRK dispatch.** Both described register_kernel_break_hook(). There is no
  registration: `call_el1_break_hook()` is a fixed chain of `IS_ENABLED()`
  tests.
- **Kernel PTE barriers.** `__set_pte_complete()` queues barriers only for a
  valid kernel entry, and in lazy MMU mode it sets `TIF_LAZY_MMU_PENDING`
  instead of issuing them. `set_pmd()` and its relatives go through the same
  queue. After a preemption only the `dsb` in `__switch_to()` is guaranteed;
  the `isb` comes when the flag is flushed. `ptep_try_set()` and
  `set_swapper_pgd()` issue the barriers directly.
- **Pending interrupt priority sync.** Reader A put `pmr_sync()` behind a
  static key, reader B behind an erratum. It is `dsb sy` patched to a nop by an
  alternative callback on `ARM64_HAS_GIC_PRIO_RELAXED_SYNC`.
- **Tag removal.** `untagged_addr()` is not gated by the tagged address ABI; it
  ANDs the address with its sign extension from bit 55, so a kernel address
  keeps its tag. `mm_untag_mask()` always returns `-1UL >> 8`. `__tag_reset()`
  does nothing without KASAN tags.
- **Kernel-mode SIMD.** `kernel_neon_begin()` and `kernel_neon_end()` take a
  `struct user_fpsimd_state *`. Reader B did not know; reader A said NULL is
  fine in softirq. NULL is accepted only from non-preemptible task context,
  the buffer also holds task-level kernel state that a softirq user displaces,
  and the two calls must be given the same pointer.
- **System calls and vector state.** `fpsimd_syscall_enter()` does not clear
  `TIF_SVE`; it leaves streaming mode, flushes the live non-FPSIMD state and
  sets `fpsimd_last_state.to_save` to `FP_STATE_FPSIMD`, and the exit hook sets
  it back to `FP_STATE_CURRENT`.
- **Vector length change.** `change_live_vector_length()` does not clear
  `TIF_SVE` or change `fp_type`, never clears streaming mode, and clears ZA
  only for an SME change.
- **Page table levels.** `lpa2_is_enabled()` reads `TCR_EL1.DS` and only
  changes the descriptor format; it is neither a capability nor what folds a
  level. Folding is decided by `pgtable_l4_enabled()` and
  `pgtable_l5_enabled()`.
- **Names.** PTE_UFFD_WP for `PTE_UFFD` (A, and C too); PTE_PROT_NONE and
  PTE_DEVMAP for `PTE_PRESENT_INVALID` (B); cpus_have_const_cap() (B);
  asid2idx() (A); cpu_set_idmap_tcr_t0sz() (A and C); on_sdei_stack() (B);
  arch_jump_label_transform() for the queue and apply pair (A); emulate_mrs()
  for `do_emulate_mrs()` (A); a .altinstr_replacement section where the tree
  uses `.subsection 1` (B and C); __no_ptrauth (A).

## What only reader B got wrong

Almost every answer of B's was more than two thirds rewritten. Beyond the above:

- `DAIF_PROCCTX_NOIRQ` is I and F, not I alone, and `GIC_PRIO_PSR_I_SET` is
  written to the priority mask register.
- `cpus_have_final_cap()` calls `BUG()` before finalisation, not a warning, and
  `alternative_has_cap_likely()` and `alternative_has_cap_unlikely()` both
  return false until patched.
- Errata use `ARM64_CPUCAP_LOCAL_CPU_ERRATUM`, which is optional for a late
  CPU, so a late CPU that needs a workaround the system has not enabled is
  killed.
- `try_page_mte_tagging()` takes `PG_mte_lock`, and losers wait for
  `PG_mte_tagged`.
- `aarch64_insn_patch_text()` always stops the machine, and it is what kprobes
  arm and disarm with.
- The second syndrome field is bits 55:32.
- `flush_tlb_kernel_range()` uses the last-level `vaale1is` and so keeps
  walk-cache entries, which `__flush_tlb_kernel_pgtable()` exists to drop.

## What the readers already knew

The files apart from the FP assembly, the documentation, the entry points for
each job, the interrupt priority masking scheme and the DAIF helpers (A and C),
the capability test helpers (A and C), what to touch to add a capability (A and
C), the MTE page flag protocol and the mapping-time tag initialisation (A and
C), lazy FP state tracking and the SME state (A and C), and, for reader C
alone, the TLB flags, the stack overflow check, the PTE setters, tag removal,
permission overlays and the vector length change.

## Where the hand-written guide is stale

- It says a DSB is required between tag stores and the PTE update and lists its
  absence as a bug. The tree orders them with `smp_wmb()`, in
  `mte_sync_tags()` and `set_page_mte_tagged()`.
- It names `__primary_switch()` as a place that must follow a TLBI with an ISB.
  That function no longer invalidates anything; the boot-time TLBIs are in
  `__cpu_setup` and in `arch/arm64/kernel/pi/map_kernel.c`.
- It speaks of FEAT_BBML2 and "the CPU-feature cap". The capability is
  `ARM64_HAS_BBML3`, and the code that depends on it is `contpte_convert()` and
  `split_kernel_leaf_mapping()`.
- It treats folded page table levels as a build-time property
  (`PGTABLE_LEVELS`). Levels are also folded at run time.
- It has nothing on the TLB flags, the sync helpers, lazy MMU mode and
  `TIF_LAZY_MMU_PENDING`, the argument to `kernel_neon_begin()`, the entry code
  names, or how the tree tests capabilities.
- Its sections on the GIC system registers and the redistributor write-pending
  bits belong to the GIC guides and are not rebuilt here.
- It cites two commits by SHA and an architecture manual section by number.
  A built guide does neither; the rules it draws from the manual are kept only
  where the tree shows them, as code or as a comment.
- Its ESR section, including the worked FPAC example, matches the tree and is
  kept as four questions.

## What was left out of the build set, and why

The build set has 65 of the 90 questions. Reader B gets nearly everything
wrong, so the choice was by importance and by what readers A and C miss, not by
dropping whatever one reader knows. Left out:

- `arm64.docs`, `arm64.entry-points`: every reader answers them.
  `arm64.selftests`: real, but no reader was far off.
- `arm64.sme-state`, `arm64.fp-traps`, `arm64.fp-ptrace`: readers A and C have
  the mechanism; the state format and vector length questions carry the names.
- `arm64.nmi-paths`, `arm64.kpti-trampoline`, `arm64.asid-allocator`,
  `arm64.ttbr-switch`, `arm64.memory-layout`, `arm64.icache-sync`,
  `arm64.tlb-batch`: places to look more than rules, each confined to a file
  or two with a good comment.
- `arm64.esr-fsc-helpers`, `arm64.idreg-sanitisation`, `arm64.add-erratum`,
  `arm64.mte-modes`: narrow, and the errors were details.
- `arm64.fault-handling`: all readers were weak, but it needs a hundred words
  to say anything and overlaps the mm guides.
- `arm64.ptrauth`, `arm64.gcs`, `arm64.poe`, `arm64.spectre`,
  `arm64.boot-flow`, `arm64.suspend-resume`, `arm64.el0-emulation`: all weak
  for A and B, none of them a topic of the hand-written guide, and together
  they would add a quarter to the size. They are the first to bring back if
  the guide is allowed to grow.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 230 corrections, 39% rewritten on average
reader B: 285 corrections, 79% rewritten on average
reader C: 163 corrections, 19% rewritten on average

question                          reader A      reader B      reader C
arm64.core-files                   1% ( 1)       7% ( 5)       5% ( 2)
arm64.entry-points                 1% ( 1)      23% ( 4)       0% ( 0)
arm64.docs                         0% ( 0)       3% ( 1)       0% ( 0)
arm64.selftests                   22% ( 1)      31% ( 1)      25% ( 3)
arm64.esr-layout                  16% ( 2)      80% ( 2)       0% ( 0)
arm64.esr-abort-iss               53% ( 4)      38% ( 1)       7% ( 2)
arm64.esr-fsc-helpers             31% ( 1)      90% ( 4)      21% ( 2)
arm64.esr-il-synthesis            49% ( 1)      78% ( 3)      42% ( 4)
arm64.esr-eret-fpac               17% ( 3)      82% ( 4)      15% ( 1)
arm64.esr-iss-usage               24% ( 3)      82% ( 2)      36% ( 1)
arm64.brk-dispatch                31% ( 5)      91% ( 3)      32% ( 1)
arm64.vector-entry-asm            62% ( 5)      79% ( 6)      30% ( 4)
arm64.entry-isb                   51% ( 1)      72% ( 1)      27% ( 2)
arm64.kpti-trampoline             45% ( 2)      86% ( 4)      11% ( 1)
arm64.entry-c-sequence            58% ( 6)      90% ( 5)      32% ( 4)
arm64.daif-helpers                21% ( 1)      55% ( 2)       3% ( 1)
arm64.handler-masks               25% ( 2)      88% ( 1)       6% ( 1)
arm64.nmi-paths                   61% ( 2)      89% ( 1)       4% ( 1)
arm64.pmr-masking                 11% ( 2)      90% ( 1)       0% ( 0)
arm64.pmr-sync-usage              32% ( 1)      80% ( 2)      17% ( 1)
arm64.stacks                      14% ( 4)      49% ( 7)       9% ( 4)
arm64.stack-overflow              47% ( 4)      82% ( 3)       0% ( 0)
arm64.sp-switch-usage             51% ( 2)      88% ( 2)      13% ( 1)
arm64.sysreg-accessors            42% ( 4)      76% ( 3)      10% ( 1)
arm64.fixed-register-insn         60% ( 5)      87% ( 3)      13% ( 1)
arm64.sysreg-file-format          54% ( 1)      91% ( 4)      20% ( 1)
arm64.sysreg-resx-masks           11% ( 1)      88% ( 1)      23% ( 1)
arm64.sysreg-mask-consumers       75% ( 1)      94% ( 1)      46% ( 2)
arm64.sctlr-init                  40% ( 1)      83% ( 1)      53% ( 1)
arm64.conditional-resx            29% ( 1)      92% ( 1)      31% ( 1)
arm64.isb-after-write-usage       42% ( 3)      79% ( 4)      11% ( 3)
arm64.self-sync-writes            55% ( 4)      86% ( 2)      39% ( 4)
arm64.readback-usage              41% ( 2)      80% ( 1)      32% ( 2)
arm64.cpucap-types                26% ( 1)      62% ( 5)      10% ( 2)
arm64.cap-check-helpers           21% ( 2)      81% ( 4)       0% ( 0)
arm64.idreg-sanitisation          20% ( 2)      84% ( 1)      24% ( 1)
arm64.add-capability               3% ( 1)      78% ( 3)      13% ( 3)
arm64.add-erratum                 18% ( 3)      68% ( 4)      15% ( 2)
arm64.alternatives                52% ( 5)      84% ( 5)      16% ( 2)
arm64.insn-patching-api           55% ( 4)      70% ( 4)      26% ( 2)
arm64.patching-sync-usage         31% ( 3)      87% ( 3)      21% ( 2)
arm64.cache-maint-names           12% ( 2)      56% ( 5)      71% ( 1)
arm64.icache-sync                 38% ( 2)      84% ( 2)      31% ( 1)
arm64.pgtable-config              56% ( 3)      89% ( 5)       0% ( 0)
arm64.pte-bits                    35% ( 3)      69% ( 3)       4% ( 1)
arm64.pte-setters                 45% ( 2)      79% ( 3)       0% ( 0)
arm64.pte-barrier-batching        61% ( 2)      91% ( 4)      36% ( 4)
arm64.ptep-accessors              26% ( 4)      69% ( 3)      23% ( 3)
arm64.contpte-fold                37% ( 3)      79% ( 3)      23% ( 3)
arm64.lockless-walk               24% ( 1)      79% ( 2)       4% ( 1)
arm64.lockless-walk-usage         30% ( 1)      81% ( 1)      18% ( 2)
arm64.tlb-api                     49% ( 3)      65% ( 6)      17% ( 3)
arm64.tlb-flags                   95% ( 1)      96% ( 1)       5% ( 2)
arm64.tlb-barrier-template        87% ( 1)      91% ( 3)      23% ( 2)
arm64.tlb-operands                37% ( 1)      88% ( 2)      15% ( 1)
arm64.tlb-batch                   34% ( 1)      87% ( 3)      32% ( 2)
arm64.bbm-safe-changes            25% ( 7)      83% ( 4)      10% ( 5)
arm64.bbm-usage                   31% ( 3)      81% ( 3)      13% ( 2)
arm64.bbm-level                   70% ( 4)      89% ( 4)      24% ( 2)
arm64.kernel-mapping-changes      42% ( 4)      86% ( 3)      21% ( 1)
arm64.asid-allocator              44% ( 3)      80% ( 3)      14% ( 1)
arm64.ttbr-switch                 49% ( 4)      87% ( 3)      28% ( 3)
arm64.fault-handling              75% ( 4)      83% ( 5)      53% ( 3)
arm64.memory-layout               26% ( 2)      72% ( 2)      19% ( 1)
arm64.untagged-addr               29% ( 2)      92% ( 5)       0% ( 0)
arm64.untag-usage                 38% ( 3)      74% ( 3)       8% ( 1)
arm64.mte-page-flags               6% ( 1)      85% ( 4)       8% ( 1)
arm64.mte-sync-tags               14% ( 1)      82% ( 3)       5% ( 1)
arm64.mte-tag-init-usage          29% ( 1)      88% ( 3)      62% ( 2)
arm64.mte-modes                   41% ( 2)      87% ( 6)      28% ( 4)
arm64.fp-state-tracking           14% ( 2)      85% ( 5)       4% ( 1)
arm64.fp-state-format             38% ( 4)      90% ( 4)       7% ( 2)
arm64.fp-context-ownership        44% ( 3)      84% ( 2)      34% ( 2)
arm64.kernel-neon                 72% ( 4)      90% ( 6)      12% ( 2)
arm64.fp-syscall                  79% ( 2)      85% ( 3)      13% ( 3)
arm64.fp-traps                    69% ( 3)      89% ( 3)      16% ( 3)
arm64.vl-change                   67% ( 4)      88% ( 4)       0% ( 0)
arm64.vl-change-usage             19% ( 1)      85% ( 2)      51% ( 2)
arm64.sme-state                   10% ( 1)      82% ( 2)       6% ( 1)
arm64.fp-signal                   24% ( 2)      85% ( 2)      10% ( 1)
arm64.fp-ptrace                   49% ( 2)      82% ( 2)      12% ( 1)
arm64.uaccess                     54% ( 4)      95% ( 6)      18% ( 3)
arm64.ptrauth                     51% ( 5)      87% ( 6)      33% ( 1)
arm64.gcs                         51% ( 3)      84% ( 4)      47% ( 3)
arm64.poe                         30% ( 3)      84% ( 3)       0% ( 0)
arm64.spectre                     49% ( 5)      91% ( 5)      32% ( 4)
arm64.boot-flow                   69% ( 6)      87% ( 6)      40% ( 3)
arm64.el2-setup                   55% ( 2)      90% ( 3)      47% ( 5)
arm64.suspend-resume              65% ( 3)      78% ( 3)      38% ( 4)
arm64.el0-emulation               62% ( 2)      87% ( 2)      26% ( 2)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `arm64.fault-handling`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `arm64.idreg-sanitisation`, `arm64.add-erratum`, `arm64.sme-state`.

## Questions reorganised

- 71 questions became 65, grouped by subject: exception entry, exception masks, syndromes, system
  register definitions, context synchronisation, CPU capabilities, patching and cache maintenance,
  page table entries, TLB invalidation, break-before-make, tagged addresses and MTE, FP/SVE/SME
  state, faults and user access.
- Merged: `arm64.vector-entry-asm` + `arm64.entry-isb` to `arm64.entry-asm-state`;
  `arm64.esr-layout` + `arm64.esr-abort-iss` to `arm64.esr-fields`; `arm64.sysreg-resx-masks` +
  `arm64.conditional-resx` to `arm64.sysreg-resx`; `arm64.add-capability` + `arm64.add-erratum` to
  `arm64.add-cap-or-erratum`; `arm64.lockless-walk` + `arm64.lockless-walk-usage` to
  `arm64.lockless-read`; `arm64.vl-change` + `arm64.vl-change-usage` to `arm64.vl-change-state`.
- No question was dropped whole. The inventories inside questions went (the stub hypervisor calls,
  which user calls which patching function, the bit-by-bit SCTLR and ESR layouts, the ordered steps
  of the entry macro); each now asks for the contract or the hazard a reviewer acts on.
