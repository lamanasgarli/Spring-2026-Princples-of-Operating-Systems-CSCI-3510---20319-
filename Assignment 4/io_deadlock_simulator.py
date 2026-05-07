"""
Assignment 4: I/O Resource Manager and Deadlock Detection Simulator

This program simulates management of nonpreemptable I/O resources and detects
deadlocks using a Resource Allocation Graph.

Author: Your Name
Course: Operating Systems

Supported commands in input file:

RESOURCE <resource_name> <type>
    Defines a resource.
    type can be BLOCK or CHARACTER.

REQUEST <process_id> <resource_name>
    Process requests a resource.

RELEASE <process_id> <resource_name>
    Process releases a resource.

STATUS
    Prints current system state.

DETECT
    Manually runs deadlock detection.

END
    Ends the simulation.

Example input:

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

If no RESOURCE commands are provided, the simulator automatically creates:
BluRay, USB, Printer, Scanner
"""

import sys
from collections import defaultdict, deque
from typing import Dict, Set, List, Tuple, Optional


class Resource:
    """
    Represents an I/O resource.

    All resources in this simulator are nonpreemptable and have exactly one instance.
    """

    def __init__(self, name: str, resource_type: str):
        self.name = name
        self.resource_type = resource_type.upper()

    def __str__(self):
        return f"{self.name} ({self.resource_type})"


class ResourceAllocationGraph:
    """
    Represents a dynamic Resource Allocation Graph.

    Nodes:
        Processes are represented as P:<process_id>
        Resources are represented as R:<resource_name>

    Edges:
        R -> P means the resource is currently allocated to the process.
        P -> R means the process is blocked and waiting for the resource.
    """

    def __init__(self):
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)

    @staticmethod
    def process_node(process_id: str) -> str:
        return f"P:{process_id}"

    @staticmethod
    def resource_node(resource_name: str) -> str:
        return f"R:{resource_name}"

    def add_node(self, node: str):
        if node not in self.adjacency:
            self.adjacency[node] = set()

    def add_edge(self, source: str, destination: str):
        self.add_node(source)
        self.add_node(destination)
        self.adjacency[source].add(destination)

    def remove_edge(self, source: str, destination: str):
        if source in self.adjacency:
            self.adjacency[source].discard(destination)

    def get_nodes(self) -> List[str]:
        nodes = set(self.adjacency.keys())

        for outgoing_nodes in self.adjacency.values():
            nodes.update(outgoing_nodes)

        return sorted(nodes)

    def get_outgoing(self, node: str) -> List[str]:
        return sorted(self.adjacency.get(node, set()))

    def has_edge(self, source: str, destination: str) -> bool:
        return destination in self.adjacency.get(source, set())

    def print_graph(self):
        print("\nResource Allocation Graph:")

        nodes = self.get_nodes()

        if not nodes:
            print("  Graph is empty.")
            return

        for node in nodes:
            outgoing = self.get_outgoing(node)

            if outgoing:
                for destination in outgoing:
                    print(f"  {node} -> {destination}")
            else:
                print(f"  {node} -> no outgoing edges")


