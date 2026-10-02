- `Documentation/filesystems/nfs/nfsd-maintainer-entry-profile.rst`: exists, and
  is the `P:` entry of "KERNEL NFSD, SUNRPC, AND LOCKD SERVERS" in
  `MAINTAINERS`.
- Profile wording is mostly preference, not prohibition; the only "must"
  statements in its sections on administrative interfaces, field
  observability and coding style are the BUG and printk bullets under "Field
  observability".
- Administrative interfaces:
  - Interfaces counted: NFSD or SUNRPC module parameters, export options in
    /etc/exports, files under /proc/fs/nfsd/ or /proc/sys/sunrpc/, the NFSD
    netlink protocol.
  - New or modified setting: "a last resort"; the profile does not forbid new
    /proc files, sysctls or module parameters outright.
  - Two destinations offered for a setting that is needed: the NFSD netlink
    protocol first, or /sys/kernel/debug/nfsd/ if it need not be a reliable
    long-term user-space feature.
  - debugfs settings: see `nfsd_debugfs_init()` in `fs/nfsd/debugfs.c`; the
    setters write globals such as `nfsd_disable_splice_read`, so they apply
    to every net namespace.
  - Without `CONFIG_DEBUG_FS`: `nfsd_debugfs_init()` is an empty stub in
    `fs/nfsd/nfsd.h`, so a debugfs setting does not exist.
  - Namespace awareness: not a requirement stated in the profile.
  - User-space support, man pages, backward compatibility: no requirement
    stated in the profile's administrative-interface section.
  - User space: kernel and user-space changes are posted as separate series
    (section "Patch submission").
- Observability:
  - `dprintk()`: not deprecated by the profile, and new call sites are not
    banned; it is called inappropriate for frequent operations like I/O.
  - Static trace points: "favored for use in hot paths"; not mandated for all
    new diagnostics.
  - General rule: "Contributors should select the most appropriate tool"
    among counters, printks, WARNings and static trace points.
  - BUG: "must be avoided if at all possible".
  - WARN: appropriate only when a full stack trace is useful.
  - printk: must not be used on paths a remote user can trigger repeatedly;
    the profile does not name rate limiting as an accepted alternative.
  - Counters: described as always on and low in per-event detail; the profile
    names no file for them.
  - Dynamic tracing (kprobes, eBPF): listed as a mechanism, noted as unusable
    under full kernel lockdown.
  - Tracepoint ABI stability: the profile says nothing.
- Coding style:
  - Exceptions to `Documentation/process/coding-style.rst`: exactly five, the
    local-variable, kdoc and three naming rules below; the "Coding style"
    section has no rule on line length, `scripts/checkpatch.pl`, `%pe`, XDR
    or xdrgen.
  - Local variables: new ones are added in reverse Christmas tree order; the
    definition the profile links to is the `rcs` label in
    `Documentation/process/maintainer-netdev.rst`.
  - Kdoc comments: to be used on non-static functions, static inline
    functions, and static functions that are callbacks or virtual functions.
  - Naming, version-independent: new function names start with `nfsd_`.
  - Naming, per version: `nfsdN_` for NFSv2, NFSv3, or code used by all NFSv4
    minor versions.
  - Naming, per NFSv4 minor version: `nfsd4M_` may be used, for example
    `nfsd41_cb_get_slot()` in `fs/nfsd/nfs4callback.c`.
  - Stand-alone clean-up patches (section "Clean-up patches"): discouraged
    when "not in the context of other work"; the examples given are
    `checkpatch.pl` warnings after merge, local variable ordering, and
    long-standing whitespace damage.
  - Variable order rule: applies to new local variables; a patch that only
    reorders existing declarations is one of the discouraged clean-ups.
  - Spelling and grammar fixes: encouraged.
