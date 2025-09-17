__must_hold(x): The specified lock is held on function entry and exit

__acquires(x): The lock is held on function exit, but not entry

__releases(x): The lock is held on function entry, but not exit

__acquire(x): Code acquires the lock x (used within a function)

__release(x): Code releases the lock x (used within a function)

__cond_lock(x, c): Conditionally acquires lock x if condition c is true
