# Questions: FUSE (measurement set)

- guide: fuse.md
- title: FUSE Subsystem

A wide set of questions about FUSE: the connection, the channel and the device,
mounting and the INIT exchange, the life of a request, the device and io-uring
transports, inodes and dentries, file I/O, virtio-fs, DAX and CUSE. The set is
used to measure what a model already knows, before anyone decides which
questions the built guide needs. The hand-written guide that the built guide
will replace covers two points about the io-uring transport and nothing else.
In these questions "the server" is the userspace program that answers requests.
Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## fuse.core-files: Source files

- section: Finding your way
- relevance: 4 - a review has to open the right file first

Which files under `fs/fuse/` hold the transport between the kernel and the
server, and which hold the filesystem operations? Which files are built only
under a config option? Start from `fs/fuse/Makefile` and `fs/fuse/Kconfig`.

## fuse.headers: Private headers

- section: Finding your way
- relevance: 4 - the header that declares a structure decides which code may use it

Which header in `fs/fuse/` declares the connection, and which declares the
channel and the device? Which of these headers does code outside the transport
include? Start from `fs/fuse/fuse_i.h`, `fs/fuse/fuse_dev_i.h`, `fs/fuse/dev.h`
and `fs/fuse/args.h`.

## fuse.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

Where do you start reading for each of these jobs: mounting, sending a request
and waiting for the reply, reading a request from the device, writing a reply
to the device, and aborting a connection?

## fuse.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 2 - says what a patch can be tested with

What documentation and tests for FUSE are in the kernel tree, and what does
each cover? Where does the rest of the testing live? Start from
`Documentation/filesystems/fuse/index.rst` and
`tools/testing/selftests/filesystems/fuse/Makefile`.

## fuse.uapi-header: Protocol header

- section: Finding your way
- relevance: 3 - a protocol change that breaks a server cannot be taken back

Which file defines the protocol between the kernel and the server, and how is
a change to the protocol recorded in that file? What are the requirements for
changing a structure in that file in order to assure safe usage by servers that
already exist? Start from `include/uapi/linux/fuse.h` and
`FUSE_KERNEL_MINOR_VERSION`.

# Connections

## fuse.main-objects: Main objects

- section: Connection, channel and mount
- relevance: 5 - every other answer is phrased in these objects

What are the main objects of a FUSE mount, from the superblock down to one
request, and which object points to which? Start from `struct fuse_conn`,
`struct fuse_chan`, `struct fuse_mount` and `struct fuse_dev`.

## fuse.conn-chan-split: Connection and channel state

- section: Connection, channel and mount
- relevance: 5 - the state of one mount is split between two structures

Which state belongs to the connection and which to the channel: the queues, the
background counters, the negotiated limits and the flag that says the server is
still connected? Which lock protects each piece of that state? Start from
`struct fuse_chan` in `fs/fuse/fuse_dev_i.h` and `struct fuse_conn` in
`fs/fuse/fuse_i.h`.

## fuse.conn-refcount: Connection reference count

- section: Connection, channel and mount
- relevance: 4 - a missing reference is a use after free at unmount

Who holds a reference to a connection, and what does the last
`fuse_conn_put()` do? In what order are the connection, the channel and the
ring freed? Start from `fuse_conn_put()` and `fuse_mount_destroy()`.

## fuse.conn-feature-bits: Connection feature bits

- section: Connection, channel and mount
- relevance: 3 - the bits are written by many tasks with no lock

How does the kernel remember that the server lacks an operation, and what are
the requirements for writing the one-bit fields of `struct fuse_conn` in order
to assure safe usage while other tasks use the connection? Start from
`conn_error`, `no_open` and `fuse_file_open()`.

## fuse.mounts-of-connection: Mounts sharing a connection

- section: Connection, channel and mount
- relevance: 4 - code that has only a node id must find the right superblock

When do several superblocks share one connection, and which lock must code
hold to use the superblock of a `struct fuse_mount`? How does code find an
inode from a node id alone? Start from `fuse_ilookup()` and `killsb`.

## fuse.submounts: Automatic submounts

