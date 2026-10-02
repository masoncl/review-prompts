- `CONFIG_SHELL`: `sh`, set unconditionally in the top-level `Makefile`; it is
  never bash by choice of the build.
- `BASH`: `bash`, set and exported in the top-level `Makefile`;
  `Documentation/kbuild/makefiles.rst` does not list it.
- Interpreter in the rule decides: `$(CONFIG_SHELL) script` runs the script
  under `sh` whatever its `#!` line says.
- `SHELL`: the top-level `Makefile` and the makefiles under `scripts/` do not
  set it; `arch/um/Makefile`, which the top-level `Makefile` includes for that
  architecture, sets `SHELL := bash`.
- Python in `Documentation/process/changes.rst`: row `Python 3.9.x`, not marked
  "(optional)"; the Python section says several configuration options require
  it.
- GNU awk in `Documentation/process/changes.rst`: marked "(optional)", needed
  for `CONFIG_BUILTIN_MODULE_RANGES`; `AWK` is `awk`.
- **Unsafe usage**: a rule that runs a script by its path alone, relying on the
  execute bit.
  - Safe: name the interpreter before the path, as `$(PERL) -w
    $(srctree)/scripts/checkincludes.pl` in the `includecheck` target and
    `$(CONFIG_SHELL) $(srctree)/scripts/rust_is_available.sh` in `prepare`;
    `Documentation/kbuild/makefiles.rst`, "Script invocation", states the
    requirement.
- **Unsafe usage**: a script that uses bash syntax, run through
  `$(CONFIG_SHELL)`.
  - Safe: run it with `$(BASH)`, as `cmd_tags` in the top-level `Makefile` runs
    `scripts/tags.sh` and `cmd_genimage` in `arch/x86/boot/Makefile` runs
    `genimage.sh`.
  - Safe: a script that keeps to POSIX sh syntax, run through
    `$(CONFIG_SHELL)`, as `scripts/rust_is_available.sh` (`#!/bin/sh`).