class DeadlockDetector:
    """
    Implements the cycle detection algorithm described in the assignment.

    Algorithm idea:
        For each node N:
            Start with empty list L.
            Mark all arcs as unmarked.
            Traverse outgoing arcs using backtracking.
            If a node appears twice in L, a cycle exists.
    """

    def __init__(self, graph: ResourceAllocationGraph):
        self.graph = graph

    def detect_deadlock(self) -> Tuple[bool, List[str]]:
        """
        Runs deadlock detection from every node in the graph.

        Returns:
            (True, cycle) if a deadlock is detected.
            (False, []) otherwise.
        """

        for start_node in self.graph.get_nodes():
            found_cycle, cycle = self._search_from_node(start_node)

            if found_cycle:
                return True, cycle

        return False, []

    def _search_from_node(self, start_node: str) -> Tuple[bool, List[str]]:
        """
        Performs the required backtracking search from one starting node.

        This follows the assignment's logic:
            - L stores the current traversal path.
            - Arcs are marked after being chosen.
            - If the current node appears twice in L, a cycle is found.
            - If a dead end is reached, backtrack.
        """

        path: List[str] = []
        marked_arcs: Set[Tuple[str, str]] = set()

        current_node = start_node

        while True:
            path.append(current_node)

            if path.count(current_node) == 2:
                first_index = path.index(current_node)
                cycle = path[first_index:]
                return True, cycle

            outgoing_arcs = self.graph.get_outgoing(current_node)

            unmarked_outgoing = [
                destination
                for destination in outgoing_arcs
                if (current_node, destination) not in marked_arcs
            ]

            if unmarked_outgoing:
                next_node = unmarked_outgoing[0]
                marked_arcs.add((current_node, next_node))
                current_node = next_node
            else:
                if current_node == start_node:
                    return False, []

                path.pop()

                if not path:
                    return False, []

                current_node = path.pop()


