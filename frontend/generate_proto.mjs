import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const frontendRoot = dirname(fileURLToPath(import.meta.url))
const protoRoot = resolve(frontendRoot, '../protos')
const outputRoot = resolve(frontendRoot, 'src/proto')
const protoc = resolve(frontendRoot, 'node_modules/.bin/grpc_tools_node_protoc')
const grpcWebPlugin = resolve(frontendRoot, 'node_modules/.bin/protoc-gen-grpc-web')

await mkdir(outputRoot, { recursive: true })

const result = spawnSync(protoc, [
  `--plugin=protoc-gen-grpc-web=${grpcWebPlugin}`,
  `--proto_path=${protoRoot}`,
  '--js_out=import_style=commonjs:src/proto',
  '--grpc-web_out=import_style=commonjs,mode=grpcwebtext:src/proto',
  resolve(protoRoot, 'user.proto'),
], { cwd: frontendRoot, stdio: 'inherit' })

if (result.status !== 0) process.exit(result.status ?? 1)

const messageStub = resolve(outputRoot, 'user_pb.js')
const source = await readFile(messageStub, 'utf8')
await writeFile(messageStub, source.replace('goog.object.extend(exports, proto.user.v1);', 'module.exports = proto.user.v1;'))
console.log('Frontend gRPC-Web stubs regenerated successfully.')