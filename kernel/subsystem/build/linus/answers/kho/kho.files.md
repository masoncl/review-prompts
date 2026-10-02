| Job | File | Easy to miss |
|---|---|---|
| KHO core | `kernel/liveupdate/kexec_handover.c` | also holds the radix tree, vmalloc preservation and kexec metadata code; none has a file of its own |
| KHO debug checks | `kernel/liveupdate/kexec_handover.c` | there is no kexec_handover_debug.c; `CONFIG_KEXEC_HANDOVER_DEBUG` builds no object and is tested with `IS_ENABLED()` |
| KHO debugfs | `kernel/liveupdate/kexec_handover_debugfs.c` | `CONFIG_KEXEC_HANDOVER_DEBUGFS`; stubs in `kernel/liveupdate/kexec_handover_internal.h` |
| Serialization blocks | `kernel/liveupdate/kho_block.c` | listed in `luo-y`, so built under `CONFIG_LIVEUPDATE`, not under `CONFIG_KEXEC_HANDOVER` alone; `include/linux/kho_block.h` has no stubs; users are `kernel/liveupdate/luo_file.c` and `kernel/liveupdate/luo_session.c` |
| LUO | `kernel/liveupdate/luo_core.c`, `kernel/liveupdate/luo_session.c`, `kernel/liveupdate/luo_file.c`, `kernel/liveupdate/luo_flb.c`, `kernel/liveupdate/luo_internal.h` | the four `.c` files are linked into `luo.o` together with `kho_block.o` |
| Public headers | `include/linux/kexec_handover.h`, `include/asm-generic/kexec_handover.h`, `include/linux/kho_radix_tree.h`, `include/linux/kho_block.h`, `include/linux/liveupdate.h`, `include/uapi/linux/liveupdate.h` | the radix tree and the blocks each have their own header; `struct kho_scratch` is in `include/asm-generic/kexec_handover.h` |
| ABI between kernels | `include/linux/kho/abi/kexec_handover.h`, `include/linux/kho/abi/kexec_metadata.h`, `include/linux/kho/abi/block.h`, `include/linux/kho/abi/luo.h`, `include/linux/kho/abi/memfd.h`, `include/linux/kho/abi/memblock.h` | six headers; `include/linux/kho/abi/memblock.h` is used by `mm/memblock.c`, `include/linux/kho/abi/kexec_metadata.h` by `kernel/liveupdate/kexec_handover.c` |
| memfd handler | `mm/memfd_luo.c` | `CONFIG_LIVEUPDATE_MEMFD` |
| In-kernel test, KHO | `lib/test_kho.c` | symbol is `CONFIG_TEST_KEXEC_HANDOVER`; there is no CONFIG_TEST_KHO; plain `module_init()`, not KUnit |
| In-kernel test, LUO | `lib/tests/liveupdate.c` | `CONFIG_LIVEUPDATE_TEST`; not KUnit and no initcall; `liveupdate_register_file_handler()` calls `liveupdate_test_register()` |
| Selftests, KHO | `tools/testing/selftests/kho/` | no Makefile and not in `TARGETS`; run through `tools/testing/selftests/kho/vmtest.sh` |
| Selftests, LUO | `tools/testing/selftests/liveupdate/` | in `TARGETS` of `tools/testing/selftests/Makefile` |
