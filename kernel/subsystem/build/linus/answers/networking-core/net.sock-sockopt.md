- `struct proto_ops` has three option methods: `setsockopt` (`sockptr_t`,
  `unsigned int`), `getsockopt` (`char __user *`, `int __user *`) and
  `getsockopt_iter` (`sockopt_t *`).
- `sockopt_t` is `struct sockopt` in `include/linux/net.h`: `iter_in`,
  `iter_out` over the same buffer, and `optlen` as input size and output
  length.
- `do_sock_getsockopt()` order: `SOL_SOCKET` goes to `sk_getsockopt()`, with no
  `SOCK_CUSTOM_SOCKOPT` test; otherwise `getsockopt_iter` if set; otherwise
  `getsockopt`; otherwise `-EOPNOTSUPP`.
- There is no sock_getsockopt() in this tree; `sk_getsockopt()` in
  `net/core/sock.c` does that job.
- `getsockopt` path: still `__user` only; a kernel `sockptr_t` gets
  `WARN_ONCE()` and `-EOPNOTSUPP`. The `getsockopt_iter` path accepts kernel
  pointers.
- `getsockopt_iter` path, before the handler: `sockptr_to_sockopt()` in
  `net/socket.c` reads the length, returns `-EINVAL` if negative, and bounds
  both iterators to it, so `copy_to_iter()` on `iter_out` cannot write past
  the caller's buffer.
- `getsockopt_iter` path, after the handler: the core writes `opt->optlen`
  back even when the handler failed; `raw_getsockopt()` in `net/can/raw.c`
  relies on that to report the needed size with `-ERANGE`.
- A `getsockopt_iter` handler sets `opt->optlen` to the length returned; it is
  given no pointer to the caller's length, the core copies `opt->optlen` back.
- `struct proto` `getsockopt` still takes `__user` pointers; converted
  protocols wrap with `sockopt_init_user()` and `put_user()` the length only on
  success, as `udp_getsockopt()` does.
- `do_sock_setsockopt()`: returns `-EINVAL` for negative `optlen` before any
  handler; when a cgroup BPF program ran and left a non-zero `optlen`,
  `optval` becomes `KERNEL_SOCKPTR()` of a kernel buffer that can be as small
  as that `optlen` (`__cgroup_bpf_run_filter_setsockopt()` in
  `kernel/bpf/cgroup.c`), so a copy larger than `optlen` reads past a slab
  object.
- `copy_struct_from_sockptr()`: never reads more than the caller's size;
  accepts a shorter value and zero-fills the rest; returns `-E2BIG` when the
  excess bytes are non-zero.
- `copy_safe_from_sockptr()`: rejects a shorter value with `-EINVAL`, and
  ignores excess bytes.
