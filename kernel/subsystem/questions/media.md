# Questions: Media and V4L2

- guide: media.md
- title: Media and V4L2 Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/media-measurement.md` is the
wider set the readers were measured on and `catalogue/media-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## media.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## media.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

Which files hold video device registration, the ioctl dispatcher, file handles,
sub-devices, the control framework, async registration and firmware parsing,
the memory-to-memory framework, the media controller and videobuf2? Which
header under `include/media/` declares each? Start from
`drivers/media/v4l2-core/Makefile`, `drivers/media/mc/Makefile` and
`drivers/media/common/videobuf2/Makefile`.

## media.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules for drivers are written only there

Which files under `Documentation/driver-api/media/` and
`Documentation/userspace-api/media/` are the authority on sub-devices and
their state, on camera sensor drivers, on transmitter and receiver drivers, on
controls, on videobuf2, on the request API, and on what a patch must pass
before it is submitted?

## media.config-symbols: Configuration symbols

- section: Finding your way
- relevance: 4 - a check that is compiled out is not a check

Which configuration symbols compile parts of the core out, and what do the
affected functions do or return when their part is compiled out? Start from
`CONFIG_MEDIA_CONTROLLER`, `CONFIG_VIDEO_V4L2_SUBDEV_API` and
`CONFIG_VIDEO_ADV_DEBUG`.

# Video devices

## media.vdev-release: Release callback

- section: Video devices
- relevance: 5 - decides when driver memory may be freed

When does the core call the `release` callback of `struct video_device`, and
what may still use the structure after `video_unregister_device()` returns?
Which release helpers does the core provide, and when is each one valid? Start
from `v4l2_device_release()` in `drivers/media/v4l2-core/v4l2-dev.c`.

## media.vdev-unregister: Unregistering a video device

- section: Video devices
- relevance: 5 - hot unplug with open files is a recurring source of bugs

What does `video_unregister_device()` guarantee about files that are still
open and about ioctls that are in progress? What does each file operation
return for a device that is no longer registered? Start from `v4l2_open()`,
`v4l2_ioctl()` and `__video_do_ioctl()`.

## media.vdev-register-failure: Failed registration

- section: Video devices
- relevance: 4 - error paths in probe are where leaks and double frees are

When `video_register_device()` fails, what has the core already undone, and
what must the caller free or release? Does the `release` callback of
`struct video_device` run on that path? Start from the error paths of
`__video_register_device()`.

## media.v4l2-device-lifetime: Lifetime of the parent device

- section: Video devices
- relevance: 4 - the parent structure usually holds the driver data

Who holds references to a `struct v4l2_device`, and when does its `release`
callback run? What do `v4l2_device_register()`, `v4l2_device_disconnect()` and
`v4l2_device_unregister()` each do to the parent `struct device`? Start from
`drivers/media/v4l2-core/v4l2-device.c`.

## media.valid-ioctls: Enabled ioctls

- section: Video devices
- relevance: 4 - decides whether a callback can be reached at all

How does the core decide which ioctls a video device node accepts, and at what
point is that decided? What are the requirements for calling
`v4l2_disable_ioctl()` in order to assure safe usage? Start from
`determine_valid_ioctls()`.

## media.vdev-register: Registering a video device

- section: Video devices
- relevance: 5 - the node can be opened before probe has finished

What are the requirements for a driver that calls `video_register_device()` in
order to assure safe usage: what must `struct video_device` hold before the
call, and from which point may userspace open the node? Start from
`__video_register_device()`.

# File handles

## media.fh-lifecycle: File handle lifecycle

- section: File handles
- relevance: 4 - the signatures are easy to get wrong from memory

Which functions create, add, remove and free a `struct v4l2_fh`, what
arguments does each take, and in what order must an `open` and a `release`
file operation call them? Start from `v4l2_fh_open()` and `v4l2_fh_release()`.

## media.fh-use: Use of file handles

- section: File handles
- relevance: 5 - decides whether the private data of a file can be trusted

Is a driver required to use `struct v4l2_fh`, and what does the core do when a
device node is opened by a driver that does not? Start from `v4l2_open()` and
`v4l2_fh_init()`.

## media.ioctl-priv-argument: Callback arguments

- section: File handles
- relevance: 5 - every ioctl callback of every driver receives it

