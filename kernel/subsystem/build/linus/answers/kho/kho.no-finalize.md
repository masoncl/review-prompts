- No finalize or abort step, notifier chain or debugfs control file exists;
  there is no kho_finalize() or register_kho_notifier() in this tree.
- Stale text: the help of `CONFIG_KEXEC_HANDOVER_DEBUGFS` and a comment in
  `kernel/liveupdate/luo_flb.c` still mention finalize; no code implements it.
- Debugfs in `kernel/liveupdate/kexec_handover_debugfs.c`: every file is
  created with mode 0400.
- Root FDT: built once by `kho_out_fdt_setup()` in `kho_init()`, with the
  physical address of `kho_out.radix_tree.root` in it, then edited in place.
- `kho_fill_kimage()`: generates nothing; it stores `virt_to_phys(kho_out.fdt)`
  in `image->kho.fdt` and adds the `kho_scratch` array as a kexec buffer.
- The root FDT and the radix tree are not copied at load or at
  `kernel_kexec()`; the next kernel reads the root FDT page and radix tree
  pages as they are in memory at the jump.
- Precondition for any handover: the image was loaded through
  `kernel/kexec_file.c`, the only caller of `kho_fill_kimage()`, with
  `kho_enable` true and a non-crash image; otherwise `image->kho.fdt` stays 0
  and `setup_kho()` in `arch/x86/kernel/kexec-bzimage64.c` adds nothing.
