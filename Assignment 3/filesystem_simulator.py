from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union


# ============================================================
# Utility Exceptions
# ============================================================

class FileSystemError(Exception):
    """Base class for file system related errors."""


class PathResolutionError(FileSystemError):
    """Raised when a path cannot be resolved."""


class AllocationError(FileSystemError):
    """Raised when allocation fails."""


class FileOpenError(FileSystemError):
    """Raised when file open/close logic fails."""


# ============================================================
# Journal
# ============================================================

class Journal:
    """
    Basic write-ahead log.
    We log intended operations before executing them.
    """

    def __init__(self) -> None:
        self.entries: List[str] = []

    def log(self, entry: str) -> None:
        self.entries.append(entry)

    def dump(self) -> None:
        print("\n=== JOURNAL LOG ===")
        for i, entry in enumerate(self.entries, start=1):
            print(f"{i:03d}: {entry}")


# ============================================================
# Disk and Free Space Management
# ============================================================

class Disk:
    """
    Simulate a disk as a linear sequence of fixed-size blocks.
    We do not store actual file bytes in detail; we simulate block ownership.
    """

    def __init__(self, total_blocks: int, block_size: int = 4096) -> None:
        self.total_blocks = total_blocks
        self.block_size = block_size
        self.blocks: List[Optional[str]] = [None] * total_blocks  # owner tag

    def mark_allocated(self, block_indices: List[int], owner: str) -> None:
        for idx in block_indices:
            if idx < 0 or idx >= self.total_blocks:
                raise AllocationError(f"Invalid block index {idx}.")
            if self.blocks[idx] is not None:
                raise AllocationError(f"Block {idx} is already allocated.")
            self.blocks[idx] = owner

    def mark_free(self, block_indices: List[int]) -> None:
        for idx in block_indices:
            if idx < 0 or idx >= self.total_blocks:
                raise AllocationError(f"Invalid block index {idx}.")
            self.blocks[idx] = None

    def free_blocks(self) -> List[int]:
        return [i for i, owner in enumerate(self.blocks) if owner is None]

    def count_free(self) -> int:
        return sum(1 for b in self.blocks if b is None)

    def count_used(self) -> int:
        return self.total_blocks - self.count_free()

    def contiguous_free_runs(self) -> List[Tuple[int, int]]:
        """
        Return list of (start, length) for free runs.
        """
        runs: List[Tuple[int, int]] = []
        start = None

        for i, blk in enumerate(self.blocks):
            if blk is None and start is None:
                start = i
            elif blk is not None and start is not None:
                runs.append((start, i - start))
                start = None

        if start is not None:
            runs.append((start, self.total_blocks - start))

        return runs

    def fragmentation_stats(self) -> Dict[str, Union[int, float]]:
        """
        External fragmentation view:
        - number of free fragments (runs)
        - largest free run
        - free blocks
        - fragmentation ratio:
          if free blocks exist, ratio = 1 - largest_run / free_blocks
        """
        runs = self.contiguous_free_runs()
        free_blocks = self.count_free()
        num_fragments = len(runs)
        largest_run = max((length for _, length in runs), default=0)
        frag_ratio = 0.0
        if free_blocks > 0:
            frag_ratio = 1.0 - (largest_run / free_blocks)

        return {
            "free_blocks": free_blocks,
            "num_free_fragments": num_fragments,
            "largest_free_run": largest_run,
            "external_fragmentation_ratio": round(frag_ratio, 4),
        }

    def dump_map(self, width: int = 64) -> None:
        """
        Show disk map: '.' free, '#' used.
        """
        print("\n=== DISK MAP ===")
        line = []
        for i, blk in enumerate(self.blocks):
            line.append('.' if blk is None else '#')
            if (i + 1) % width == 0:
                print(''.join(line))
                line = []
        if line:
            print(''.join(line))


# ============================================================
# File System Nodes
# ============================================================

