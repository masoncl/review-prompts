# Questions: SMB server, ksmbd (measurement set)

- guide: smb-ksmbd.md
- title: SMB/ksmbd Subsystem

A wide set of questions about the in-kernel SMB server under `fs/smb/server/`
and what it shares with the client: the path of a request, how it is
validated, connections and work items, sessions and tree connects, open files,
oplocks and leases, the VFS side, the netlink interface to the user-space
daemon, and SMB Direct. It is used to measure what a model already knows
before deciding what the built guide should spend its words on. The
hand-written guide it will replace is 365 words and covers one thing only, the
order in which an SMB Direct connection grants credits. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## ksmbd.source-layout: Source layout

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files under `fs/smb/server/` hold the per-connection receive loop, the
request dispatcher, the SMB2 command handlers, the checks made on a message
before a handler runs, the dialect tables, sessions, tree connects and share
configuration, open file handles, oplocks and leases, the VFS wrappers,
authentication and signing, security descriptors, and the transports? A
table. Start from `fs/smb/server/Makefile`.

## ksmbd.shared-with-client: Code shared with the client

- section: Finding your way
- relevance: 3 - a change there has a second user
- words: 70

What lives in `fs/smb/common/`, which of it do both the client under
`fs/smb/client/` and the server include or link, and which definitions of
structures that go on the wire does the server keep for itself? Start from
`fs/smb/common/smb2pdu.h` and `fs/smb/server/smb2pdu.h`.

## ksmbd.smbdirect-location: Location of the RDMA transport

- section: Finding your way
- relevance: 4 - a reader who looks in the wrong place reviews the wrong code
- words: 70

Where in this tree is the SMB Direct protocol (SMB over RDMA) implemented for
the server: which directory, which Kconfig symbols build it, who else uses the
same code, and what does `fs/smb/server/transport_rdma.c` itself hold? Start
from `CONFIG_SMB_SERVER_SMBDIRECT` in `fs/smb/server/Makefile`. If the tree has
no SMB Direct support, say so and stop.

# The path of a request

## ksmbd.request-path: From socket to handler

- section: Dispatch
- relevance: 5 - nothing else makes sense without it
- words: 110

Trace one SMB2 request from the bytes arriving on a connection to the
response being written: which thread reads it and what limits does it apply,
which function allocates the work item, which workqueue runs it, which
function loops over the commands of a compound, and in what order are the
session check, the tree connect check, signature verification, the handler,
credit granting and signing done? Start from `ksmbd_conn_handler_loop()` and
`__handle_ksmbd_work()`.

## ksmbd.transforms-order: Encryption, compression and signing order

- section: Dispatch
- relevance: 3 - the order is fixed by the protocol and easy to break
- words: 70

On receive and on send, in what order does the dispatcher apply decryption,
decompression, signature checking, the pre-authentication integrity hash,
compression and encryption, and which requests must be signed or are refused
when they arrive unencrypted? Start from `__handle_ksmbd_work()` and
`__process_request()`.

## ksmbd.compound-state: Compound request state

- section: Dispatch
- relevance: 4 - handlers that read the wrong header are a recurring bug
- words: 90

How is state carried from one command of a compound request to the next: which
fields of `struct ksmbd_work` hold the offsets of the current request and
response and the file id, session and status of an earlier command, which
helpers return the current request and response headers, and how are the
session and tree connect checked for a command that is not the first? Start
from `ksmbd_req_buf_next()` and `init_chained_smb2_rsp()`.

## ksmbd.response-buffers: Building the response

- section: Dispatch
- relevance: 3 - the iov bookkeeping is local and easy to get wrong
- words: 80

How does a handler build its response: how is the response buffer sized and
allocated, how does a handler add its fixed part and any separately allocated
payload to the vector that is sent, who frees such a payload, and how is the
length in the transport header kept in step? Start from
`smb2_allocate_rsp_buf()` and `ksmbd_iov_pin_rsp()`.

## ksmbd.message-checks: Checks before a handler runs

- section: Validating a request
- relevance: 5 - decides what a handler may assume about its input
- words: 110

What does the server verify about an SMB2 request before its handler runs
(length against the transport header, the next command offset, the header and
fixed structure sizes, the variable data area for each command), what
mismatches between calculated and actual length does it tolerate, and what
does a handler therefore still have to bounds-check itself? Start from
`ksmbd_smb2_check_message()` and `smb2_get_data_area_len()`.

## ksmbd.request-field-usage: Offsets and lengths from the client

- section: Validating a request
- relevance: 5 - out-of-bounds reads in handlers are the commonest security bug here
- words: 90

