# 🧠 Memory Allocation and Management Simulator

## 📌 Overview

This project is a simulation of **contiguous memory management** in operating systems. It demonstrates how memory is dynamically allocated and deallocated for processes using different allocation strategies.

The simulator models a fixed-size physical memory and processes a sequence of allocation and termination operations. It tracks memory usage using a **Linked List** and visualizes how memory changes over time.

* * *

## 🎯 Objective

The main goal of this project is to:

-   Implement memory allocation algorithms used in operating systems
    
-   Simulate dynamic memory allocation and deallocation
    
-   Handle memory fragmentation and merging of free spaces (holes)
    
-   Compare the performance of different allocation strategies
    

* * *

## ⚙️ Features

-   Fixed-size memory simulation (default: 256 MB)
    
-   Linked List-based memory representation
    
-   Supports 4 allocation algorithms:
    
    -   First Fit
        
    -   Next Fit
        
    -   Best Fit
        
    -   Worst Fit
        
-   Dynamic allocation and deallocation of processes
    
-   Automatic merging of adjacent free memory blocks
    
-   Detailed logging after every operation
    
-   Summary statistics and fragmentation analysis
    
-   Input from file or built-in workload
    
-   Comparison of all algorithms in one run
    

* * *

## 🧩 Memory Representation

Memory is represented as a **Linked List**, where each node is a memory block.

Each block contains:

-   Start address
    
-   Size (in MB)
    
-   Status (Free or Allocated)
    
-   Process ID (if allocated)
    

### Example Memory State

    [A:40 MB] [B:25 MB] [Hole:191 MB]
    

* * *

## 🧠 Allocation Algorithms

### 1\. First Fit

-   Selects the first hole large enough
    
-   Fast but may cause fragmentation
    

### 2\. Next Fit

-   Similar to First Fit, but continues from last position
    
-   Slightly more efficient in some cases
    

### 3\. Best Fit

-   Chooses the smallest hole that fits the process
    
-   Minimizes leftover space but creates small fragments
    

### 4\. Worst Fit

-   Chooses the largest available hole
    
-   Leaves larger remaining holes
    

* * *

## 🔁 Operations

### Allocation

    ALLOCATE A 40
    

-   Allocates 40 MB for process A
    
-   Splits hole if needed
    

### Deallocation

    TERMINATE A
    

-   Frees memory used by process A
    
-   Merges adjacent holes
    

* * *

## 🧾 Logging

After each operation, memory state is printed:

    ======================================================================
    Algorithm : first_fit
    Operation : ALLOCATE A 40 MB -> SUCCESS
    Memory    : [A:40 MB] [Hole:216 MB]
    Detailed State:
      0- 39 MB : PROCESS A    | Size = 40 MB
     40-255 MB : HOLE         | Size = 216 MB
    ======================================================================
    

* * *

## 📊 Metrics & Analysis

At the end of execution, the simulator outputs:

-   Number of successful allocations
    
-   Number of failed allocations
    
-   Number of holes
    
-   Total free memory
    
-   Largest hole
    
-   Average hole size
    
-   External fragmentation ratio
    

* * *

## ▶️ How to Run

### 🔹 1. Requirements

-   Python 3.x installed
    

* * *

### 🔹 2. Run with default (built-in workload)

    python memory_manager.py
    

* * *

### 🔹 3. Run with specific algorithm

    python memory_manager.py --algorithm first_fit
    python memory_manager.py --algorithm next_fit
    python memory_manager.py --algorithm best_fit
    python memory_manager.py --algorithm worst_fit
    

* * *

### 🔹 4. Run all algorithms (recommended)

    python memory_manager.py --algorithm all
    

* * *

### 🔹 5. Run with custom memory size

    python memory_manager.py --algorithm all --memory 512
    

* * *

### 🔹 6. Run with input file

    python memory_manager.py --algorithm all --input input.txt
    

* * *

## 📄 Input File Format

Create a file like `input.txt`:

    ALLOCATE A 40
    ALLOCATE B 25
    ALLOCATE C 30
    TERMINATE B
    ALLOCATE D 10
    ALLOCATE E 15
    TERMINATE A
    ALLOCATE F 35
    TERMINATE C
    

### Rules:

-   One operation per line
    
-   Case-insensitive
    
-   Use:
    
    -   `ALLOCATE <ProcessID> <Size>`
        
    -   `TERMINATE <ProcessID>`
        

* * *

## 🔧 Implementation Details

### Data Structure

-   Doubly Linked List
    
-   Each node represents a memory block
    

### Key Functions

-   Allocation (with splitting)
    
-   Deallocation (with merging)
    
-   Hole detection
    
-   Algorithm selection logic
    
-   Logging system
    

* * *

## ⚠️ Edge Cases Handled

-   Allocation failure when no suitable hole exists
    
-   Duplicate process allocation
    
-   Termination of non-existing process
    
-   Proper merging of adjacent holes
    
-   Next Fit pointer tracking
    

* * *

## 📈 Comparison of Algorithms

The simulator allows comparison of:

| Algorithm | Speed | Fragmentation |
| --- | --- | --- |
| First Fit | Fast | Moderate |
| Next Fit | Faster | Slightly worse |
| Best Fit | Slow | High fragmentation |
| Worst Fit | Slow | Lower fragmentation |
    

* * *

## 🚀 Conclusion

This simulator demonstrates how different memory allocation strategies impact:

-   Memory utilization
    
-   Fragmentation
    
-   Allocation success rate
    

It provides a practical understanding of operating system memory management concepts through simulation.

* * *

