# BPF Subsystem Delta

## Verifier Invariants
- All memory accesses must be bounds-checked by verifier
- Register types tracked through program flow
- Stack slots must be initialized before use
- Helper functions have specific argument requirements

## BPF Map Operations
- Map lookups can return NULL
- Map updates need to check max_entries
- Spin locks in maps require bpf_spin_lock/unlock
- Per-CPU maps need bpf_get_cpu_ptr/put_cpu_ptr

## Reference Tracking
- Some helpers return "acquired" references
- Must release with corresponding release helper
- Verifier tracks reference state per register

## Context Access
- Context pointer is read-only
- Field access must be within ctx structure size
- Some fields require specific program types

## BPF Kernel Functions (kfuncs)
- __bpf_kfunc, BTF_KFUNCS*, KF_* flags, etc
- read `Documentation/bpf/kfuncs.rst` to better understand these

### Kfunc Argument Validation by the Verifier

The BPF verifier performs extensive validation of kfunc arguments at program load time.
Understanding what the verifier guarantees is critical to avoid false positive bug reports.

#### Scalar and Enum Arguments

When a kfunc takes a scalar argument (int, u32, enum, etc.), the verifier:

1. **Tracks the register type**: Ensures the register is `SCALAR_VALUE` (not a pointer)
2. **Tracks value ranges**: Maintains min/max bounds for scalar values
3. **Tracks constant values**: When values are compile-time constants, the verifier knows the exact value via `tnum_is_const(reg->var_off)`

**Important**: Enum types in BTF are treated as scalars (`btf_type_is_scalar()` returns true for both integers and enums). See `include/linux/btf.h`:

```c
static inline bool btf_type_is_scalar(const struct btf_type *t)
{
    return btf_type_is_int(t) || btf_type_is_enum(t);
}
```

#### Why Enum Bounds Checks Are Often Unnecessary in Kfuncs

When a BPF program uses enum constants (e.g., `MEMCG_OOM`, `PGFAULT`, `NR_ANON_MAPPED`):

1. **Source of enum values**: BPF programs include `vmlinux.h`, which is generated from the kernel's BTF. This file contains the authoritative enum definitions directly from the running kernel.

2. **Compile-time substitution**: The C compiler substitutes enum constants with their integer values at compile time. The BPF program literally cannot reference an enum value that doesn't exist in the kernel.

3. **Verifier sees constants**: When a BPF program passes `MEMCG_OOM` to a kfunc, the verifier sees a constant scalar value (the actual integer). The verifier tracks this as a known constant via `tnum_is_const()`.

4. **No runtime user input**: Unlike syscall parameters, kfunc enum arguments come from the compiled BPF program, not from runtime user input. There's no attack vector for passing arbitrary values.

**Example - this bounds check is UNNECESSARY**:
```c
// The BPF program can only pass valid enum values from vmlinux.h
__bpf_kfunc unsigned long bpf_mem_cgroup_memory_events(struct mem_cgroup *memcg,
                        enum memcg_memory_event event)
{
    // This check is defensive but not strictly necessary:
    // if (event >= MEMCG_NR_MEMORY_EVENTS)
    //     return (unsigned long)-1;

    // BPF programs using enum constants from vmlinux.h cannot pass invalid values
    return atomic_long_read(&memcg->memory_events[event]);
}
```

#### When Bounds Checks ARE Necessary

Bounds checking IS required when:

1. **Plain integer parameters**: If the kfunc takes `int idx` instead of `enum foo idx`, the type system doesn't constrain the value. Example:
   ```c
   // idx is int, not an enum - bounds check needed
   __bpf_kfunc unsigned long bpf_mem_cgroup_page_state(struct mem_cgroup *memcg, int idx)
   {
       if (idx < 0 || idx >= MEMCG_NR_STAT)  // Necessary!
           return (unsigned long)-1;
       return memcg_page_state_output(memcg, idx);
   }
   ```

2. **Values derived from BPF map lookups**: If the enum/index value comes from a map (user-controlled data), validation is required.

3. **Values computed at runtime**: If the BPF program computes the index value rather than using a constant, the verifier may not know the exact value.

#### Summary: Kfunc Enum Argument Safety

| Scenario | Bounds Check Needed? | Reason |
|----------|---------------------|--------|
| Enum type parameter with constant | No | Compiler substitutes valid value from vmlinux.h |
| Enum type parameter from map/computation | Yes | Value not known at compile time |
| Plain int/u32 parameter | Yes | No type constraint on values |
| Pointer parameters | N/A | Verifier validates pointer types separately |

