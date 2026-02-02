- queue_work() only schedules execution; flush_work()/flush_workqueue() wait for
  completion or cancellation, but they do NOT free the work struct. The caller
  owns the lifetime and must manage it explicitly.