- section: Connection, channel and mount
- relevance: 3 - two inodes stand for one node of the server

How does a directory become the root of a submount? How is the lookup count of
the node of that directory shared between the two superblocks, and when is the
FORGET for that node sent? Start from `fuse_dentry_automount()`,
`fuse_fill_super_submount()` and `struct fuse_submount_lookup`.

## fuse.device-lifetime: Device object life cycle

- section: Connection, channel and mount
- relevance: 5 - the pointer is read without a lock on every device operation

Through which states does the channel pointer of a `struct fuse_dev` go between
opening the device file and closing it, and what are the requirements for
reading that pointer in order to assure safe usage? Start from
`fuse_dev_open()`, `fuse_dev_install()`, `fuse_get_dev()` and
`fuse_dev_release()`.

## fuse.device-clone: Cloned devices

- section: Connection, channel and mount
- relevance: 3 - each device has state of its own

What does cloning a device give the server? Which queues does a cloned device
share with the original device, and which does the cloned device own? What
happens to the connection when one of several devices is closed? Start from
`fuse_dev_ioctl_clone()`.

## fuse.control-fs: Control filesystem

- section: Connection, channel and mount
- relevance: 3 - a control file can be open when its connection goes away

What does the control filesystem show for each connection? How does a control
file reach its connection safely after an unmount? What does `fuse_mutex`
protect? Start from `fs/fuse/control.c` and `fuse_conn_list`.

# Mounting

## fuse.mount-setup: Mount setup

- section: Mount and INIT
- relevance: 4 - the error paths free objects that other objects point to

In what order does a mount create the connection, the channel, the superblock
and the root inode, and at which point is the device attached to the channel?
What is undone when a step fails? Start from `fuse_get_tree()` and
`fuse_fill_super_common()`.

## fuse.init-reply: INIT reply processing

- section: Mount and INIT
- relevance: 5 - every negotiated feature is decided here

What does the kernel do with the INIT reply? In which task does that code run
when INIT is sent in the background and when it is sent synchronously? What
happens to the connection when the reply is refused? Start from
`process_init_reply()`, `fuse_send_init()` and `FUSE_DEV_IOC_SYNC_INIT`.

## fuse.init-new-flag: Adding an INIT flag

- section: Mount and INIT
- relevance: 4 - most new features start with a new flag

What are the requirements for adding a new feature flag to the INIT exchange in
order to assure safe usage with a server that does not know the flag? Start
from `fuse_new_init()`, `FUSE_INIT_EXT` and `flags2`.

## fuse.size-limits: Request size limits

- section: Mount and INIT
- relevance: 4 - buffers are sized from these numbers

Which limits bound the size of one request, and where is each limit negotiated
or clamped? Which limit applies to a file name? Start from `max_pages`,
`max_write`, `max_read`, `name_max` and `fuse_max_pages_limit`.

## fuse.unmount-order: Unmount order

- section: Mount and INIT
- relevance: 5 - the wrong order frees a structure that a request still uses

In what order does unmount send DESTROY, abort the channel, wait for requests
and drop the connection, and what is different for a forced unmount? Start from
`fuse_kill_sb_anon()`, `fuse_conn_destroy()` and `fuse_umount_begin()`.

## fuse.access-by-other-users: Access by other users

- section: Mount and INIT
- relevance: 4 - a new operation that skips the check is a security bug

Which tasks may call into a FUSE filesystem, and which test decides it? What
are the requirements for a new inode or file operation in order to keep that
test in force? Start from `fuse_allow_current_process()`.

## fuse.user-namespaces: Namespaces and credentials

- section: Mount and INIT
- relevance: 4 - the server must see ids it can understand

Which user namespace and PID namespace does a connection record, and how are
the uid, gid and pid of a request translated for the server? What changes when
the mount is idmapped? Start from `fuse_fill_creds()`, `FUSE_ALLOW_IDMAP` and
`fuse_simple_idmap_request()`.

# Requests

## fuse.request-arguments: Request arguments

- section: Sending a request
- relevance: 5 - every operation builds one of these

