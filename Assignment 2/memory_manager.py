from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
import argparse
import copy


@dataclass
class MemoryBlock:
    start: int
    size: int
    is_free: bool = True
    process_id: Optional[str] = None
    prev: Optional["MemoryBlock"] = None
    next: Optional["MemoryBlock"] = None

    def end(self) -> int:
        return self.start + self.size - 1

    def label(self) -> str:
        if self.is_free:
            return f"Hole({self.size} MB)"
        return f"{self.process_id}({self.size} MB)"


class MemoryManager:
    def __init__(self, total_memory: int, algorithm: str):
        self.total_memory = total_memory
        self.algorithm = algorithm.lower().strip()

        if self.algorithm not in {"first_fit", "next_fit", "best_fit", "worst_fit"}:
            raise ValueError(
                "Algorithm must be one of: first_fit, next_fit, best_fit, worst_fit"
            )

        # Memory starts as one large free hole
        self.head = MemoryBlock(start=0, size=total_memory, is_free=True, process_id=None)

        # Used by next fit
        self.last_position: MemoryBlock = self.head

        # Statistics
        self.successful_allocations = 0
        self.failed_allocations = 0
        self.deallocations = 0

    # ----------------------------
    # Linked-list helper functions
    # ----------------------------
    def _iter_blocks(self):
        current = self.head
        while current:
            yield current
            current = current.next

    def _find_process_block(self, process_id: str) -> Optional[MemoryBlock]:
        for block in self._iter_blocks():
            if not block.is_free and block.process_id == process_id:
                return block
        return None

    def _replace_block(self, old_block: MemoryBlock, new_block: MemoryBlock) -> None:
        new_block.prev = old_block.prev
        new_block.next = old_block.next

        if old_block.prev:
            old_block.prev.next = new_block
        else:
            self.head = new_block

        if old_block.next:
            old_block.next.prev = new_block

    def _insert_after(self, block: MemoryBlock, new_block: MemoryBlock) -> None:
        new_block.prev = block
        new_block.next = block.next
        if block.next:
            block.next.prev = new_block
        block.next = new_block

    def _merge_with_next(self, block: MemoryBlock) -> None:
        nxt = block.next
        if nxt and block.is_free and nxt.is_free:
            block.size += nxt.size
            block.next = nxt.next
            if nxt.next:
                nxt.next.prev = block

            # If next-fit pointer points to removed block, move it safely
            if self.last_position is nxt:
                self.last_position = block

    def _coalesce(self, block: MemoryBlock) -> MemoryBlock:
        """
        Merge adjacent free holes around the given block.
        Returns the final merged block.
        """
        if not block.is_free:
            return block

        # Merge with previous if previous is free
        if block.prev and block.prev.is_free:
            prev_block = block.prev
            prev_block.size += block.size
            prev_block.next = block.next
            if block.next:
                block.next.prev = prev_block

            if self.last_position is block:
                self.last_position = prev_block

            block = prev_block

        # Merge repeatedly with next free blocks
        while block.next and block.next.is_free:
            self._merge_with_next(block)

        return block

    # ----------------------------
    # Allocation strategy functions
    # ----------------------------
    def _find_hole_first_fit(self, requested_size: int) -> Optional[MemoryBlock]:
        for block in self._iter_blocks():
            if block.is_free and block.size >= requested_size:
                return block
        return None

    def _find_hole_best_fit(self, requested_size: int) -> Optional[MemoryBlock]:
        best = None
        for block in self._iter_blocks():
            if block.is_free and block.size >= requested_size:
                if best is None or block.size < best.size:
                    best = block
        return best

    def _find_hole_worst_fit(self, requested_size: int) -> Optional[MemoryBlock]:
        worst = None
        for block in self._iter_blocks():
            if block.is_free and block.size >= requested_size:
                if worst is None or block.size > worst.size:
                    worst = block
        return worst

    def _find_hole_next_fit(self, requested_size: int) -> Optional[MemoryBlock]:
        if self.last_position is None:
            self.last_position = self.head

        start = self.last_position
        current = start

        while True:
            if current.is_free and current.size >= requested_size:
                return current

            current = current.next if current.next else self.head

            if current is start:
                break

        return None

    def _find_suitable_hole(self, requested_size: int) -> Optional[MemoryBlock]:
        if self.algorithm == "first_fit":
            return self._find_hole_first_fit(requested_size)
        if self.algorithm == "next_fit":
            return self._find_hole_next_fit(requested_size)
        if self.algorithm == "best_fit":
            return self._find_hole_best_fit(requested_size)
        if self.algorithm == "worst_fit":
            return self._find_hole_worst_fit(requested_size)
        return None

    # ----------------------------
    # Core operations
    # ----------------------------
    def allocate(self, process_id: str, requested_size: int) -> bool:
        if requested_size <= 0:
            print(f"[ERROR] Allocation size for {process_id} must be positive.")
            return False

        if self._find_process_block(process_id):
            print(f"[ERROR] Process {process_id} is already allocated.")
            return False

        hole = self._find_suitable_hole(requested_size)

        if hole is None:
            self.failed_allocations += 1
            self._log_operation(
                f"ALLOCATE {process_id} {requested_size} MB -> FAILED (No suitable hole)"
            )
            return False

        if hole.size == requested_size:
            hole.is_free = False
            hole.process_id = process_id

            if self.algorithm == "next_fit":
                self.last_position = hole.next if hole.next else self.head

        else:
            # Split the hole into allocated block + remaining free hole
            allocated_block = MemoryBlock(
                start=hole.start,
                size=requested_size,
                is_free=False,
                process_id=process_id
            )

            remaining_hole = MemoryBlock(
                start=hole.start + requested_size,
                size=hole.size - requested_size,
                is_free=True,
                process_id=None
            )

            # Link them in place of original hole
            allocated_block.prev = hole.prev
            allocated_block.next = remaining_hole

            remaining_hole.prev = allocated_block
            remaining_hole.next = hole.next

            if hole.prev:
                hole.prev.next = allocated_block
            else:
                self.head = allocated_block

            if hole.next:
                hole.next.prev = remaining_hole

            if self.algorithm == "next_fit":
                self.last_position = remaining_hole

        self.successful_allocations += 1
        self._log_operation(f"ALLOCATE {process_id} {requested_size} MB -> SUCCESS")
        return True

    def deallocate(self, process_id: str) -> bool:
        block = self._find_process_block(process_id)

        if block is None:
            self._log_operation(f"TERMINATE {process_id} -> FAILED (Process not found)")
            return False

        block.is_free = True
        block.process_id = None
        merged_block = self._coalesce(block)

        if self.algorithm == "next_fit":
            self.last_position = merged_block

        self.deallocations += 1
        self._log_operation(f"TERMINATE {process_id} -> SUCCESS")
        return True

    # ----------------------------
    # Logging and reporting
    # ----------------------------
    def memory_state_line(self) -> str:
        parts = []
        for block in self._iter_blocks():
            if block.is_free:
                parts.append(f"[Hole:{block.size} MB]")
            else:
                parts.append(f"[{block.process_id}:{block.size} MB]")
        return " ".join(parts)

    def detailed_memory_state(self) -> str:
        lines = []
        for block in self._iter_blocks():
            block_type = "HOLE" if block.is_free else f"PROCESS {block.process_id}"
            lines.append(
                f"{block.start:>3}-{block.end():>3} MB : {block_type:<12} | Size = {block.size} MB"
            )
        return "\n".join(lines)

    def _log_operation(self, operation: str) -> None:
        print("=" * 70)
        print(f"Algorithm : {self.algorithm}")
        print(f"Operation : {operation}")
        print("Memory    :", self.memory_state_line())
        print("Detailed State:")
        print(self.detailed_memory_state())
        print("=" * 70)
        print()

    def metrics(self) -> Dict[str, float]:
        holes = []
        total_free = 0

        for block in self._iter_blocks():
            if block.is_free:
                holes.append(block.size)
                total_free += block.size

        number_of_holes = len(holes)
        largest_hole = max(holes) if holes else 0
        average_hole_size = (sum(holes) / len(holes)) if holes else 0

        # A simple external fragmentation indicator:
        # if total free exists but the largest hole is much smaller than total free,
        # fragmentation is more severe.
        external_fragmentation_ratio = 0.0
        if total_free > 0:
            external_fragmentation_ratio = 1 - (largest_hole / total_free)

        return {
            "total_free_memory": total_free,
            "number_of_holes": number_of_holes,
            "largest_hole": largest_hole,
            "average_hole_size": average_hole_size,
            "successful_allocations": self.successful_allocations,
            "failed_allocations": self.failed_allocations,
            "deallocations": self.deallocations,
            "external_fragmentation_ratio": external_fragmentation_ratio,
        }

    def print_summary(self) -> None:
        m = self.metrics()
        print(f"\nSUMMARY FOR {self.algorithm.upper()}")
        print("-" * 40)
        print(f"Successful allocations     : {m['successful_allocations']}")
        print(f"Failed allocations         : {m['failed_allocations']}")
        print(f"Deallocations              : {m['deallocations']}")
        print(f"Total free memory          : {m['total_free_memory']} MB")
        print(f"Number of holes            : {m['number_of_holes']}")
        print(f"Largest hole               : {m['largest_hole']} MB")
        print(f"Average hole size          : {m['average_hole_size']:.2f} MB")
        print(f"External fragmentation     : {m['external_fragmentation_ratio']:.4f}")
        print()

    # ----------------------------
    # Workload execution
    # ----------------------------
    def execute_workload(self, operations: List[Tuple]) -> None:
        for op in operations:
            command = op[0].upper()

            if command == "ALLOCATE":
                if len(op) != 3:
                    print(f"[ERROR] Invalid ALLOCATE operation format: {op}")
                    continue
                process_id = str(op[1])
                size = int(op[2])
                self.allocate(process_id, size)

            elif command == "TERMINATE":
                if len(op) != 2:
                    print(f"[ERROR] Invalid TERMINATE operation format: {op}")
                    continue
                process_id = str(op[1])
                self.deallocate(process_id)

            else:
                print(f"[ERROR] Unknown command: {op}")


