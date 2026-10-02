- `CC_FLAGS_DIALECT` in the top-level `Makefile`: holds the dialect; exported and
  appended to `KBUILD_CFLAGS`. There is no CSTD_FLAG in this tree.
- `CC_FLAGS_DIALECT` contents, in order: `-std=gnu11`; the value of
  `CONFIG_CC_MS_EXTENSIONS`; under `CONFIG_CC_IS_CLANG` also `-Wno-gnu` and
  `-Wno-microsoft-anon-tag`.
- `CONFIG_CC_MS_EXTENSIONS` (string, `init/Kconfig`): `-fms-anonymous-structs`
  when the compiler accepts it, `-fms-extensions` otherwise; `-fms-extensions`
  is therefore not on every command line.
- `-include $(srctree)/include/linux/compiler_types.h`: added by `c_flags` in
  `scripts/Makefile.lib`, not by `LINUXINCLUDE`.
- `USERINCLUDE` (part of `LINUXINCLUDE`): force-includes
  `include/linux/compiler-version.h` and `include/linux/kconfig.h`.