What must a caller fill in `struct fuse_args` before sending? How long must the
structure and its buffers stay valid for a synchronous request and for a
background request, and who frees them? Start from `FUSE_ARGS` and
`struct fuse_args_pages`.

## fuse.send-variants: Send functions

- section: Sending a request
- relevance: 5 - the return value differs between the functions

Which function sends a request and waits, and which sends a request in the
background? Which function answers a notification? What does each of these
functions return on success and on failure? Start from `fuse_simple_request()`,
`fuse_simple_background()` and `fuse_simple_notify_reply()`.

## fuse.argument-flags: Flags on request arguments

- section: Sending a request
- relevance: 4 - the flags decide whether a request can fail or be interrupted

What do the flags `force`, `nocreds`, `noreply` and `abort_on_kill` of
`struct fuse_args` change about how a request is allocated, sent and waited
for, and which combinations does the code warn about? Start from
`fuse_chan_send()` and `fuse_req_prep()`.

## fuse.request-allocation-blocking: Blocking in request allocation

- section: Sending a request
- relevance: 4 - a caller that holds a lock here can deadlock with the server

Under which conditions does allocating a request sleep, and what wakes the
sleeper? Which signals end the sleep? Start from `fuse_get_req()` and
`fuse_block_alloc()`.

## fuse.background-accounting: Background request accounting

- section: Sending a request
- relevance: 4 - a counter that is not dropped blocks every later request

Which counters limit background requests, and which lock protects those
counters? What happens to a background request that arrives when the limit is
reached? Start from `fuse_request_queue_background()`, `flush_bg_queue()` and
`congestion_threshold`.

## fuse.end-callback: Completion callback

- section: Sending a request
- relevance: 5 - the callback runs in a context its author did not choose

What are the requirements for the `end` callback of a request in order to
assure safe usage? In which contexts can the callback run, and may the callback
sleep? Is the callback called when the send function returns an error? Start
from `fuse_request_end()` and `may_block`.

## fuse.reply-size-check: Reply size checks

- section: Sending a request
- relevance: 4 - the server chooses the length of every reply

How does the kernel check the length of a reply against the length that the
request specifies, and which requests accept a shorter reply? How does the
caller learn the real length? Start from `fuse_copy_out_args()` and
`out_argvar`.

## fuse.request-flag-bits: Request flag bits

- section: Request state
- relevance: 4 - the bits are the state machine of a request

What does each request flag bit record? Which bits are changed only under a
lock, and which lock is that? Start from `enum fuse_req_flag`.

## fuse.request-lists: Lists a request is on

- section: Request state
- relevance: 5 - a request on two lists, or on none, is the usual bug

Which lists does a request move through on the device path between being
queued and being ended, and which lock protects each list? Start from
`fuse_dev_queue_req()`, `fuse_dev_do_read()` and `fuse_dev_do_write()`.

## fuse.request-end-contract: Ending a request

- section: Request state
- relevance: 5 - every transport and every error path calls it

What are the requirements for calling `fuse_request_end()` in order to assure
safe usage? Which flag bits must be clear, and which list may the request be
on? Which reference does the call consume? Start from `fuse_request_end()` and
`fuse_put_request()`.

## fuse.waiting-for-reply: Waiting for a reply

- section: Request state
- relevance: 4 - decides when a killed task can leave a request behind

How does a task wait for the reply to a synchronous request? Which signals end
each stage of the wait, and in which cases does the task return before the
server has replied? Start from `request_wait_answer()`.

## fuse.interrupts: Interrupt requests

- section: Request state
- relevance: 4 - the ordering has no lock and rests on barriers

How is an INTERRUPT request queued, and how does it name the request it
interrupts? What orders the test of the sent bit against the test of the
interrupted bit between the waiting task and the task that reads the device?
Start from `queue_interrupt()` and `fuse_dev_queue_interrupt()`.

## fuse.unique-ids: Request identifiers

- section: Request state
- relevance: 3 - the server matches replies by this number

How is the identifier of a request chosen, and which bits of the identifier
carry a meaning of their own? What does a resend notification do to the
identifier of a request the server already read? Start from
`fuse_get_unique()`, `FUSE_INT_REQ_BIT` and `fuse_chan_resend()`.

