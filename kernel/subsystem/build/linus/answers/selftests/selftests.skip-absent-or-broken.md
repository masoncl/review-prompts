- Plain C, whole program: `test_clone3_supported()` in
  `tools/testing/selftests/clone3/clone3_selftests.h` skips on `ENOSYS`;
  `tools/testing/selftests/clone3/clone3.c` has no `ENOSYS` test of its own.
- Plain C, one case: `test_pidfd_send_signal_syscall_support()` in
  `tools/testing/selftests/pidfd/pidfd_test.c` gives `ksft_test_result_skip()`
  on `ENOSYS` and `ksft_exit_fail_msg()` on any other error.
- `tools/testing/selftests/pidfd/pidfd_open_test.c`: has no skip.
- Harness: `TEST_F(child, fetch_fd)` in
  `tools/testing/selftests/pidfd/pidfd_getfd_test.c` skips on `ENOSYS` from
  `sys_kcmp()`; any other result reaches `EXPECT_EQ(ret, 0)`.
- Harness, unknown flag: `TEST(close_range_cloexec)` in
  `tools/testing/selftests/core/close_range_test.c` skips on `ENOSYS` or
  `EINVAL` from a probe call; any other probe result carries on to the real
  calls, which `ASSERT_EQ(0, ret)` checks.
- `tools/testing/selftests/seccomp/seccomp_bpf.c`: `SKIP()` gated on `errno`
  inside the block after `ASSERT_EQ()`, for example around
  `unshare(CLONE_NEWPID)`.
- Landlock tests: no `SKIP()` under `tools/testing/selftests/landlock/` is
  gated on `ENOSYS` or `EOPNOTSUPP`.
- Probe without `errno`: `supports_filesystem()` in
  `tools/testing/selftests/landlock/fs_test.c` looks the name up in
  `/proc/filesystems`.
- openat2 tests: they are in `tools/testing/selftests/filesystems/openat2/`;
  `__detect_openat2_supported()` sets `openat2_supported` from `fd >= 0` and
  does not look at `errno`, so it does not separate absent from broken.
- `rseq_available()` in `tools/testing/selftests/rseq/rseq.c`: `ENOSYS` is
  false, `EINVAL` is true, anything else calls `abort()`; its caller in
  `tools/testing/selftests/rseq/syscall_errors_test.c` jumps to `error` and
  does not skip.
