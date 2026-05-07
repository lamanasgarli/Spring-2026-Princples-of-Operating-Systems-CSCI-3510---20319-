# Assignment 4: I/O Resource Manager and Deadlock Detection Simulator

## 📌 Project Title

# 

**I/O Resource Manager and Deadlock Detection Simulator**

* * *

## 👨‍💻 Course

# 

**Principles of Operating Systems - CSCI-3510**

* * *

## 🎯 Objective

# 

The objective of this assignment is to simulate how an operating system manages **I/O resources** and detects **deadlocks** between concurrent processes.

In real operating systems, processes often request exclusive access to I/O devices such as printers, scanners, USB drives, or Blu-ray recorders. These devices are usually **nonpreemptable**, meaning that once a process gets the device, the operating system cannot forcibly take it away without causing possible errors or data corruption.

This simulator models that situation by managing resource requests and releases. It also maintains a **Resource Allocation Graph** and uses a **cycle-detection algorithm** to determine whether the system has entered a deadlocked state.

* * *

## 🧠 Main Idea of the Project

# 

This program simulates:

✅ Processes requesting I/O resources  
✅ Processes releasing I/O resources  
✅ Resources being allocated if available  
✅ Processes becoming blocked if a resource is busy  
✅ A dynamic Resource Allocation Graph  
✅ Deadlock detection using graph cycle detection  
✅ Deadlock cycle reporting  
✅ Current system status printing

The simulator shows how deadlocks occur when several processes hold resources while waiting for other resources held by each other.

* * *

## 🖥️ Programming Language

# 

This project is implemented in:

**Python 3**

Python was chosen because it is readable, easy to test, and suitable for implementing graph-based algorithms clearly.

* * *

## 📂 Project Files

# 

The submission archive contains the following files:

    io_deadlock_simulator.py
    README.md
    written_report.pdf

### File Descriptions

# 

    io_deadlock_simulator.py

This is the main source code file. It contains the full simulator implementation, including:

-   Resource representation
-   Resource manager
-   Resource Allocation Graph
-   Deadlock detector
-   Input command processor
-   Interactive mode

    README.md

This file explains the project, how it works, how to run it, and how to test it.

    written_report.pdf

This is the written analysis report required by the assignment. It discusses deadlock conditions, I/O software layers, and the Ostrich Algorithm.

* * *

## ⚙️ How the Simulator Works

# 

The simulator reads a sequence of commands from an input file or from the terminal.

The main commands are:

    RESOURCE <resource_name> <type>
    REQUEST <process_id> <resource_name>
    RELEASE <process_id> <resource_name>
    STATUS
    DETECT
    END

Each command changes the state of the system.

For example:

    REQUEST P1 Printer

means that process `P1` is requesting the resource `Printer`.

If the printer is free, it is immediately allocated to `P1`.

If the printer is already held by another process, `P1` becomes blocked and waits for it. The simulator then runs deadlock detection.

* * *

## 🧱 Resource Representation

# 

The simulator supports two types of I/O resources:

### 1\. Block Devices

# 

Block devices transfer data in blocks.

Examples:

    BluRay
    USB

### 2\. Character Devices

# 

Character devices transfer data character by character or stream-based.

Examples:

    Printer
    Scanner

All resources in this simulator are treated as:

    Nonpreemptable resources with one instance each

This means only one process can hold a resource at a time.

* * *

## 🔒 Nonpreemptable Resources

# 

A nonpreemptable resource cannot be forcibly taken away from a process.

For example, if a process is using a printer, the operating system should not suddenly take the printer away and give it to another process. Doing so could corrupt the print job.

Because of this rule, a process must release the resource voluntarily.

This behavior is important because it allows deadlocks to occur.

* * *

## 🔁 Resource Allocation Graph

# 

The simulator maintains a dynamic **Resource Allocation Graph**.

The graph contains two types of nodes:

    Process nodes
    Resource nodes

In the source code, they are represented like this:

    P:P1
    P:P2
    R:Printer
    R:Scanner

* * *

## ➡️ Graph Edges

# 

The graph uses directed edges.

### Resource to Process Edge

# 

    R:Printer -> P:P1

This means:

    Printer is currently allocated to process P1.

### Process to Resource Edge

# 

    P:P2 -> R:Printer

This means:

    Process P2 is waiting for Printer.

* * *

## 🧩 Example Graph Situation

# 

Suppose we have:

    P1 holds BluRay
    P2 holds Scanner
    P1 waits for Scanner
    P2 waits for BluRay

