# Subsystem Guide Index

Load subsystem guides from the prompt directory based on what the code touches.
Each guide contains subsystem-specific invariants, API contracts, and common
bug patterns. Each subsystem guide may reference additional pattern files to
load conditionally.

The triggers column below includes both path names, function calls, and symbols
regexes

## Subsystem Guides

| Subsystem | Triggers | File |
|-----------|----------|------|
| Networking | net/, drivers/net/, skb_, sockets | networking.md |
| Memory Management | mm/, page/folio ops, alloc/free, slab, vmalloc, `__GFP_*`, `page_*`, `folio_*`, `kmalloc`, `kmem_cache_*`, `vmalloc`, `alloc_pages` | mm.md |
| VFS | inode, dentry, vfs_, fs/*.c | vfs.md |
| Locking | spin_lock*, mutex_*, rwsem*, seqlock*, *seqcount* | locking.md |
| Scheduler | kernel/sched/, sched_, schedule, *wakeup* | scheduler.md |
| BPF | kernel/bpf/, bpf, verifier | bpf.md |
| RCU | rcu*, call_rcu, synchronize_rcu, kfree_rcu | rcu.md |
| Encryption | crypto, fscrypt_ | fscrypt.md |
| Tracing | trace_, tracepoints | tracing.md |
| Workqueue | kernel/workqueue.c, work_struct | workqueue.md |
| Syscalls | syscall definitions | syscall.md |
| btrfs | fs/btrfs/ | btrfs.md |
| DAX | dax operations | dax.md |
| Block/NVMe | block layer, nvme | block.md |
| NFSD | fs/nfsd/*, fs/lockd/* | nfsd.md |
| SunRPC | net/sunrpc/* | sunrpc.md |
| io_uring | io_uring/, io_uring_, io_ring_, io_sq_, io_cq_, io_wq_, IORING_ | io_uring.md |
| Cleanup API | `__free`, `guard(`, `scoped_guard`, `DEFINE_FREE`, `DEFINE_GUARD`, `no_free_ptr`, `return_ptr` | cleanup.md |
| RCU lifecycle | `call_rcu(`, `kfree_rcu(`, `synchronize_rcu(`, `rhashtable_*` + `call_rcu`, `hlist_del_rcu` + `call_rcu`, `list_del_rcu` + `call_rcu` | rcu.md |

## Optional Patterns

Load only when explicitly requested in the prompt:

- **Subjective Review** (subjective-review.md): Subjective general assessment