# ---------------------------------
# Workload parsing
# ---------------------------------
def parse_workload_file(filename: str) -> List[Tuple]:
    """
    Supported input file format (one operation per line):
        ALLOCATE A 12
        ALLOCATE B 30
        TERMINATE A

    Blank lines and lines starting with # are ignored.
    """
    operations = []

    with open(filename, "r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()
            command = parts[0].upper()

            if command == "ALLOCATE":
                if len(parts) != 3:
                    raise ValueError(
                        f"Invalid ALLOCATE format on line {line_number}: {raw_line.strip()}"
                    )
                process_id = parts[1]
                size = int(parts[2])
                operations.append(("ALLOCATE", process_id, size))

            elif command == "TERMINATE":
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid TERMINATE format on line {line_number}: {raw_line.strip()}"
                    )
                process_id = parts[1]
                operations.append(("TERMINATE", process_id))

            else:
                raise ValueError(
                    f"Unknown command on line {line_number}: {raw_line.strip()}"
                )

    return operations


def sample_workload() -> List[Tuple]:
    """
    Built-in sample workload if no input file is provided.
    """
    return [
        ("ALLOCATE", "A", 40),
        ("ALLOCATE", "B", 25),
        ("ALLOCATE", "C", 30),
        ("TERMINATE", "B"),
        ("ALLOCATE", "D", 10),
        ("ALLOCATE", "E", 15),
        ("TERMINATE", "A"),
        ("ALLOCATE", "F", 35),
        ("TERMINATE", "C"),
        ("ALLOCATE", "G", 20),
        ("ALLOCATE", "H", 18),
        ("TERMINATE", "D"),
        ("TERMINATE", "E"),
        ("ALLOCATE", "I", 22),
    ]


