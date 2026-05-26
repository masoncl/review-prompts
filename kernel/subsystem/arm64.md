# ARM64 Subsystem Details

This guide covers architectural invariants, memory ordering rules, and common
bug patterns for the ARM64 (AArch64) architecture, derived from historical
lore and the ARM Architecture Reference Manual (ARM ARM).

## Memory Tagging Extension (MTE) and Tagged Addresses

Mishandling MTE tags or tagged addresses causes `KASAN invalid-access` panics,
spurious tag check faults, and memory permission corruption.

- **Pointer Arithmetic:** The Top Byte Ignore (TBI) hardware feature allows
  the MMU to ignore bits [63:56] during address translation. However,
  **software-side arithmetic** (e.g., bit-shifts to compute page indices) MUST
  explicitly untag the address (e.g., via `untagged_addr()`) to prevent tag
  bits from corrupting calculation results.
    - **Note:** If `FEAT_PAuth` is implemented, `TCR_ELx.TBIDn` selects
      whether TBI applies to instruction fetches as well as data; otherwise
      TBI applies to both unconditionally.
- **Tag Initialization Barriers:** A DSB between tag stores (`STG`/`STZG`) and
  the PTE update is required so the explicit tag stores complete before the
  table walker's implicit TTD reads observe the mapping.
- **Shared Page Tag Initialization:** Marking a shared or special page (e.g.,
  the **Linux-specific** huge zero folio) as MTE-tagged too early during
  initialization causes userspace to map the page before its tags are
  definitively cleared. Tag clearing MUST be synchronized and visible before
  the page is made accessible to other observers.

**REPORT as bugs:**
- Using a virtual address directly in a bit-shift or mask operation to find a
  page-table entry without calling `untagged_addr()`.
- Updating a PTE for an MTE-enabled page without a preceding `DSB` after the
  tags were written to ensure visibility to the walker.

## System Register and Context Synchronization

Updates to architectural configuration system registers (e.g., `GCR_EL1`,
`SCTLR_EL1`, `TCR_EL1`) are not guaranteed to be visible to subsequent
instructions without an explicit Context Synchronization Event (CSE).

Missing synchronization results in unpredictable behavior where the CPU
operates under a stale configuration for several cycles, breaking memory
safety semantics or causing unexpected traps.

- **Context Synchronization Events (CSE):** A CSE ensures preceding state
  changes are resolved. Events that constitute a CSE include:
    - Executing an `isb` instruction.
    - Exception entry or return (subject to `SCTLR_ELx.{EIS, EOS}` bits and
      `FEAT_ExS`).
- **Immediate Synchronization:** Every write to a control-plane system
  register MUST be followed by an `isb()` *as the very next instruction*. The
  barrier must precede any subsequent read-back, comparison, conditional
  branch, return, or further sysreg access — not just appear "somewhere later"
  in the function. Code that places *any* instruction between the write and
  the `isb()` is buggy, even when an `isb()` is eventually issued, because the
  intervening instruction observes architecturally undefined pipeline state.
- **GIC Synchronization:**
    - Writes to most `ICC_*_EL1` registers require a CSE to be visible to
      subsequent instructions. Notable exceptions: writes to `ICC_PMR_EL1` and
      reads of `ICC_IAR{0,1}_EL1` / `ICC_NMIAR1_EL1` (when `PSTATE.{I,F} ==
      {0,0}`) are self-synchronizing.
    - Writes to specific memory-mapped GIC registers require polling the RWP
      bit. `GICD_CTLR.RWP` tracks group-enable disables (1→0), `GICD_CTLR`
      ARE/DS field writes, and `GICD_ICENABLER<n>`. `GICR_CTLR.RWP` tracks
      `GICR_ICENABLER0`, `GICR_CTLR.EnableLPIs` (1→0), and DPG writes.
      Priority, routing, and enable-set writes are NOT tracked by either RWP
      bit.

**REPORT as bugs:**
- Writing to a control system register without an `isb()` as the very next
  instruction. Includes patterns that delay the barrier behind a
  read-back-and-verify, a conditional branch, or any other instruction. Worked
  example of the bug:
    ```c
    write_sysreg_s(val, SYS_HFGRTR_EL2);
    if (read_sysreg_s(SYS_HFGRTR_EL2) != val)   /* observes pipeline */
        return -EIO;
    isb();                                       /* too late — read-back already executed */
    ```
  The `isb()` exists, but the read-back has already executed against
  architecturally undefined pipeline state. Correct ordering is `write → isb()
  → read-back`.