What does the core pass as the `priv` argument of a callback in
`struct v4l2_ioctl_ops`, and how does a callback reach the `struct v4l2_fh`
and the driver data of the open file? Start from `__video_do_ioctl()`,
`v4l_querycap()` and `file_to_v4l2_fh()`.

## media.events: Event queue

- section: File handles
- relevance: 3 - events are queued from interrupt handlers

Which lock protects the event lists of a `struct v4l2_fh`, from which contexts
may a driver call `v4l2_event_queue()`, and what does the core do when the
queue of a subscription is full? What does `v4l2_event_dequeue()` do with the
lock of the video device while it waits? Start from
`__v4l2_event_queue_fh()`.

# Ioctl dispatch

## media.ioctl-locking: Locks taken by the dispatcher

- section: Ioctl dispatch
- relevance: 5 - says what a callback may assume is serialised

Which mutex does `video_ioctl2()` take for which ioctl, and in what order when
it takes more than one? Which ioctls run with no core lock held? Start from
`v4l2_ioctl_get_lock()` and `__video_do_ioctl()`.

## media.ioctl-usercopy: Copying arguments

- section: Ioctl dispatch
- relevance: 4 - says which pointers in an argument are kernel memory

How does `video_usercopy()` copy the argument of an ioctl in and out,
including an argument that points at an array, and which limits does it
enforce on the array? When does it copy the result back although the handler
returned an error? Start from `check_array_args()` and `INFO_FL_ALWAYS_COPY`.

## media.ioctl-sanitize: Checks before the driver runs

- section: Ioctl dispatch
- relevance: 4 - says which values a driver must still validate

What does the core validate, clamp or clear in the argument of the format
ioctls before it calls the driver, and what does it leave to the driver? Start
from `check_fmt()`, `v4l_sanitize_format()` and `v4l_s_fmt()`.

## media.compat-ioctl: 32-bit compatibility

- section: Ioctl dispatch
- relevance: 3 - a new or resized structure needs work here

Where does the core convert the ioctls of a 32-bit process and the ioctls that
carry a 32-bit time, and what must a change that adds or resizes an ioctl
structure do there? Start from `v4l2_compat_ioctl32()` and
`v4l2_translate_cmd()`.

## media.uapi-compatibility: Changing the userspace API

- section: Ioctl dispatch
- relevance: 4 - a mistake here cannot be taken back

What must a change to a structure or an ioctl in
`include/uapi/linux/videodev2.h`, `include/uapi/linux/v4l2-subdev.h` or
`include/uapi/linux/media.h` preserve, and how does the core treat the
reserved fields of an argument? Where must a new ioctl be added in the core?
Start from the `v4l2_ioctls` table and `INFO_FL_CLEAR`.

## media.format-negotiation: Format negotiation contract

- section: Ioctl dispatch
- relevance: 4 - the compliance tools test it and drivers get it wrong

What does the userspace API require of a driver that implements
`VIDIOC_TRY_FMT` and `VIDIOC_S_FMT` when the requested format is not
supported, and when may `VIDIOC_S_FMT` return an error? Which document states
it? Start from `Documentation/userspace-api/media/v4l/vidioc-g-fmt.rst`.

# Sub-device registration

## media.subdev-register: Registering with a parent

- section: Sub-device registration
- relevance: 4 - says what the bridge driver gets for free and must undo

What does `v4l2_device_register_subdev()` do besides adding the sub-device to
a list: which reference does it take, what does it register, and which
callback does it call? What does it undo when it fails? Start from
`__v4l2_device_register_subdev()`.

## media.subdev-devnode: Device nodes of sub-devices

- section: Sub-device registration
- relevance: 3 - decides which operations userspace can reach

How does a sub-device get a device node, who allocates and frees the
`struct video_device` behind it, and which ioctls does a read-only node refuse?
Start from `__v4l2_device_register_subdev_nodes()` and
`V4L2_FL_SUBDEV_RO_DEVNODE`.

## media.subdev-init: Initialising a sub-device

- section: Sub-device registration
- relevance: 5 - the order decides what a callback may find uninitialised

In what order must a driver initialise a `struct v4l2_subdev`, its pads, its
control handler and its active state before it registers the sub-device, and
what must it undo, in what order, on removal? Start from `v4l2_subdev_init()`,
`media_entity_pads_init()` and `v4l2_subdev_init_finalize()`.

## media.subdev-release: Unregistering and freeing

- section: Sub-device registration
- relevance: 5 - decides when the memory of a sub-device may be freed

