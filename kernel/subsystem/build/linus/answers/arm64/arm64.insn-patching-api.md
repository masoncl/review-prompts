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
