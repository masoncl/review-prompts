- Prefixing is done with `patsubst` at the point of the include; in `lib.mk`,
  `addprefix` appears only where out-of-tree `run_tests` prefixes `TEST_PROGS`
  after copying them.
- Before the include the three variables hold bare names. A rule for a bare
  name defines a different target from the one `all` depends on.
- `landlock/Makefile` shows the consequence: it writes the same
  target-specific assignments twice, before the include for the bare names
  and after it for the prefixed ones.
- `OUTPUT` default: `lib.mk` sets `OUTPUT := $(shell pwd)` only under
  `ifeq (0,$(MAKELEVEL))`. A Makefile that recurses into subdirectories passes
  `OUTPUT=` itself, as `arm64/Makefile` does.
- **Potentially unsafe usage**: a rule or prerequisite written as
  `$(OUTPUT)/name` before the include.
  - Unsafe: when the directory is built directly with no `OUTPUT=`; `OUTPUT`
    is still empty when make reads the rule, so the target is `/name`.
  - Safe: when a parent make passes `OUTPUT=`, as
    `tools/testing/selftests/Makefile` does in each of its per-directory
    loops.
  - Safe: after the include, as in `net/Makefile` and `vDSO/Makefile`.
- Assigned after the include: an entry is not prefixed and is not a
  prerequisite of `all`. The `run_tests`, `install`, `emit_tests` and `clean`
  recipes still see it, because recipes expand when they run.
- `lkdtm/Makefile` assigns `TEST_GEN_PROGS` after the include; it writes
  `$(OUTPUT)/` itself and adds `all: $(TEST_GEN_PROGS)`.