## fuse.forget: FORGET and lookup counts

- section: Request state
- relevance: 5 - a lost count leaks an inode in the server for ever

What are the requirements for code that receives a node id in a reply in order
to keep the lookup count of the server correct? When is the count raised, and
when must a FORGET be queued? When is the memory for a FORGET allocated? Start
from `fuse_iget()`, `fuse_chan_queue_forget()` and `fuse_alloc_forget()`.

## fuse.request-timeout: Request timeouts

- section: Request state
- relevance: 3 - a new list of requests has to be added to the check

Does this tree abort a connection whose server does not reply in time? How is
the time limit chosen, and which lists does the check look at? If the tree has
no such timeout, say so. Start from `fuse_init_server_timeout()` and
`fuse_check_timeout()`.

## fuse.abort: Aborting a connection

- section: Request state
- relevance: 5 - abort races with every other path that touches a request

What does aborting a channel do, in order, to requests that are pending, being
copied, sent and in the background? Which error does each waiter see, and who
calls the abort? Start from `fuse_chan_abort()` and
`fuse_chan_wait_aborted()`.

# The device

## fuse.device-read: Reading a request

- section: Device read and write
- relevance: 4 - the server sees exactly what this path copies

What does one read of the device return, and in which order does the read
choose among interrupts, forgets and requests? What happens to a request that
does not fit the buffer? Start from `fuse_dev_do_read()`.

## fuse.device-write: Writing a reply

- section: Device read and write
- relevance: 4 - everything in the write comes from the server

How does a write to the device find its request, and what does a write with a
zero identifier mean? Which error values in a reply header does the kernel
accept? Start from `fuse_dev_do_write()` and `fuse_request_find()`.

## fuse.copy-and-abort: Copying and abort

- section: Device read and write
- relevance: 4 - the copy can fault and sleep while an abort runs

What are the requirements for copying request data to or from the buffer of the
server in order to assure safe usage against an abort that runs at the same
time? Start from `lock_request()`, `unlock_request()` and
`struct fuse_copy_state`.

## fuse.splice-and-folio-move: Splice and moved folios

- section: Device read and write
- relevance: 3 - a folio from the server ends up in the page cache

When does a reply written through splice avoid a copy, and what are the
requirements for the folios involved in order to assure safe usage? Start from
`fuse_dev_splice_write()`, `fuse_try_move_folio()` and `page_replace`.

## fuse.transport-callbacks: Transport callbacks

- section: Device read and write
- relevance: 4 - each transport repeats steps the device path does for it

Which transports implement `struct fuse_iqueue_ops`? What are the requirements
for a `send_req` callback in order to assure safe usage? What must the callback
do with the identifier, the pending bit and a request it cannot send? Start
from `fuse_dev_fiq_ops` and `virtio_fs_fiq_ops`.

## fuse.notifications: Notifications from the server

- section: Device read and write
- relevance: 4 - a notification names objects that may be gone

Which notifications can the server send, and in which states of the connection
are they accepted? Which lock does a notification hold while it uses an inode?
Start from `fuse_notify()` and `enum fuse_notify_code`.

# The io-uring transport

## fuse.uring-enabling: Enabling io-uring

- section: Rings
- relevance: 4 - requests can be made before the ring is usable

What has to be true for a connection to use io-uring, and at which point do
requests start to go through the ring? What happens to a request made before
that point? Start from `fuse_uring_enabled()`, `fuse_uring_conn_init()` and
`fuse_uring_ready()`.

## fuse.uring-commands: Ring commands

- section: Rings
- relevance: 4 - the return value tells io_uring who completes the command

Which commands does the io-uring handler of the device accept, and what does
the handler return to io_uring for each command? Which kinds of message still
go through reads and writes of the device when the ring is in use? Start from
`fuse_uring_cmd()`, `enum fuse_uring_cmd` and `fuse_io_uring_ops`.

## fuse.uring-pointer-publication: Publishing ring pointers

- section: Rings
- relevance: 4 - readers take no lock

