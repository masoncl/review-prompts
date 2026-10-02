- Rust: `foo-rust := y`, a flag and not an object list; the crate root is
  `foo.rs`. See `samples/rust/hostprogs/Makefile`.
- `foo-y` for a host program: not read; `scripts/Makefile.host` reads only
  `$(foo-objs)`, `$(foo-cxxobjs)` and `$(foo-rust)`, so
  `foo-$(CONFIG_X) += x.o` adds nothing.
- `hostprogs-always-y += foo`: shorthand for `hostprogs` plus `always-y`,
  expanded in `scripts/Makefile.build`.
- Per-directory link flags: no such variable; HOST_EXTRALDFLAGS does not exist
  in this tree.
- Link variables: `KBUILD_HOSTLDFLAGS` and `KBUILD_HOSTLDLIBS` globally,
  `HOSTLDLIBS_foo` per program, nothing in between.
- Rust per-program flags: `HOSTRUSTFLAGS_foo`, without `.o`; the C and C++
  per-file variables keep the `.o`.
- Rust link: `cmd_host-rust` passes `KBUILD_HOSTLDFLAGS` through `-Clink-args`
  and uses neither `KBUILD_HOSTLDLIBS` nor `HOSTLDLIBS_foo`.