@dataclass
class FileMetadata:
    """
    Represents a real file object.
    For hard links, multiple directory entries can point to the same FileMetadata.
    """
    file_id: int
    name: str
    strategy_name: str
    size_bytes: int = 0
    block_count: int = 0
    open_count: int = 0
    link_count: int = 1

    # Contiguous allocation metadata
    contiguous_start: Optional[int] = None

    # FAT allocation metadata
    fat_start: Optional[int] = None
    fat_blocks: List[int] = field(default_factory=list)

    # Inode allocation metadata
    inode_direct_blocks: List[int] = field(default_factory=list)
    inode_indirect_pointer_block: Optional[int] = None
    inode_indirect_data_blocks: List[int] = field(default_factory=list)
    inode_loaded_in_memory: bool = False

    def owner_tag(self) -> str:
        return f"FILE:{self.file_id}"


@dataclass
class Directory:
    name: str
    parent: Optional["Directory"] = None
    entries: Dict[str, Union["Directory", "HardLinkEntry", "SoftLinkEntry"]] = field(default_factory=dict)

    def path(self) -> str:
        if self.parent is None:
            return "/"
        parts = []
        cur: Optional[Directory] = self
        while cur and cur.parent is not None:
            parts.append(cur.name)
            cur = cur.parent
        return "/" + "/".join(reversed(parts))


@dataclass
class HardLinkEntry:
    """
    A directory entry pointing to a real file metadata object.
    """
    name: str
    target: FileMetadata


@dataclass
class SoftLinkEntry:
    """
    A symbolic link is a separate file-like entry storing a target path.
    If target disappears, it becomes broken.
    """
    name: str
    target_path: str


# ============================================================
# Allocation Strategies
# ============================================================

class BaseAllocator:
    def __init__(self, disk: Disk):
        self.disk = disk

    def allocate(self, file_meta: FileMetadata, num_blocks: int) -> List[int]:
        raise NotImplementedError

    def free(self, file_meta: FileMetadata) -> None:
        raise NotImplementedError

    def extend(self, file_meta: FileMetadata, additional_blocks: int) -> List[int]:
        raise NotImplementedError

    def get_file_blocks(self, file_meta: FileMetadata) -> List[int]:
        raise NotImplementedError

    def memory_overhead_bytes(self) -> int:
        return 0

    def stats(self) -> Dict[str, Union[int, float]]:
        return {}


class ContiguousAllocator(BaseAllocator):
    """
    Allocate files in contiguous chunks.
    """

    def allocate(self, file_meta: FileMetadata, num_blocks: int) -> List[int]:
        if num_blocks == 0:
            return []

        runs = self.disk.contiguous_free_runs()
        for start, length in runs:
            if length >= num_blocks:
                blocks = list(range(start, start + num_blocks))
                self.disk.mark_allocated(blocks, file_meta.owner_tag())
                file_meta.contiguous_start = start
                return blocks

        raise AllocationError("Contiguous allocation failed: no sufficiently large free run.")

    def free(self, file_meta: FileMetadata) -> None:
        blocks = self.get_file_blocks(file_meta)
        self.disk.mark_free(blocks)
        file_meta.contiguous_start = None

    def extend(self, file_meta: FileMetadata, additional_blocks: int) -> List[int]:
        if additional_blocks == 0:
            return self.get_file_blocks(file_meta)

        current_blocks = self.get_file_blocks(file_meta)
        if not current_blocks:
            return self.allocate(file_meta, additional_blocks)

        start = file_meta.contiguous_start
        assert start is not None

        next_block = start + len(current_blocks)
        needed = list(range(next_block, next_block + additional_blocks))

        if any(b >= self.disk.total_blocks for b in needed):
            raise AllocationError("Contiguous extension failed: disk boundary reached.")

        if any(self.disk.blocks[b] is not None for b in needed):
            raise AllocationError("Contiguous extension failed: adjacent space unavailable (external fragmentation).")

        self.disk.mark_allocated(needed, file_meta.owner_tag())
        return current_blocks + needed

    def get_file_blocks(self, file_meta: FileMetadata) -> List[int]:
        if file_meta.block_count == 0 or file_meta.contiguous_start is None:
            return []
        return list(range(file_meta.contiguous_start, file_meta.contiguous_start + file_meta.block_count))

    def stats(self) -> Dict[str, Union[int, float]]:
        return self.disk.fragmentation_stats()


