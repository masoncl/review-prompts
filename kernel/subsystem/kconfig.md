# Kconfig Subsystem Details

## Config Symbol References

Referencing a non-existent config symbol in `select` or `depends on` causes
silent build failures: the dependency is never satisfied, or selecting a
non-existent symbol has no effect, leaving required drivers or features
disabled when the user expects them to be built.

- All config names in `select FOO` and `depends on FOO` must correspond to a
  `config FOO` definition somewhere in the kernel tree
- Watch for typos between similar prefixes: `QCM_` vs `QCS_`, `IMX8M_` vs
  `IMX8MM_`, etc.
- When adding a new config that selects an existing one, verify the selected
  symbol's name by searching for its `config` definition

## Dependency Propagation

Selecting a config symbol without inheriting its dependencies causes Kconfig
warnings at build time (`sym_warn_unmet_dep()` in
`scripts/kconfig/symbol.c`). Config A can be enabled on platforms where
config B (which A selects) cannot be enabled, producing unmet dependency
warnings and potential build failures.

- When `config A` uses `select B`, config A must have dependencies compatible
  with (same or more restrictive than) config B's `depends on` line
- Common case: if B has `depends on ARM64 || COMPILE_TEST`, then A must also
  have `depends on ARM64 || COMPILE_TEST`

```
// WRONG: Missing architecture dependency
config QCS_DISPCC_615
    tristate "QCS615 Display Clock Controller"
    select QCS_GCC_615  // QCS_GCC_615 depends on ARM64 || COMPILE_TEST
    // Missing: depends on ARM64 || COMPILE_TEST

// CORRECT: Proper dependency inheritance (drivers/clk/qcom/Kconfig)
config QCS_DISPCC_615
    tristate "QCS615 Display Clock Controller"
    depends on ARM64 || COMPILE_TEST
    select QCS_GCC_615
```

The resulting Kconfig warning looks like:
```
WARNING: unmet direct dependencies detected for QCS_GCC_615
  Depends on [n]: ARM64 || COMPILE_TEST
  Selected by [m]:
  - QCS_DISPCC_615 [=m]
```

## Cross-Config Consistency

When multiple related configs are added together (e.g., clock controllers
for the same SoC family), inconsistencies between them often indicate
copy-paste errors or typos.

- Compare new configs with existing similar configs in the same file
- Check that related configs (e.g., `QCS_DISPCC_615`, `QCS_GPUCC_615`,
  `QCS_VIDEOCC_615`) follow the same dependency and select patterns
- If one config in a series differs from the others, verify the difference
  is intentional

## Architecture-Specific Symbols in COMPILE_TEST Drivers

Using `select` for architecture-specific symbols in drivers that support
`COMPILE_TEST` can cause unmet dependency warnings or build failures on
unsupported architectures. The `select` statement forces the symbol on
regardless of its own dependencies, and if the selected symbol pulls in
arch-specific infrastructure, compilation may fail.

- `COMPILE_TEST` (defined in `init/Kconfig`) allows drivers to be compiled
  on any architecture for build coverage testing, even when the hardware
  only exists on one arch
- When a Kconfig has `depends on ARCH_FOO || COMPILE_TEST`, the driver can
  be built on architectures other than `ARCH_FOO`
- Using `select ARCH_SPECIFIC_SYMBOL` in such a driver triggers unmet
  dependency warnings on architectures where that symbol's own dependencies
  are not met

When a `select` target has arch-specific dependencies, prefer one of these
approaches:

- Use conditional selection:
  ```
  select SOME_SUBSYSTEM if ARM64
  ```
- Change `select` to `depends on` so the driver is only available when the
  infrastructure exists:
  ```
  depends on SOME_SUBSYSTEM
  ```

## Cross-Module Link Dependencies

A patch may introduce a link-time failure without modifying any Kconfig or
Makefile. An external reference emitted by the caller must resolve to a
definition reachable from that caller. A missing direct `depends on` or
`select` is a clue, not proof of a regression: inherited dependencies,
call-site guards, or header stubs may make the call safe.

