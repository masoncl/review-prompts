# Questions: SMB/ksmbd Subsystem

- guide: smb-ksmbd.md
- title: SMB/ksmbd Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/smb-ksmbd-measurement.md` is the
wider set the readers were measured on and `catalogue/smb-ksmbd-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## ksmbd.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Request dispatch and validation

## ksmbd.request-path: Reader thread and dispatcher

- section: Request dispatch and validation
- relevance: 5 - nothing else makes sense without it

Which thread reads a request from a connection, and which runs its handler? In what order does
`__handle_ksmbd_work()` run its steps for each command of a compound request, and which steps run
once for the whole message? Start from `ksmbd_conn_handler_loop()` and `__handle_ksmbd_work()`.

## ksmbd.message-checks: Checks before a handler runs

- section: Request dispatch and validation
- relevance: 5 - decides what a handler may assume about its input

What does the server verify about the size and the layout of an SMB2 request before its handler
runs, which mismatches between the calculated and the actual length does it accept, and what does
a handler still have to bounds-check itself? Start from `ksmbd_smb2_check_message()` and
`smb2_get_data_area_len()`.

## ksmbd.credits-and-sequence: Credits and message ids

- section: Request dispatch and validation
- relevance: 4 - every reader said message ids are not policed

Where is a request's credit charge checked and taken, and where are credits given back, on the
normal path and on the paths that send an error or no response? Which lock covers the credit state
of a connection? Start from `smb2_validate_credit_charge()` and `smb2_set_rsp_credits()`.

## ksmbd.message-id-window: Message id window

- section: Request dispatch and validation
- relevance: 4 - decides what a handler may assume about the message id of its request

What does the server do with a request whose message id is outside the granted range or has been
used already, and which lock covers the sequence state of a connection? Start from
`ksmbd_smb2_check_message()`.

## ksmbd.compound-state: Compound request state

- section: Request dispatch and validation
- relevance: 4 - handlers that read the wrong header are a recurring bug

What are the requirements for reading the request buffer, writing the response buffer and taking a
file id in a handler that may run as a later command of a compound request, in order to assure
safe usage? Which helpers return the current request and response headers and the file id of an
earlier command? How are the session and the tree connect checked for a command that is not the
first? Start from `ksmbd_req_buf_next()` and `init_chained_smb2_rsp()`.

## ksmbd.request-field-usage: Client-supplied offsets and lengths

- section: Request dispatch and validation
- relevance: 5 - out-of-bounds reads in handlers are the commonest security bug here

What are the requirements for an offset, length or count field taken from a request, before a
command handler uses it, in order to assure safe usage? Name in-tree code that shows it for a list
of variable-length entries inside a request. Start from `smb2_find_context_vals()`,
`smb2_set_ea()` and `parse_sec_desc()`.

# Connections and work items

## ksmbd.conn-lifetime: Connection lifetime

- section: Connections and work items
- relevance: 5 - use after free of the connection is a recurring bug class

What does each counter and the reference count of a `struct ksmbd_conn` stand for, and which
longer-lived objects take the reference? Where and in what context is the structure freed? Start
from `ksmbd_conn_free()`, `ksmbd_conn_put()` and `ksmbd_conn_r_count_dec()`.

## ksmbd.conn-teardown-order: Connection teardown order

- section: Connections and work items
- relevance: 4 - reordering these steps frees things still in use

In what order does the teardown of a connection run, from the exit of the receive loop in
`ksmbd_conn_handler_loop()` to the freeing of the `struct ksmbd_conn`, and what does each step
require the step before it to have finished? Which lock orders a change of connection status
against a request being linked as asynchronous? Start from the end of `ksmbd_conn_handler_loop()`
and `ksmbd_server_terminate_conn()`.

## ksmbd.work-lifetime: Work item lifetime

- section: Connections and work items
- relevance: 4 - every request and every server-initiated message is one

What does `ksmbd_free_work_struct()` release, including references to other objects? Who allocates
and frees a `struct ksmbd_work` for a client request, and who for a message that the server sends
on its own initiative? Which counters of the `struct ksmbd_conn` must be adjusted when a work item
is queued and when it is freed? Start from `ksmbd_free_work_struct()` and `handle_ksmbd_work()`.

## ksmbd.async-and-cancel: Asynchronous requests and cancel

- section: Connections and work items
- relevance: 4 - the cancel callback runs under a spinlock from another thread

How does a handler that may block for a long time turn its request into an asynchronous one? How
does the handler learn that its request was cancelled, or that the file was closed while it
waited? Start from `setup_async_work()`, `release_async_work()` and `smb2_cancel()`.

## ksmbd.cancel-callback: Cancel callback context

- section: Connections and work items
- relevance: 4 - the callback runs in the context of its caller and not in that of the handler