In what order can the `unregistered`, `close` and `release` operations of
`struct v4l2_subdev_internal_ops` run, and what are the requirements for
freeing the memory that holds a `struct v4l2_subdev` in order to assure safe
usage? Start from `v4l2_device_unregister_subdev()` and
`v4l2_subdev_release()`.

# Calling sub-device operations

## media.subdev-call: Calling an operation

- section: Calling sub-device operations
- relevance: 5 - the return values are tested in every bridge driver

What does `v4l2_subdev_call()` return for a NULL sub-device and for an
operation that the driver does not implement, and how must a caller treat each
value? Start from `v4l2_subdev_call()` in `include/media/v4l2-subdev.h`.

## media.subdev-wrappers: Operation wrappers

- section: Calling sub-device operations
- relevance: 5 - decides what a driver callback may assume about its arguments

Which sub-device operations does the core wrap before it calls the driver, and
what does a wrapper change besides checking its arguments? What does a wrapper
do when the caller passes a NULL state? Start from `v4l2_subdev_call_wrappers`
and `DEFINE_STATE_WRAPPER` in `drivers/media/v4l2-core/v4l2-subdev.c`.

## media.subdev-call-paths: Paths to an operation

- section: Calling sub-device operations
- relevance: 4 - a check holds only on the paths that make it

Which macros and helpers that invoke a sub-device operation go through
`v4l2_subdev_call_wrappers`, and does any of them call the operation of the
driver without the wrapper? Where should a reviewer search for other direct
calls? Start from `v4l2_subdev_call()`, `v4l2_device_call_all()` and
`__v4l2_device_call_subdevs_p()`.

## media.subdev-argument-checks: State, pad and stream checks

- section: Calling sub-device operations
- relevance: 5 - decides whether a lookup in a callback can fail

What does the core check about the `which`, `pad`, `stream` and state
arguments before it calls a pad operation that takes a state? Does the check
depend on `V4L2_SUBDEV_FL_STREAMS` or on `CONFIG_VIDEO_V4L2_SUBDEV_API`? Start
from `check_state()`, `check_pad()` and `check_format()`.

## media.subdev-node-ioctls: Sub-device node ioctls

- section: Calling sub-device operations
- relevance: 4 - says what a pad operation receives from userspace

Which locks does the ioctl path of a sub-device node take, and which state does
it pass to a pad operation for each value of `which`? What does it do to the
`stream` field of an argument before it calls the driver? Start from
`subdev_do_ioctl_lock()`, `subdev_ioctl_get_state()` and `subdev_do_ioctl()`.

## media.subdev-frame-interval: Frame interval operations

- section: Calling sub-device operations
- relevance: 4 - old and new drivers spell these differently

Which group in `struct v4l2_subdev_ops` holds the operations that get and set
a frame interval, what arguments do they take, and how does the core choose the
value of `which` for them? Start from `call_get_frame_interval()` and
`V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH`.

# Sub-device state

## media.subdev-state-kinds: Active state and try state

- section: Sub-device state
- relevance: 5 - nothing about pad operations makes sense without it

What is a `struct v4l2_subdev_state`, who allocates and frees the active state
and the try state, and when does the core call the `init_state` operation?
Which sub-devices have no active state? Start from
`__v4l2_subdev_state_alloc()` and `subdev_fh_init()`.

## media.subdev-state-accessors: State accessors

- section: Sub-device state
- relevance: 5 - the result is dereferenced in nearly every pad operation

What do `v4l2_subdev_state_get_format()`, `v4l2_subdev_state_get_crop()`,
`v4l2_subdev_state_get_compose()` and `v4l2_subdev_state_get_interval()` return
for a pad or a stream that the state does not hold, and for a NULL state?
Which lock must the caller hold? Start from
`__v4l2_subdev_state_get_format()`.

## media.subdev-state-locking: Locking a state

- section: Sub-device state
- relevance: 4 - lockdep catches part of it, and only when the path runs

Which helpers lock and unlock a sub-device state, which helpers return the
active state, and what does each assert about the lock? How can a driver make
the state, the controls and its own data share one lock? Start from
`v4l2_subdev_lock_and_get_active_state()` and the `state_lock` field of
`struct v4l2_subdev`.

# Streams and routing

## media.subdev-streams-enabled: Streams API availability

- section: Streams and routing
- relevance: 4 - decides which values of a stream id can reach a driver

