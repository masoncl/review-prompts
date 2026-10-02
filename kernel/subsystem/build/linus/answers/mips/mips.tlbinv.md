- `decode_config4()` in `arch/mips/kernel/cpu-probe.c`: sets
  `MIPS_CPU_TLBINV` only when the `MIPS_CONF4_IE` field equals 2; values 1
  and 3 do not set it.
- IE values: compared as the literal 2; `decode_config4()` does not use
  `MIPS_CONF4_TLBINV` from `arch/mips/include/asm/mipsregs.h`.
- `cpu_probe_loongson()`: sets `MIPS_CPU_TLBINV` for `PRID_IMP_LOONGSON_64C`
  whatever Config4 says.
- `cpu_has_tlbinv`: tests `cpu_data[0].options`, so the boot CPU's probe
  result is used on every CPU.
- Forcing off: only a platform `cpu-feature-overrides.h` that defines
  `cpu_has_tlbinv` as 0; search for the name under
  `arch/mips/include/asm`.
- Command line: no parameter clears it; `noftlb` leaves `MIPS_CPU_TLBINV`
  set.
- `local_flush_tlb_all()` with `cpu_has_tlbinv` and wired entries: no
  `tlbinvf()`; it loops from `num_wired_entries()` with
  `tlb_write_indexed()` of `UNIQUE_ENTRYHI(entry)`, which then carries
  `MIPS_ENTRYHI_EHINV`.