This is especially common when:
- Code is moved from a driver-layer file to an arch-level file (or vice versa)
  where different CONFIG_ guards apply
- A function using `EXPORT_SYMBOL_GPL` is called from a new caller whose
  Makefile entry has a different CONFIG_ guard than the exporting file
- A patch adds an `mshv_`/driver-prefixed function into a non-driver arch
  file, creating a cross-layer dependency

**Detection steps** (perform when a patch adds new cross-file function calls):

1. For each new external function call added in the diff, identify:
  - The caller's and callee's source files and their Makefile rules
  - Parent-directory gates, conditional Makefile blocks, and composite
    objects that determine whether each file ends up built-in or in a module

2. Check whether the reference is actually emitted in the configuration:
  - Inspect `#if` branches, `IS_ENABLED()`/`IS_REACHABLE()` guards, and
    header stubs or alternative definitions
  - `IS_ENABLED(CONFIG_Y)` is true for both `y` and `m`; it does not protect
    built-in code from calling a module. `IS_REACHABLE(CONFIG_Y)` is false
    for a built-in caller when `CONFIG_Y=m`

3. Determine valid configurations using the full Kconfig dependencies,
  including inherited and transitive dependencies and conditional selects.
  Do not assume that the absence of a direct dependency permits a combination.

4. Check valid `n`/`m`/`y` combinations for references that remain:
  - A built-in caller requires a built-in definition. `CONFIG_X=y` with
    `CONFIG_Y=m` is not safe merely because both objects are built
  - A module can call a built-in provider or another module, but symbols
    crossing module boundaries need an appropriate `EXPORT_SYMBOL*` and
    must satisfy its license and namespace requirements. The objects do
    not need to be linked into the same module
  - With the provider disabled (`CONFIG_Y=n`), verify that a guard removes
    the reference or a stub/alternative definition supplies it

5. Report a **link-time regression** only after identifying a valid config
  where the patch leaves an unresolved reference. Reproduce the failure
  with a build when possible; otherwise show the exact dependency and
  build-rule path, ruling out guards, stubs, and alternative providers.

Example build rules:

`arch/x86/hyperv/Makefile`:
```make
obj-$(CONFIG_HYPERV_VTL_MODE) += hv_vtl.o
```

`drivers/hv/Makefile`:
```make
ifneq ($(CONFIG_MSHV_ROOT)$(CONFIG_MSHV_VTL),)
   obj-y += mshv_common.o
endif
```

The candidate failing configuration is `CONFIG_HYPERV_VTL_MODE=y`,
`CONFIG_MSHV_ROOT=n`, and `CONFIG_MSHV_VTL=n`. Both driver options must be
disabled (unset in Make): either one enables `mshv_common.o` in the shown
conditional. If this configuration is permitted, and `hv_vtl.c` emits a
reference to `hv_call_set_vp_registers()` defined only in `mshv_common.c`
with no applicable stub, the result is an undefined reference.

**Fixes**: Correct the Kconfig dependency without bypassing the callee's own
dependencies, move the shared implementation to reachable common code, or
provide the appropriate export for a module caller. Use a guard or stub only
when omitting the feature is semantically valid.

## Quick Checks

- **Selected symbol existence**: Verify every `select FOO` references a
  config that actually exists
- **Dependency inheritance**: When selecting a config with `depends on`,
  ensure the selector has compatible dependencies
- **Naming consistency**: Check for typos by comparing with related configs
  in the same subsystem
- **COMPILE_TEST with arch-specific select**: When a driver uses
  `depends on ... || COMPILE_TEST`, verify that all `select` statements
  reference symbols available on all architectures
- **Cross-module link deps**: When a patch adds a call to an external
  function (especially cross-directory), verify that every emitted reference
  has a reachable definition for valid `n`/`m`/`y` combinations, accounting
  for guards, stubs, and module exports
