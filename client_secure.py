"""Client Python en TLS (ou mTLS) + JWT.

Serveur :
  scripts/generate_certs.sh
  TLS_CERT_FILE=certs/server.crt TLS_KEY_FILE=certs/server.key uv run python server.py
  # mTLS : ajouter TLS_CLIENT_CA_FILE=certs/ca.crt
Client :
  uv run python client_secure.py          # TLS
  uv run python client_secure.py --mtls   # mTLS
"""
import sys
from pathlib import Path

import grpc

from generated import user_pb2, user_pb2_grpc

CERTS = Path(__file__).resolve().parent / "certs"


def channel_credentials(use_mtls):
    ca = (CERTS / "ca.crt").read_bytes()
    if not use_mtls:
        return grpc.ssl_channel_credentials(root_certificates=ca)
    return grpc.ssl_channel_credentials(
        root_certificates=ca,
        private_key=(CERTS / "client.key").read_bytes(),
        certificate_chain=(CERTS / "client.crt").read_bytes(),
    )


with grpc.secure_channel("localhost:50051", channel_credentials("--mtls" in sys.argv)) as channel:
    stub = user_pb2_grpc.UserServiceStub(channel)

    info = stub.GetServerInfo(user_pb2.ServerInfoRequest(), timeout=2)
    print(f"Connecté à {info.hostname} (TLS : {info.tls_enabled})")

    token = stub.Login(user_pb2.LoginRequest(username="maxime", password="grpc"), timeout=2).token
    auth_metadata = (("authorization", f"Bearer {token}"),)

    response = stub.SendChatMessage(user_pb2.ChatMessage(text="Bonjour en TLS"), metadata=auth_metadata, timeout=2)
    print(f"Message diffusé à {response.subscriber_count} abonné(s)")
