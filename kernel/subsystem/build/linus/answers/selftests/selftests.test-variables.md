- `TEST_GEN_MODS_DIR` (a directory of test modules): `all` builds it with a
  sub-make through `gen_mods_dir`; `install` copies only its `*.ko` files, into
  a subdirectory of the same name; `clean` runs the sub-make's `clean` through
  `clean_mods_dir`; not run, not listed. See `livepatch/Makefile` under
  `tools/testing/selftests/`.
- `TEST_CUSTOM_PROGS`: not a prerequisite of `all` in
  `tools/testing/selftests/lib.mk`. The Makefile adds
  `all: $(TEST_CUSTOM_PROGS)` itself, writes the `$(OUTPUT)/` prefix itself and
  lists the program in `EXTRA_CLEAN`, as `sync/Makefile` does.
- `clean`: `CLEAN` in `lib.mk` removes `TEST_GEN_PROGS`,
  `TEST_GEN_PROGS_EXTENDED`, `TEST_GEN_FILES` and `EXTRA_CLEAN`, with
  `$(RM) -r`, and nothing else.
- `TEST_GEN_FILES` and the other two prefixed lists: every entry is a
  prerequisite of `all`, but the common pattern rules only make
  `$(OUTPUT)/name` from `name.c` or `name.S`, and `$(OUTPUT)/name.o` from
  `name.S`. `lib.mk` has no rule for any other entry.
- `OVERRIDE_TARGETS` set: `lib.mk` defines no pattern rule at all; the entries
  stay prerequisites of `all`.
