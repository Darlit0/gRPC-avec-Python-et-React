import userServiceModule from './proto/user_grpc_web_pb.js'

const grpcEndpoint = import.meta.env.VITE_GRPC_WEB_ENDPOINT || 'http://localhost:8080'

export const proto = userServiceModule
export const endpointLabel = grpcEndpoint.replace(/^https?:\/\//, '')
export const client = new userServiceModule.UserServiceClient(grpcEndpoint, null, null)

export function buildMetadata({ timeoutMs } = {}) {
  const metadata = { 'client-id': 'react-web' }
  if (timeoutMs) metadata['grpc-timeout'] = `${timeoutMs}m`
  return metadata
}