The graph becomes:

    R:BluRay -> P:P1
    P:P1 -> R:Scanner
    R:Scanner -> P:P2
    P:P2 -> R:BluRay

This creates a cycle:

    P:P1 -> R:Scanner -> P:P2 -> R:BluRay -> P:P1

Because a cycle exists, the system is deadlocked.

* * *

## 🚨 Deadlock Detection

# 

The simulator runs deadlock detection after every resource request that cannot be immediately satisfied.

This means detection runs only when a process becomes blocked.

For example:

    REQUEST P1 Printer

If `Printer` is free, no deadlock detection is needed.

But if `Printer` is already held by another process, `P1` becomes blocked, and the simulator runs the graph cycle-detection algorithm.

* * *

## 🔍 Detection Algorithm

# 

The assignment requires a specific graph traversal algorithm.

The simulator follows this logic:

1.  For each node in the graph, start a traversal.
2.  Create an empty list called `L`.
3.  Mark all arcs as unmarked.
4.  Add the current node to `L`.
5.  If the current node appears twice in `L`, a cycle exists.
6.  If there is an unmarked outgoing arc, follow it.
7.  If there is no unmarked outgoing arc, backtrack.
8.  If the traversal returns to the initial node with no cycle found, continue with the next node.
9.  If any traversal finds a cycle, report a deadlock.

* * *

## ✅ Why Cycle Means Deadlock

# 

In a Resource Allocation Graph with one instance of each resource, a cycle means deadlock.

For example:

    P1 waits for a resource held by P2
    P2 waits for a resource held by P3
    P3 waits for a resource held by P1

No process can continue because each process is waiting for another process in the same cycle.

Therefore, the system is deadlocked.

* * *

## 🧪 How to Run the Program

### Step 1: Make sure Python is installed

# 

Check Python version:

    python --version

or:

    python3 --version

The program requires Python 3.

* * *

### Step 2: Save the source code

# 

Save the main source code as:

    io_deadlock_simulator.py

* * *

### Step 3: Create an input file

# 

Create a text file named:

    input.txt

Example content:

    RESOURCE BluRay BLOCK
    RESOURCE USB BLOCK
    RESOURCE Printer CHARACTER
    RESOURCE Scanner CHARACTER
    
    REQUEST P1 BluRay
    REQUEST P2 Scanner
    REQUEST P1 Scanner
    REQUEST P2 BluRay
    
    STATUS
    END

* * *

### Step 4: Run the simulator

# 

Use this command:

    python io_deadlock_simulator.py input.txt

or depending on your system:

    python3 io_deadlock_simulator.py input.txt

* * *

## 💬 Interactive Mode

# 

The program can also be run without an input file.

Command:

    python io_deadlock_simulator.py

Then commands can be typed manually:

    REQUEST P1 Printer
    REQUEST P2 Scanner
    STATUS
    END

This is useful for testing different cases quickly.

* * *

## 📝 Supported Commands

## 1\. RESOURCE Command

# 

    RESOURCE <resource_name> <type>

Defines a new resource.

The type must be either:

    BLOCK
    CHARACTER

Example:

    RESOURCE Printer CHARACTER
    RESOURCE USB BLOCK

If no resources are defined manually, the program automatically creates default resources:

    BluRay BLOCK
    USB BLOCK
    Printer CHARACTER
    Scanner CHARACTER

* * *

## 2\. REQUEST Command

# 

    REQUEST <process_id> <resource_name>

Requests a resource for a process.

Example:

    REQUEST P1 Printer

If the resource is free:

    [GRANTED] Printer was free and is now allocated to P1.

If the resource is busy:

    [BLOCKED] Printer is currently held by another process.

Then the simulator runs deadlock detection.

* * *

## 3\. RELEASE Command

# 

    RELEASE <process_id> <resource_name>

Releases a resource held by a process.

Example:

    RELEASE P1 Printer

If another process is waiting for that resource, the resource is automatically allocated to the next waiting process using FIFO order.

* * *

## 4\. STATUS Command

# 

    STATUS

Prints the current state of the system.

It displays:

✅ All resources  
✅ Which process holds each resource  
✅ Processes and their held resources  
✅ Processes and their waiting resources  
✅ Waiting queues  
✅ Resource Allocation Graph

* * *

## 5\. DETECT Command

# 

    DETECT

Manually runs the deadlock detection algorithm.

This is useful for testing.

