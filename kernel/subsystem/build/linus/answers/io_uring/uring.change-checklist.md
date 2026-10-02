- `BUILD_BUG_SQE_ELEM()` lines in `io_uring_init()`: do not cover every member
  of `struct io_uring_sqe`; for example `optval`, `optlen`, `level`,
  `uring_cmd_flags` and `zcrx_ifq_idx` have no line.
- SQE member without a line: only the 64-byte size check and the offsets of
  the listed members after it constrain it; nothing forces a line for a new
  union member.
- `struct io_uring_cqe`, `struct io_uring_params`, `struct io_sqring_offsets`,
  `struct io_cqring_offsets`: `io_uring_init()` has no size or offset check
  for them; review their layout by hand.
- `struct io_uring_cqe`: the one `BUILD_BUG_ON()` under `io_uring/` that names
  it is in `io_process_timestamp_skb()` in `io_uring/cmd_net.c`; it requires
  the same size as `struct io_timespec`.
- Headers under `include/uapi/linux/io_uring/`: no layout check in
  `io_uring_init()`.
- `struct io_uring_rsrc_update` against `struct io_uring_rsrc_update2`: the
  check compares `sizeof` only (first not larger than second); field overlap
  is not checked.
- `IORING_OP_LAST`: no build-time check that it fits in a `u8`.
- Per-opcode command struct size: checked by `io_kiocb_cmd_sz_check()` in
  `include/linux/io_uring_types.h`, at each `io_kiocb_to_cmd()` use, not in
  `io_uring_init()`.
- `IORING_URING_CMD_MASK`: `io_uring_init()` requires its top 8 bits clear;
  kernel-internal `IORING_URING_CMD_CANCELABLE` and `IORING_URING_CMD_REISSUE`
  in `include/linux/io_uring/cmd.h` use that range.
- `tools/testing/selftests/`: has no io_uring directory.
- In-tree tests that use io_uring: in the directories of other subsystems;
  search `tools/testing` for `io_uring`; for example
  `tools/testing/selftests/net/io_uring_zerocopy_tx.c`,
  `tools/testing/selftests/drivers/net/hw/iou-zcrx.c` and
  `tools/testing/vsock/vsock_uring_test.c`.
- `io_uring/mock_file.c`, built with `CONFIG_IO_URING_MOCK_FILE` from
  `init/Kconfig`: test-only misc device `io_uring_mock`;
  `io_create_mock_file()` sets `TAINT_TEST`; nothing under `tools/` uses it.
- `tools/include/uapi/linux/io_uring.h`: not identical to
  `include/uapi/linux/io_uring.h`; for example it has no `IORING_OP_PIPE`.
