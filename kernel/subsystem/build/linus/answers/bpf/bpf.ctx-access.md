- `check_ctx_access()`: checks the register offset itself;
  `check_mem_access()` has not done it before the call.
- Register offset allowed, by program type:

| Program | Register offset |
|---|---|
| `BPF_PROG_TYPE_SYSCALL` (`is_var_ctx_off_allowed()`) | variable, bounded by `U16_MAX` |
| no `convert_ctx_access` in its ops | constant, not negative |
| has `convert_ctx_access` | zero |

- `struct bpf_reg_state`: has no off member; the register offset is in
  `var_off`, constant when `tnum_is_const()` and then read as
  `var_off.value`; see `__check_ptr_off_reg()`.
- `off` passed to `is_valid_access()`: `insn->off` plus `reg_umax()` of the
  register, so for a syscall program it is called once with the largest offset.
- `off` can be negative, except for `BPF_PROG_TYPE_SYSCALL`: only the register
  part is tested for sign, so `is_valid_access()` must reject `off < 0`, as
  `kprobe_prog_is_valid_access()` does.
- Alignment: `check_ptr_alignment()` tests a context access only under strict
  alignment; `is_valid_access()` must test `off % size`.
- Stored value: known not to be a pointer only when `env->allow_ptr_leaks` is
  false.
- `BPF_ST` into the context: checked like `BPF_STX`, as `BPF_WRITE`;
  `bpf_convert_ctx_accesses()` passes `BPF_ST` and `BPF_STX` to the converter
  as `BPF_WRITE`.
- `struct bpf_insn_access_aux`: the reference field is `ref_id`;
  `check_mem_access()` copies it to the loaded register's `id`.
- `__check_ctx_access()`: for a `PTR_TO_BTF_ID` result it does not record
  `ctx_field_size`, which shares a union with `btf`, `btf_id` and `ref_id`.
- `__check_ctx_access()`: fails with "Reference may already be released" when
  `ref_id` is set and no longer in the reference state.
- Narrow write, in a type with `convert_ctx_access`: if `is_valid_access()`
  leaves `ctx_field_size` larger than the size of a `BPF_WRITE`,
  `bpf_convert_ctx_accesses()` fails with a verifier bug.
- `kprobe_prog_is_valid_access()`: accepts `BPF_WRITE` and sets
  `prog->aux->kprobe_write_ctx`; the attach decides:
  `__perf_event_set_bpf_prog()` rejects such a program unless the event is a
  uprobe, and `bpf_kprobe_multi_link_attach()` always rejects it.
- `gen_prologue`: must be set if any path can set `env->seen_direct_write`;
  `bpf_convert_ctx_accesses()` reports a verifier bug otherwise.
