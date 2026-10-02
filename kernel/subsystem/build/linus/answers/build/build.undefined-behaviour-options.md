- `-fno-strict-overflow` and `-fno-delete-null-pointer-checks`: plain
  `KBUILD_CFLAGS +=`, no `cc-option`, no `ifdef`.
- `-fwrapv`: no makefile passes it.
- `--param=allow-store-data-races=0` and `-fno-allow-store-data-races`: each
  through `cc-option`, both inside `ifdef CONFIG_CC_IS_GCC`.
- Probe only (`cc-option`, any compiler): `-fzero-init-padding-bits=all`,
  `-fstrict-flex-arrays=3`, `-fno-stack-clash-protection`.
