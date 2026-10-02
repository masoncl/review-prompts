# What the mips measurement found

Three models were asked the 32 questions in `mips-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader A said it assumed kernels 6.12 to
6.17, reader B 6.6 to 6.10 and reader C 6.12 to 7.0. Reader C is current: it
described the rewritten TLB uniquification almost line for line. Reader A knows
the step exists but describes the version before the rewrite. Reader B made the
algorithm up, and was wrong about where things are defined and about which
CPUs run what. The hand-written guide was never checked against current
sources, so differences between it and the built guide are expected and are
noted near the end.

The hand-written guide is about one hazard, duplicate TLB entries during early
initialisation, so 22 of the questions are about the TLB and 10 sample the rest
of `arch/mips`.

## What all three readers got wrong

- **Which CPUs and which paths initialise the TLB.** Reader A sent resume
  through `arch/mips/kernel/pm.c` and `tlb_init()`; reader B said secondary
  CPUs and resume skip uniquification; reader C implied secondaries only
  reprogram the walker registers. `per_cpu_trap_init()` runs the whole of
  `tlb_init()` on every CPU. After a power state that lost the TLB,
  `r4k_tlb_pm_notifier()` calls `r4k_tlb_configure()` alone, on `CPU_PM_EXIT`
  and on `CPU_PM_ENTER_FAILED`, and that function uniquifies again whenever
  `cpu_has_tlbinv` is false, this time with slab available.
- **The full flush with wired entries.** All three described
  `local_flush_tlb_all()` as using `tlbinvf()` whenever the CPU has it. It does
  so only when `num_wired_entries()` is zero (and for the VTLB only when
  `tlbsizevtlb` is non-zero); otherwise it loops from the wired count writing
  `UNIQUE_ENTRYHI()` values, which carry `MIPS_ENTRYHI_EHINV` on such hardware.
  `decode_config4()` sets `MIPS_CPU_TLBINV` only for Config4.IE equal to 2;
  two readers gave other values. `cpu_probe_loongson()` also sets it and
  several platforms override `cpu_has_tlbinv` to 0.
- **Wired entries.** `add_wired_entry()` is called only from the Jazz setup
  and interrupt-init code (`arch/mips/jazz/setup.c`, `arch/mips/jazz/irq.c`)
  and `arch/mips/pci/pci-alchemy.c`; `kmap_coherent()` open-codes the
  Wired increment in `__kmap_pgprot()` and `kunmap_coherent()` lowers it again.
  `num_wired_entries()` masks with `MIPSR6_WIRED_WIRED` on R6 only.
  `r4k_tlb_configure()` writes Wired to 0, so it drops every wired entry at
  boot and on power-state exit. `tlb-r3k.c` has its own `add_wired_entry()`.
- **PageMask.** None listed `r4k_tlb_uniquify()` among the routines that change
  it (it writes `PM_4K` and restores `PM_DEFAULT_MASK`), and none said that
  `r4k_tlb_configure()` panics when the register will not hold
  `PM_DEFAULT_MASK`. The R4600 1.7 reason in the comment (`tlbp` misses pages
  smaller than PageMask) was replaced by an invented erratum or a machine
  check.
- **The handler generator.** The refill handler's size rule: on 64-bit, 32
  instructions at `ebase + 0x80` with the overflow folded into the slot at
  `ebase`; on 32-bit, 64 instructions from `ebase`. The load, store and modify
  handlers are `FASTPATH_SIZE` slots in `arch/mips/mm/tlb-funcs.S`, not near
  `ebase`. Overflow is a `panic()`, except that the Loongson-3 refill builder
  has no check. `build_tlb_refill_handler()` runs on every CPU; only the first
  call generates code, and later calls redo `setup_pw()`,
  `config_xpa_params()` and `config_htw_params()`, each behind its own feature
  test.
- **Probe races in the handlers.** `cpu_has_tlbex_tlbp_race()` is true for
  `cpu_has_htw` or `cpu_has_shared_ftlb_ram`, nothing else. The huge-page paths
  of the load, store and modify builders probe without the check, and the
  RI/XI path has only a build-time `WARN()`.
- **KVM.** Only VZ exists (`config KVM` depends on `CPU_SUPPORTS_VZ`). The TLB
  routines are in `arch/mips/kvm/tlb.c`, not `vz.c`.
  `kvm_mips_build_tlb_refill_exception()` in `arch/mips/kvm/entry.c` calls the
  exported tlbex builders; what it copies is `c0_kscratch()` and, on
  Loongson64, the open-coded `lddir`/`ldpte` walk. `_kvm_mips_host_tlb_inv()`
  mirrors `local_flush_tlb_page()`.
- **Platform layout.** `arch/mips/Kbuild.platforms` sets `platform-y`;
  the `Platform` files set `cflags-y`, `load-y` and image targets;
  `arch/mips/Makefile` adds the `mach-generic` include path last. The generic
  kernel matches boards in `plat_get_fdt()` over `struct mips_machine`.
- **Feature macros.** Most read `cpu_data[0]`, so they are safe anywhere;
  `cpu_has_fpu` reads `current_cpu_data` and has `raw_cpu_has_fpu` beside it;
  the cache macros read `cpu_data[0].dcache.flags`; composites such as
  `cpu_has_mips_r6` have no `#ifndef` around them.
