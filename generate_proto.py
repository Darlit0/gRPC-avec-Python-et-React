from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROTO_DIR = ROOT / 'protos'
GENERATED_DIR = ROOT / 'generated'

GENERATED_DIR.mkdir(exist_ok=True)

cmd = [
    sys.executable,
    '-m',
    'grpc_tools.protoc',
    '--proto_path=protos',
    '--python_out=generated',
    '--pyi_out=generated',
    '--grpc_python_out=generated',
    'protos/user.proto',
]

subprocess.run(cmd, cwd=str(ROOT), check=True)

grpc_file = GENERATED_DIR / 'user_pb2_grpc.py'
text = grpc_file.read_text(encoding='utf-8')
old = "import user_pb2 as user__pb2"
new = "from . import user_pb2 as user__pb2"
if old in text and new not in text:
    grpc_file.write_text(text.replace(old, new), encoding='utf-8')

print('gRPC stubs regenerated successfully.')
