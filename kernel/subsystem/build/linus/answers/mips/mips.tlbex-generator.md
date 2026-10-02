- Load, store and modify handlers: generated in place in `handle_tlbl`,
  `handle_tlbs` and `handle_tlbm`, fixed areas of `FASTPATH_SIZE`
  instructions in `arch/mips/mm/tlb-funcs.S`; no memory is allocated.
- In-place overflow check: runs after generation (`p >= handle_tlbl_end`
  and the like), so the following area is already overwritten when the
  panic fires, and code that fills the area exactly also panics.
- Refill handler: generated in the `tlb_handler` buffer and then copied to
  `ebase`; `build_r3000_tlb_refill_handler()` and
  `build_r4000_tlb_refill_handler()` check the size before the copy.
- `build_r4000_tlb_refill_handler()` on 32-bit kernels and
  `CPU_LOONGSON2EF`: the refill handler starts at `ebase` and may use 64
  instructions, running on through the 0x80 slot.
- `build_r4000_tlb_refill_handler()` on other 64-bit kernels: the refill
  handler starts at `ebase + 0x80`; code past `MIPS64_REFILL_INSNS` is
  folded into the slot before it, at `ebase`.
- `build_loongson3_tlb_refill_handler()`: copies 0x80 bytes to
  `ebase + 0x80` and has no size check.
- Refill handler, how often: built once. All three refill builders are
  inside a `run_once` block of `build_tlb_refill_handler()`, whatever its
  comment says.
- Every call of `build_tlb_refill_handler()`: the XPA/RIXI panic test,
  `output_pgtable_bits_defines()`, `check_pabits()`, the
  `check_for_high_segbits` computation (`CONFIG_64BIT`), then `setup_pw()`,
  `config_xpa_params()` and `config_htw_params()`, each under its feature
  test.
- `cpu_has_3kex`: returns before `setup_pw()`, `config_xpa_params()` and
  `config_htw_params()`.
