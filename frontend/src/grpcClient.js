import userServiceModule from './proto/user_grpc_web_pb.js'

const grpcEndpoint = import.meta.env.VITE_GRPC_WEB_ENDPOINT || 'http://localhost:8080'

export const proto = userServiceModule
export const endpointLabel = grpcEndpoint.replace(/^https?:\/\//, '')
export const client = new userServiceModule.UserServiceClient(grpcEndpoint, null, null)

// Salon de chat : Envoy l'utilise pour router toutes les requêtes du chat vers la même réplique
export const CHAT_ROOM = 'general'

// Codes gRPC utiles côté UI (https://grpc.io/docs/guides/status-codes/)
export const StatusCode = {
  CANCELLED: 1,
  INVALID_ARGUMENT: 3,
  DEADLINE_EXCEEDED: 4,
  NOT_FOUND: 5,
  UNAUTHENTICATED: 16,
  UNAVAILABLE: 14,
}

export function buildMetadata({ timeoutMs, token, chatRoom } = {}) {
  const metadata = { 'client-id': 'react-web' }
  if (timeoutMs) metadata['grpc-timeout'] = `${timeoutMs}m`
  if (token) metadata.authorization = `Bearer ${token}`
  if (chatRoom) metadata['x-chat-room'] = chatRoom
  return metadata
}

// Traduit une erreur gRPC en message lisible pour l'utilisateur
export function describeGrpcError(error) {
  switch (error?.code) {
    case StatusCode.DEADLINE_EXCEEDED:
      return 'Le serveur a mis trop de temps à répondre (deadline dépassée).'
    case StatusCode.UNAUTHENTICATED:
      return `Authentification requise : ${error.message}`
    case StatusCode.INVALID_ARGUMENT:
      return `Requête invalide : ${error.message}`
    case StatusCode.NOT_FOUND:
      return `Introuvable : ${error.message}`
    case StatusCode.UNAVAILABLE:
      return 'Service indisponible : vérifiez que le serveur Python et Envoy sont démarrés.'
    default:
      return error?.message || 'Erreur inconnue'
  }
}
