- Queue Freezing Synchronization Rule: When analyzing potential races between
  bio completion paths and queue teardown functions: blk_mq_freeze_queue()
  ensures all in-flight bios complete by waiting for q->q_usage_counter to
  reach zero. Since every bio holds a reference to q->q_usage_counter from
  submission (blk_try_enter_queue) to completion (blk_queue_exit), teardown
  functions cannot complete while bios with QoS flags are still executing their
  completion paths.