How are the pointer to the ring, the pointers to its queues and the ready flag
made visible to readers that take no lock, and what are the requirements for
such a reader in order to assure safe usage? Start from `fuse_uring_create()`,
`fuse_uring_create_queue()` and `fuse_uring_do_register()`.

## fuse.uring-sqe-access: Reading the submission entry

- section: Rings
- relevance: 4 - the entry is memory that the server can write

What are the requirements for reading fields of the submission queue entry in
the command handler in order to assure safe usage? Until when does the entry
stay valid, and which code in `io_uring/` decides that? Start from
`fuse_uring_cmd()` and `io_uring_sqe128_cmd`.

## fuse.uring-entry-states: Ring entry states

- section: Rings
- relevance: 4 - a state that does not match its list is reported as a bug

Through which states and lists does a ring entry move, and which lock protects
them? In which states does the entry hold an io_uring command? Start from
`enum fuse_ring_req_state` and `struct fuse_ring_queue`.

## fuse.uring-queue-choice: Choosing a queue

- section: Rings
- relevance: 3 - decides which server thread sees a request

How does a request choose its ring queue, and what happens when that queue
does not exist? How are background requests limited when the ring is in use?
Start from `fuse_uring_task_to_queue()` and `fuse_uring_flush_bg()`.

## fuse.uring-commit-and-fetch: Commit and fetch

- section: Rings
- relevance: 4 - the server chooses every value in the command

How does a commit find the request it answers, and what does the commit check
before it copies the reply? What happens to the command when no further request
is waiting? Start from `fuse_uring_commit_fetch()`.

## fuse.uring-copy-context: Context of ring copies

- section: Rings
- relevance: 4 - a copy in the wrong task writes to the wrong address space

In which task does the kernel copy a request into the buffers of a ring entry,
and how does the request get to that task? Which issue flags does each path
pass to io_uring? Start from `fuse_uring_send_in_task()` and
`fuse_uring_dispatch_ent()`.

## fuse.uring-teardown: Ring teardown

- section: Rings
- relevance: 5 - io_uring can cancel a command while the ring is torn down

What are the requirements for freeing a ring entry in order to assure safe
usage against a cancel from io_uring? What does the count of queue references
wait for, and when are the queues and the ring freed? Start from
`fuse_uring_cancel()`, `fuse_uring_stop_queues()` and `fuse_uring_destruct()`.

## fuse.uring-buffers: Payload buffers

- section: Rings
- relevance: 3 - an entry may have no buffer at all

In which ways can a ring queue get its payload buffers, and when is the way
fixed for a queue? When is a buffer taken and given back? If the tree has only
one way, say so. Start from `enum fuse_queue_payload_mode` and
`fuse_uring_select_buffer()`.

## fuse.uring-zero-copy: Payloads without a copy

- section: Rings
- relevance: 3 - folios stay registered with io_uring while the server works

Does this tree let the server reach the folios of a request without a copy?
Which requests qualify, and when are the folios released? If the tree has no
such path, say so. Start from `can_zero_copy_req()` and
`fuse_uring_set_up_zero_copy()`.

## fuse.uring-lock-order: Ring lock order

- section: Rings
- relevance: 4 - lockdep sees only the orders that a test happens to run

In which order may code take the lock of a ring queue, the background lock of
the channel, the lock of the channel and the lock of an inode, and where does
the code drop a lock to keep that order? Start from `fuse_uring_req_end()` and
`fuse_uring_abort_end_queue_requests()`.

# Inodes and names

## fuse.inode-identity: Inode identity

- section: Inodes and attributes
- relevance: 4 - the server can give one number to two files

What identifies a FUSE inode in the inode cache, and what happens when the
server reuses a node id for another file? What does marking an inode bad change
for later operations? Start from `fuse_iget()`, `fuse_stale_inode()` and
`fuse_make_bad()`.

## fuse.attribute-versions: Attribute versions

- section: Inodes and attributes
- relevance: 5 - a reply can arrive after the change that makes it wrong

How does the kernel decide that the attributes in a reply are older than what
it already has? Which counters does a caller read before it sends, and which
local changes raise them? Start from `fuse_change_attributes()`,
`attr_version` and `evict_ctr`.

