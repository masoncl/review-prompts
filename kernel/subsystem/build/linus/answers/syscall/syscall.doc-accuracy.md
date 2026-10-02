| Subject in the document | Document | Tree |
|---|---|---|
| x86 numbers | examples differ (333 and 380) | same number in both tables (472 for `fchroot`) |
| x86 compat column | name with the `__ia32_compat_sys_` prefix | plain `compat_sys_` name |
| x32 line | for a pointer-to-pointer argument, the `syscall_64.tbl` entry split into a `333 64` row plus a `555 x32` row naming an __x32_compat_sys_ function | no such prefix; no `x32` line above 547 |
| Returning elsewhere | stub_ and stub32_ entry points in assembly | none under `arch/x86/entry/` |
| um mapping | a stub_ define in `arch/x86/um/sys_call_table_64.c` | file has no stub_ define |

- New x32-specific line: ruled out by the comments in
  `arch/x86/entry/syscalls/syscall_64.tbl`; 512–547 is closed and 548 and above
  "are not to be used for x32-specific syscalls". A new call gets one `common`
  line.
- `execve`, `clone`, `rt_sigreturn`: the tables name `sys_execve`, `sys_clone`
  and `sys_rt_sigreturn` directly.
- `noreturn`: an optional sixth column that the document does not describe,
  used by `exit` and `exit_group`, with `-` as the placeholder in the compat
  column.
