# Syscall Subsystem Guide

## ABI Compatibility

- Adding additional arguments to a syscall does not break ABI as long as the
existing arguments are not changed

## Syscall Parameter Trust Boundaries

Syscall parameters come from user-controlled registers or stack slots. Parameters that are only meaningful when a specific flag is set may contain arbitrary garbage when that flag is absent — userspace is not required to zero-fill unused arguments. When syscall args are copied into a kernel struct, each field inherits the trust boundary of its source argument and remains garbage outside the flag gate even though it looks initialized in C. When refactoring moves a check across a flag gate, verify that every variable the check uses is valid in the broader scope.

**REPORT as bugs**: Any validation, arithmetic, or comparison that uses a flag-gated syscall parameter outside the scope of its flag gate.

## Checkpoint/Restore Support for New User Interfaces

Introducing a new user interface that creates or modifies persistent kernel state (for a process, thread, file descriptor, memory mapping, socket, or namespace) without providing a way for userspace to query and recreate that state breaks checkpoint/restore tools like CRIU (Checkpoint/Restore In Userspace). Processes using the new feature cannot be checkpointed, or will be restored with missing or inconsistent state.

When a patch adds a new user-space interface or extends an existing one (such as a new syscall, flag, `ioctl()`, `prctl()`, `fcntl()`, `setsockopt()`, file descriptor type via `anon_inode_getfd()` / `anon_inode_getfile()`, VMA attribute via `mmap()` / `madvise()`, or `/proc`, `sysfs`, `cgroup`, or `netlink` knob) that establishes or mutates persistent state:

- **State inspection (Checkpoint)**: Userspace tools like CRIU must be able to read back all required information to save the state. Verify that a corresponding query or dump mechanism exists:
  - **File descriptors** (anon inodes, eventfd, timerfd, signalfd, fanotify, inotify, pidfd, etc.): a `.show_fdinfo` callback in `struct file_operations` (exposed via `/proc/<pid>/fdinfo/<fd>`) or a dedicated `ioctl()` / `fcntl()` getter that exposes flags, offsets, and internal state.
  - **Task / thread state** (`prctl()`, `arch_prctl()`, `ptrace()`, `rseq`, etc.): a corresponding `PR_GET_*` command, `ptrace` regset / request, or `/proc/<pid>/status` / `/proc/<pid>/stat` field.
  - **Sockets** (`setsockopt()`, socket `ioctl()`): a corresponding `getsockopt()` option or `sock_diag` netlink dump (`inet_diag`, `unix_diag`, `netlink_diag`, `packet_diag`) that returns the configured state.
  - **Memory mappings** (`mmap()`, `madvise()`, `prctl()`): visibility in `/proc/<pid>/smaps` (`show_smap` / `vm_flags` mnemonics) or `PROCMAP_QUERY` ioctl.
  - **Namespaces, IPC, and networking**: netlink dump or `/proc` / `sysfs` exposure of configuration and object identifiers.
- **State reconstruction (Restore)**: Userspace must be able to recreate the saved state on restore using available user interfaces.
- **Stateless operations and exceptions**: One-shot operations that do not create or modify persistent state (or interfaces that only query existing state) do not need additional checkpoint/restore support. There can also be exceptions for interfaces that change system-level configuration or depend on hardware or external resources, where checkpoint/restore support should be considered but is not strictly required.
- **Patch series**: In a multi-patch series, the inspection/restore support may be added in a subsequent patch; check forward in the series before flagging.

**REPORT as a tension (Open Question):**
- Any new user interface (syscall, ioctl, prctl, fcntl, setsockopt, anon_inode file descriptor, VMA attribute, namespace feature, etc.) that introduces or modifies persistent kernel state without providing a way for userspace tools like CRIU to retrieve all required information to restore that state later (unless an exception like system-level or hardware-dependent configuration applies, or it is provided in a later patch in the same series).