What usage in a command handler of an offset, length or count field taken
from a request is unsafe, and what that looks similar is correct? Name
in-tree code that shows the correct form for a list of variable-length
entries inside a request. Start from `smb2_find_context_vals()`,
`smb2_set_ea()` and `parse_sec_desc()`.

## ksmbd.credits-and-sequence: Credits and message ids

- section: Validating a request
- relevance: 4 - a leak or a missed check stalls or exposes the connection
- words: 100

How does the server account for SMB2 credits and message ids on a connection:
which fields of `struct ksmbd_conn` hold what has been granted and what is
outstanding, which lock protects them, where is a request's credit charge
checked and taken, where is it given back on the normal and on the error
paths, and what is done with a message id that is outside the granted range
or has been used already? Start from `smb2_validate_credit_charge()` and
`smb2_set_rsp_credits()`.

# Objects and their lifetimes

## ksmbd.conn-lifetime: Connection lifetime

- section: Connections and work items
- relevance: 5 - use after free of the connection is a recurring bug class
- words: 110

What keeps a `struct ksmbd_conn` alive: which counters and reference counts
does it carry, what does each one count and who takes it, what does the
connection's own thread wait for before it tears the connection down, which
objects hold a pointer to the connection past that point, and where and in
what context is the structure finally freed? Start from `ksmbd_conn_free()`,
`ksmbd_conn_put()` and `ksmbd_conn_r_count_dec()`.

## ksmbd.conn-status: Connection status

- section: Connections and work items
- relevance: 3 - transitions race with teardown
- words: 70

Which status values can a connection have, how is the status read and
written, which lock orders a change to the exiting or releasing states against
code that queues new work on the connection, and which function shuts a
connection down from outside its own thread? Start from `ksmbd_conn_abort()`
and `ksmbd_all_conn_set_status()`.

## ksmbd.conn-teardown-order: Connection teardown order

- section: Connections and work items
- relevance: 4 - reordering these steps frees things still in use
- words: 80

List in order what happens from the moment a connection's receive loop exits
to the moment its memory is freed: status change, cancelling of pending
asynchronous requests, what is waited for, what the terminate callback cleans
up, and how the transport is disconnected and freed. Start from the end of
`ksmbd_conn_handler_loop()` and `ksmbd_server_terminate_conn()`.

## ksmbd.work-lifetime: Work item lifetime

- section: Connections and work items
- relevance: 4 - every request and every server-initiated message is one
- words: 80

What does a `struct ksmbd_work` own and free (request and response buffers,
transform and compression buffers, references to other objects), what are
its states, who allocates and frees it for a client request and for a message
the server sends on its own initiative such as an oplock break, and what must
be balanced on the connection when it is freed? Start from
`ksmbd_free_work_struct()` and `handle_ksmbd_work()`.

## ksmbd.async-and-cancel: Asynchronous requests and cancel

- section: Connections and work items
- relevance: 4 - the cancel callback runs under a spinlock from another thread
- words: 90

How does a handler that may block for a long time (a byte-range lock, a change
notify, a wait for an oplock break) turn its request into an asynchronous one:
what does it register, where is the work linked and under which lock, what
sends the interim response, who may call the cancel callback and in what
context, and how does the handler find out it was cancelled or that the file
was closed under it? Start from `setup_async_work()`, `release_async_work()`
and `smb2_cancel()`.

## ksmbd.session-lifetime: Session lifetime

- section: Sessions and tree connects
- relevance: 5 - sessions are reachable from several connections at once
- words: 110

Where is a `struct ksmbd_session` registered (which tables, which locks), what
is its reference count initialised to and who owns those references, which
lookup functions return a session with a reference taken and which do not,
what session states are there (constant names in full) and which of them do
the lookups accept, and which paths drop the last reference? Start from
`ksmbd_session_lookup_all()`, `ksmbd_session_register()` and
`ksmbd_user_session_put()`.

## ksmbd.session-pointer-usage: Using a session pointer

- section: Sessions and tree connects
- relevance: 4 - a session can be logged off by another channel mid-request
- words: 70

What usage of a session pointer (from a lookup, from `work->sess`, or stored
in a longer-lived object such as an oplock) is unsafe, and what that looks
similar is correct? Say who puts the reference the dispatcher took for
`work->sess`, and what a handler that replaces or clears `work->sess` must do.

## ksmbd.session-setup-paths: Session setup paths

- section: Sessions and tree connects
- relevance: 4 - authentication state bugs are security bugs
- words: 100

