- Files not in the table: `io_uring/Makefile` gives the option of each; those
  on its `obj-$(CONFIG_IO_URING)` line need no other option.
- `Kbuild` enters `io_uring/` only under `CONFIG_IO_URING`, so every option
  in the table is in addition to that one.

| Job | File | Built only under | Easy to miss |
|---|---|---|---|
| Task work | `io_uring/tw.c` | — | `tctx_task_work()` is here, not in `io_uring/io_uring.c`; `io_req_task_work_add()` is an inline in `io_uring/tw.h` |
| Waiting for completions | `io_uring/wait.c` | — | `io_cqring_wait()` is here, not in `io_uring/io_uring.c` |
| Registered resources | `io_uring/rsrc.c` | — | `io_fixed_fd_install()` and `io_fixed_fd_remove()` are in `io_uring/filetable.c` |
| Worker pool | `io_uring/io-wq.c` | `CONFIG_IO_WQ` | promptless `bool` in `fs/Kconfig`; `config IO_URING` in `init/Kconfig` selects it, so it is built whenever io_uring is |
| Zero-copy send notifications | `io_uring/notif.c` | — | not gated on `CONFIG_NET`; the only caller of `io_alloc_notif()` is in `io_uring/net.c`, which is built under `CONFIG_NET` |
| Zero-copy receive | `io_uring/zcrx.c` | `CONFIG_IO_URING_ZCRX` | `def_bool y` with no prompt in `io_uring/Kconfig`; its `depends on` lines decide it, for example `NET_RX_BUSY_POLL` |
| Passthrough commands | `io_uring/uring_cmd.c` | — | socket commands (`io_uring_cmd_sock()`) are in `io_uring/cmd_net.c`, built under `CONFIG_NET` |
| BPF hooks: per-opcode filters | `io_uring/bpf_filter.c` | `CONFIG_IO_URING_BPF` | classic BPF programs, run from `io_submit_sqe()` in `io_uring/io_uring.c`; `def_bool y` in `io_uring/Kconfig`, depends on `BPF` and `NET` |
| BPF hooks: struct_ops | `io_uring/bpf-ops.c` | `CONFIG_IO_URING_BPF_OPS` | `def_bool y` in `io_uring/Kconfig`, depends for example on `DEBUG_INFO_BTF`; there is no bpf.c under `io_uring/` |
| BPF hooks: the loop that calls `loop_step` | `io_uring/loop.c` | — | built without `CONFIG_IO_URING_BPF_OPS`, but only `io_uring/bpf-ops.c` sets `ctx->loop_step` |
| Test-only file | `io_uring/mock_file.c` | `CONFIG_IO_URING_MOCK_FILE` | `tristate` in `init/Kconfig`, so it can be a module; registers a misc device |