- **Cache aliases.** `__update_cache()` is called from `set_ptes()`, not from
  `update_mmu_cache_range()`. The deferring function is
  `__flush_dcache_folio_pages()`; two readers named one that no longer exists.
- **Atomics.** There is no asm/llsc.h and no __LL or __SC helper; the loops are
  open-coded in `asm/atomic.h`, `asm/cmpxchg.h` and `asm/bitops.h`, and the
  macro is `SC_BEQZ`. Nearly every barrier kind maps to `__SYNC_full` except on
  Octeon.
- **Errata.** There is no asm/war.h; workarounds are `CONFIG_WAR_` and
  `CONFIG_CPU_` Kconfig symbols tested with `IS_ENABLED()` or `#ifdef`. The
  64-bit bug probe is `arch/mips/kernel/r4k-bugs64.c`.
- **Changing TLB code.** Two readers named a third TLB file that does not
  exist; `arch/mips/mm/` has `tlb-r4k.c` and `tlb-r3k.c`, chosen by Kconfig at
  build time. `local_flush_tlb_one()` exists only in `tlb-r4k.c`. The debug
  aids are `dump_handler()` (through `pr_debug()`), `dump_tlb_all()` in
  `arch/mips/lib/dump_tlb.c` and `r3k_dump_tlb.c`, and SysRq `x`.

## What only some readers got wrong

- **Uniquification** (readers A and B). Reader A: only the VPN2 is recorded,
  large pages are truncated in place, replacements are values in the style of
  `UNIQUE_ENTRYHI()`, memory comes from kmalloc_array(). Reader B: only
  colliding entries are rewritten, with a value derived from the index, from a
  table on the stack. In the tree `r4k_tlb_uniquify_read()` records index,
  wired, global, ASID, VPN masked by PageMask and page size in a
  `struct tlbent`; `sort()` with `r4k_entry_cmp()` puts wired first, then
  global, then ascending VPN and ASID with larger pages first; and
  `r4k_tlb_uniquify_write()` rewrites every non-wired entry with a 4KiB user
  VPN and ASID counted up from zero, stepping over the span of any wired,
  global or not yet rewritten entry, so that nothing can clash with a
  `UNIQUE_ENTRYHI()` value either. The table is `kmalloc()` with `GFP_ATOMIC`
  once slab is up and `memblock_alloc_raw()` before that.
- **When it is skipped** (readers A and B). Reader A was unsure of the
  condition; reader B said `cpu_has_mmid`. It is `cpu_has_tlbinv`. The
  algorithm cannot handle an FTLB, MMIDs or an R6 core without 4KiB pages, and
  relies on all of those implying EHINV.
- **Writing back what was read** (reader B). Reader B called reading an entry
  and writing it back unchanged safe, and the base step of the walk. The
  in-tree code never writes back a value it read.
