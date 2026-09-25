import subprocess
import tempfile
import threading
import time
from pathlib import Path

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from generated import user_pb2, user_pb2_grpc
import server as backend

ROOT = Path(__file__).resolve().parent


def start_server(credentials=None):
    """Démarre un serveur en mémoire sur un port libre (pas besoin de lancer server.py)."""
    grpc_server, _, port = backend.build_server("localhost:0", credentials)
    grpc_server.start()
    return grpc_server, f"localhost:{port}"


def login(stub, username="maxime", password="grpc"):
    return stub.Login(user_pb2.LoginRequest(username=username, password=password), timeout=2).token


def test_unknown_user_returns_not_found(stub):
    try:
        stub.GetUser(user_pb2.GetUserRequest(user_id=999), timeout=2)
    except grpc.RpcError as error:
        assert error.code() == grpc.StatusCode.NOT_FOUND
    else:
        raise AssertionError("Expected NOT_FOUND for an unknown user")


def test_new_proto_fields_are_available():
    user = user_pb2.User(
        id=4,
        name="Dana",
        email="dana@example.com",
        nickname="D",
        address=user_pb2.Address(street="Main Street", city="Dublin"),
    )
    encoded = user.SerializeToString()
    decoded = user_pb2.User.FromString(encoded)
    assert decoded.nickname == "D"
    assert decoded.address.city == "Dublin"


def test_login_rejects_bad_password(stub):
    try:
        login(stub, password="wrong")
    except grpc.RpcError as error:
        assert error.code() == grpc.StatusCode.UNAUTHENTICATED
    else:
        raise AssertionError("Expected UNAUTHENTICATED for a bad password")


def test_protected_method_requires_token(stub):
    for metadata in [(), (("authorization", "Bearer not-a-jwt"),)]:
        try:
            stub.SendChatMessage(user_pb2.ChatMessage(text="hi"), metadata=metadata, timeout=2)
        except grpc.RpcError as error:
            assert error.code() == grpc.StatusCode.UNAUTHENTICATED
        else:
            raise AssertionError("Expected UNAUTHENTICATED without a valid token")


def test_chat_broadcasts_to_subscribers(stub):
    token = login(stub, "jorys")
    subscription = stub.SubscribeChat(user_pb2.SubscribeChatRequest(), timeout=5)
    received = []

    def read_first_message():
        received.append(next(subscription))

    reader = threading.Thread(target=read_first_message)
    reader.start()
    time.sleep(0.3)  # laisse le temps à l'abonnement de s'enregistrer
    response = stub.SendChatMessage(
        user_pb2.ChatMessage(text="Salut", author="usurpateur"),
        metadata=(("authorization", f"Bearer {token}"),),
        timeout=2,
    )
    reader.join(timeout=3)
    subscription.cancel()

    assert response.subscriber_count >= 1
    assert received and received[0].text == "Salut"
    assert received[0].author == "jorys"  # l'auteur vient du JWT, pas du client


def test_deadline_exceeded_on_idle_stream(stub):
    try:
        for _ in stub.SubscribeChat(user_pb2.SubscribeChatRequest(), timeout=0.5):
            pass
    except grpc.RpcError as error:
        assert error.code() == grpc.StatusCode.DEADLINE_EXCEEDED
    else:
        raise AssertionError("Expected DEADLINE_EXCEEDED")


def test_health_check(channel):
    response = health_pb2_grpc.HealthStub(channel).Check(
        health_pb2.HealthCheckRequest(service="user.v1.UserService"), timeout=2
    )
    assert response.status == health_pb2.HealthCheckResponse.SERVING


def test_tls_and_mtls():
    with tempfile.TemporaryDirectory() as certs_dir:
        subprocess.run([ROOT / "scripts/generate_certs.sh", certs_dir], check=True, capture_output=True)
        certs = {name: (Path(certs_dir) / name).read_bytes() for name in
                 ["ca.crt", "server.crt", "server.key", "client.crt", "client.key"]}

        # TLS simple : le client vérifie le serveur grâce à la CA
        tls_server, address = start_server(grpc.ssl_server_credentials([(certs["server.key"], certs["server.crt"])]))
        with grpc.secure_channel(address, grpc.ssl_channel_credentials(certs["ca.crt"])) as channel:
            info = user_pb2_grpc.UserServiceStub(channel).GetServerInfo(user_pb2.ServerInfoRequest(), timeout=2)
            assert info.tls_enabled
        tls_server.stop(None)

        # mTLS : le serveur exige aussi un certificat client signé par la CA
        mtls_server, address = start_server(grpc.ssl_server_credentials(
            [(certs["server.key"], certs["server.crt"])],
            root_certificates=certs["ca.crt"],
            require_client_auth=True,
        ))
        without_cert = grpc.ssl_channel_credentials(certs["ca.crt"])
        with grpc.secure_channel(address, without_cert) as channel:
            try:
                user_pb2_grpc.UserServiceStub(channel).GetServerInfo(user_pb2.ServerInfoRequest(), timeout=2)
            except grpc.RpcError as error:
                assert error.code() == grpc.StatusCode.UNAVAILABLE
            else:
                raise AssertionError("mTLS should reject a client without certificate")
        with_cert = grpc.ssl_channel_credentials(certs["ca.crt"], certs["client.key"], certs["client.crt"])
        with grpc.secure_channel(address, with_cert) as channel:
            user_pb2_grpc.UserServiceStub(channel).GetServerInfo(user_pb2.ServerInfoRequest(), timeout=2)
        mtls_server.stop(None)


if __name__ == "__main__":
    grpc_server, address = start_server()
    with grpc.insecure_channel(address) as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        test_unknown_user_returns_not_found(stub)
        test_new_proto_fields_are_available()
        test_login_rejects_bad_password(stub)
        test_protected_method_requires_token(stub)
        test_chat_broadcasts_to_subscribers(stub)
        test_deadline_exceeded_on_idle_stream(stub)
        test_health_check(channel)
    grpc_server.stop(None)
    test_tls_and_mtls()
    print("Backend tests passed.")