Can userspace use the streams and routing ioctls on a sub-device node in this
tree, and what decides it? What does a sub-device that sets
`V4L2_SUBDEV_FL_STREAMS` have to implement? Start from
`v4l2_subdev_enable_streams_api` and `__v4l2_subdev_init_finalize()`.

## media.subdev-routing: Setting a routing table

- section: Streams and routing
- relevance: 4 - the table comes from userspace and sizes later lookups

What does the core check in a routing table before it calls the `set_routing`
operation, and what do `v4l2_subdev_set_routing()` and
`v4l2_subdev_routing_validate()` each do? What happens to the formats that the
state held before the routing changed? Start from the
`VIDIOC_SUBDEV_S_ROUTING` case of `subdev_do_ioctl()`.

## media.subdev-routing-lookups: Lookups through the routing table

- section: Streams and routing
- relevance: 4 - the result is used as a pointer or as a mask

What do `v4l2_subdev_routing_find_opposite_end()`,
`v4l2_subdev_state_get_opposite_stream_format()` and
`v4l2_subdev_state_xlate_streams()` return when no route matches? Do they
consider routes that are not active?

## media.subdev-enable-streams: Enabling and disabling streams

- section: Streams and routing
- relevance: 5 - bridge drivers branch on the error codes

What does `v4l2_subdev_enable_streams()` return for each kind of invalid
request, and what does it do for a sub-device that implements only `s_stream`?
What does `v4l2_subdev_disable_streams()` do when the driver returns an error?
Start from `v4l2_subdev_collect_streams()`.

## media.subdev-s-stream: The s_stream operation

- section: Streams and routing
- relevance: 4 - unbalanced calls are common in bridge drivers

What does the core do when `s_stream` is called to start a sub-device that is
already started, and what does it do with an error that the driver returns
when it stops? What does `v4l2_subdev_is_streaming()` report, and under which
lock? Start from `call_s_stream()`.

# Async registration

## media.async-callbacks: Notifier callbacks

- section: Async registration
- relevance: 4 - says what a callback may call back into

When does the core call the `bound`, `unbind`, `complete` and `destroy`
operations of a notifier, and under which lock? What does the core undo when
`bound` or `complete` returns an error? Start from `v4l2_async_match_notify()`
and `v4l2_async_nf_try_complete()`.

## media.async-notifier-lifecycle: Notifier lifecycle

- section: Async registration
- relevance: 5 - error paths in probe leak or free twice

What are the requirements for the order of initialising, filling, registering,
unregistering and cleaning up a `struct v4l2_async_notifier` in order to
assure safe usage? Who owns the memory of each connection, and who drops the
reference to its fwnode? Start from `v4l2_async_nf_register()` and
`v4l2_async_nf_cleanup()`.

## media.async-subdev-register: Registering an async sub-device

- section: Async registration
- relevance: 5 - the sub-device can be called before probe returns

What are the requirements for a sub-device driver before it calls
`v4l2_async_register_subdev()` in order to assure safe usage? Which fwnode does
the core match the sub-device by, and what does the core refuse? Start from
`__v4l2_async_register_subdev()` and `match_fwnode()`.

# Firmware and sensors

## media.fwnode-endpoint: Parsing an endpoint

- section: Firmware and sensors
- relevance: 4 - callers pick between two variants

What is the difference between `v4l2_fwnode_endpoint_parse()` and
`v4l2_fwnode_endpoint_alloc_parse()`, and what must the caller set in
`struct v4l2_fwnode_endpoint` before the call? What does each return for a
NULL fwnode and for a bus type that does not match? Start from
`__v4l2_fwnode_endpoint_parse()`.

## media.link-frequency: Link frequency helpers

- section: Firmware and sensors
- relevance: 3 - receivers size their timing from the result

What arguments does `v4l2_get_link_freq()` take, where does it look for the
link frequency, and in what order? What does `v4l2_link_freq_to_bitmap()`
return when firmware lists no frequency or when no frequency matches?

## media.sensor-clock: Sensor clock helper

- section: Firmware and sensors
- relevance: 3 - new sensor drivers are asked to use it

Which helper should a camera sensor driver use to get its external clock, and
what does the helper do on a system with ACPI or with no clock provider? Start
from `__devm_v4l2_sensor_clk_get()` and
`Documentation/driver-api/media/camera-sensor.rst`.

## media.sensor-power: Power management of sensors

- section: Firmware and sensors
- relevance: 4 - the rules are in the documentation, not in the code