class FATAllocator(BaseAllocator):
    """
    Linked list allocation using an in-memory FAT table.
    Directory stores only the first block.
    The whole FAT table remains in memory.
    """
    END = -1
    FREE = None

    def __init__(self, disk: Disk):
        super().__init__(disk)
        self.fat_table: List[Optional[int]] = [self.FREE] * disk.total_blocks
        self.pointer_size_bytes = 4

    def _allocate_individual_blocks(self, owner: str, count: int) -> List[int]:
        free = self.disk.free_blocks()
        if len(free) < count:
            raise AllocationError("FAT allocation failed: not enough free blocks.")
        chosen = free[:count]
        self.disk.mark_allocated(chosen, owner)
        return chosen

    def allocate(self, file_meta: FileMetadata, num_blocks: int) -> List[int]:
        if num_blocks == 0:
            return []

        blocks = self._allocate_individual_blocks(file_meta.owner_tag(), num_blocks)

        for i in range(len(blocks) - 1):
            self.fat_table[blocks[i]] = blocks[i + 1]
        self.fat_table[blocks[-1]] = self.END

        file_meta.fat_start = blocks[0]
        file_meta.fat_blocks = blocks[:]
        return blocks

    def free(self, file_meta: FileMetadata) -> None:
        blocks = self.get_file_blocks(file_meta)
        for b in blocks:
            self.fat_table[b] = self.FREE
        self.disk.mark_free(blocks)
        file_meta.fat_start = None
        file_meta.fat_blocks.clear()

    def extend(self, file_meta: FileMetadata, additional_blocks: int) -> List[int]:
        if additional_blocks == 0:
            return self.get_file_blocks(file_meta)

        if file_meta.block_count == 0:
            return self.allocate(file_meta, additional_blocks)

        new_blocks = self._allocate_individual_blocks(file_meta.owner_tag(), additional_blocks)

        if not file_meta.fat_blocks:
            raise AllocationError("FAT metadata corrupted: missing block list.")

        last_old = file_meta.fat_blocks[-1]
        self.fat_table[last_old] = new_blocks[0]

        for i in range(len(new_blocks) - 1):
            self.fat_table[new_blocks[i]] = new_blocks[i + 1]
        self.fat_table[new_blocks[-1]] = self.END

        file_meta.fat_blocks.extend(new_blocks)
        return file_meta.fat_blocks[:]

    def get_file_blocks(self, file_meta: FileMetadata) -> List[int]:
        return file_meta.fat_blocks[:]

    def memory_overhead_bytes(self) -> int:
        # Entire FAT table must remain in memory
        return len(self.fat_table) * self.pointer_size_bytes

    def stats(self) -> Dict[str, Union[int, float]]:
        return {
            "fat_table_entries": len(self.fat_table),
            "fat_memory_overhead_bytes": self.memory_overhead_bytes(),
        }


