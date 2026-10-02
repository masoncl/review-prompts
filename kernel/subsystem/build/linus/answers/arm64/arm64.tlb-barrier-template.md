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
