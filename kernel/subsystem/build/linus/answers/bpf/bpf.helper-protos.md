- Size argument types: there is no ARG_CONST_SIZE or ARG_CONST_SIZE_OR_ZERO
  here; `ARG_MEM_SIZE` and `ARG_MEM_SIZE_OR_ZERO` in `enum bpf_arg_type`
  (`include/linux/bpf.h`) do that job, see `arg_type_is_mem_size()`.
- `ARG_CONST_ALLOC_SIZE_OR_ZERO`: unchanged; it is the one size type that must
  be a constant.
- `ARG_PTR_TO_UNINIT_MEM`, `ARG_PTR_TO_MEM_OR_NULL`,
  `ARG_PTR_TO_FIXED_SIZE_MEM`: still defined, as enum values composed from
  `ARG_PTR_TO_MEM` plus flags.
- `arg_type`, `arg_btf_id`, `arg_size` in `struct bpf_func_proto`: arrays of
  `MAX_BPF_FUNC_ARGS` (12); `check_helper_call()` checks only the first
  `MAX_BPF_FUNC_REG_ARGS` (5).
- `check_func_proto()`: also runs `check_mem_arg_rw_flag_ok()` and
  `check_proto_release_reg()`; a failure is reported as a verifier bug for
  every call of the helper.
- `check_mem_arg_rw_flag_ok()`: every `ARG_PTR_TO_MEM` must carry `MEM_WRITE`
  or `MEM_RDONLY`.
- `check_proto_release_reg()`: at most one argument may carry `OBJ_RELEASE`.
- `check_args_pair_invalid()`: only `ARG_PTR_TO_MEM` may precede a size
  argument; it needs either a following size argument, or `MEM_FIXED_SIZE`
  with a non-zero `arg_size`, never both.
- Access type: `check_func_arg()` checks the buffer as `BPF_WRITE` only when
  the memory argument has `MEM_WRITE`, otherwise as `BPF_READ`.
- **Unsafe usage**: a helper body that writes through a memory argument
  whose prototype has `MEM_RDONLY` and no `MEM_WRITE`; read-only memory
  passes the check.
  - Safe: tag the argument `MEM_WRITE`, as `ARG_PTR_TO_UNINIT_MEM` does and
    as `bpf_xdp_fib_lookup_proto` does for `params`; `check_func_arg()` then
    checks the buffer as `BPF_WRITE` in `check_helper_mem_access()`.
- `ARG_ANYTHING`: accepts a pointer register when `env->allow_ptr_leaks`;
  `ARG_SCALAR` requires `SCALAR_VALUE` (used by `bpf_loop_proto`).
- `ARG_PTR_TO_BTF_ID` and `ARG_PTR_TO_BTF_ID_SOCK_COMMON`: `btf_ptr_types` and
  `btf_id_sock_common_types` accept a plain `PTR_TO_BTF_ID`, which may come
  from walking a struct and may be NULL at run time; the helper is left to
  test it, as `bpf_skc_to_tcp_sock()` in `net/core/filter.c` does for its
  `ARG_PTR_TO_BTF_ID_SOCK_COMMON` argument.