* * *

## 6\. END Command

# 

    END

Stops the simulation.

* * *

## 🧪 Test Case 1 — No Deadlock

# 

Input:

    RESOURCE Printer CHARACTER
    RESOURCE Scanner CHARACTER
    REQUEST P1 Printer
    REQUEST P2 Scanner
    RELEASE P1 Printer
    STATUS
    END

Explanation:

    P1 gets Printer.
    P2 gets Scanner.
    P1 releases Printer.
    No process is waiting in a circular chain.

Expected result:

    No deadlock.

* * *

## 🧪 Test Case 2 — Deadlock Between Two Processes

# 

Input:

    RESOURCE BluRay BLOCK
    RESOURCE Scanner CHARACTER
    REQUEST P1 BluRay
    REQUEST P2 Scanner
    REQUEST P1 Scanner
    REQUEST P2 BluRay
    STATUS
    END

Explanation:

    P1 holds BluRay.
    P2 holds Scanner.
    P1 waits for Scanner.
    P2 waits for BluRay.

This creates the cycle:

    P:P1 -> R:Scanner -> P:P2 -> R:BluRay -> P:P1

Expected result:

    [DEADLOCK DETECTED]

* * *

## 🧪 Test Case 3 — Deadlock Among Three Processes

# 

Input:

    RESOURCE Printer CHARACTER
    RESOURCE Scanner CHARACTER
    RESOURCE USB BLOCK
    
    REQUEST P1 Printer
    REQUEST P2 Scanner
    REQUEST P3 USB
   
    REQUEST P1 Scanner
    REQUEST P2 USB
    REQUEST P3 Printer
    
    STATUS
    END

Explanation:

    P1 holds Printer and waits for Scanner.
    P2 holds Scanner and waits for USB.
    P3 holds USB and waits for Printer.

This creates the cycle:

    P1 -> Scanner -> P2 -> USB -> P3 -> Printer -> P1

Expected result:

    [DEADLOCK DETECTED]

* * *

## 🧪 Test Case 4 — Waiting Without Deadlock

# 

Input:

    RESOURCE Printer CHARACTE
    RRESOURCE Scanner CHARACTER
    
    REQUEST P1 Printer
    REQUEST P2 Printer
    REQUEST P3 Scanner
    
    STATUS
    END

Explanation:

    P1 holds Printer.
    P2 waits for Printer.
    P3 holds Scanner.

There is waiting, but no cycle.

Expected result:

    [NO DEADLOCK]

* * *

## 📤 Example Output

# 

Example input:

    RESOURCE BluRay BLOCK
    RESOURCE Scanner CHARACTER
    
    REQUEST P1 BluRay
    REQUEST P2 Scanner
    REQUEST P1 Scanner
    REQUEST P2 BluRay
    END

Possible output:

    [RESOURCE ADDED] BluRay as BLOCK
    [RESOURCE ADDED] Scanner as CHARACTER
    
    Step 1: REQUEST P1 BluRay
    [GRANTED] BluRay was free and is now allocated to P1.
    
    Step 2: REQUEST P2 Scanner
    [GRANTED] Scanner was free and is now allocated to P2.
    
    Step 3: REQUEST P1 Scanner
    [BLOCKED] Scanner is currently held by P2. P1 is now waiting.
    [NO DEADLOCK] No cycle found after this blocked request.
    
    Step 4: REQUEST P2 BluRay
    [BLOCKED] BluRay is currently held by P1. P2 is now waiting.
    [DEADLOCK DETECTED]
    Cycle:  
    P:P1 -> R:Scanner -> P:P2 -> R:BluRay -> P:P1
    
    Simulation ended.

* * *

## 🧠 Code Structure

# 

The source code is organized into several classes.

* * *

## 1\. Resource Class

# 

    Resource

Represents an I/O resource.

Each resource has:

    name
    resource_type

Example:

    Printer CHARACTER
    USB BLOCK

* * *

## 2\. ResourceAllocationGraph Class

# 

    ResourceAllocationGraph

Maintains the graph structure.

Responsibilities:

✅ Add process nodes  
✅ Add resource nodes  
✅ Add edges  
✅ Remove edges  
✅ Print graph  
✅ Return outgoing edges

This class represents the current state of allocations and waiting relationships.

* * *

## 3\. DeadlockDetector Class

# 

    DeadlockDetector

Implements the cycle-detection algorithm.

Responsibilities:

