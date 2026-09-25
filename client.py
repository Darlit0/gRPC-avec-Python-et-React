import grpc

from generated import user_pb2, user_pb2_grpc


with grpc.insecure_channel("localhost:50051") as channel:
    stub = user_pb2_grpc.UserServiceStub(channel)
    response = stub.GetUser(user_pb2.GetUserRequest(user_id=1))
    print(f"Nom : {response.user.name}")
    print(f"Email : {response.user.email}")