- **Hazard barriers** (readers A and B). Reader B put the macros in
  `asm/mipsregs.h`, as the hand-written guide does; they are in
  `asm/hazards.h`. Both were wrong about the expansions: `ehb` for R2, R5 and
  R6 except Octeon and Loongson64; `ssnop`s then `ehb` for R1 (not Alchemy) and
  BMIPS; nothing for Alchemy, Octeon, Loongson, R10000, R5500 and SB1; plain
  `nop`s for the rest. Reader B put `tlbw_use_hazard()` where
  `tlb_probe_hazard()` belongs.
- **Wrappers** (readers A and B). Reader B said the guest TLB instructions have
  no C wrappers; `guest_tlb_probe()`, `guest_tlb_read()`,
  `guest_tlb_write_indexed()`, `guest_tlb_write_random()` and
  `guest_tlbinvf()` are in `asm/mipsregs.h`. Both said no wrapper does hazard
  handling; `tlb_read()` does under `CONFIG_WAR_MIPS34K_MISSED_ITLB`.
- **The invalid EntryHi value** (reader B). `UNIQUE_ENTRYHI()` is in
  `arch/mips/include/asm/tlb.h`, not `tlb-r4k.c`, and the guest variant uses
  `CKSEG1`.
- **The machine check** (reader B). `do_mcheck()` calls `panic()`, not die(),
  whether or not `ST0_TS` is set, and is installed only when `cpu_has_mcheck`.
- **The walker** (reader B). `htw_stop()` and `htw_start()` nest through the
  counter `htw_seq`; no enable state is saved.
- **The single-entry flush** (all, in small ways). EntryLo0 and EntryLo1 are
  zeroed before the index test, not only on a hit. With MMIDs EntryHi gets the
  bare page and the identifier goes to MemoryMapID, which is saved after
  `htw_stop()`.
- **Address space identifiers** (readers B and C). `get_new_mmid()` bumps
  `mmid_version` and then calls `flush_context()`; each CPU does its pending
  flush in `check_switch_mmu_context()`. `drop_mmu_context()` has three cases:
  `ginvt_mmid()`, a new ASID written to EntryHi when the mm is active here, or
  a zeroed context.
- **Reader B on the rest of the architecture.** The o32 entry file on a 64-bit
  kernel is `scall64-o32.S`; `own_fpu()` does not restore MSA and the
  non-`_inatomic` helpers disable preemption themselves; `mips_cm_lock_other()`
  disables interrupts and preemption itself and `boot_core()` busy-waits with
  `mdelay()` and nests `mips_cpc_lock_other()` while holding it; there is a
  link-time checker, `arch/mips/tools/loongson3-llsc-check.c`; `KSEG1ADDR()`
  exists on 32-bit kernels only.

## What the readers already knew

Readers A and C: what `UNIQUE_ENTRYHI()` computes and why, what the machine
check handler does, that the uniquify step avoids the probe and the random
write, the outline of the single-entry flush, the three ABIs and their tables,
floating point ownership, delay slot handling, the coherence manager lock.
Reader C also knew the hazard macros and their expansions, the uniquify
algorithm, its gate and what it relies on. All three knew roughly which file
holds what.

## Where the hand-written guide is stale