class IOResourceManager:
    """
    Manages I/O resources, process requests, releases, waiting queues,
    and the resource allocation graph.
    """

    def __init__(self):
        self.resources: Dict[str, Resource] = {}

        self.processes: Set[str] = set()

        # resource_name -> process_id
        self.allocated_to: Dict[str, Optional[str]] = {}

        # process_id -> set of resource names
        self.held_resources: Dict[str, Set[str]] = defaultdict(set)

        # process_id -> set of resource names it is waiting for
        self.waiting_for: Dict[str, Set[str]] = defaultdict(set)

        # resource_name -> FIFO queue of waiting processes
        self.wait_queues: Dict[str, deque] = defaultdict(deque)

        self.graph = ResourceAllocationGraph()
        self.detector = DeadlockDetector(self.graph)

        self.step_counter = 0

    def add_default_resources_if_needed(self):
        """
        Adds default resources if no RESOURCE commands are found.
        This ensures the simulation includes both block and character devices.
        """

        if self.resources:
            return

        self.add_resource("BluRay", "BLOCK")
        self.add_resource("USB", "BLOCK")
        self.add_resource("Printer", "CHARACTER")
        self.add_resource("Scanner", "CHARACTER")

    def add_resource(self, resource_name: str, resource_type: str):
        resource_type = resource_type.upper()

        if resource_type not in {"BLOCK", "CHARACTER"}:
            raise ValueError(
                f"Invalid resource type '{resource_type}'. "
                "Use BLOCK or CHARACTER."
            )

        if resource_name in self.resources:
            print(f"[INFO] Resource {resource_name} already exists.")
            return

        self.resources[resource_name] = Resource(resource_name, resource_type)
        self.allocated_to[resource_name] = None

        resource_node = self.graph.resource_node(resource_name)
        self.graph.add_node(resource_node)

        print(f"[RESOURCE ADDED] {resource_name} as {resource_type}")

    def ensure_process_exists(self, process_id: str):
        if process_id not in self.processes:
            self.processes.add(process_id)
            process_node = self.graph.process_node(process_id)
            self.graph.add_node(process_node)

    def request_resource(self, process_id: str, resource_name: str):
        """
        Handles a process request.

        If the resource is free:
            Allocate it immediately and add R -> P edge.

        If the resource is busy:
            Block the process, add P -> R edge, and run deadlock detection.
        """

        self.step_counter += 1
        print(f"\nStep {self.step_counter}: REQUEST {process_id} {resource_name}")

        if resource_name not in self.resources:
            print(f"[ERROR] Resource {resource_name} does not exist.")
            return

        self.ensure_process_exists(process_id)

        process_node = self.graph.process_node(process_id)
        resource_node = self.graph.resource_node(resource_name)

        current_holder = self.allocated_to[resource_name]

        if current_holder is None:
            self.allocated_to[resource_name] = process_id
            self.held_resources[process_id].add(resource_name)
            self.graph.add_edge(resource_node, process_node)

            print(
                f"[GRANTED] {resource_name} was free and is now allocated to {process_id}."
            )
            return

        if current_holder == process_id:
            print(
                f"[INFO] {process_id} already holds {resource_name}. "
                "Duplicate request ignored."
            )
            return

        if resource_name in self.waiting_for[process_id]:
            print(
                f"[INFO] {process_id} is already waiting for {resource_name}. "
                "Duplicate waiting request ignored."
            )
            return

        self.waiting_for[process_id].add(resource_name)
        self.wait_queues[resource_name].append(process_id)
        self.graph.add_edge(process_node, resource_node)

        print(
            f"[BLOCKED] {resource_name} is currently held by {current_holder}. "
            f"{process_id} is now waiting."
        )

        deadlocked, cycle = self.detector.detect_deadlock()

        if deadlocked:
            print("[DEADLOCK DETECTED]")
            print("Cycle:")
            print("  " + " -> ".join(cycle))
        else:
            print("[NO DEADLOCK] No cycle found after this blocked request.")

    def release_resource(self, process_id: str, resource_name: str):
        """
        Handles a process releasing a resource.

        When a resource is released:
            - Remove R -> P edge.
            - If another process is waiting for it, allocate it to the next process.
            - Remove that process's P -> R waiting edge.
        """

        self.step_counter += 1
        print(f"\nStep {self.step_counter}: RELEASE {process_id} {resource_name}")

        if resource_name not in self.resources:
            print(f"[ERROR] Resource {resource_name} does not exist.")
            return

        self.ensure_process_exists(process_id)

        current_holder = self.allocated_to[resource_name]

        if current_holder != process_id:
            print(
                f"[ERROR] {process_id} cannot release {resource_name} "
                f"because it is held by {current_holder}."
            )
            return

        resource_node = self.graph.resource_node(resource_name)
        process_node = self.graph.process_node(process_id)

        self.graph.remove_edge(resource_node, process_node)
        self.allocated_to[resource_name] = None
        self.held_resources[process_id].discard(resource_name)

        print(f"[RELEASED] {process_id} released {resource_name}.")

        self._allocate_to_next_waiting_process(resource_name)

    def _allocate_to_next_waiting_process(self, resource_name: str):
        """
        Allocates a released resource to the next waiting process using FIFO order.
        """

        while self.wait_queues[resource_name]:
            next_process = self.wait_queues[resource_name].popleft()

            if resource_name not in self.waiting_for[next_process]:
                continue

            self.waiting_for[next_process].discard(resource_name)

            process_node = self.graph.process_node(next_process)
            resource_node = self.graph.resource_node(resource_name)

            self.graph.remove_edge(process_node, resource_node)

            self.allocated_to[resource_name] = next_process
            self.held_resources[next_process].add(resource_name)
            self.graph.add_edge(resource_node, process_node)

            print(
                f"[GRANTED AFTER RELEASE] {resource_name} is now allocated to {next_process}."
            )
            return

        print(f"[AVAILABLE] {resource_name} is now free.")

    def manual_deadlock_detection(self):
        """
        Runs deadlock detection manually.
        """

        self.step_counter += 1
        print(f"\nStep {self.step_counter}: DETECT")

        deadlocked, cycle = self.detector.detect_deadlock()

        if deadlocked:
            print("[DEADLOCK DETECTED]")
            print("Cycle:")
            print("  " + " -> ".join(cycle))
        else:
            print("[NO DEADLOCK] No cycle exists in the graph.")

    def print_status(self):
        """
        Prints resources, allocations, waiting processes, and graph state.
        """

        self.step_counter += 1
        print(f"\nStep {self.step_counter}: STATUS")

        print("\nResources:")
        for resource_name in sorted(self.resources):
            resource = self.resources[resource_name]
            holder = self.allocated_to[resource_name]

            if holder is None:
                print(f"  {resource} -> FREE")
            else:
                print(f"  {resource} -> held by {holder}")

        print("\nProcesses:")
        if not self.processes:
            print("  No processes created yet.")
        else:
            for process_id in sorted(self.processes):
                held = sorted(self.held_resources[process_id])
                waiting = sorted(self.waiting_for[process_id])

                held_text = ", ".join(held) if held else "none"
                waiting_text = ", ".join(waiting) if waiting else "none"

                print(
                    f"  {process_id}: "
                    f"holding [{held_text}], waiting for [{waiting_text}]"
                )

        print("\nWaiting Queues:")
        for resource_name in sorted(self.resources):
            queue = list(self.wait_queues[resource_name])
            queue_text = ", ".join(queue) if queue else "empty"
            print(f"  {resource_name}: {queue_text}")

        self.graph.print_graph()


