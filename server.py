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


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("✅ Serveur gRPC en écoute sur le port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
