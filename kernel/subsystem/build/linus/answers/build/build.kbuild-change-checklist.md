- Path variables per setup, all set in the top `Makefile`; make always runs
  in the output directory:

  | Setup | `srctree` | `srcroot` | `objtree` | `building_out_of_srctree` | `VPATH` |
  |---|---|---|---|---|---|
  | in-tree | `.` | `.` | `.` | unset | empty |
  | `O=` | `..` or absolute | same as `srctree` | `.` | 1 | `$(srcroot)` |
  | `M=`, built in the module directory | absolute | `.` | absolute | unset | empty |
  | `M=` with `MO=` | absolute | `..` or absolute, module source | absolute | 1 | `$(srcroot)` |

- `KBUILD_ABS_SRCTREE`: keeps `srcroot` absolute in every row, so `$(src)` is
  absolute even in an in-tree build.
- `src`: `src := $(srcroot)/$(obj)` in `scripts/Makefile.build` and
  `scripts/Makefile.clean`; `obj` is relative to the current directory, except
  that `rust-analyzer` under `KBUILD_EXTMOD` passes `$(objtree)/rust` with
  `src=` on the command line.
- There is no extmod_prefix or kbuild-dir here, and Kbuild does not define
  `abs_objtree`; `kbuild-file` in `scripts/Kbuild.include` finds the makefile
  through `$(src)`, and the top `Makefile` uses `abs_output`.
- `KBUILD_OUTPUT` (`O=`) under `KBUILD_EXTMOD`: names the kernel build
  directory and becomes `objtree`; it must exist.
- `KBUILD_EXTMOD_OUTPUT`: the variable that `MO=` on the command line sets;
  when it is set it is the module output directory, ahead of the other cases.
  See `output` in the top `Makefile`.
- `Module.symvers`, `modules.order` and `.module-common.o` of an external
  module: written to the current directory, which is the module output
  directory.
- `KBUILD_EXTMOD` in the makefiles under `scripts/`: tested only for being
  set, never used as a path; `scripts/Makefile.lib` and
  `scripts/Makefile.modfinal` do not name it at all.
- `scripts/Makefile.modpost` under `KBUILD_EXTMOD`: sets `obj := .` and
  `src := $(srcroot)` and includes the module's `$(kbuild-file)` again, to
  read `KBUILD_EXTRA_SYMBOLS`.
- `INSTALL_MOD_DIR`: read only under `KBUILD_EXTMOD` in
  `scripts/Makefile.modinst`; in-tree modules go to `$(MODLIB)/kernel`.
- Compile pattern rules in `scripts/Makefile.build`: the prerequisite is
  `$(obj)/%.c`, not `$(src)/%.c`; `VPATH` finds a checked-in source, so one
  rule serves generated and checked-in files.
- Rules whose input is always checked in name `$(src)/%`, for example
  `$(obj)/%.lds` in `scripts/Makefile.build` and `$(obj)/%.lex.c` in
  `scripts/Makefile.host`.
- Include paths added under `building_out_of_srctree`: `scripts/Makefile.lib`
  adds `-I` for `$(src)` and `$(obj)` to `_c_flags`, `_a_flags` and
  `_cpp_flags`; `scripts/Makefile.host` adds only `$(obj)`;
  `scripts/Makefile.userprogs` adds none.
- `-fmacro-prefix-map=$(srcroot)/=`: added by the top `Makefile` only under
  `building_out_of_srctree`; no makefile in this tree passes
  -ffile-prefix-map.
- Read-only source tree: `cmd_copy` in `scripts/Makefile.lib` uses `cat`,
  because `cp` would carry the read-only mode to the copy and the next run of
  the rule would fail.
- `KBUILD_BUILTIN` and `KBUILD_MODULES`: the `$(obj)/` rule in
  `scripts/Makefile.build` builds `targets-for-builtin` only with the first,
  `targets-for-modules` only with the second, and `always-y` regardless of
  both.
- `KBUILD_BUILTIN` under `KBUILD_EXTMOD`: empty, so the `$(obj)/` rule builds
  no `extra-y`, `lib.a` or `built-in.a` for an external module.
- Single targets: `scripts/Makefile.build` has no `ifdef` on `single-build`
  and there is no KBUILD_SINGLE_TARGETS; the top `Makefile` passes
  `single-goals` as make goals, and `single-subdirs` and
  `single-subdir-goals` in `scripts/Makefile.build` hand each to its
  directory.
- Single-target suffixes: listed in `single-targets` in the top `Makefile`;
  `%.symtypes` is not among them.
- Single-target `.cmd` files: `scripts/Makefile.build` adds the goals to
  `targets`, so the goal's `.cmd` file is read even if nothing else lists it.
- `scripts/package/install-extmod-build`: fills the module build tree that
  the deb, rpm and pacman packages ship; it copies `scripts/` minus what
  `find_in_scripts()` prunes (for example `dtc` and `kconfig`), and tools
  outside `scripts/` only by name.
- A shared rule that runs a new tool for modules needs that tool copied by
  `scripts/package/install-extmod-build`.
- `vmlinux`: not copied by `scripts/package/install-extmod-build`;
  `cmd_btf_ko` in `scripts/Makefile.modfinal` tests for `$(objtree)/vmlinux`
  and skips BTF without it.
- `CC` differs from `HOSTCC` when packaging:
  `scripts/package/install-extmod-build` rebuilds the copied `scripts/`
  through `$(build)` with `HOSTCC` set to the target compiler, `VPATH` empty
  and `srcroot=.`.
- Source packages: `check-git` in `scripts/Makefile.package` fails them
  outside a git repository.
- `quiet_cmd_`: optional; `quiet_log_print` in `scripts/Kbuild.include`
  prints nothing for a `cmd_` without one, as for `cmd_mod` and
  `cmd_gen_order` in `scripts/Makefile.build`.
- `make -s`: `silent_log_print` runs `exec >/dev/null` before the command, so
  anything a `cmd_` prints on stdout is dropped; messages go to stderr.
- **Unsafe usage**: writing `$(srctree)/$(src)`.
  - Unsafe: `$(src)` already starts with `$(srcroot)`, so the path is wrong
    whenever `srcroot` is not `.`.
  - Safe: `$(src)/file`, as `$(obj)/%: $(src)/%_shipped` in
    `scripts/Makefile.lib`; `src` is defined in `scripts/Makefile.build`.
- **Potentially unsafe usage**: a bare relative path in a recipe or
  prerequisite of a shared makefile.
  - Unsafe: the path names a kernel file (a tool under `scripts/`, a
    generated header, a kernel source) and the rule can run under
    `KBUILD_EXTMOD`; the current directory is the module output directory and
    `VPATH` is empty or the module source.
  - Safe: the path names an output of the tree being built, as
    `modules.order` and `Module.symvers` in `scripts/Makefile.modpost`.
  - Safe: a kernel file with its root spelled out, as
    `$(srctree)/scripts/module-common.c` and `$(objtree)/scripts/module.lds`
    in `scripts/Makefile.modfinal`; the top `Makefile` makes both roots
    absolute under `KBUILD_EXTMOD`.
  - Safe: a makefile run only for the kernel, as `scripts/Makefile.vmlinux`,
    which the top `Makefile` invokes inside `ifeq ($(KBUILD_EXTMOD),)`; the
    current directory is `objtree`, and a checked-in file is named bare only
    as a prerequisite, where `VPATH` finds it, as `scripts/link-vmlinux.sh`,
    which the recipe runs as `$<`.