class InodeAllocator(BaseAllocator):
    """
    I-node allocation:
    - direct block pointers
    - one indirect pointer block that points to more data blocks
    The inode only needs to be loaded in memory when the file is open.
    """
    def __init__(self, disk: Disk, num_direct_pointers: int = 4):
        super().__init__(disk)
        self.num_direct_pointers = num_direct_pointers
        self.pointer_size_bytes = 4
        self.loaded_inode_count = 0

    def _allocate_free_blocks(self, owner: str, count: int) -> List[int]:
        free = self.disk.free_blocks()
        if len(free) < count:
            raise AllocationError("I-node allocation failed: not enough free blocks.")
        chosen = free[:count]
        self.disk.mark_allocated(chosen, owner)
        return chosen

    def load_inode(self, file_meta: FileMetadata) -> None:
        if not file_meta.inode_loaded_in_memory:
            file_meta.inode_loaded_in_memory = True
            self.loaded_inode_count += 1

    def unload_inode(self, file_meta: FileMetadata) -> None:
        if file_meta.inode_loaded_in_memory:
            file_meta.inode_loaded_in_memory = False
            self.loaded_inode_count -= 1

    def allocate(self, file_meta: FileMetadata, num_blocks: int) -> List[int]:
        if num_blocks == 0:
            return []

        blocks_to_allocate = self._allocate_free_blocks(file_meta.owner_tag(), num_blocks)
        self._attach_blocks_to_inode(file_meta, blocks_to_allocate)
        return self.get_file_blocks(file_meta)

    def extend(self, file_meta: FileMetadata, additional_blocks: int) -> List[int]:
        if additional_blocks == 0:
            return self.get_file_blocks(file_meta)

        if file_meta.block_count == 0:
            return self.allocate(file_meta, additional_blocks)

        new_blocks = self._allocate_free_blocks(file_meta.owner_tag(), additional_blocks)
        self._attach_blocks_to_inode(file_meta, new_blocks)
        return self.get_file_blocks(file_meta)

    def _attach_blocks_to_inode(self, file_meta: FileMetadata, blocks: List[int]) -> None:
        for blk in blocks:
            if len(file_meta.inode_direct_blocks) < self.num_direct_pointers:
                file_meta.inode_direct_blocks.append(blk)
            else:
                if file_meta.inode_indirect_pointer_block is None:
                    pointer_block = self._allocate_free_blocks(file_meta.owner_tag(), 1)[0]
                    file_meta.inode_indirect_pointer_block = pointer_block
                file_meta.inode_indirect_data_blocks.append(blk)

    def free(self, file_meta: FileMetadata) -> None:
        blocks = self.get_file_blocks(file_meta)
        if file_meta.inode_indirect_pointer_block is not None:
            blocks.append(file_meta.inode_indirect_pointer_block)

        self.disk.mark_free(blocks)
        file_meta.inode_direct_blocks.clear()
        file_meta.inode_indirect_data_blocks.clear()
        file_meta.inode_indirect_pointer_block = None

    def get_file_blocks(self, file_meta: FileMetadata) -> List[int]:
        return file_meta.inode_direct_blocks[:] + file_meta.inode_indirect_data_blocks[:]

    def memory_overhead_bytes(self) -> int:
        # Only loaded inodes count as active memory overhead here
        inode_size_estimate = 128
        return self.loaded_inode_count * inode_size_estimate

    def stats(self) -> Dict[str, Union[int, float]]:
        return {
            "loaded_inodes": self.loaded_inode_count,
            "inode_memory_overhead_bytes": self.memory_overhead_bytes(),
            "num_direct_pointers": self.num_direct_pointers,
        }


# ============================================================
# File System Core
# ============================================================