What are the requirements for runtime power management in a camera sensor
driver in order to assure safe usage: when must the device be powered, where
does the driver take and drop its runtime PM reference, and which operations
must a new driver leave unimplemented? Start from
`Documentation/driver-api/media/camera-sensor.rst`.

# Control framework

## media.ctrl-handler-lifecycle: Handler lifecycle

- section: Control framework
- relevance: 5 - nearly every driver has this sequence in probe

How does a driver initialise a `struct v4l2_ctrl_handler`, add controls and
find out that adding a control failed? What does `v4l2_ctrl_handler_free()`
return, and may it be called on a handler whose initialisation failed? Start
from `v4l2_ctrl_handler_init_class()` and `handler_set_err()`.

## media.ctrl-locking: Handler lock

- section: Control framework
- relevance: 5 - a wrong variant deadlocks or races

Which lock protects the controls of a handler, and which control operations
does the core call with that lock held? Which helpers take the lock and which
require the caller to hold it? Start from `v4l2_ctrl_lock()`,
`__v4l2_ctrl_s_ctrl()` and `v4l2_ctrl_s_ctrl()`.

## media.ctrl-ops: Control operations

- section: Control framework
- relevance: 4 - says which value a callback must read

What do the `s_ctrl`, `try_ctrl` and `g_volatile_ctrl` operations receive,
where does each read or write the value, and when does the core skip the call
to `s_ctrl`? Start from `try_or_set_cluster()` and `cluster_changed()`.

## media.ctrl-inheritance: Controls shared between handlers

- section: Control framework
- relevance: 4 - decides who may free a control

How do the controls of a sub-device become visible on a video device node,
which controls are left out, and who owns a control that two handlers refer
to? Start from `v4l2_ctrl_add_handler()` and
`__v4l2_device_register_subdev()`.

## media.ctrl-clusters: Control clusters

- section: Control framework
- relevance: 3 - the callback sees one control of several

What is a control cluster, which control of a cluster do the operations
receive, and what does `v4l2_ctrl_auto_cluster()` add? What are the
requirements for the array passed to `v4l2_ctrl_cluster()` in order to assure
safe usage?

## media.ctrl-handler-setup: Applying control values

- section: Control framework
- relevance: 4 - it writes to hardware that may be powered off

What does `v4l2_ctrl_handler_setup()` do, which controls does it skip, and what
are the requirements for calling it from a power management callback in order
to assure safe usage? Start from `__v4l2_ctrl_handler_setup()` and
`Documentation/driver-api/media/camera-sensor.rst`.

# videobuf2

## media.vb2-callback-order: Order of queue operations

- section: videobuf2
- relevance: 4 - says what is initialised when a callback runs

In what order does the core call `buf_init`, `buf_out_validate`,
`buf_prepare`, `buf_queue`, `buf_finish` and `buf_cleanup` for one buffer, and
`prepare_streaming`, `start_streaming`, `stop_streaming` and
`unprepare_streaming` for the queue? Which of them can be called before
streaming starts? Start from `vb2_core_qbuf()` and `vb2_core_streamon()`.

## media.vb2-locking: Locks around queue operations

- section: videobuf2
- relevance: 5 - says what a callback may assume is serialised

Which lock does the core hold when it calls each operation in
`struct vb2_ops`, and what protects the done list against the interrupt
handler of a driver? What does a blocking `VIDIOC_DQBUF` do with the queue lock
while it waits, and does a driver supply operations for that? Start from
`__vb2_wait_for_done_vb()` and the `lock` field of `struct vb2_queue`.

## media.vb2-queue-owner: Queue ownership

- section: videobuf2
- relevance: 4 - a driver that writes its own ioctl must repeat the test

How do the ioctl helpers and the file operation helpers of videobuf2 decide
which open file owns a queue, which calls does a file that is not the owner
get refused, and when is the ownership dropped? Start from
`vb2_queue_is_busy()` and `vb2_ioctl_reqbufs()`.

## media.vb2-queue-setup: The queue_setup operation

- section: videobuf2
- relevance: 5 - it sizes every buffer the hardware writes to

What must the `queue_setup` operation do when it is called for
`VIDIOC_REQBUFS` and when it is called for `VIDIOC_CREATE_BUFS`, and how does
it tell the two apart? What does the core check in what `queue_setup` returns?
Start from `vb2_core_reqbufs()` and `vb2_core_create_bufs()`.

## media.vb2-imported-buffers: Imported buffers