class Simulator:
    """
    Reads and executes commands for the I/O Resource Manager.
    """

    def __init__(self):
        self.manager = IOResourceManager()
        self.resource_commands_seen = False

    def run_file(self, filename: str):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except FileNotFoundError:
            print(f"[ERROR] Input file not found: {filename}")
            return

        self._prepare_resources(lines)
        self._execute_lines(lines)

    def run_interactive(self):
        print("I/O Resource Manager and Deadlock Detection Simulator")
        print("Type commands manually. Type END to quit.")
        print("Example: REQUEST P1 Printer")

        self.manager.add_default_resources_if_needed()

        while True:
            try:
                line = input("> ")
            except EOFError:
                break

            should_continue = self._execute_line(line)

            if not should_continue:
                break

    def _prepare_resources(self, lines: List[str]):
        """
        First pass:
            Read RESOURCE commands before executing requests/releases.
        """

        for line in lines:
            clean_line = self._clean_line(line)

            if not clean_line:
                continue

            parts = clean_line.split()
            command = parts[0].upper()

            if command == "RESOURCE":
                if len(parts) != 3:
                    print(f"[ERROR] Invalid RESOURCE command: {line.strip()}")
                    continue

                _, resource_name, resource_type = parts
                self.manager.add_resource(resource_name, resource_type)
                self.resource_commands_seen = True

        self.manager.add_default_resources_if_needed()

    def _execute_lines(self, lines: List[str]):
        for line in lines:
            should_continue = self._execute_line(line)

            if not should_continue:
                break

    def _execute_line(self, line: str) -> bool:
        clean_line = self._clean_line(line)

        if not clean_line:
            return True

        parts = clean_line.split()
        command = parts[0].upper()

        try:
            if command == "RESOURCE":
                return True

            if command == "REQUEST":
                if len(parts) != 3:
                    print(f"[ERROR] Invalid REQUEST command: {clean_line}")
                    return True

                _, process_id, resource_name = parts
                self.manager.request_resource(process_id, resource_name)

            elif command == "RELEASE":
                if len(parts) != 3:
                    print(f"[ERROR] Invalid RELEASE command: {clean_line}")
                    return True

                _, process_id, resource_name = parts
                self.manager.release_resource(process_id, resource_name)

            elif command == "STATUS":
                self.manager.print_status()

            elif command == "DETECT":
                self.manager.manual_deadlock_detection()

            elif command == "END":
                print("\nSimulation ended.")
                return False

            else:
                print(f"[ERROR] Unknown command: {command}")

        except Exception as error:
            print(f"[ERROR] {error}")

        return True

    @staticmethod
    def _clean_line(line: str) -> str:
        """
        Removes comments and whitespace.

        Anything after # is treated as a comment.
        """

        return line.split("#", 1)[0].strip()


def print_usage():
    print("Usage:")
    print("  python io_deadlock_simulator.py <input_file>")
    print("  python io_deadlock_simulator.py")
    print()
    print("If no input file is provided, interactive mode starts.")


def main():
    simulator = Simulator()

    if len(sys.argv) == 1:
        simulator.run_interactive()

    elif len(sys.argv) == 2:
        filename = sys.argv[1]
        simulator.run_file(filename)

    else:
        print_usage()


if __name__ == "__main__":
    main()