Which distinct cases does the session setup handler separate (a new session,
binding an existing session to another connection, re-authentication of an
existing session), what does it check before it accepts a binding, when do
the session and the connection become valid, and what is undone when
authentication fails? Start from `smb2_sess_setup()` and
`ksmbd_session_unregister()`.

## ksmbd.session-channels: Session channels

- section: Sessions and tree connects
- relevance: 3 - only matters with multichannel on
- words: 70

How is a session that is bound to several connections represented: where is
the list of channels, what is it indexed by, which lock protects it, what does
each channel carry, and how does connection teardown decide whether to destroy
a session or only remove its own channel? Start from `struct channel` and
`ksmbd_conn_sessions_cleanup()`.

## ksmbd.tree-connect-lifetime: Tree connect lifetime

- section: Sessions and tree connects
- relevance: 4 - the dispatcher and disconnect race on every request
- words: 80

Where are a session's tree connects stored and under which lock, what states
does a `struct ksmbd_tree_connect` go through, which function looks one up and
what does it check and take, who drops the reference the dispatcher took, and
what does tree disconnect do to the entry and to the files opened through it?
Start from `ksmbd_tree_conn_lookup()` and `ksmbd_tree_conn_disconnect()`.

## ksmbd.file-handle-lifetime: Open file handle lifetime

- section: Open files
- relevance: 5 - every file command starts with a lookup and must end with a put
- words: 110

How is an open represented and found: where do `struct ksmbd_file` objects
live (per session and globally), what are the volatile and persistent ids,
what states does a handle go through from creation to close, what do the
lookup helpers check besides the id before they return a handle with a
reference, and what does dropping the last reference do? Start from
`ksmbd_open_fd()`, `ksmbd_lookup_fd_fast()`, `ksmbd_lookup_fd_slow()` and
`ksmbd_fd_put()`.

## ksmbd.file-handle-usage: Using a file handle

- section: Open files
- relevance: 5 - leaked and over-put handles are the commonest lifetime bug here
- words: 80

What usage of a `struct ksmbd_file` pointer in a command handler is unsafe
(around lookup and put on every exit path, close racing with other commands
on the same id, handles reached by walking an inode's list, the `conn` and
`tcon` members of a handle), and what that looks similar is correct? Name
in-tree code that shows it.

## ksmbd.inode-object: Per-inode shared state

- section: Open files
- relevance: 4 - share modes, delete-on-close and oplocks all hang off it
- words: 80

What is `struct ksmbd_inode`: what is it keyed by and where is it hashed, what
lists does it carry and which lock protects them, how is it reference counted,
and how are delete-on-close and delete-pending recorded for a file and for a
named stream? Start from `ksmbd_inode_get()` and
`ksmbd_fd_set_delete_on_close()`.

## ksmbd.durable-handles: Durable handles

- section: Open files
- relevance: 3 - a second owner of handles that outlives the session
- words: 90

How does a durable handle survive its session: what decides at session
teardown whether a handle is kept, which of its members are cleared and which
references dropped when it is kept, where is it found again, what is checked
at reconnect, and what finally closes one that is never reclaimed? Start from
`session_fd_check()`, `ksmbd_reopen_durable_fd()` and
`ksmbd_durable_scavenger()`.

# Oplocks and leases

## ksmbd.opinfo-lifetime: Oplock object lifetime

- section: Oplock and lease objects
- relevance: 5 - freed objects reached through an inode's list have been a recurring bug
- words: 110

What is a `struct oplock_info`: which lists is it on and which locks protect
them, how is it reference counted and freed, how does a handle point at it and
how is that pointer read safely, which of the objects it points at (the
connection, the session, the file handle, the lease) does it hold a reference
on and which does it not? Start from `alloc_opinfo()`, `opinfo_get()`,
`opinfo_put()` and `close_id_del_oplock()`.

## ksmbd.opinfo-usage: Using an oplock object

- section: Oplock and lease objects
- relevance: 5 - the wrong access pattern is a use after free
- words: 80

What usage of an oplock object reached from a file handle or from an inode's
oplock list is unsafe, and what that looks similar is correct? Cover
dereferencing its file handle, session and connection pointers while a close
or a disconnect may be running. Name in-tree code that shows it.

## ksmbd.lease-objects: Lease objects and tables

- section: Oplock and lease objects
- relevance: 4 - several opens share one lease
- words: 90

How are leases represented: what is the relation between a `struct lease` and
the opens that share its key, is a lease reference counted and if so what
holds the references, how are leases grouped by client, which locks protect
the per-client tables and the lists in them, and when is a table created and
destroyed? Start from `alloc_lease()`, `add_lease_global_list()` and
`destroy_lease_table()`.