**DO NOT report as bugs**: Kfuncs that take enum-typed parameters and use constants from vmlinux.h without explicit bounds checks. The verifier and compiler together guarantee these values are valid.

## Quick Checks
- Helpers marked with BPF_RET_PTR_TO_MAP_VALUE_OR_NULL need NULL checks
- ARG_PTR_TO_MEM arguments need size validation
- Tail calls limited to 33 levels
- Stack usage limited to 512 bytes

## BPF Skeleton API (Selftests)

### Generated Skeleton Functions
BPF skeletons are generated by `bpftool gen skeleton` and provide type-safe wrappers.
Each skeleton includes these functions (where `example` is the object name):

- `example__open()` - Opens BPF object (does not load programs)
- `example__load()` - Creates maps, loads and verifies all BPF programs
- `example__open_and_load()` - Combines open + load in one operation
- `example__destroy()` - Detaches, unloads programs, frees resources

### Skeleton Guarantees After Successful `__open_and_load()`

**IMPORTANT**: After successful `skel = example__open_and_load()`:
- The skeleton pointer is valid (not NULL/ERR_PTR)
- **ALL programs are loaded with valid FDs** (>= 0)
- **ALL maps are created with valid FDs** (>= 0)
- Skeleton fields like `skel->progs.prog_name` and `skel->maps.map_name` are guaranteed valid

This means:
- `bpf_program__fd(skel->progs.prog_name)` **CANNOT return negative** after successful load
- `bpf_map__fd(skel->maps.map_name)` **CANNOT return negative** after successful load
- **NO additional FD validation needed** when using skeleton-generated fields

### When FD Checks ARE Required

FD checks with `CHECK_FAIL(fd < 0)` or similar are needed when using:
- Manual lookup APIs: `bpf_object__find_program_by_name()` - can return NULL if name not found
- Manual lookup APIs: `bpf_object__find_map_by_name()` - can return NULL if name not found
- Old-style loading: `bpf_prog_test_load()` - different API contract

### Skeleton vs Manual Lookup Pattern

```c
// Skeleton pattern - NO FD checks needed after successful __open_and_load()
skel = example__open_and_load();
if (!ASSERT_OK_PTR(skel, "open_and_load"))
    return;
prog_fd = bpf_program__fd(skel->progs.my_prog);  // Cannot fail here
map_fd = bpf_map__fd(skel->maps.my_map);          // Cannot fail here

// Manual lookup pattern - FD checks REQUIRED (using modern ASSERT_* macros)
obj = bpf_object__open_file("example.o", NULL);
prog = bpf_object__find_program_by_name(obj, "my_prog");  // Can return NULL
if (!ASSERT_OK_PTR(prog, "find_program"))
    goto cleanup;
prog_fd = bpf_program__fd(prog);  // Can return negative if prog is invalid
if (!ASSERT_GE(prog_fd, 0, "bpf_program__fd"))
    goto cleanup;
```

## BPF Selftest Assertion Macros

### Modern ASSERT_*() Macros (Preferred)

**Use ASSERT_*() macros for all new tests and when updating existing tests.**

The modern ASSERT family includes type-specific macros like `ASSERT_OK()`, `ASSERT_ERR()`,
`ASSERT_EQ()`, `ASSERT_OK_PTR()`, `ASSERT_OK_FD()`, and many others. See
`tools/testing/selftests/bpf/test_progs.h` for the complete list.

### Deprecated CHECK() Macros (Avoid in New Code)

**DO NOT use in new tests or patches:**

- `CHECK(condition, tag, format...)` - **DEPRECATED** - Use `ASSERT_*()` instead
- `CHECK_FAIL(condition)` - **DEPRECATED** - Use `ASSERT_*()` instead
- `CHECK_ATTR(condition, tag, format...)` - **DEPRECATED** - Use `ASSERT_*()` instead

**Why ASSERT_*() is preferred:**
1. Uses static duration variable instead of requiring global `duration` variable
2. More specific and type-safe macros for different check types
3. Better error messages with actual vs expected values
4. Modern BPF selftest standard since 2020

**Migration example:**
```c
// OLD (deprecated):
static int duration = 0;  // Global/static variable required
if (CHECK(fd < 0, "open_fd", "failed to open: %d\n", errno))
    return;

// NEW (preferred):
if (!ASSERT_OK_FD(fd, "open_fd"))  // No duration variable needed
    return;
```

## BPF Patterns

Conditionally load these additional patterns
- BPF-001 (map operations with copy_map_value*) → `patterns/BPF-001.md`
- LIBBPF-001 (tools/lib/bpf*) → `patterns/LIBBPF-001.md`