## fuse.attribute-cache: Attribute cache validity

- section: Inodes and attributes
- relevance: 4 - stale attributes reach user space through stat and read

What makes cached attributes valid or stale, and how is one attribute marked
stale? Which attributes does the kernel keep from its own copy when the
writeback cache is on? Start from `fuse_update_attributes()`,
`fuse_invalidate_attr_mask()` and `fuse_get_cache_mask()`.

## fuse.inode-locks: Locks of an inode

- section: Inodes and attributes
- relevance: 4 - the comment on a lock names less than the lock covers

What does each lock in `struct fuse_inode` protect, and when do lookup and
readdir take the mutex of the directory? Start from `fuse_lock_inode()`.

## fuse.reply-attribute-checks: Checks on replies

- section: Inodes and attributes
- relevance: 4 - the server is not trusted

What are the requirements for using an entry or attributes from a reply in
order to assure safe usage with a server that sends wrong data: which checks
must run before an inode is created or updated? Start from
`fuse_invalid_attr()` and `invalid_nodeid()`.

## fuse.dentry-validity: Dentry validity

- section: Dentries and directories
- relevance: 4 - revalidation runs in RCU walk, where it must not sleep

What does a FUSE dentry store about its own validity? When does revalidation
send a LOOKUP, and what does revalidation return during an RCU walk? Start from
`fuse_dentry_revalidate()` and `struct fuse_dentry`.

## fuse.epoch: Epoch and expired dentries

- section: Dentries and directories
- relevance: 3 - a second way for a dentry to become invalid

What raises the epoch of a connection, and which cached objects compare
themselves with it? Does this tree remove a dentry whose timeout has passed,
without waiting for a lookup? Start from `fuse_notify_inc_epoch()`,
`fuse_dentry_set_epoch()` and `fuse_dentry_tree_work()`.

## fuse.reverse-invalidation: Invalidation from the server

- section: Dentries and directories
- relevance: 3 - the server names a dentry that a task may be using

What does each of the notifications that invalidate an inode, invalidate an
entry, delete an entry and prune inodes do to the dentry and inode caches, and
which errors can each return to the server? Start from
`fuse_reverse_inval_entry()`, `fuse_reverse_inval_inode()` and
`fuse_try_prune_one_inode()`.

## fuse.permission-checks: Permission checks

- section: Dentries and directories
- relevance: 4 - the kernel and the server each check in a different mode

Who checks access to a file when the mount has default permissions and when it
does not, and when does a permission check send a request to the server? Start
from `fuse_permission()` and `fuse_access()`.

## fuse.create-and-open: Create and open

- section: Dentries and directories
- relevance: 3 - the server has made a file that the kernel may fail to use

How does creating and opening a file in one request work, and what does the
kernel do when the server lacks that request? What is undone when a later step
fails after the server created the file? Start from `fuse_atomic_open()` and
`fuse_create_open()`.

## fuse.readdir-cache: Readdir cache

- section: Dentries and directories
- relevance: 3 - several readers fill and read one cache

Where does the kernel cache directory entries, and what makes the cache
invalid? How does a reader notice that the cache changed between two calls?
Start from `fuse_readdir_cached()` and `fuse_add_dirent_to_cache()`.

## fuse.readdirplus: Entries with attributes

- section: Dentries and directories
- relevance: 3 - every entry linked raises a lookup count

When does the kernel ask for directory entries with attributes, and what does
the kernel do with an entry whose node id is zero? How does the kernel keep the
lookup count right for each entry it links? Start from
`fuse_use_readdirplus()` and `fuse_direntplus_link()`.

## fuse.xattr-and-acl: Extended attributes and ACLs

- section: Dentries and directories
- relevance: 3 - ACLs are cached by the VFS and stored by the server

How are POSIX ACLs read and set through the server, and when does the kernel
use them for its own permission checks? What must be invalidated after an
extended attribute changes? Start from `fuse_set_acl()`,
`fuse_get_inode_acl()` and `fuse_setxattr()`.

## fuse.killpriv: Clearing setuid and setgid