- Writing to `ICC_*_EL1` registers (excluding `ICC_PMR_EL1`) without an
  `isb()`.
- Writing to tracked memory-mapped GIC registers without polling the
  appropriate `GICD_CTLR.RWP` or `GICR_CTLR.RWP`.

## TLB Invalidation and Break-Before-Make (BBM)

Failure to follow the correct invalidation and synchronization sequence leads
to pipeline inconsistencies, stale TLB usage, and TLB Conflict Aborts.

### TLB Maintenance Observer Rules

The completion of a TLB maintenance instruction (`TLBI`) is guaranteed
**only** by the execution of a `DSB` by the **same** Processing Element (PE)
that performed the `TLBI`.

- **Global Visibility:** A broadcast `TLBI` (e.g., `TLBI VAE1IS`) is only
  guaranteed to be finished for all other PEs after the issuing PE executes a
  `DSB ISH`.
- **Remote DSB Inefficacy:** CPU B cannot use its own `DSB` to force CPU A's
  broadcasted `TLBI` to complete.
- **Local Synchronization:** `isb` instructions are NOT broadcast. Each
  observing PE MUST independently execute its own `isb()` (or undergo a CSE)
  locally *after* the issuing PE's `DSB` completes to ensure the invalidation
  is visible to the local fetch path.

### Break-Before-Make (BBM) Requirements

When updating a live translation table entry (shared across multiple threads),
you MUST follow the BBM sequence to prevent TLB conflicts.

**BBM is strictly required when:**
- **Changing block or table sizes:** `FEAT_BBML1/2` relax the requirement for
  an explicitly-invalid intermediate descriptor; TLB maintenance is still
  required.
- **Creating a global entry** that overlaps existing non-global entries.
- **Changing the Output Address (OA):** Strictly required by the architecture
  if the contents of memory at the new OA do not match the contents at the
  previous OA.
- **Changing memory attributes** (type or cacheability).

**The BBM Sequence:**
1. Replace the old entry with an invalid entry.
2. Execute a `DSB` (ensure invalid entry is globally visible).
3. Invalidate relevant TLB entries (Broadcast `TLBI`).
4. Execute another `DSB` (ensure invalidation is complete).
5. Write the new, updated translation table entry.
6. Execute a final `DSB`.

**REPORT as bugs:**
- Code performing `TLBI` without both a subsequent `DSB` and `isb()` on the
  issuing CPU (for executable mappings or where local synchronization is
  required).
- Missing `isb()` after TLBI in mode-entry paths (e.g., `enter_vhe()`, nVHE
  `__tlb_switch_to_guest()`, `__primary_switch()`); the TLBI is not
  synchronized to the new execution context without it.
- Updating a live page table entry (changing OA to a non-matching address or
  attributes) without an intervening invalidation (skipping the "Break" step).
- Kernel block/page-mapping changes on systems where secondary CPUs may not
  support `FEAT_BBML2`, without gating on the CPU-feature cap or falling back
  to full BBM.

## Instruction and Data Coherency (PoC vs PoU)

The architecture does not inherently ensure coherency between instruction
caches and memory. Software must manage this manually using the Point of
Unification (PoU) or Point of Coherency (PoC).

- **Self-Modifying Code (PoU):** When writing new instructions as data (e.g.,
  JIT), software MUST:
    1. Clean the data cache to the PoU (`DC CVAU`).
    2. Execute `DSB ISH`.
    3. Invalidate the instruction cache to the PoU (`IC IVAU`).
    4. Execute `DSB ISH`.
    5. Ensure an `isb()` occurs on **all observing CPUs** (e.g., via IPI).
- **Instruction Patching (CMODX):** Concurrent modification and execution of
  instructions is safe only for the architecturally enumerated CMODX set: `B`,
  `B.cond`, `BL`, `BRK`, `CB<cc>`, `CBB<cc>`, `CBH<cc>`, `CBNZ`, `CBZ`, `HVC`,
  `ISB`, `NOP`, `SMC`, `SVC`, `TBNZ`, `TBZ`, `TRCIT`, and `UDF`. For all other
  instructions, an explicit `isb()` or CSE is mandatory on **all observing
  CPUs** before execution.
- **External Agents (PoC):** Communicating with non-coherent DMA controllers
  or managing mismatched memory attributes requires cleaning/invalidating to
  the Point of Coherency (PoC) (e.g., `DC CVAC`).

