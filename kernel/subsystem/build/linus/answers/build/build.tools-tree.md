- Kbuild makefiles under `tools/` (those that set `obj-m`, for example
  `tools/testing/cxl/Kbuild` and `tools/testing/nvdimm/Kbuild`): their objects
  are compiled with `KBUILD_CFLAGS`.
- `tools/testing/cxl/Kbuild`, `tools/testing/cxl/test/Kbuild`,
  `tools/testing/nvdimm/Kbuild`: filter two warnings out of `KBUILD_CFLAGS`.
  No other makefile under `tools/` refers to `KBUILD_CFLAGS`.
- `tools/scripts/Makefile.include`: defines `EXTRA_WARNINGS`, which a tool must
  add to `CFLAGS` itself; the only thing it appends to `CFLAGS` is
  `$(CLANG_CROSS_FLAGS)`. It sets no `-std=`, `-O` or `-g`.
- `-fno-strict-aliasing` in `tools/scripts/Makefile.include`: added to
  `EXTRA_WARNINGS` only when `MAKE_VERSION` is 3.x.
- Options that tools set themselves, for example:

| Makefile | Options |
|---|---|
| `tools/perf/Makefile.config` | `-std=gnu11`, `-funsigned-char`, `-fno-strict-aliasing` |
| `tools/objtool/Makefile` | `-std=gnu11` |
| `tools/lib/bpf/Makefile` | `-std=gnu89`, not the kernel's `-std=gnu11` |
| `tools/virtio/Makefile`, `tools/testing/vsock/Makefile` | `-fno-strict-overflow`, `-fno-strict-aliasing`, `-fno-common` |

- `-fno-delete-null-pointer-checks` and `-fshort-wchar`: in no makefile under
  `tools/`.
- `CFLAGS_$(obj)` and `CFLAGS_REMOVE_$(obj)` in `tools/build/Build.include`:
  keyed by the name given to `$(build)=` (for example `objtool`), not by
  directory.
- `KBUILD_HOSTCFLAGS`: `tools/build/Makefile` passes it as `HOSTCFLAGS` when it
  builds fixdep; `tools/objtool/Makefile` appends `$(HOSTCFLAGS)` to
  `OBJTOOL_CFLAGS`.
- `tools/objtool/sync-check.sh`: run by the `$(OBJTOOL_IN)` rule on every
  objtool build; `tools/perf/check-headers.sh` runs from the `check-headers`
  target in `tools/perf/Makefile`.
- Headers from the real tree: not every tool uses only the copies; for example
  `tools/virtio/Makefile` force-includes `../../include/linux/kconfig.h`, and
  `tools/platform/x86/amd/Makefile` adds `-I$(srctree)/include`.