Who calls the cancel callback that a handler passes to `setup_async_work()`, and in what context?
What are the requirements for the callback in that context in order to assure safe usage? Start
from `smb2_cancel()`.

# Sessions and tree connects

## ksmbd.session-lifetime: Session lifetime

- section: Sessions and tree connects
- relevance: 5 - sessions are reachable from several connections at once

What is the reference count of a `struct ksmbd_session` initialised to, and who owns those
references? Which paths drop the reference that the session table holds? Start from
`ksmbd_session_register()` and `ksmbd_user_session_put()`.

## ksmbd.session-lookup: Session lookup functions

- section: Sessions and tree connects
- relevance: 5 - the lookup decides in which states of a session a request may run

Which lookup functions return a `struct ksmbd_session` with a reference taken, which session
states does each accept, and which one does the dispatcher use? Start from
`ksmbd_session_lookup_all()`.

## ksmbd.session-setup-paths: Session setup paths

- section: Sessions and tree connects
- relevance: 4 - authentication state bugs are security bugs

What does the session setup handler check before it binds an existing session
to another connection or re-authenticates one, when do the session and the
connection become valid, and what is undone when authentication fails? Start
from `smb2_sess_setup()`.

## ksmbd.tree-connect-lifetime: Tree connect lifetime

- section: Sessions and tree connects
- relevance: 4 - the dispatcher and disconnect race on every request

What does `ksmbd_tree_conn_lookup()` check and take, under which lock, and who drops the reference
that the dispatcher took? In what order does a tree disconnect run its steps? Start from
`ksmbd_tree_conn_lookup()` and `ksmbd_tree_conn_disconnect()`.

## ksmbd.session-pointer-usage: Using a session pointer

- section: Sessions and tree connects
- relevance: 4 - a session can be logged off by another channel mid-request

What are the requirements for using a `struct ksmbd_session` pointer in order to assure safe
usage, for a pointer that a lookup function returns and for a pointer stored in an object that
outlives the request? Who puts the reference that the dispatcher took for `work->sess`, and what
must a handler that replaces or clears `work->sess` do?

# Open files

## ksmbd.file-handle-lifetime: Open file handle lifetime

- section: Open files
- relevance: 5 - every file command starts with a lookup and must end with a put

Which of the volatile and the persistent id does every open get, and in which table is each id
registered? What do the lookup helpers check besides the id before they return a handle with a
reference? What does dropping the last reference do? Start from `ksmbd_open_fd()`,
`ksmbd_lookup_fd_fast()`, `ksmbd_lookup_fd_slow()` and `ksmbd_fd_put()`.

## ksmbd.inode-object: Per-inode shared state

- section: Open files
- relevance: 4 - share modes, delete-on-close and oplocks all hang off it

What is a `struct ksmbd_inode` keyed by, so which opens share one, what kind of
lock protects its lists, and how are delete-on-close and delete-pending
recorded for a file and for a named stream? Start from `ksmbd_inode_get()` and
`ksmbd_fd_set_delete_on_close()`.

## ksmbd.file-handle-usage: Using a file handle

- section: Open files
- relevance: 5 - leaked and over-put handles are the commonest lifetime bug here

What are the requirements for using a `struct ksmbd_file` pointer in a command handler, from the
lookup to the put, in order to assure safe usage? What are the requirements for a handle that is
reached by walking the list of a `struct ksmbd_inode`? Name in-tree code that shows it.

## ksmbd.file-handle-members: File handle back pointers

- section: Open files
- relevance: 5 - a handler reaches the connection and the tree connect through the handle

When does the server set and clear the `conn` and `tcon` members of a `struct ksmbd_file`? What
are the requirements for reading them in order to assure safe usage?

# Names and credentials

## ksmbd.path-confinement: Confining names to the share

- section: Names and credentials
- relevance: 5 - an escape from the share root is a security bug

With which root and lookup flags does the server resolve a file name sent by a client, and how
does that lookup treat symbolic links, `..` components and mount points under the share? Which
share flags change that treatment, and does the server code test each of them? Start from
`ksmbd_vfs_kern_path()` and `ksmbd_vfs_kern_path_create()`.

## ksmbd.name-validation: File name validation

- section: Names and credentials
- relevance: 5 - a name reaches the lookup in the form that the validation leaves it in

What does the server check about a file name sent by a client before it resolves the name, and
which functions must a handler that takes a name from a request call? Start from `smb2_get_name()`
and `ksmbd_validate_filename()`.

## ksmbd.credential-override: Credential override and revert

- section: Names and credentials
- relevance: 4 - an unbalanced override leaks credentials into a kernel thread

What are the credentials that `ksmbd_override_fsids()` installs built from? What are the
requirements for calling `ksmbd_override_fsids()` and `ksmbd_revert_fsids()` in order to assure
safe usage? Name an in-tree handler that shows it. Which access checks does the server do itself
and not leave to the VFS?

