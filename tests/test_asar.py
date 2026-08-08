import io
import json
import struct
import unittest
from tifea.detector.asar import parse_asar_header, walk_asar_files, read_asar_file

def create_mock_asar(files: dict[str, bytes]) -> bytes:
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

class TestAsarParser(unittest.TestCase):
    def test_parse_and_extract_asar(self):
        asar_data = create_mock_asar({
            "package.json": b'{"name":"mockapp","version":"1.2.3"}',
            "resources/linux/code.png": b'\x89PNG\r\n\x1a\nfake_png_data'
        })
        stream = io.BytesIO(asar_data)
        header, base_offset = parse_asar_header(stream)
        files = dict(walk_asar_files(header.get("files", {})))

        self.assertIn("package.json", files)
        self.assertIn("resources/linux/code.png", files)

        pkg_bytes = read_asar_file(stream, base_offset, files["package.json"])
        self.assertEqual(pkg_bytes, b'{"name":"mockapp","version":"1.2.3"}')

        img_bytes = read_asar_file(stream, base_offset, files["resources/linux/code.png"])
        self.assertEqual(img_bytes, b'\x89PNG\r\n\x1a\nfake_png_data')

if __name__ == '__main__':
    unittest.main()