# ---------------------------------
# Running and comparing algorithms
# ---------------------------------
def run_single_algorithm(total_memory: int, algorithm: str, operations: List[Tuple]) -> None:
    manager = MemoryManager(total_memory=total_memory, algorithm=algorithm)
    manager.execute_workload(operations)
    manager.print_summary()


def compare_all_algorithms(total_memory: int, operations: List[Tuple]) -> None:
    algorithms = ["first_fit", "next_fit", "best_fit", "worst_fit"]
    results = {}

    for algo in algorithms:
        print("\n" + "#" * 80)
        print(f"RUNNING SIMULATION WITH {algo.upper()}")
        print("#" * 80 + "\n")

        manager = MemoryManager(total_memory=total_memory, algorithm=algo)
        manager.execute_workload(operations)
        manager.print_summary()
        results[algo] = manager.metrics()

    print("\n" + "=" * 90)
    print("FINAL COMPARISON")
    print("=" * 90)
    print(
        f"{'Algorithm':<12} | {'Success':<7} | {'Failed':<6} | {'Holes':<5} | "
        f"{'Largest Hole':<12} | {'Total Free':<10} | {'Frag. Ratio':<11}"
    )
    print("-" * 90)

    for algo, m in results.items():
        print(
            f"{algo:<12} | "
            f"{m['successful_allocations']:<7} | "
            f"{m['failed_allocations']:<6} | "
            f"{m['number_of_holes']:<5} | "
            f"{m['largest_hole']:<12} | "
            f"{m['total_free_memory']:<10} | "
            f"{m['external_fragmentation_ratio']:<11.4f}"
        )
    print("=" * 90)


# ---------------------------------
# Main
# ---------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Memory Allocation and Management Simulator"
    )
    parser.add_argument(
        "--memory",
        type=int,
        default=256,
        help="Total physical memory size in MB (default: 256)"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="first_fit",
        choices=["first_fit", "next_fit", "best_fit", "worst_fit", "all"],
        help="Allocation algorithm to use"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to workload input file"
    )

    args = parser.parse_args()

    if args.input:
        operations = parse_workload_file(args.input)
    else:
        operations = sample_workload()

    if args.algorithm == "all":
        compare_all_algorithms(args.memory, operations)
    else:
        run_single_algorithm(args.memory, args.algorithm, operations)


if __name__ == "__main__":
    main()