# Oplocks and leases

## ksmbd.opinfo-lifetime: Oplock object lifetime

- section: Oplocks and leases
- relevance: 5 - freed objects reached through an inode's list have been a recurring bug

How is a `struct oplock_info` reference counted and freed? How must code read the pointer from a
`struct ksmbd_file` to its `struct oplock_info`? On which of the objects that a `struct
oplock_info` points at does it hold a reference, and until when? Start from `alloc_opinfo()`,
`opinfo_get()`, `opinfo_put()` and `close_id_del_oplock()`.

## ksmbd.lease-objects: Lease objects and tables

- section: Oplocks and leases
- relevance: 4 - several opens share one lease

Do the opens that share a lease key share one `struct lease`, or does each open have its own, and
what frees a lease? Which lock protects the per-client lease tables and the lists in them? Start
from `alloc_lease()`, `add_lease_global_list()` and `destroy_lease_table()`.

## ksmbd.break-sequence: Break sequence

- section: Oplocks and leases
- relevance: 4 - the waits and the states decide whether an open hangs

When an open or a write conflicts with an oplock or lease held by another open, for which holders
does the server wait for an acknowledgement? When no acknowledgement arrives in time, what state
is the holder left in, by constant name in full, and what does the opener then do? Start from
`oplock_break()`, `wait_for_break_ack()` and `smb2_oplock_break()`.

## ksmbd.break-notification-route: Break notification route

- section: Oplocks and leases
- relevance: 4 - the holder of an oplock or lease can lose its connection before the break is sent

Which function sends an oplock or lease break notification, and which handles its acknowledgement?
On which connection does the notification go out, and what does the server do when the connection
of the holder is gone? Start from `oplock_break()` and `smb2_oplock_break()`.

## ksmbd.opinfo-usage: Using an oplock object

- section: Oplocks and leases
- relevance: 5 - the wrong access pattern is a use after free

What are the requirements for using a `struct oplock_info` that is reached from a `struct
ksmbd_file` or from the oplock list of a `struct ksmbd_inode`, and for following the pointers that
it holds to other objects, in order to assure safe usage? Name in-tree code that shows it.

# The user-space daemon

## ksmbd.ipc-round-trip: Request and response over netlink

- section: The user-space daemon
- relevance: 4 - every login and tree connect goes through it

How is a request to the user-space daemon matched with its response? What does the caller get back
when the daemon is absent, is slow or sends the wrong type? Who frees the response? Start from
`ipc_msg_send_request()` and `handle_response()` in `fs/smb/server/transport_ipc.c`.

## ksmbd.ipc-response-checks: Daemon response validation

- section: The user-space daemon
- relevance: 4 - sizes in the payload come from user space

What does the server check about a response from the daemon before the caller sees it, for which
event types, and what do callers still have to check themselves? Start from `ksmbd_nl_policy` and
`ipc_validate_msg()`.

# SMB Direct

## ksmbd.smbdirect-location: Location of the RDMA transport

- section: SMB Direct
- relevance: 4 - every reader looked for it in the wrong place

Where in this tree is the SMB Direct protocol (SMB over RDMA) implemented for the server, which
other code in the tree uses the same implementation, and what does
`fs/smb/server/transport_rdma.c` hold? Start from `CONFIG_SMB_SERVER_SMBDIRECT` in
`fs/smb/server/Makefile`. If the tree has no SMB Direct support, say so and stop.

## ksmbd.smbdirect-credit-order: First credit grant

- section: SMB Direct
- relevance: 4 - the one thing the hand-written guide was about

On the accepting side of an SMB Direct connection, which message is the first that grants receive
credits to the peer? Which work items can post receive buffers or send a message that grants
credits, and does anything stop them from running before that first message is sent? Start from
`smbdirect_socket_init()` and `smbdirect_accept_negotiate_finish()`. If the tree has no SMB Direct
support, say so and stop.

## ksmbd.smbdirect-first-grant-time: Time of the first grant

- section: SMB Direct
- relevance: 4 - the peer may send as soon as it holds credits

On the accepting side of an SMB Direct connection, when is the first message that grants receive
credits to the peer sent, relative to the application accepting the connection? Start from
`smbdirect_accept_negotiate_finish()`. If the tree has no SMB Direct support, say so and stop.

## ksmbd.smbdirect-work-usage: Work item initialisation

- section: SMB Direct
- relevance: 4 - a reordering is invisible in a diff and breaks the protocol

In the SMB Direct socket code, what are the requirements for setting up and queueing a work item
of the socket in order to assure safe usage? What does `queue_work()` do with a work item that has
been disabled? Which handler does a work item have between `smbdirect_socket_init()` and the point
where the handler for an established connection is set?

# Model gaps

## ksmbd.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