- section: videobuf2
- relevance: 3 - the size of the memory comes from userspace

What does the core check about the size of an imported or user pointer buffer
before it calls `buf_prepare`, and what must `buf_prepare` still check itself?
When does the core call `buf_cleanup` and `buf_init` again for a buffer that is
already allocated? Start from `__prepare_dmabuf()` and `__prepare_userptr()`.

## media.vb2-queue-init: Initialising a queue

- section: videobuf2
- relevance: 5 - the core refuses a queue that is set up wrongly

What are the requirements for a `struct vb2_queue` that a driver passes to
`vb2_queue_init()` in order to assure safe usage, and which combinations does
the core refuse? Is the `lock` field optional? Start from
`vb2_core_queue_init()` and `vb2_queue_init_name()`.

## media.vb2-start-streaming: Starting to stream

- section: videobuf2
- relevance: 5 - the error path is wrong in many drivers

When does the core call `start_streaming`, and what are the requirements for a
`start_streaming` operation that fails in order to assure safe usage? What
does the core do when the requirements are not met? Start from
`vb2_start_streaming()`.

## media.vb2-stop-streaming: Stopping a stream

- section: videobuf2
- relevance: 5 - buffers left with the hardware are freed under it

What are the requirements for a `stop_streaming` operation in order to assure
safe usage, and on which paths does the core call it? What does the core do
with buffers that the driver still owns afterwards? Start from
`__vb2_queue_cancel()`.

## media.vb2-buffer-done: Returning a buffer

- section: videobuf2
- relevance: 5 - called from interrupt handlers in every driver

What are the requirements for calling `vb2_buffer_done()` in order to assure
safe usage: in which buffer state, with which target states and from which
contexts? What does it do for a buffer that belongs to a request? Start from
`vb2_buffer_done()`.

## media.vb2-release: Releasing a queue

- section: videobuf2
- relevance: 4 - removal with an open file must stop the hardware first

What is the difference between `vb2_fop_release()` and `_vb2_fop_release()`,
and what does `vb2_video_unregister_device()` do that
`video_unregister_device()` does not? What are the requirements for releasing
a queue when the device is removed while a file is open in order to assure
safe usage?

# Memory-to-memory devices

## media.m2m-scheduling: Job scheduling

- section: Memory-to-memory devices
- relevance: 5 - says what `device_run` may assume and may do

Which conditions must hold before the core runs a job for a context, and in
which context does it call `device_run`? From which contexts may a driver call
`v4l2_m2m_try_schedule()`? Start from `__v4l2_m2m_try_queue()` and
`v4l2_m2m_try_run()`.

## media.m2m-draining: Stop commands and draining

- section: Memory-to-memory devices
- relevance: 3 - confined to codec drivers

How do the memory-to-memory helpers handle the encoder and decoder stop
commands: which state do they keep in the context, and which helper marks the
last buffer? Start from `v4l2_m2m_encoder_cmd()`,
`v4l2_update_last_buf_state()` and `v4l2_m2m_last_buffer_done()`.

## media.m2m-locking: Queue locks of a context

- section: Memory-to-memory devices
- relevance: 4 - both queues are used from one ioctl path

What are the requirements for the `lock` fields of the two queues that
`queue_init` sets up in order to assure safe usage, and which lock does the
ioctl dispatcher take for a memory-to-memory device? Start from
`v4l2_m2m_ctx_init()` and `v4l2_ioctl_get_lock()`.

## media.m2m-job-finish: Finishing and aborting a job

- section: Memory-to-memory devices
- relevance: 5 - a job that never finishes blocks close for ever

What are the requirements for ending a job in order to assure safe usage:
which function does a driver call, from which contexts, and in what order does
it return the source and the destination buffer? What must a driver do when
the core calls `job_abort`? Start from `v4l2_m2m_job_finish()`,
`v4l2_m2m_buf_done_and_job_finish()` and `v4l2_m2m_cancel_job()`.

# Media controller graph

## media.mc-setup-link: Changing a link

- section: Media controller graph
- relevance: 4 - userspace can ask for it while a pipeline runs

Under which conditions does the core refuse to enable or disable a link, which
callbacks does it call and in what order, and what does it undo when a callback
fails? Start from `__media_entity_setup_link()` and
`__media_entity_setup_link_notify()`.

## media.mc-graph-mutex: Graph mutex

- section: Media controller graph
- relevance: 4 - half of the graph functions have a locked variant