**REPORT as bugs:**
- Modifying instructions (e.g., jump label patching) without ensuring an
  `isb()` or CSE occurs on all CPUs executing the modified code.

## Lockless Page Table Walks

Lockless walkers (e.g., GUP or fast-path page faults) must carefully manage
compiler ordering to avoid observing inconsistent page table states.

- **Atomicity and Ordering:** Software MUST use `READ_ONCE()` when loading a
  descriptor from a shared page table in a lockless walk to prevent the
  compiler from splitting the load or reordering it against subsequent logic.
- **Folded Level Handling:** When some page-table levels are statically folded
  (`PGTABLE_LEVELS ≤ 2`), lockless walks must account for the folded topology.
  The standard multi-level `READ_ONCE()` pattern applied at a folded level
  will observe stale or incorrect state.

**REPORT as bugs:**
- Dereferencing a shared PTE/PMD/PUD/PGD pointer in a lockless walk without
  using `READ_ONCE()`.
- Lockless walk logic that assumes all page-table levels are live without
  checking for folded-level conditions.

## Exception Handling and Stack Management

Manipulating the Stack Pointer (`SP`) is architecturally hazardous due to
potential clobbering of exception return state (`ELR_ELx`, `SPSR_ELx`).

- **DAIF Masking:** Asynchronous exceptions (IRQ, FIQ, SError) MUST be masked
  during stack transitions or pivots (e.g., when switching to a
  **Linux-specific** Shadow Call Stack). An exception hitting while `SP` is
  being moved or state is out of sync will cause fatal recursive faults.
- **Stack Alignment:** `SCTLR_ELx.SA` enforces 16-byte SP alignment for memory
  accesses at ELx; `SCTLR_EL1.SA0` controls the same check at EL0. Check is on
  memory access via SP, not on SP modification.

**REPORT as bugs:**
- Manipulating `SP` or switching stacks without masking `DAIF`.

## SVE, SME, and FPSIMD Register State

Vector-length changes and signal-return paths have a history of leaving stale
register state or performing incorrect state merges.

- **VL-Change State Invalidation:** When the SVE or SME vector length is
  changed for a task, any context derived from the old VL (buffers, register
  views, ptrace payloads) MUST be invalidated or rebuilt before execution
  continues. Incomplete invalidation resurrects stale data in the new
  vector-width context.
- **Streaming-Mode SVE Payload:** When entering streaming SVE mode, the
  ptrace/signal interface requires an explicit SVE payload for streaming-mode
  state; inheriting previous non-streaming state is architecturally incorrect.
- **FPSIMD/SVE State Merge on Signal Return:** When returning from a signal
  handler, FPSIMD and SVE state must be merged in a single coherent step.
  Partial or incorrectly ordered merges silently corrupt the Z-register upper
  halves.

**REPORT as bugs:**
- VL-change paths that do not invalidate or rebuild SVE/SME register context
  for the new length.
- Signal-return paths that merge FPSIMD and SVE register state incorrectly or
  in multiple non-atomic steps.

## Quick Checks

- **System Instructions with Fixed Register Requirements:** Inline assembly
  for system instructions that demand specific registers (e.g., `GIC CDEOI`
  requiring `XZR` / register 31) MUST hardcode the exact register in the
  instruction string. Relying solely on compiler constraints (like `r`) can
  lead to misencoded instructions if the compiler selects a general-purpose
  register, causing `CONSTRAINED UNPREDICTABLE` behavior.
- **CONSTRAINED UNPREDICTABLE:** Triggered by invalid encodings or register
  overlaps. Hardware may execute as a `NOP`, treat as `UNDEFINED`, or generate
  `Alignment/MMU faults`. It results in **UNKNOWN** state and MUST NOT be
  relied upon.
- **TLBI Range Operands:** Range-based invalidation (e.g., `TLBI RVAE1IS`)
  requires correct `SCALE` and `NUM` encoding. If `TG` does not match the
  current granule, the TLBI is CONSTRAINED UNPREDICTABLE — possibly including
  no invalidation.
- **PTE Barrier Batching:** Batching DSB/ISB across multiple kernel-mapping
  PTE updates is only correct in contexts that cannot be interrupted
  mid-batch. In interrupt contexts the batching window is broken and an
  explicit barrier must be issued before the interrupted path observes the
  mappings.
