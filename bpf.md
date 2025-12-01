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

## Quick Checks
- Helpers marked with BPF_RET_PTR_TO_MAP_VALUE_OR_NULL need NULL checks
- ARG_PTR_TO_MEM arguments need size validation
- Tail calls limited to 33 levels
- Stack usage limited to 512 bytes

## BPF Patterns

Conditionally load these additional patterns
- BPF-001 (map operations with copy_map_value*) → `patterns/BPF-001.md`
- LIBBPF-001 (tools/lib/bpf*) → `patterns/LIBBPF-001.md`
