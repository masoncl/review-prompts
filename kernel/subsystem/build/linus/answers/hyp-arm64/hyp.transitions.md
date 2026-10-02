- There is no struct pkvm_mem_transition, check_share(), check_unshare(),
  check_donation() or __do_share() here; each transition function in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` open-codes its checks, most with
  `__host_check_page_state_range()`, `__hyp_check_page_state_range()` and
  `__guest_check_page_state_range()`.

| Function | Initiator | Before | After |
|---|---|---|---|
| `__pkvm_host_share_ffa()` | host | host `PKVM_PAGE_OWNED` | host `PKVM_PAGE_SHARED_OWNED`; no second side |
| `__pkvm_host_unshare_ffa()` | host | host `PKVM_PAGE_SHARED_OWNED` | host `PKVM_PAGE_OWNED` |
| `__pkvm_host_share_guest()` | host | guest `PKVM_NOPAGE`; each host page `PKVM_PAGE_OWNED`, or `PKVM_PAGE_SHARED_OWNED` with `host_share_guest_count` non-zero and below `U32_MAX` | host `PKVM_PAGE_SHARED_OWNED`, count + 1; guest `PKVM_PAGE_SHARED_BORROWED` |
| `__pkvm_host_unshare_guest()` | host | guest leaf `PKVM_PAGE_SHARED_BORROWED`; host `PKVM_PAGE_SHARED_OWNED`, count non-zero | guest unmapped; count - 1, host `PKVM_PAGE_OWNED` only at 0 |
| `__pkvm_guest_share_host()` | guest | guest `PKVM_PAGE_OWNED`; host `PKVM_NOPAGE` | guest `PKVM_PAGE_SHARED_OWNED`; host `PKVM_PAGE_SHARED_BORROWED` |
| `__pkvm_guest_unshare_host()` | guest | guest `PKVM_PAGE_SHARED_OWNED`; host `PKVM_PAGE_SHARED_BORROWED` | guest `PKVM_PAGE_OWNED`; host `PKVM_NOPAGE`, guest annotation |
| `__pkvm_host_reclaim_page_guest()` | host | guest `PKVM_PAGE_OWNED` (host `PKVM_NOPAGE`) or guest `PKVM_PAGE_SHARED_OWNED` (host `PKVM_PAGE_SHARED_BORROWED`) | guest unmapped; host `PKVM_PAGE_OWNED` |
| `__pkvm_host_force_reclaim_page_guest()` | host | host `PKVM_NOPAGE` with guest annotation; guest `PKVM_PAGE_OWNED` | guest `PKVM_POISON`; host `PKVM_PAGE_OWNED` |

- Host `PKVM_PAGE_SHARED_OWNED` with count 0 (shared with hyp or FF-A):
  `__pkvm_host_share_guest()` returns `-EPERM`.
- Guest-initiated functions: need a valid last-level PTE at the IPA; see
  `get_valid_guest_pte()` for `-ENOENT`, `-E2BIG` and `-EHWPOISON`.
- `__pkvm_guest_share_host()` returning `-ENOENT`: `pkvm_memshare_call()`
  exits to the host as a fake data abort so the page gets faulted in.
- VM kind is enforced by the handlers in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`, not in the transition: share and
  unshare with a guest reject protected VMs,
  `handle___pkvm_host_donate_guest()` rejects non-protected ones.
