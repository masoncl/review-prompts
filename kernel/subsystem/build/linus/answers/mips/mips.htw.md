- `htw_stop()` and `htw_start()`: macros in
  `arch/mips/include/asm/pgtable.h`.
- Nesting: counted in `htw_seq` of `struct cpuinfo_mips`, reached through
  `raw_current_cpu_data`. Only the outermost stop clears the
  `MIPS_PWCTL_PWEN_SHIFT` bit and only the matching start sets it.
- Interrupts: each macro wraps its counter update and PWCtl write in its own
  `local_irq_save()`, so the caller need not have interrupts off to call
  them.
- **Unsafe usage**: a `htw_stop()` and `htw_start()` pair across which the
  task can move to another CPU; each CPU's `htw_seq` is then left
  unbalanced.
  - Safe: under `preempt_disable()`, as the `cpu_has_mmid` branch of
    `flush_tlb_page()` in `arch/mips/kernel/smp.c` does.
  - Safe: under `local_irq_save()`, as `local_flush_tlb_page()` does.
- `pte_clear()` in `arch/mips/include/asm/pgtable.h`: brackets its page
  table write with the pair, though it touches no TLB register.
- Generated load, store and modify handlers: do not stop the walker. With
  `cpu_has_htw`, `cpu_has_tlbex_tlbp_race()` in `arch/mips/mm/tlbex.c` makes
  them test Index after the probe and leave if it missed.
- PWBase: written by `htw_set_pwbase()` inside
  `TLBMISS_HANDLER_SETUP_PGD()` in `arch/mips/include/asm/mmu_context.h`,
  not by the generated `tlbmiss_handler_setup_pgd`, which writes
  `C0_PWBASE` only for `cpu_has_ldpte`.
- `arch/mips/kvm/entry.c`: repeats `TLBMISS_HANDLER_SETUP_PGD()` in uasm,
  including the PWBase write.
