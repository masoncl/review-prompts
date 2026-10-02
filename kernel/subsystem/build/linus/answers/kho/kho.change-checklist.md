- `CONFIG_KEXEC_HANDOVER=n`: stubs also live in
  `include/linux/kho_radix_tree.h` and `kernel/kexec_internal.h`, besides
  `include/linux/kexec_handover.h`.
- KHO options: `kernel/liveupdate/Kconfig`; `TEST_KEXEC_HANDOVER` and
  `LIVEUPDATE_TEST` are in `lib/Kconfig.debug`.
- Userspace memblock tests: `tools/testing/memblock/` compiles
  `mm/memblock.c` with empty `linux/kexec_handover.h` and
  `linux/kho/abi/memblock.h` and a `kho_scratch_overlap()` stub in
  `tools/testing/memblock/internal.h`. A new KHO call outside
  `#ifdef CONFIG_KEXEC_HANDOVER` needs a stub there.
- Documentation build: kernel-doc directives under `Documentation/` name
  `DOC:` titles and source files, for example in
  `Documentation/core-api/kho/abi.rst`,
  `Documentation/core-api/kho/index.rst` and
  `Documentation/core-api/liveupdate.rst`; renaming either breaks them.
- x86 decompressor: `process_kho_entries()` in
  `arch/x86/boot/compressed/kaslr.c` reads `struct kho_scratch` from
  `include/asm-generic/kexec_handover.h` and `struct kho_data` from
  `arch/x86/include/uapi/asm/setup_data.h`.
- EFI boot: `drivers/firmware/efi/efi-init.c` keeps only scratch regions when
  `is_kho_boot()` is true.
- Crash images: `kho_fill_kimage()` and `kho_locate_mem_hole()` skip
  `KEXEC_TYPE_CRASH`.
- Selftests: both `tools/testing/selftests/kho/` and
  `tools/testing/selftests/liveupdate/` exist; `vmtest.sh` in the first
  embeds its own kernel config.
