- `BPF_F_CPU` and `BPF_F_ALL_CPUS`: exist in `include/uapi/linux/bpf.h`; with
  either, `bpf_map_value_size()` returns `map->value_size`, one unrounded
  value.
- `BPF_F_CPU`: the CPU is `flags >> 32`; lookup copies that CPU's value,
  update writes that CPU only.
- `BPF_F_ALL_CPUS`: update only; writes the one value to every possible
  CPU.
- `bpf_map_check_op_flags()` in `include/linux/bpf.h`: `-EINVAL` for both
  flags together, for a map that is not per-CPU, or for upper bits without
  `BPF_F_CPU`; `-ERANGE` when the CPU is `>= nr_cpu_ids` or not possible.
- Allowed flags: lookup and lookup batch take `BPF_F_CPU`; update and update
  batch take both; see the callers of `bpf_map_check_op_flags()`.
- Lookup-and-delete: always uses the full layout, since
  `map_lookup_and_delete_elem()` calls `bpf_map_value_size(map, 0)`.
- `BPF_F_CPU` on a new hash element: `pcpu_init_value()` zeroes the other
  CPUs' values.
- From a program: per-CPU update ops return `-EINVAL` for flags above
  `BPF_EXIST`, so neither flag is available; see
  `htab_map_check_update_flags()`.
- `bpf_map_is_percpu_map()`: also lists
  `BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`, which uses the same system call
  layout; a program reaches it only through `bpf_get_local_storage()`.
- Full-layout lookup: copies `round_up(value_size, 8)` bytes per slot with
  `copy_map_value_long()`.
- Full-layout update: copies only `value_size` bytes from each slot with
  `copy_map_value()`; the padding in the buffer is ignored.
- Slot order: slot i is the i-th CPU of `for_each_possible_cpu()`, not the
  CPU number, when the possible mask has holes.
- Direct value access: for `BPF_MAP_TYPE_PERCPU_ARRAY` with
  `max_entries == 1`, `bpf_do_misc_fixups()` appends
  `BPF_MOV64_PERCPU_REG()` to the `ld_imm64`, giving this CPU's value with no
  lookup.
- That path needs `bpf_jit_supports_percpu_insn()`; otherwise
  `percpu_array_map_direct_value_addr()` returns `-EOPNOTSUPP`.
- Inlined `map_gen_lookup` on a per-CPU map: `bpf_do_misc_fixups()` sets
  `prog->jit_required`, so the program cannot fall back to the interpreter.
- `map_lookup_percpu_elem`: tests `cpu >= nr_cpu_ids` only, not
  `cpu_possible()`.
- Sleepable programs: also run with migration disabled; for example
  `__bpf_prog_enter_sleepable()` calls `migrate_disable()`.
