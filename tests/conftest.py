import io
import json
import struct
import tarfile
import pytest

@pytest.fixture
def mock_asar_builder():
    def _create(files: dict[str, bytes]) -> bytes:
        tree = {}
        current_offset = 0
        payload_parts = []
        for path_str, content in files.items():
            parts = path_str.split('/')
            curr = tree
            for part in parts[:-1]:
                if part not in curr:
                    curr[part] = {"files": {}}
                curr = curr[part]["files"]
            filename = parts[-1]
            curr[filename] = {"size": len(content), "offset": str(current_offset)}
            payload_parts.append(content)
            current_offset += len(content)

        header_obj = {"files": tree}
        json_bytes = json.dumps(header_obj).encode('utf-8')
        json_len = len(json_bytes)
        payload_size = 8 + json_len
        header_bytes = struct.pack("<IIII", 4, payload_size, 4 + json_len, json_len) + json_bytes
        padding_len = (4 - (len(header_bytes) % 4)) % 4
        header_bytes += b'\x00' * padding_len
        return header_bytes + b''.join(payload_parts)
    return _create
