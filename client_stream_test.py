import grpc
from generated import user_pb2, user_pb2_grpc

with grpc.insecure_channel('localhost:50051') as channel:
    stub = user_pb2_grpc.UserServiceStub(channel)

    print('--- GetUser ---')
    response = stub.GetUser(user_pb2.GetUserRequest(user_id=1))
    print(f"Nom : {response.user.name}")

    print('--- ListUsers ---')
    for user in stub.ListUsers(user_pb2.ListUsersRequest()):
        print(f"{user.id}: {user.name} <{user.email}>")

    print('--- Login (JWT) ---')
    token = stub.Login(user_pb2.LoginRequest(username='maxime', password='grpc'), timeout=2).token
    print(f"Token reçu : {token[:20]}…")

    print('--- CreateUsers ---')
    created = stub.CreateUsers(iter([
        user_pb2.User(id=3, name='Charlie', email='charlie@example.com'),
    ]), timeout=2, metadata=(('client-id', 'python-smoke-test'), ('authorization', f'Bearer {token}')))
    print(f"Créés : {created.created_count}")

    print('--- Chat ---')
    for message in stub.Chat(
        iter([user_pb2.ChatMessage(text='Bonjour'), user_pb2.ChatMessage(text='gRPC')]),
        timeout=2,
    ):
        print(message.text)
