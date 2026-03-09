# Readers–Writers Problem with Load Balancing
Operating Systems – Assignment 1

---

# Project Overview

This project implements the **Readers–Writers synchronization problem with writer priority and load balancing**.

The system simulates multiple **reader threads** and one **writer thread** accessing shared files.  
Three replicas of the same file are used so that readers can read from different replicas. The system distributes readers across replicas to keep the load balanced.

The writer thread periodically updates all replicas while blocking readers.

This program demonstrates:

- Thread synchronization
- Writer priority
- Load balancing between file replicas
- Logging of all operations

---

# Problem Description

The system contains:

- Multiple **reader threads**
- One **writer thread**
- **Three replicas** of the same file

Readers read from a replica file once and terminate.  
The writer periodically updates the files.

The system ensures:

- Readers and writer **cannot access files simultaneously**
- **Writer has priority over readers**
- Readers are **distributed evenly across replicas**
- All operations are **logged in a log file**

---

# System Components

## Reader Threads

Reader threads perform the following steps:

1. Spawn at random intervals.
2. Wait if a writer is active or waiting.
3. Select the replica with the **lowest number of active readers**.
4. Read the file content.
5. Log the read operation.
6. Terminate after reading once.

---

## Writer Thread

The writer thread performs the following steps:

1. Sleeps for a random duration.
2. Signals its intention to write.
3. Waits until all readers finish.
4. Obtains exclusive access to all files.
5. Updates **all replicas simultaneously**.
6. Logs the write operation.
7. Releases the lock so readers can continue.

While the writer is writing, **no readers can access the files**.

---

# File Replicas

The program uses three replicas:

```
replica1.txt
replica2.txt
replica3.txt
```

All replicas contain identical content.  
When the writer updates the file, **all replicas are updated together**.

---

# Synchronization Mechanism

The program uses the following synchronization primitives.

## Mutex

A mutex protects shared variables such as:

- number of active readers
- number of readers per replica
- writer status
- logging operations

This prevents race conditions when multiple threads access shared data.

---

## Condition Variables

Condition variables allow threads to wait until it is safe to proceed.

Readers wait when:

- a writer is currently writing
- a writer is waiting to write

This guarantees **writer priority** and prevents writer starvation.

---

# Writer Priority

Writer priority ensures that writers cannot be indefinitely delayed.

When a writer intends to write:

1. It signals its intention.
2. New readers must wait.
3. The writer waits until all active readers finish.
4. The writer obtains exclusive access.
5. After writing, readers are allowed again.

---

# Load Balancing

To distribute readers evenly, the program keeps track of the number of readers per replica.

```
readersPerReplica[3]
```

When a reader begins reading:

1. The system checks how many readers are currently accessing each replica.
2. The reader selects the replica with the **smallest number of readers**.

Example:

```
Replica1 → 2 readers
Replica2 → 1 reader
Replica3 → 1 reader
```

The next reader will select **Replica2 or Replica3**.

This ensures balanced system usage.

---

# Logging

Every read or write operation generates a log entry written to:

```
log.txt
```

Each log entry includes:

- Operation type (READ or WRITE)
- Thread ID
- Replica accessed
- Number of readers per replica
- Whether the writer is active
- Current file contents

Example log entry:

```
Operation: READ
Thread ID: 4
Replica Accessed: replica2.txt

Readers per replica: [1,2,0]
Writer active: NO
```

Logging helps verify synchronization correctness and load balancing.

---

# Program Configuration

The following values can be modified at the top of the source code:

```cpp
const int REPLICA_COUNT = 3;
const int TOTAL_READERS = 18;
const int TOTAL_WRITES = 6;
```

These values control:

- number of replicas
- number of reader threads
- number of writer updates

---

# How the Program Works

1. The program initializes the replica files.
2. The writer thread starts running.
3. Reader threads spawn randomly.
4. Readers select replicas using load balancing.
5. The writer periodically updates all replicas.
6. Every operation is written to the log file.
7. The program finishes after all threads terminate.

---

# How to Compile

Use the following command to compile the program:

```bash
g++ main.cpp -o readers_writers -pthread
```

---

# How to Run

Run the program using:

```bash
./readers_writers
```

---

# Output Files

After running the program, the following files will be generated:

```
replica1.txt
replica2.txt
replica3.txt
log.txt
```

- The replica files contain the current shared content.
- The log file records all read and write operations.

---

# Correctness of the Solution

This implementation satisfies all assignment requirements:

- Thread-safe synchronization
- Writer priority over readers
- Balanced reader distribution
- Simultaneous replica updates
- Detailed logging of operations

---

# Conclusion

This project demonstrates an implementation of the **Readers–Writers problem with writer priority and load balancing**.

The system ensures safe concurrent access to shared resources while distributing reader load efficiently across file replicas. The use of synchronization primitives guarantees correct behavior under concurrent execution.
