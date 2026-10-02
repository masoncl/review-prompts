- `arch/arm64/tools/cpucaps`: the file is not sorted;
  `arch/arm64/tools/gen-cpucaps.awk` numbers names in file order, and
  `update_cpu_capabilities()` probes in number order, so order matters where
  one cap's `.matches` reads another, as the `BUILD_BUG_ON()` in
  `can_use_gic_priorities()` checks.
- `arch/arm64/tools/gen-cpucaps.awk`: fails the build only for a line that is
  neither blank, nor a `#` comment, nor made of upper case, digits,
  underscore and lower-case v.
- Generated header: `asm/cpucap-defs.h`; `cpucap_is_possible()` is
  hand-written in `arch/arm64/include/asm/cpucaps.h`.
- `KERNEL_HWCAP_` constants: generated into `asm/kernel-hwcap.h` by
  `arch/arm64/tools/gen-kernel-hwcaps.sh` from
  `arch/arm64/include/uapi/asm/hwcap.h`; the constant needs only the uapi
  define, not a hand-written `KERNEL_HWCAP_` line.
- Table entry without `.matches`: `init_cpucap_indirect_list_from_array()`
  treats it as the end of the table, so every later entry is silently
  dropped.
- Name in `arch/arm64/tools/cpucaps` with no table entry: builds and boots;
  the cap is never set and `this_cpu_has_cap()` returns false.
- `.type` scope of a MIDR-based erratum: checked at boot; the matchers such as
  `is_affected_midr_range_list()` `WARN_ON()` a scope other than
  `SCOPE_LOCAL_CPU`. The late-CPU bits are checked by nothing.
- Feature with `has_cpuid_feature()`: the register must be in
  `__read_sysreg_by_encoding()`, else `BUG()`; at boot for a scope other than
  `SCOPE_SYSTEM`, and for `SCOPE_SYSTEM` only when `verify_local_cpu_caps()`
  checks a late CPU or `this_cpu_has_cap()` is called.
- `#ifdef` around the table entry and the `cpucap_is_possible()` case: nothing
  checks that they name the same option; with the entry built and the case
  false, `cpus_have_cap()` on a constant reads false while the bit is set, as
  for `ARM64_HAS_TLB_RANGE` without `CONFIG_ARM64_TLB_RANGE`.
- `arm64_errata` guards: not always a `CONFIG_ARM64_ERRATUM_` option; some
  entries use a shared hidden option such as
  `CONFIG_ARM64_WORKAROUND_REPEAT_TLBI_SYNC`, and some have no guard.
- `ERRATA_MIDR_RANGE()` and its relatives in `arch/arm64/kernel/cpu_errata.c`
  set `.type` and `.matches`; an entry written by hand must set both.
