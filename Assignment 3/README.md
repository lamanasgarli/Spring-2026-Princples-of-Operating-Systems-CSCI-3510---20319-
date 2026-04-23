# 📁 README

## 🖥️ Assignment 3: File System Allocation Simulator

* * *

## 📌 Overview

This project is a simulation of file system allocation methods for a Principles of Operating Systems course assignment. The simulator models how an operating system manages files on disk, allocates and deallocates disk blocks, tracks free space, handles directory structures, supports hard and soft links, and records journaling information for important file operations.

🎯 The main objective of the project is to compare three file block allocation strategies:

-   📦 Contiguous Allocation
-   🔗 FAT (File Allocation Table)
-   📑 I-node Allocation

The simulator demonstrates their strengths and weaknesses in terms of:

-   ✔️ Allocation correctness
-   📉 External fragmentation
-   🧠 Memory overhead
-   ⚡ File access efficiency
-   🔄 Link behavior
-   📝 Journaling

* * *

## ⚙️ Features

This simulator includes:

-   💾 Disk simulation using fixed-size blocks
-   🧮 Free space management
-   📂 File system operations:
    -   MKDIR, CREATE, DELETE
    -   OPEN, CLOSE
    -   READ, WRITE
    -   HARDLINK, SOFTLINK
    -   LS, STAT
-   🌳 Hierarchical directory structure
-   🔗 Hard and soft links
-   📝 Basic journaling system
-   📊 Fragmentation & memory analysis

* * *

## 🧠 Allocation Methods

### 📦 1. Contiguous Allocation

Files are stored in consecutive disk blocks.

✅ Advantages:

-   Fast sequential access
-   Only one seek needed

❌ Disadvantages:

-   External fragmentation
-   Difficult to extend files

* * *

### 🔗 2. FAT (File Allocation Table)

Files are stored as linked blocks using a FAT table in memory.

✅ Advantages:

-   No need for contiguous space
-   Easy file growth

❌ Disadvantages:

-   High memory usage (FAT in RAM)
-   Slower access due to pointer traversal

* * *

### 📑 3. I-node Allocation

Each file has an i-node containing block pointers.

✅ Advantages:

-   Efficient structure
-   Loaded into memory only when file is open
-   Supports large files via indirect pointers

❌ Disadvantages:

-   More complex implementation
-   Indirect access adds overhead

* * *

## 📂 Directory & Link System

### 🌳 Directories

-   Supports hierarchical structure
-   Uses absolute paths

Examples:

-   `/docs`
-   `/docs/projects`
-   `/media/video.bin`

* * *

### 🔗 Hard Links

-   Multiple directory entries → same file
-   File exists until all links are deleted

* * *

### 🔗 Soft Links (Symbolic Links)

-   Stores path reference
-   Becomes ❌ broken if target is deleted

* * *

## 📝 Journaling

The system logs operations **before execution** (write-ahead logging).

Example (file deletion):

1.  Remove file from directory
2.  Decrease link count
3.  Free disk blocks

📌 This simulates real systems like NTFS/ext3.

* * *

## 📁 Project Structure

📄 filesystem\_simulator.py

Contains:

-   Disk simulation
-   Allocation algorithms
-   File & directory logic
-   Link handling
-   Journaling
-   Workload execution
-   Statistics

* * *

## 🧾 Requirements

-   🐍 Python 3.8+

No external libraries needed.

* * *

## ▶️ How to Run

### Step 1: Check Python

python --version

or

python3 --version

### Step 2: Run program

python filesystem\_simulator.py

* * *

## 🚀 Program Behavior

The simulator automatically runs for:

-   📦 CONTIGUOUS
-   🔗 FAT
-   📑 INODE

For each, it outputs:

-   📊 Disk usage
-   📉 Fragmentation stats
-   🧠 Memory overhead
-   📂 File info
-   🧾 Journal logs
-   🗺️ Disk map

* * *

## 💻 Supported Commands

### 📁 Directory

-   MKDIR /path
-   LS /path

### 📄 File

-   CREATE /path
-   DELETE /path
-   OPEN /path
-   CLOSE /path

### 📊 I/O

-   WRITE /path bytes
-   READ /path bytes

### 🔗 Links

-   HARDLINK target link
-   SOFTLINK target link

### 🔍 Info

-   STAT /path

* * *

## 🧪 Example Workload

The built-in workload demonstrates:

-   Directory creation
-   File operations
-   Read/write behavior
-   Hard & soft links
-   Deletion effects
-   Fragmentation creation

* * *

## 🏗️ Design Summary

### 💾 Disk

-   Linear array of blocks

### 📊 Free Space

-   Tracked via scanning
-   Fragmentation calculated

### 📄 File Metadata

Includes:

-   ID
-   Size
-   Block count
-   Open count
-   Link count

* * *

## 📊 Output & Analysis

The simulator reports:

-   Total / free blocks
-   Fragment count
-   Largest free block
-   Fragmentation ratio
-   FAT memory usage
-   Loaded i-nodes

👉 These are directly used in the report.

* * *

## 🎓 Educational Purpose

This is a **simulation**, not a real OS file system.

It is designed to:

-   Explain allocation strategies
-   Compare performance trade-offs
-   Demonstrate internal OS behavior

* * *

## ⚠️ Limitations

-   No real file content storage
-   Simplified journaling
-   Single indirect pointer only
-   Absolute paths only

* * *

## ✅ Assignment Coverage

✔ Disk simulation  
✔ All required operations  
✔ 3 allocation methods  
✔ Directory system  
✔ Hard & soft links  
✔ Correct deletion logic  
✔ Journaling  
✔ Fragmentation & memory analysis
