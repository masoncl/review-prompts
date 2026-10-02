- `OPEN_HOW_SIZE_VER0` and `OPEN_HOW_SIZE_LATEST`: defined in
  `include/linux/fcntl.h`, which is not a uapi header;
  `include/uapi/linux/openat2.h` defines `struct open_how` but no size
  constant.
- `CLONE_ARGS_SIZE_VER0`, `CLONE_ARGS_SIZE_VER1` and `CLONE_ARGS_SIZE_VER2`:
  defined in `include/uapi/linux/sched.h`, next to `struct clone_args`.
