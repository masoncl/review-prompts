| State | Lock | Easy to miss |
|---|---|---|
| FF-A `host_buffers`, `hyp_buffers`, `ffa_desc_buf` | `host_buffers.lock` in `arch/arm64/kvm/hyp/nvhe/ffa.c` | `hyp_buffers.lock` is initialised and never taken |
| FF-A `hyp_ffa_version`, `has_version_negotiated` (writes) | `version_lock` in `arch/arm64/kvm/hyp/nvhe/ffa.c` | taken only in `do_ffa_version()` |
| Block fixmap slot `hyp_fixblock_slot` | `hyp_fixblock_lock` in `arch/arm64/kvm/hyp/nvhe/mm.c` | exists only `#if PAGE_SHIFT < 16` |
| Trace buffer load, unload, enable, reset, reader swap | `trace_buffer.lock` in `arch/arm64/kvm/hyp/nvhe/trace.c` | built only with `CONFIG_NVHE_EL2_TRACING`, which sits inside `if NVHE_EL2_DEBUG` |

- FF-A buffers and FF-A version: two locks, not one.
- `hyp_ffa_version` reads in the memory handlers: under `host_buffers.lock`
  or no lock, never `version_lock`.
- `hyp_ffa_version` stability: `do_ffa_version()` stops writing it once
  `has_version_negotiated` is set, and `kvm_host_ffa_handler()` rejects every
  other call until then.
- `hyp_fixblock_lock`: taken in `hyp_fixblock_map()` and still held on
  return; `hyp_fixblock_unmap()` releases it.
- `PAGE_SHIFT >= 16`: `hyp_fixblock_map()` falls back to the per-CPU
  `hyp_fixmap_map()` and takes no lock.
- Trace event writes: `tracing_reserve_entry()` and `tracing_commit_entry()`
  take no lock; they use the per-CPU `status` word in
  `kernel/trace/simple_ring_buffer.c`.
- `__hyp_check_page_state_range()`: has no `hyp_assert_lock_held()`;
  `__host_check_page_state_range()` and `__guest_check_page_state_range()`
  assert their lock.
- **Potentially unsafe usage**: writing hyp page state with `set_hyp_state()`
  without holding `host_mmu.lock`.
  - Unsafe: while another CPU can write host state under `host_mmu.lock`;
    `__host_state` and `__hyp_state_comp` are adjacent bit-fields in
    `struct hyp_page`, so one write can undo the other.
  - Safe: holding `host_mmu.lock` and `pkvm_pgd_lock` together, as every
    caller of `__hyp_set_page_state_range()` does, for example
    `__pkvm_host_donate_hyp()`.
  - Safe: with no lock inside the `__pkvm_init` hypercall, as
    `fix_host_ownership_walker()` does; `kvm_arm_init()` runs
    `init_hyp_mode()` before `init_subsystems()` gives the other CPUs EL2
    through `cpu_hyp_init()`.
- `pkvm_pgd_lock`: also covers the private-VA cursor `__io_map_next`, not
  `__io_map_base`; `__pkvm_alloc_private_va_range()` asserts it.
- `refcount` in `struct hyp_page`: under the pool lock only through
  `hyp_alloc_pages()`, `hyp_get_page()` and `hyp_put_page()`.
- `vm_table_lock`: also covers writes of `is_dying`, `loaded_hyp_vcpu` in
  `struct pkvm_hyp_vcpu`, and vCPU registration in `__pkvm_init_vcpu()`.
- `vm_table_lock` asserts: for example `get_vm_by_handle()`; one is outside
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`, in `kvm_init_pvm_id_regs()`
  (`arch/arm64/kvm/hyp/nvhe/sys_regs.c`).