- Its description of `r4k_tlb_uniquify()` ("read all entries by index first,
  detect duplicates in software, then overwrite duplicates") and its sample
  code (an `existing_vpns[]` array filled from `read_c0_entryhi() & vpn_mask`)
  are the version before the rewrite. The function now sorts a table of
  `struct tlbent`, rewrites every non-wired entry rather than only duplicates,
  and reads EntryHi through `read_c0_entryhi_native()`.
- It does not say that the step is skipped on hardware with `cpu_has_tlbinv`,
  which is every R6, FTLB or MMID core, or that it runs again on secondary
  CPUs and after a power state.
- It says the hazard barriers are defined in `asm/mipsregs.h`. They are in
  `asm/hazards.h`; only the instruction wrappers are in `asm/mipsregs.h`.
- It calls the indexed read safe and says an indexed write is "safe because
  each write removes a duplicate". The in-tree code does not rely on that: it
  chooses each value so that it clashes with no entry still in the TLB, and it
  never writes back what it read.
- Its list of affected CPU families (R4x00, microAptiv, OCTEON3, SB1) and its
  SGI IP22 PROM example are in no file in the tree. They came from commit
  messages. The tree's own examples are the SB1 note in
  `arch/mips/lib/dump_tlb.c`, the OCTEON3 inhibit bit in `arch/mips/kvm/tlb.c`
  and the 4Kc note in `arch/mips/mm/tlbex.c`.
- It says `do_mcheck()` "cannot recover". True, but it leaves out that the
  handler exists only with `cpu_has_mcheck`, and that on the boot CPU
  `tlb_init()` runs from `per_cpu_trap_init()` before `trap_init()` has
  installed any vector.
- It says nothing of the hardware walker (`htw_stop()` and `htw_start()`), of
  MMIDs, of wired entries, of the KVM copies, or of the R3000 implementation.
- Its quick checks tell a reviewer what is suspect. The build set asks for
  the unsafe usage and the correct usage that looks like it.

## What was left out of the build set and why

The build set has 11 of the 32 questions and keeps the hand-written guide's
emphasis on the TLB. That guide's 480 words are under the 600-word floor for a
built guide, so the set is sized to 600 words (480 to 720) with no question
budgeted under 40: 530 words of budget, the two tables at 60 each, which with
titles and headings comes to about 650. Raising the eleven to the floor used
all of that room, so nothing below came back. Left out:

- Everything outside the TLB: platform layout, feature macros, cache aliases,
  address segments, ABIs, floating point, delay slots, atomics, the coherence
  manager, errata. All readers got parts of these wrong, but 600 words do not
  stretch to them and the old guide never covered them. They stay in the
  measurement set for a larger MIPS guide.
- TLB topics that all readers got partly wrong but that fewer patches touch:
  the handler generator and its probe races, KVM's routines, wired entries,
  PageMask, the VTLB and FTLB sizes, `__update_tlb()`, the R3000 code, MMID
  allocation. The change checklist names the copies and the second
  implementation so that a reviewer at least knows they are there.
- The hardware invalidate question: what is relied on in place of
  uniquification is asked by the gating question, and with 40 words instead of
  25 its answer has room to say that the full flush can use `tlbinvf()` there
  because Wired has just been written to 0. It is the first question to bring
  back if the guide grows: all three readers got the full flush with wired
  entries wrong.
- The wrapper question: the hazard question's table names the instruction each
  barrier sits beside, and the core files table gives the header.
- The core files question is narrowed in the build set to the TLB and the
  files a TLB change also has to look at.
- Five other kept questions are reworded there so that the tree alone can
  answer them. The machine check question no longer asks which hardware
  operations raise the exception and asks instead on which CPUs a handler is
  installed. The initialisation order question also asks where the exception
  vectors are installed in that order. The hazard question asks which macros
  are empty on some builds rather than for every expansion, and for the
  configuration symbols in full. The question on operations before
  initialisation asks whether the in-tree code ever writes back a value it
  read, rather than whether doing so is safe. The walker question asks which
  functions stop and restart the walker, so that the answer names them, and
  what the tree says the walker can do while it runs, rather than what goes
  wrong without the calls; nothing in the tree says.
- Two more have a clause changed so that it does not presuppose the answer.
  The invalid EntryHi question asks whether an extra bit is set on hardware
  that supports one, not which, and for the macro names in full. The gating
  question asks whether the step is skipped on any hardware before asking
  where, and says what to do on a tree that has no such step.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           73        44%      3     21   6.12 to 6.17
reader B          110        79%      0     31   6.6 to 6.10
reader C           65        28%      6     10   6.12 to 7.0

question                      reader A      reader B      reader C   verdict
mips.core-files               18% ( 3)      24% ( 6)      24% ( 4)   middling
mips.platform-layout          76% ( 3)      90% ( 3)      42% ( 4)   all weak
mips.tlb-wrappers             46% ( 2)      73% ( 4)      17% ( 3)   weak: reader A, reader B
mips.hazard-barriers          49% ( 3)      85% ( 3)       5% ( 1)   weak: reader A, reader B
mips.unique-entryhi            0% ( 0)      58% ( 2)       9% ( 1)   weak: reader B
mips.machine-check             6% ( 1)      71% ( 2)       9% ( 0)   weak: reader B
mips.tlb-init-sequence        74% ( 4)      75% ( 5)      22% ( 3)   weak: reader A, reader B
mips.uniquify                 72% ( 5)      92% ( 3)      16% ( 3)   weak: reader A, reader B
mips.uniquify-gating          77% ( 1)      88% ( 2)      28% ( 1)   weak: reader A, reader B
mips.init-tlb-usage           23% ( 1)      84% ( 1)      31% ( 1)   weak: reader B
mips.tlbinv                   46% ( 1)      78% ( 2)      23% ( 1)   weak: reader A, reader B
mips.vtlb-ftlb                27% ( 4)      92% ( 5)      44% ( 5)   weak: reader B, reader C
mips.wired-entries            41% ( 4)      87% ( 4)      45% ( 3)   all weak
mips.pagemask                 53% ( 3)      84% ( 3)      41% ( 2)   all weak
mips.local-flush-pattern      27% ( 1)      71% ( 2)      31% ( 1)   weak: reader B
mips.htw                      53% ( 1)      74% ( 2)      23% ( 1)   weak: reader A, reader B
mips.asid-mmid                29% ( 1)      89% ( 1)      41% ( 1)   weak: reader B, reader C
mips.update-tlb               46% ( 1)      83% ( 1)      23% ( 1)   weak: reader A, reader B
mips.r3k-tlb                  53% ( 2)      80% ( 1)      37% ( 1)   weak: reader A, reader B
mips.tlbex-generator          63% ( 5)      84% ( 6)      34% ( 4)   weak: reader A, reader B
mips.tlbex-probe-race         66% ( 2)      92% ( 3)      28% ( 2)   weak: reader A, reader B
mips.kvm-tlb                  82% ( 4)      88% ( 4)      41% ( 4)   all weak
mips.cpu-features             40% ( 3)      75% ( 5)      43% ( 3)   all weak
mips.cache-aliases            50% ( 3)      82% ( 4)      25% ( 4)   weak: reader A, reader B
mips.address-segments         44% ( 2)      82% ( 4)      47% ( 1)   all weak
mips.abis-syscalls            13% ( 2)      80% ( 5)       0% ( 1)   weak: reader B
mips.fpu-context              21% ( 1)      82% ( 5)      13% ( 1)   weak: reader B
mips.delay-slots              37% ( 1)      73% ( 2)       0% ( 0)   weak: reader B
mips.llsc-barriers            44% ( 1)      92% ( 3)      28% ( 1)   weak: reader A, reader B
mips.cm-access                25% ( 1)      77% ( 4)      35% ( 1)   weak: reader B
mips.workarounds              41% ( 1)      82% ( 3)      59% ( 1)   all weak
mips.change-checklist         73% ( 6)      91% (10)      49% ( 5)   all weak
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `mips.wired-entries`, `mips.pagemask`, `mips.tlbex-generator`, `mips.cpu-features`, `mips.cache-aliases`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `mips.tlb-wrappers`, `mips.tlbinv`, `mips.asid-mmid`.

## Questions reorganised

Grouped by subject: TLB entries and primitives, TLB initialisation, TLB maintenance, CPU features and
caches, after the file table. 21 questions became 20.
Merged: `mips.hazard-barriers` and `mips.tlb-wrappers` into `mips.hazards-and-wrappers` (which barrier
goes where, and whether any wrapper does hazard handling itself).
`mips.uniquify` asks what is guaranteed about each value written, not how the algorithm works; the
instructions to avoid are left to `mips.init-tlb-usage`. `mips.wired-entries`, `mips.tlbex-generator`,
`mips.asid-mmid`, `mips.cache-aliases` and `mips.local-flush-pattern` were cut to three things each;
who uses wired entries and how to inspect generated code went. Nothing was dropped.