class FileSystemSimulator:
    """
    One file system simulator instance runs ONE allocation strategy.
    """

    def __init__(self, strategy_name: str, total_blocks: int = 128, block_size: int = 4096):
        self.strategy_name = strategy_name.upper()
        self.disk = Disk(total_blocks=total_blocks, block_size=block_size)
        self.journal = Journal()
        self.root = Directory(name="/", parent=None)
        self.next_file_id = 1

        if self.strategy_name == "CONTIGUOUS":
            self.allocator: BaseAllocator = ContiguousAllocator(self.disk)
        elif self.strategy_name == "FAT":
            self.allocator = FATAllocator(self.disk)
        elif self.strategy_name == "INODE":
            self.allocator = InodeAllocator(self.disk, num_direct_pointers=4)
        else:
            raise ValueError("Unknown strategy. Use CONTIGUOUS, FAT, or INODE.")

    # --------------------------------------------------------
    # Path Helpers
    # --------------------------------------------------------

    def _normalize_path(self, path: str) -> str:
        if not path.startswith("/"):
            raise PathResolutionError("Only absolute paths are supported.")
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return path

    def _split_path(self, path: str) -> List[str]:
        path = self._normalize_path(path)
        if path == "/":
            return []
        return [p for p in path.split("/") if p]

    def _get_dir(self, path: str) -> Directory:
        path = self._normalize_path(path)
        if path == "/":
            return self.root

        parts = self._split_path(path)
        cur: Directory = self.root

        for part in parts:
            node = cur.entries.get(part)
            if not isinstance(node, Directory):
                raise PathResolutionError(f"Directory not found: {path}")
            cur = node

        return cur

    def _get_parent_dir_and_name(self, path: str) -> Tuple[Directory, str]:
        path = self._normalize_path(path)
        if path == "/":
            raise PathResolutionError("Root has no parent.")
        parts = self._split_path(path)
        parent_path_parts = parts[:-1]
        name = parts[-1]

        cur = self.root
        for part in parent_path_parts:
            node = cur.entries.get(part)
            if not isinstance(node, Directory):
                raise PathResolutionError(f"Parent directory does not exist for path: {path}")
            cur = node

        return cur, name

    def _resolve_entry(
        self,
        path: str,
        follow_soft_links: bool = True,
        max_symlink_depth: int = 10
    ) -> Union[Directory, HardLinkEntry, SoftLinkEntry]:
        path = self._normalize_path(path)
        if path == "/":
            return self.root

        parts = self._split_path(path)
        cur: Directory = self.root
        resolved_path = "/"

        for i, part in enumerate(parts):
            if part not in cur.entries:
                raise PathResolutionError(f"Path does not exist: {path}")

            entry = cur.entries[part]
            is_last = (i == len(parts) - 1)

            if isinstance(entry, Directory):
                cur = entry
                resolved_path = os.path.join(resolved_path, part).replace("\\", "/")
            elif isinstance(entry, HardLinkEntry):
                if not is_last:
                    raise PathResolutionError(f"Cannot descend into file path: {path}")
                return entry
            elif isinstance(entry, SoftLinkEntry):
                if not follow_soft_links:
                    if not is_last:
                        raise PathResolutionError(f"Cannot descend through unresolved symlink: {path}")
                    return entry

                if max_symlink_depth <= 0:
                    raise PathResolutionError("Too many symbolic link resolutions.")

                target = entry.target_path
                if is_last:
                    return self._resolve_entry(target, follow_soft_links=True, max_symlink_depth=max_symlink_depth - 1)
                else:
                    # Resolve target directory then continue remaining path
                    remaining = "/" + "/".join(parts[i + 1:]) if i + 1 < len(parts) else ""
                    new_path = (target + remaining) if target != "/" else remaining or "/"
                    return self._resolve_entry(new_path, follow_soft_links=True, max_symlink_depth=max_symlink_depth - 1)
            else:
                raise PathResolutionError("Unknown directory entry type encountered.")

        return cur

    def _resolve_file_metadata(self, path: str) -> FileMetadata:
        entry = self._resolve_entry(path, follow_soft_links=True)
        if isinstance(entry, HardLinkEntry):
            return entry.target
        raise PathResolutionError(f"Path is not a file: {path}")

    # --------------------------------------------------------
    # Directory Operations
    # --------------------------------------------------------

    def mkdir(self, path: str) -> None:
        parent, name = self._get_parent_dir_and_name(path)
        if name in parent.entries:
            raise FileSystemError(f"Entry already exists: {path}")
        parent.entries[name] = Directory(name=name, parent=parent)
        self.journal.log(f"MKDIR intent: create directory {path}")

    # --------------------------------------------------------
    # File Operations
    # --------------------------------------------------------

    def create(self, path: str) -> None:
        parent, name = self._get_parent_dir_and_name(path)
        if name in parent.entries:
            raise FileSystemError(f"Entry already exists: {path}")

        file_meta = FileMetadata(
            file_id=self.next_file_id,
            name=name,
            strategy_name=self.strategy_name
        )
        self.next_file_id += 1

        parent.entries[name] = HardLinkEntry(name=name, target=file_meta)
        self.journal.log(f"CREATE intent: create file {path}")

    def open(self, path: str) -> None:
        file_meta = self._resolve_file_metadata(path)
        file_meta.open_count += 1

        if self.strategy_name == "INODE":
            assert isinstance(self.allocator, InodeAllocator)
            self.allocator.load_inode(file_meta)

        self.journal.log(f"OPEN intent: open file {path}")

    def close(self, path: str) -> None:
        file_meta = self._resolve_file_metadata(path)
        if file_meta.open_count <= 0:
            raise FileOpenError(f"File is not open: {path}")

        file_meta.open_count -= 1

        if self.strategy_name == "INODE" and file_meta.open_count == 0:
            assert isinstance(self.allocator, InodeAllocator)
            self.allocator.unload_inode(file_meta)

        self.journal.log(f"CLOSE intent: close file {path}")

    def write(self, path: str, num_bytes: int) -> None:
        if num_bytes < 0:
            raise FileSystemError("Write size cannot be negative.")

        file_meta = self._resolve_file_metadata(path)
        old_blocks = file_meta.block_count
        old_size = file_meta.size_bytes

        new_size = old_size + num_bytes
        required_blocks = math.ceil(new_size / self.disk.block_size)
        additional_blocks = required_blocks - old_blocks

        self.journal.log(
            f"WRITE intent: path={path}, bytes={num_bytes}, old_size={old_size}, new_size={new_size}, "
            f"additional_blocks={additional_blocks}"
        )

        if additional_blocks > 0:
            if old_blocks == 0:
                self.allocator.allocate(file_meta, additional_blocks)
            else:
                self.allocator.extend(file_meta, additional_blocks)

        file_meta.size_bytes = new_size
        file_meta.block_count = required_blocks

    def read(self, path: str, num_bytes: int) -> None:
        if num_bytes < 0:
            raise FileSystemError("Read size cannot be negative.")

        file_meta = self._resolve_file_metadata(path)
        readable = min(num_bytes, file_meta.size_bytes)
        blocks = self.allocator.get_file_blocks(file_meta)

        self.journal.log(
            f"READ intent: path={path}, requested={num_bytes}, readable={readable}, blocks={blocks}"
        )

        print(
            f"[READ] path={path}, requested={num_bytes}, readable={readable}, "
            f"blocks_accessed={blocks}"
        )

        if self.strategy_name == "CONTIGUOUS" and blocks:
            print("        Contiguous allocation note: excellent sequential read performance (one initial seek).")
        elif self.strategy_name == "FAT" and blocks:
            print("        FAT allocation note: may require following block chain through FAT table.")
        elif self.strategy_name == "INODE" and blocks:
            print("        I-node allocation note: block addresses resolved via direct/indirect inode pointers.")

    def delete(self, path: str) -> None:
        """
        Deletion behavior:
        - Remove directory entry
        - Decrement hard link count
        - If count reaches zero:
            - file must not be open
            - release blocks
            - release metadata
        Soft links only remove the symlink itself.
        """
        parent, name = self._get_parent_dir_and_name(path)
        if name not in parent.entries:
            raise PathResolutionError(f"Entry not found: {path}")

        entry = parent.entries[name]

        # Write-ahead log entries
        self.journal.log(f"DELETE intent step 1: remove directory entry {path}")

        if isinstance(entry, Directory):
            if entry.entries:
                raise FileSystemError("Cannot delete non-empty directory.")
            del parent.entries[name]
            self.journal.log(f"DELETE commit: directory removed {path}")
            return

        if isinstance(entry, SoftLinkEntry):
            del parent.entries[name]
            self.journal.log(f"DELETE commit: soft link removed {path}")
            return

        if isinstance(entry, HardLinkEntry):
            file_meta = entry.target

            # Step 1: remove directory entry
            del parent.entries[name]

            # Step 2: decrease link count / release inode if needed
            self.journal.log(f"DELETE intent step 2: decrease link count for file_id={file_meta.file_id}")
            file_meta.link_count -= 1

            if file_meta.link_count > 0:
                self.journal.log(
                    f"DELETE commit: file data preserved because hard links remain "
                    f"(file_id={file_meta.file_id}, remaining_links={file_meta.link_count})"
                )
                return

            # Final removal only when no hard links remain
            if file_meta.open_count > 0:
                raise FileSystemError("Cannot fully delete a file that is still open.")

            self.journal.log(f"DELETE intent step 3: free blocks for file_id={file_meta.file_id}")
            self.allocator.free(file_meta)
            file_meta.size_bytes = 0
            file_meta.block_count = 0
            self.journal.log(f"DELETE commit: file fully removed file_id={file_meta.file_id}")
            return

        raise FileSystemError("Unknown entry type during delete.")

    def hardlink(self, target_path: str, link_path: str) -> None:
        file_meta = self._resolve_file_metadata(target_path)
        parent, name = self._get_parent_dir_and_name(link_path)
        if name in parent.entries:
            raise FileSystemError(f"Entry already exists: {link_path}")

        parent.entries[name] = HardLinkEntry(name=name, target=file_meta)
        file_meta.link_count += 1
        self.journal.log(
            f"HARDLINK intent: create hard link {link_path} -> file_id={file_meta.file_id} ({target_path})"
        )

    def softlink(self, target_path: str, link_path: str) -> None:
        parent, name = self._get_parent_dir_and_name(link_path)
        if name in parent.entries:
            raise FileSystemError(f"Entry already exists: {link_path}")

        parent.entries[name] = SoftLinkEntry(name=name, target_path=target_path)
        self.journal.log(f"SOFTLINK intent: create symlink {link_path} -> {target_path}")

    # --------------------------------------------------------
    # Information / Reporting
    # --------------------------------------------------------

    def stat_file(self, path: str) -> None:
        entry = self._resolve_entry(path, follow_soft_links=False)

        if isinstance(entry, Directory):
            print(f"[STAT] {path} is a directory")
            return

        if isinstance(entry, SoftLinkEntry):
            print(f"[STAT] {path} is a soft link -> {entry.target_path}")
            try:
                target_meta = self._resolve_file_metadata(path)
                print(f"       target file_id={target_meta.file_id} is accessible")
            except FileSystemError:
                print(f"       target is BROKEN / inaccessible")
            return

        if isinstance(entry, HardLinkEntry):
            file_meta = entry.target
            blocks = self.allocator.get_file_blocks(file_meta)
            print(
                f"[STAT] file={path}, file_id={file_meta.file_id}, size={file_meta.size_bytes} bytes, "
                f"blocks={blocks}, link_count={file_meta.link_count}, open_count={file_meta.open_count}"
            )

    def ls(self, path: str = "/") -> None:
        directory = self._get_dir(path)
        print(f"\n[LS] {path}")
        for name, entry in sorted(directory.entries.items()):
            if isinstance(entry, Directory):
                print(f"  <DIR>  {name}")
            elif isinstance(entry, HardLinkEntry):
                print(f"  <FILE> {name}  -> file_id={entry.target.file_id}")
            elif isinstance(entry, SoftLinkEntry):
                print(f"  <SYML> {name}  -> {entry.target_path}")

    def print_summary(self) -> None:
        print("\n" + "=" * 60)
        print(f"FILE SYSTEM SUMMARY ({self.strategy_name})")
        print("=" * 60)

        print(f"Disk total blocks: {self.disk.total_blocks}")
        print(f"Disk used blocks : {self.disk.count_used()}")
        print(f"Disk free blocks : {self.disk.count_free()}")

        disk_stats = self.disk.fragmentation_stats()
        allocator_stats = self.allocator.stats()

        print("\nDisk / Fragmentation Stats:")
        for k, v in disk_stats.items():
            print(f"  {k}: {v}")

        print("\nAllocator Stats:")
        if allocator_stats:
            for k, v in allocator_stats.items():
                print(f"  {k}: {v}")
        else:
            print("  (no extra allocator-specific stats)")

        print(f"\nGeneral memory overhead estimate: {self.allocator.memory_overhead_bytes()} bytes")

    # --------------------------------------------------------
    # Workload Parsing
    # --------------------------------------------------------

    def execute_command(self, line: str) -> None:
        """
        Supported commands:
          MKDIR /dir
          CREATE /dir/file
          OPEN /dir/file
          CLOSE /dir/file
          WRITE /dir/file 9000
          READ /dir/file 4096
          DELETE /dir/file
          HARDLINK /dir/file /dir/file_hard
          SOFTLINK /dir/file /dir/file_soft
          LS /dir
          STAT /dir/file
        """
        line = line.strip()
        if not line or line.startswith("#"):
            return

        parts = line.split()
        cmd = parts[0].upper()

        try:
            if cmd == "MKDIR":
                if len(parts) != 2:
                    raise FileSystemError("Usage: MKDIR /path")
                self.mkdir(parts[1])

            elif cmd == "CREATE":
                if len(parts) != 2:
                    raise FileSystemError("Usage: CREATE /path")
                self.create(parts[1])

            elif cmd == "OPEN":
                if len(parts) != 2:
                    raise FileSystemError("Usage: OPEN /path")
                self.open(parts[1])

            elif cmd == "CLOSE":
                if len(parts) != 2:
                    raise FileSystemError("Usage: CLOSE /path")
                self.close(parts[1])

            elif cmd == "WRITE":
                if len(parts) != 3:
                    raise FileSystemError("Usage: WRITE /path num_bytes")
                self.write(parts[1], int(parts[2]))

            elif cmd == "READ":
                if len(parts) != 3:
                    raise FileSystemError("Usage: READ /path num_bytes")
                self.read(parts[1], int(parts[2]))

            elif cmd == "DELETE":
                if len(parts) != 2:
                    raise FileSystemError("Usage: DELETE /path")
                self.delete(parts[1])

            elif cmd == "HARDLINK":
                if len(parts) != 3:
                    raise FileSystemError("Usage: HARDLINK target_path link_path")
                self.hardlink(parts[1], parts[2])

            elif cmd == "SOFTLINK":
                if len(parts) != 3:
                    raise FileSystemError("Usage: SOFTLINK target_path link_path")
                self.softlink(parts[1], parts[2])

            elif cmd == "LS":
                if len(parts) == 1:
                    self.ls("/")
                elif len(parts) == 2:
                    self.ls(parts[1])
                else:
                    raise FileSystemError("Usage: LS [/path]")

            elif cmd == "STAT":
                if len(parts) != 2:
                    raise FileSystemError("Usage: STAT /path")
                self.stat_file(parts[1])

            else:
                raise FileSystemError(f"Unknown command: {cmd}")

        except Exception as e:
            print(f"[ERROR] {line} -> {e}")

    def execute_workload(self, workload_lines: List[str]) -> None:
        for line in workload_lines:
            self.execute_command(line)


