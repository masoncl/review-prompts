| | in-tree | `O=` | external, built in its source dir | external, other output dir (`MO=`) |
|---|---|---|---|---|
| `$(objtree)` | `.` | `.` | kernel build dir, absolute | same |
| `$(srcroot)` | `.` | `..` or absolute | `.` | `..` or absolute |
| `$(obj)` | `drivers/foo` | `drivers/foo` | `.` at the top, `sub` below | same |
| `$(src)` | `./drivers/foo` | `$(srcroot)/drivers/foo` | `./.` at the top | `$(srcroot)/.` at the top |
| `building_out_of_srctree` | unset | `1` | unset | `1` |

- `$(srcroot)` is `..` when the working directory is a direct child of the
  source directory; `KBUILD_ABS_SRCTREE` keeps it absolute in every build.
- `$(srctree)`: equals `$(srcroot)` for kernel builds; for an external module
  it is the absolute kernel source and differs from `$(srcroot)`.
- `building_out_of_srctree` for an external module: compares the module
  source directory with the working directory, not the kernel tree; a module
  built in place gets no `VPATH` and no automatic `-I`.
- Automatic `-I$(src) -I$(obj)`: only under `building_out_of_srctree`; added
  to `_c_flags`, `_a_flags` and `_cpp_flags`, not to `_rust_flags`;
  `scripts/Makefile.host` adds only `-I $(obj)`.
- `-include` files in assembler and linker-script preprocessing: `a_flags`
  and `cpp_flags` in `scripts/Makefile.lib` carry `LINUXINCLUDE`, so both get
  `include/linux/compiler-version.h` and `include/linux/kconfig.h`; neither
  gets `include/linux/compiler_types.h`, which only `c_flags` adds.
- **Potentially unsafe usage**: `$(srctree)/$(obj)` or `$(objtree)/$(obj)`.
  - Unsafe: in a makefile that can be built as an external module; there
    `$(srctree)` and `$(objtree)` are the kernel trees while `$(obj)` is
    relative to the module.
  - Safe: in a makefile built only as part of the kernel, as
    `arch/powerpc/boot/Makefile`; the top `Makefile` sets `srctree` to
    `$(srcroot)` and `objtree` to `.` when `KBUILD_EXTMOD` is unset.
- **Potentially unsafe usage**: no explicit `-I$(src)` for a header in the
  makefile's own directory.
  - Unsafe: when the header is included from a file in another directory,
    such as `include/trace/define_trace.h` including `TRACE_INCLUDE_FILE`;
    it builds with `O=` and fails in-tree, where `scripts/Makefile.lib` adds
    no `-I`.
  - Safe: when the including file is in the same directory and uses quotes,
    as `kernel/trace/trace.c` including `trace.h`; with a separate output
    directory `scripts/Makefile.lib` adds `-I$(src) -I$(obj)`.
  - Safe: with `-I$(src)` given, as `CFLAGS_bpf_trace.o` in
    `kernel/trace/Makefile`.
