import json
import struct
from typing import Any, BinaryIO, Generator

def parse_asar_header(stream: BinaryIO) -> tuple[dict[str, Any], int]:
    """Parse ASAR header from stream. Returns (header_json, base_data_offset)."""
    stream.seek(0)
    header_bytes = stream.read(16)
    if len(header_bytes) < 16:
        raise ValueError("Invalid ASAR header size")
    _, payload_size, _, json_size = struct.unpack("<IIII", header_bytes)
    json_bytes = stream.read(json_size)
    header = json.loads(json_bytes.decode("utf-8"))
    header_total = 8 + payload_size
    if header_total % 4 != 0:
        header_total += 4 - (header_total % 4)
    return header, header_total

def walk_asar_files(header_files: dict[str, Any], current_path: str = "") -> Generator[tuple[str, dict[str, Any]], None, None]:
    """Recursively yield (relative_path, info_dict) for files in ASAR directory tree."""
    for name, info in header_files.items():
        rel = f"{current_path}/{name}" if current_path else name
        if "files" in info:
            yield from walk_asar_files(info["files"], rel)
        else:
            yield rel, info

def read_asar_file(stream: BinaryIO, base_offset: int, file_info: dict[str, Any]) -> bytes | None:
    """Read file content bytes from ASAR stream given file info node."""
    if file_info.get("unpacked"):
        return None
    offset = int(file_info["offset"])
    size = file_info["size"]
    stream.seek(base_offset + offset)
    return stream.read(size)