- section: Dentries and directories
- relevance: 3 - either side can be the one that clears the bits

Who clears the setuid and setgid bits on write, truncate and chown, and how
does the kernel tell the server to do it? What does the kernel do to its cached
mode afterwards? Start from `handle_killpriv_v2`, `FUSE_OPEN_KILL_SUIDGID` and
`FUSE_WRITE_KILL_SUIDGID`.

# File I/O

## fuse.open-file-lifetime: Open file life cycle

- section: Open files
- relevance: 4 - requests in flight use the file after close

Who holds a reference to a `struct fuse_file`? When is RELEASE sent
synchronously and when in the background, and what keeps the inode alive until
RELEASE completes? Start from `fuse_file_put()` and `fuse_prepare_release()`.

## fuse.io-path-choice: Choosing the I/O path

- section: Open files
- relevance: 4 - the flags of the open reply select the code that runs

How does a read or a write choose among DAX, direct I/O, passthrough and the
page cache, and which one is used when the open reply set more than one flag?
Start from `fuse_file_read_iter()` and `fuse_file_write_iter()`.

## fuse.inode-io-modes: Inode I/O modes

- section: Open files
- relevance: 4 - one counter holds two kinds of count

Which I/O modes can an inode be in, and what does the counter that tracks the
mode keep a count of? What does an open return when it asks for a mode that
conflicts with the current one? Start from `fuse_file_io_open()` and
`iocachectr`.

## fuse.buffered-read: Buffered reads

- section: Cached I/O and writeback
- relevance: 3 - a short read changes the size of the file

How does the kernel read one folio and read ahead, and what does a short read
from the server change? When is a read sent in the background? Start from
`fuse_read_folio()`, `fuse_readahead()` and `fuse_short_read()`.

## fuse.buffered-write: Buffered writes

- section: Cached I/O and writeback
- relevance: 4 - two write paths share one entry point

How does a buffered write reach the server when the writeback cache is off and
when it is on, and which lock does the write hold? Start from
`fuse_cache_write_iter()` and `fuse_perform_write()`.

## fuse.writeback-data: Data under writeback

- section: Cached I/O and writeback
- relevance: 5 - the server decides when writeback ends

While a WRITE from writeback is in flight, which memory holds the data? When
does writeback of the folio end, and which callers wait for that? Start from
`fuse_iomap_writeback_range()`, `fuse_writepage_end()` and
`fuse_page_mkwrite()`.

## fuse.write-blocking: Blocking writeback

- section: Cached I/O and writeback
- relevance: 4 - truncate and fsync rely on it

What are the requirements for calling `fuse_set_nowrite()` and
`fuse_release_nowrite()` in order to assure safe usage, and what does the write
counter of the inode count? Start from `writectr` and
`fuse_flush_writepages()`.

## fuse.truncate: Truncate and size changes

- section: Cached I/O and writeback
- relevance: 4 - the size is changed by the kernel, the server and replies in flight

How does a size change keep the page cache, the cached size and replies in
flight consistent, and what is undone when the server refuses the change? Start
from `fuse_do_setattr()` and `FUSE_I_SIZE_UNSTABLE`.

## fuse.fsync-and-syncfs: Fsync and syncfs

- section: Cached I/O and writeback
- relevance: 3 - errors from writeback arrive after the write returned

What does fsync wait for before it sends FSYNC, and how does syncfs wait for
writes that are already in flight? Where does a writeback error reach the
caller? Start from `fuse_fsync()`, `fuse_sync_fs()` and
`struct fuse_sync_bucket`.

## fuse.mmap: Memory mapping

- section: Cached I/O and writeback
- relevance: 3 - a mapping can outlive every open file

Which kinds of mapping does an open file allow in each I/O mode, and when is
dirty mapped data written back? Start from `fuse_file_mmap()` and
`fuse_vma_close()`.

## fuse.direct-io: Direct I/O

- section: Direct I/O and passthrough
- relevance: 4 - direct I/O and the page cache can hold different data

What does a direct read or write do to the page cache before and after the
request? Which inode lock does a direct write take, and when may direct writes
to one inode run at the same time? Start from `fuse_direct_io()` and
`fuse_dio_lock()`.