## ksmbd.break-sequence: Break sequence

- section: Breaking
- relevance: 4 - the waits and the states decide whether an open hangs
- words: 110

When an open or a write conflicts with an oplock or lease held by another
open, what happens in order: is a holder limited to one break at a time and
how, which states does the holder go through (constant names in full), how is
the notification sent and on which connection, how long does the opener wait
and what is done when no acknowledgement arrives, and which handlers process
the acknowledgement? Start from `oplock_break()`, `wait_for_break_ack()` and
`smb2_oplock_break()`.

# The VFS side

## ksmbd.path-confinement: Confining names to the share

- section: Files and credentials
- relevance: 5 - an escape from the share root is a security bug
- words: 90

How is a file name sent by a client resolved, and what keeps the result inside
the share: which function does the lookup and with which flags and root, how
are symbolic links, `..` components and mount points under the share treated,
what does the case-insensitive retry do, and which validation is done on the
name before the lookup? Start from `ksmbd_vfs_kern_path()` and
`ksmbd_vfs_kern_path_create()`.

## ksmbd.credential-override: Acting as the user

- section: Files and credentials
- relevance: 4 - an unbalanced override leaks credentials into a kernel thread
- words: 70

How does the server do file system operations with the identity of the
authenticated user: which function installs the credentials and what do they
contain, where is the saved set kept, what usage around it is unsafe and what
is correct, and which checks does the server do itself rather than leave to
the VFS? Start from `ksmbd_override_fsids()` and `ksmbd_revert_fsids()`.

# The user-space daemon

## ksmbd.ipc-round-trip: Request and response over netlink

- section: Netlink interface
- relevance: 4 - every login and tree connect goes through it
- words: 100

How does the kernel ask the user-space daemon a question and get the answer:
which netlink family and events, how is a request matched with its response,
which table and lock are involved, how long does a caller wait, what does it
get back when the daemon is absent, slow or sends the wrong type, and who
frees the response? Start from `ipc_msg_send_request()` and
`handle_response()` in `fs/smb/server/transport_ipc.c`.

## ksmbd.ipc-response-checks: Trusting the daemon's answers

- section: Netlink interface
- relevance: 4 - sizes in the payload come from user space
- words: 80

What is checked about a response from the daemon before the caller sees it
(the attribute policy, the payload size against the sizes stated inside it,
string termination), for which events, and what do callers still have to
check themselves? Start from `ksmbd_nl_policy` and `ipc_validate_msg()`.

## ksmbd.server-state: Start, reset and shutdown

- section: Netlink interface
- relevance: 3 - ordering bugs show up only at module unload or daemon restart
- words: 80

Which states does the server as a whole go through, what moves it between
them (the daemon's startup event, the heartbeat, the sysfs kill switch, module
unload), what does a reset tear down and in what order, and what must module
exit wait for before the code goes away? Start from
`server_ctrl_handle_reset()`, `ksmbd_server_shutdown()` and
`ksmbd_server_exit()`.

# SMB Direct

## ksmbd.smbdirect-credit-order: First credit grant

- section: RDMA transport
- relevance: 4 - the one thing the hand-written guide was about
- words: 100

On the accepting side of an SMB Direct connection, which message is the first
that grants receive credits to the peer and when is it sent relative to the
application accepting the connection, which work items can post receive
buffers or send a message that grants credits, and does anything stop them
from running before that first message? Name the functions that initialise
those work items, that give them the handlers they run with on an established
connection, and that send the negotiate response. Start from
`smbdirect_socket_init()` and `smbdirect_accept_negotiate_finish()`. If the
tree has no SMB Direct support, say so and stop.

## ksmbd.smbdirect-work-usage: Work item initialisation

- section: RDMA transport
- relevance: 4 - a reordering is invisible in a diff and breaks the protocol
- words: 70

In the SMB Direct socket code, what change to how a work item is initialised,
disabled, given its handler or queued is unsafe, and what that looks similar
is correct? Say what happens to a `queue_work()` on a work item that has been
disabled, and which handler a work item has between the initialisation of the
socket and the point where the handler it runs with is set.

# Changing the implementation

## ksmbd.command-change-checklist: Adding or changing a command

- section: What a change must preserve
- relevance: 3 - several tables have to agree
- words: 80

What else has to change when an SMB2 command handler, an info level or an
FSCTL is added or its request layout changes: the per-dialect command tables,
the table of fixed structure sizes and the data area calculation used by the
message check, the credit charge calculation, signing and encryption rules,
and the shared wire definitions? Start from `fs/smb/server/smb2ops.c` and
`smb2_req_struct_sizes`.
