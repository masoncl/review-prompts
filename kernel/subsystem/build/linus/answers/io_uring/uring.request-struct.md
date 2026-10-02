- Unions in `struct io_kiocb` (`include/linux/io_uring_types.h`); every other
  member, including `file_node`, `creds`, `apoll`, `async_data`, `link`, `cqe`
  and `big_cqe`, has its own storage:

| Union | Live member is chosen by |
|---|---|
| `file` / `cmd` | both; `file` is the first word of `cmd` |
| `kbuf` / `buf_node` | `REQ_F_BUFFER_SELECTED` / `REQ_F_BUF_NODE` |
| `comp_list` / `apoll_events` | on `free_list` or `compl_reqs` / poll armed |
| `io_task_work` / `iopoll_start` | task work queued / hybrid IOPOLL timing |
| `hash_node` / `iopoll_node` / `rcu_head` | see below |
| `cqe.fd` / `cqe.flags` | before / after `io_assign_file()` |

- `REQ_F_BUFFER_RING`: marks no union member; there is no `buf_list` pointer in
  the request, the list travels in `struct io_br_sel`.
- `kbuf` with `buf_node`: neither `io_find_buf_node()` nor
  `io_provided_buffer_select()` tests the other flag; prep must reject the
  combination, for example `io_sendmsg_prep()` and `io_recvmsg_prep()`.
- `iopoll_node`: live when `REQ_F_IOPOLL` is set, which happens at issue in
  `io_rw_init_file()` and `io_uring_cmd()`; `ctx->iopoll_list` links through
  it, not through `comp_list`.
- `hash_node`: used by poll, futex, waitid and cancelable uring_cmd lists.
- `hash_node` with `iopoll_node`: `io_init_req()` fails opcodes without
  `iopoll` in `struct io_issue_def` on an `IORING_SETUP_IOPOLL` ring, and
  `io_uring_cmd_mark_cancelable()` returns early on `REQ_F_IOPOLL`.
- `rcu_head`: only for requests allocated by `io_msg_data_remote()` and freed
  by `io_msg_tw_complete()`.
- `iopoll_start`: written at issue under `IORING_SETUP_HYBRID_IOPOLL`.
- `cqe.fd`: `io_assign_file()` also runs from `io_wq_submit_work()`, so
  `cqe.flags` must not be written before the file is assigned, except on a
  request that is failed without being issued, as `io_submit_fail_init()` does
  through `io_req_set_res()`.
- `struct io_cmd_data`: `file` plus `data[56]`, 64 bytes on 64-bit; the opcode
  struct's own leading file pointer counts toward that size.
- `struct io_rw`: starts with `struct kiocb`, not `struct file *`; it relies on
  `ki_filp` being the first member.