## fuse.backing-files: Backing files

- section: Direct I/O and passthrough
- relevance: 4 - the kernel opens a file on behalf of the server

How does the server register a backing file, and which checks does
registration make? Who holds references to the backing file until it is freed?
Start from `fuse_backing_open()` and `fuse_backing_lookup()`.

## fuse.passthrough-io: Passthrough I/O

- section: Direct I/O and passthrough
- relevance: 3 - the I/O runs with credentials that are not the caller's

Which operations on an open file go to the backing file, and with whose
credentials? How are the attributes of the FUSE inode kept current afterwards?
Start from `fuse_passthrough_open()` and `fuse_passthrough_write_iter()`.

## fuse.file-locks: File locks

- section: Other file operations
- relevance: 3 - the kernel and the server can each be the one that holds a lock

When are POSIX locks and flock locks sent to the server, and when are they
kept in the kernel? What identifies the owner of a lock to the server, and what
releases a flock lock at close? Start from `fuse_file_lock()`,
`fuse_file_flock()` and `fuse_lock_owner_id()`.

## fuse.ioctl: Ioctls on files

- section: Other file operations
- relevance: 3 - the server asks the kernel to copy memory of the caller

How does the kernel decide which memory of the caller an ioctl may read and
write, and which callers may let the server choose that memory? Which limits
bound the transfer? Start from `fuse_do_ioctl()` and
`FUSE_IOCTL_UNRESTRICTED`.

# Other transports

## fuse.virtiofs-requests: virtio-fs request path

- section: virtio-fs
- relevance: 4 - requests are sent from contexts that must not sleep

How does virtio-fs put a request on a virtqueue, and what does virtio-fs do
when the virtqueue is full or the request cannot be sent? In which context does
a request complete? Start from `virtio_fs_send_req()`,
`virtio_fs_enqueue_req()` and `virtio_fs_requests_done_work()`.

## fuse.virtiofs-lifetime: virtio-fs mount and removal

- section: virtio-fs
- relevance: 3 - the device can be removed while the filesystem is mounted

How does a virtio-fs mount find its device and create its connection? What
does unmount do that a mount through the device file does not, and what
happens to a mounted filesystem when the virtio device is removed? Start from
`virtio_fs_get_tree()`, `virtio_fs_conn_destroy()` and `virtio_fs_remove()`.

## fuse.dax: DAX mappings

- section: virtio-fs
- relevance: 3 - a mapping can be reclaimed while a fault uses it

How does FUSE DAX map a range of a file into the DAX window, and which locks
keep a mapping from being reclaimed while I/O or a fault uses it? What has to
happen before a truncate? Start from `fuse_setup_new_dax_mapping()`,
`fuse_dax_break_layouts()` and `struct fuse_dax_mapping`.

## fuse.cuse: Character devices in user space

- section: CUSE
- relevance: 3 - CUSE uses the FUSE core with no superblock and no inode

How does CUSE create its connection and its character device, and which parts
of the FUSE core does CUSE use with no superblock? What are the requirements
for a change to those parts in order to assure safe usage by CUSE? Start from
`cuse_channel_open()`, `cuse_process_init_reply()` and `cuse_open()`.

# Changing the implementation

## fuse.untrusted-server: Limits on the server

- section: What a change must preserve
- relevance: 5 - the server can be any unprivileged program

What are the requirements for a change to FUSE in order to assure that an
unprivileged server cannot block or harm tasks that do not use its filesystem,
and where does the tree state those requirements? Start from
`Documentation/filesystems/fuse/fuse.rst`, `fuse_page_mkwrite()` and
`fuse_file_release()`.

## fuse.reclaim-and-allocation: Allocation on write paths

- section: What a change must preserve
- relevance: 4 - the server itself may need memory to answer the request

What are the requirements for allocating memory on the paths that write back
data or release a file in order to assure that memory reclaim cannot wait on
the server for ever? Start from `fuse_send_writepage()`,
`fuse_writepage_args_alloc()` and `fuse_file_open()`.
