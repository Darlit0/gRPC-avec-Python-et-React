import hmac
import logging
import os
import time

import grpc
import jwt

JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", "3600"))
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-change-me-in-production-0123")

# Comptes de démonstration : "user:password,user2:password2"
DEMO_USERS = dict(
    entry.split(":", 1)
    for entry in os.environ.get("DEMO_USERS", "maxime:grpc,jorys:grpc").split(",")
    if ":" in entry
)

# Méthodes qui exigent un JWT valide dans la metadata "authorization"
PROTECTED_METHODS = {
    "/user.v1.UserService/CreateUsers",
    "/user.v1.UserService/SendChatMessage",
}

if JWT_SECRET == "dev-only-secret-change-me-in-production-0123":
    logging.getLogger(__name__).warning("JWT_SECRET non défini : secret de développement utilisé")


def check_credentials(username, password):
    expected = DEMO_USERS.get(username)
    return expected is not None and hmac.compare_digest(expected, password)


def issue_token(username):
    expires_at = int(time.time()) + JWT_TTL_SECONDS
    token = jwt.encode({"sub": username, "exp": expires_at}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at * 1000


def decode_token(token):
    """Retourne le username du token, ou lève jwt.InvalidTokenError."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])["sub"]


def _bearer_token(metadata):
    for key, value in metadata or ():
        if key == "authorization" and value.startswith("Bearer "):
            return value.removeprefix("Bearer ")
    return None


def username_from_context(context):
    """Utilisé par le servicer : l'intercepteur a déjà validé le token."""
    return decode_token(_bearer_token(context.invocation_metadata()))


def _deny(handler, code, details):
    def abort(_request, context):
        context.abort(code, details)

    if handler.request_streaming and handler.response_streaming:
        factory = grpc.stream_stream_rpc_method_handler
    elif handler.request_streaming:
        factory = grpc.stream_unary_rpc_method_handler
    elif handler.response_streaming:
        factory = grpc.unary_stream_rpc_method_handler
    else:
        factory = grpc.unary_unary_rpc_method_handler
    return factory(abort, handler.request_deserializer, handler.response_serializer)


class JwtAuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None or handler_call_details.method not in PROTECTED_METHODS:
            return handler

        token = _bearer_token(handler_call_details.invocation_metadata)
        if token is None:
            return _deny(handler, grpc.StatusCode.UNAUTHENTICATED, "Missing bearer token")
        try:
            decode_token(token)
        except jwt.ExpiredSignatureError:
            return _deny(handler, grpc.StatusCode.UNAUTHENTICATED, "Token expired")
        except jwt.InvalidTokenError:
            return _deny(handler, grpc.StatusCode.UNAUTHENTICATED, "Invalid token")
        return handler