✅ Traverse graph from each node  
✅ Maintain current path list  
✅ Mark traversed arcs  
✅ Backtrack from dead ends  
✅ Detect repeated nodes  
✅ Return the deadlock cycle

This class is responsible for detecting whether the graph contains a cycle.

* * *

## 4\. IOResourceManager Class

# 

    IOResourceManager

This is the main logic manager.

Responsibilities:

✅ Add resources  
✅ Create processes  
✅ Handle requests  
✅ Handle releases  
✅ Manage waiting queues  
✅ Update the graph  
✅ Trigger deadlock detection  
✅ Print system status

This class simulates the resource management behavior of an operating system.

* * *

## 5\. Simulator Class

# 

    Simulator

Handles input commands.

Responsibilities:

✅ Read commands from file  
✅ Read commands interactively  
✅ Parse commands  
✅ Execute commands  
✅ Ignore comments and blank lines

* * *

## 🔄 Request Handling Logic

# 

When a process requests a resource, the simulator checks whether the resource is free.

### Case 1: Resource is free

# 

The resource is immediately allocated.

Graph edge added:

    Resource -> Process

Example:

    R:Printer -> P:P1

* * *

### Case 2: Resource is busy

# 

The process becomes blocked.

Graph edge added:

    Process -> Resource

Example:

    P:P2 -> R:Printer

Then the simulator runs deadlock detection.

* * *

## 🔓 Release Handling Logic

# 

When a process releases a resource:

1.  The allocation edge is removed.
2.  The resource becomes free.
3.  The simulator checks if any process is waiting for it.
4.  If yes, the resource is given to the next waiting process.
5.  The waiting edge is removed.
6.  A new allocation edge is added.

This allows the simulation to continue correctly after resources are released.

* * *

## 📊 Waiting Queue

# 

Each resource has a FIFO waiting queue.

FIFO means:

    First In, First Out

If multiple processes are waiting for the same resource, the process that requested it first gets it first after the resource is released.

Example:

    Printer waiting queue: P2, P3, P4

If `Printer` is released, it is given to `P2`.

* * *

## ⚡ Efficiency

# 

The graph is stored using an adjacency list.

This is efficient because each node only stores its outgoing edges.

The structure is:

    node -> set of outgoing nodes

This avoids unnecessary memory usage compared to an adjacency matrix.

The detector only runs after blocked requests, not after every successful request. This is efficient because a deadlock can only appear when a process starts waiting.

* * *

## 🧼 Error Handling

# 

The program handles common errors, such as:

❌ Requesting a resource that does not exist  
❌ Releasing a resource that the process does not hold  
❌ Duplicate resource definitions  
❌ Invalid command formats  
❌ Invalid resource types  
❌ Unknown commands

Example:

    REQUEST P1 Camera

If `Camera` does not exist, the program prints:

    [ERROR] Resource Camera does not exist.

* * *

## 💡 Comments in Input Files

# 

The simulator supports comments using `#`.

Example:

    # P1 requests the printer
    REQUEST P1 Printer

The program ignores everything after `#`.

Blank lines are also ignored.

* * *

## ✅ Assignment Requirements Checklist

# 

| Requirement | Status |
| --- | --- |
| Simulate I/O resources | ✅ Completed |
| Include block devices | ✅ Completed |
| Include character devices | ✅ Completed |
| Treat resources as nonpreemptable | ✅ Completed |
| One instance of each resource | ✅ Completed |
| Read requests and releases | ✅ Completed |
| Maintain Resource Allocation Graph | ✅ Completed |
| Use process and resource nodes | ✅ Completed |
| Add Resource → Process allocation arcs | ✅ Completed |
| Add Process → Resource waiting arcs | ✅ Completed |
| Run detection after blocked requests | ✅ Completed |
| Detect cycles | ✅ Completed |
| Backtrack from dead ends | ✅ Completed |
| Report deadlock cycle | ✅ Completed |
| Modular source code | ✅ Completed |
| Documented and readable code | ✅ Completed |

* * *

## 🏁 Conclusion

# 

This project successfully simulates an operating system resource manager for I/O devices. It models block and character devices as nonpreemptable resources with one instance each.

The simulator dynamically updates a Resource Allocation Graph whenever a process requests or releases a resource. When a process becomes blocked, the program runs a graph-based cycle detection algorithm to check whether the system has entered a deadlock state.

By showing allocations, waiting relationships, graph edges, and detected cycles, the program clearly demonstrates how deadlocks happen and how an operating system can detect them.