# ============================================================
# Demonstration / Sample Workload
# ============================================================

def demo_workload() -> List[str]:
    """
    Sample workload used to demonstrate all required behaviors.
    You can replace this with reading from a text file.
    """
    return [
        "# Create directories",
        "MKDIR /docs",
        "MKDIR /docs/projects",
        "MKDIR /media",

        "# Create files",
        "CREATE /docs/projects/report.txt",
        "CREATE /media/video.bin",

        "# Open/write/read",
        "OPEN /docs/projects/report.txt",
        "WRITE /docs/projects/report.txt 6000",
        "READ /docs/projects/report.txt 4000",
        "CLOSE /docs/projects/report.txt",

        "OPEN /media/video.bin",
        "WRITE /media/video.bin 25000",
        "READ /media/video.bin 10000",
        "CLOSE /media/video.bin",

        "# Hard and soft links",
        "HARDLINK /docs/projects/report.txt /docs/projects/report_hard.txt",
        "SOFTLINK /docs/projects/report.txt /docs/projects/report_soft.txt",

        "STAT /docs/projects/report.txt",
        "STAT /docs/projects/report_hard.txt",
        "STAT /docs/projects/report_soft.txt",

        "# Deletion behavior",
        "DELETE /docs/projects/report.txt",
        "STAT /docs/projects/report_hard.txt",
        "STAT /docs/projects/report_soft.txt",

        "# Delete hard link too, now original data removed",
        "DELETE /docs/projects/report_hard.txt",
        "STAT /docs/projects/report_soft.txt",

        "# Additional file activity to show fragmentation behavior",
        "CREATE /docs/a.bin",
        "CREATE /docs/b.bin",
        "CREATE /docs/c.bin",
        "WRITE /docs/a.bin 9000",
        "WRITE /docs/b.bin 12000",
        "WRITE /docs/c.bin 5000",
        "DELETE /docs/b.bin",
        "LS /docs",
    ]


def run_simulation(strategy_name: str) -> None:
    print("\n" + "#" * 70)
    print(f"RUNNING FILE SYSTEM SIMULATION WITH STRATEGY: {strategy_name}")
    print("#" * 70)

    fs = FileSystemSimulator(strategy_name=strategy_name, total_blocks=64, block_size=4096)
    fs.execute_workload(demo_workload())
    fs.print_summary()
    fs.disk.dump_map()
    fs.journal.dump()


if __name__ == "__main__":
    # Run all three allocation strategies for comparison
    for strategy in ["CONTIGUOUS", "FAT", "INODE"]:
        run_simulation(strategy)
