- Task context: the section stays preemptible and may migrate;
  `kernel_neon_begin()` calls `put_cpu_fpsimd_context()` before it returns.
- Softirq section on a non-RT kernel: sets no flag, so nothing would save its
  registers at a context switch; it relies on softirq context not being
  preempted.
- `kernel_neon_end()` with `TIF_KERNEL_FPSTATE` clear: returns at once; this
  is the softirq section that interrupted no task-level section.
- `may_use_simd()`: has no `irqs_disabled()` test and no per-CPU busy flag; it
  is true in task context with IRQs disabled.
