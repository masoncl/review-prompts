| File | Range | Reason the comment gives |
|---|---|---|
| `scripts/syscall.tbl` | 244–259 | architectures may provide up to 16 calls of their own |
| `scripts/syscall.tbl` | 295–402 | "unassigned to sync up with generic numbers" |
| `arch/x86/entry/syscalls/syscall_64.tbl` | 387–423 | none given |
| `arch/x86/entry/syscalls/syscall_64.tbl` | 512–547 | "historical design error": x32 numbering differs from native |

- 337–386 in `arch/x86/entry/syscalls/syscall_64.tbl`: no line and no comment;
  the 387–423 comment does not cover them.
- 548 and above in `arch/x86/entry/syscalls/syscall_64.tbl`: the comment after
  547 says they "are not to be used for x32-specific syscalls"; the comment
  before 512 says they are available for non-x32 use.
