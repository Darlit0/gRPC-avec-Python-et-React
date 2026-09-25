import grpc
from concurrent import futures

from generated import user_pb2, user_pb2_grpc

FAKE_DB = {
    1: user_pb2.User(
        id=1,
        name="Mounir",
        email="mounir@example.com",
        nickname="Momo",
        address=user_pb2.Address(street="Rue de Paris", city="Paris"),
    ),
    2: user_pb2.User(
        id=2,
        name="Alice",
        email="alice@example.com",
        nickname="Ali",
        address=user_pb2.Address(street="King Street", city="London"),
    ),
}


class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        user = FAKE_DB.get(request.user_id)
        if user is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.user_id} not found")
        return user_pb2.GetUserResponse(user=user)

    def ListUsers(self, request, context):
        for user in FAKE_DB.values():
            yield user

    def CreateUsers(self, request_iterator, context):
        created_count = 0
        for user in request_iterator:
            if not user.email:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "User email is required")
            FAKE_DB[user.id] = user
            created_count += 1
        return user_pb2.CreateUsersResponse(created_count=created_count)

    def Chat(self, request_iterator, context):
        for message in request_iterator:
            yield user_pb2.ChatMessage(text=f"echo: {message.text}")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("✅ Serveur gRPC en écoute sur le port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