What does the `graph_mutex` of `struct media_device` protect, which functions
take it themselves and which require the caller to hold it? Which ioctls of the
media device node run under it? Start from `media_device_ioctl()` and
`__media_pipeline_start()`.

## media.mc-device-lifecycle: Media device lifecycle

- section: Media controller graph
- relevance: 5 - the device node can outlive the driver data

In what order must a driver call `media_device_init()`,
`media_device_register()`, `media_device_unregister()` and
`media_device_cleanup()`, and what may still use the `struct media_device`
after it is unregistered? Who allocates and frees the `struct media_devnode`?
Start from `__media_device_register()` and `media_devnode_release()`.

## media.mc-entity-register: Registering an entity

- section: Media controller graph
- relevance: 4 - most sub-device drivers do this by hand

What must a driver set in a `struct media_entity` and its pads before the
entity is registered, and what does `media_entity_pads_init()` refuse? What
does `media_device_unregister_entity()` remove besides the entity? Start from
`media_device_register_entity()`.

## media.mc-link-kinds: Kinds of link

- section: Media controller graph
- relevance: 5 - a loop over the list reads fields of every link

Which kinds of link can the `links` list of an entity hold, which fields of
`struct media_link` are valid for each kind, and what are the requirements for
walking that list in order to assure safe usage? Start from
`media_create_pad_link()`, `media_create_ancillary_link()` and
`for_each_media_entity_data_link()`.

# Pipelines

## media.mc-pipeline-start: Starting a pipeline

- section: Pipelines
- relevance: 5 - the arguments and the bookkeeping have changed

What does `media_pipeline_start()` take as its starting point, which pads does
it add to the pipeline, and where does it record that a pad belongs to a
pipeline? What does a second start of the same pipeline do? Start from
`__media_pipeline_start()` and `media_pipeline_explore_next_link()`.

## media.mc-pipeline-validation: Validation at pipeline start

- section: Pipelines
- relevance: 5 - it is the last check before the hardware streams

Which links does the core validate when a pipeline starts, on which entity
does it call `link_validate`, and what does it return for a pad that is busy or
that has `MEDIA_PAD_FL_MUST_CONNECT` set? What does it undo when validation
fails? Start from `__media_pipeline_start()`.

## media.mc-subdev-link-validate: Link validation for sub-devices

- section: Pipelines
- relevance: 5 - it decides which format mismatches reach the hardware

What does `v4l2_subdev_link_validate()` check, which states does it lock, and
what does it do when the source of the link is a video device? What does it do
with a stream whose format it cannot read? Start from
`v4l2_subdev_link_validate_locked()` and
`v4l2_subdev_link_validate_default()`.

# Requests

## media.req-lifecycle: Request states

- section: Requests
- relevance: 4 - every access to a request depends on its state

Which states can a `struct media_request` be in, which function makes each
transition, and what must a driver hold or call before it reads or changes the
objects of a request? Start from `media_request_ioctl_queue()`,
`media_request_lock_for_update()` and `media_request_lock_for_access()`.

## media.req-manual-completion: Manual completion

- section: Requests
- relevance: 3 - confined to drivers that finish a request late

Does this tree let a driver complete a request by hand, and if so, which
functions does the driver call and what do they require? Start from
`media_request_manual_complete()`. If the tree has no such function, say so
and stop.

## media.ctrl-requests: Controls in a request

- section: Requests
- relevance: 3 - stateless codec drivers depend on it

How are control values stored in a request, and which functions must a driver
call to apply them and to mark them complete? Start from
`v4l2_ctrl_request_setup()` and `v4l2_ctrl_request_complete()`.

## media.req-objects: Request objects

- section: Requests
- relevance: 4 - an object that never completes blocks userspace

What are the requirements for binding, completing and unbinding a
`struct media_request_object` in order to assure safe usage, and when does a
request become complete? Start from `media_request_object_bind()`,
`media_request_object_complete()` and `media_request_object_unbind()`.

## media.vb2-requests: Queues that use requests

- section: Requests
- relevance: 3 - confined to codec and a few camera drivers

What are the requirements for a queue that supports or requires requests in
order to assure safe usage: what must the driver set in `struct vb2_queue`,
and what must it implement? What does the core refuse when buffers are queued
both directly and through a request? Start from `vb2_core_qbuf()` and
`vb2_request_validate()`.

# Model gaps

## media.model-gaps: Other mistakes models make

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
