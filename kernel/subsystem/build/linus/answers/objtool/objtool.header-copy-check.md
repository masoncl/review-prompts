- `include/linux/objtool_types.h`: compared for every `SRCARCH`; every other
  file only when `SRCARCH` is `x86`.
- Files compared: read `FILES` and `SYNC_CHECK_FILES` in
  `tools/objtool/sync-check.sh`; the x86 list here also has
  `include/linux/interval_tree_generic.h` and
  `include/linux/livepatch_external.h`.
- A difference: prints "Warning: Kernel ABI header at ... differs from latest
  version at ..." to stderr and the build goes on.
- SKIP_SYNC_CHECK: not in this tree, and the script does not look at git.
- `tools/objtool/sync-check.sh`: exits 0 without comparing when `../../kernel`,
  `../../tools` or `../objtool` is not a directory.
- objtool is compiled against the copy (`-I$(srctree)/tools/include` in
  `tools/objtool/Makefile`), so a patch that changes only the kernel header
  builds with a warning and objtool keeps the old values.
