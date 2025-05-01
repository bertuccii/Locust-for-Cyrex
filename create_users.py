import time
import json
import re
import grpc
import random
from pymailtm import MailTm
from proto import auth_service_pb2_grpc, auth_service_pb2
from proto import rpc_signup_user_pb2
from dotenv import load_dotenv
import os

load_dotenv()
SERVER = os.getenv("SERVER")

# Funções auxiliares
def random_name():
    names = ["John", "Mary", "Peter", "Anna", "Luke", "Emily", "Michael", "Claire", "Thomas", "Isabelle"]
    lastnames = ["Smith", "Johnson", "Brown", "Taylor", "Anderson", "Walker", "Harris", "Young", "Robinson", "Lewis"]
    return random.choice(names) + " " + random.choice(lastnames)

def get_code(account):
    timeout = 30
    start_time = time.time()

    while time.time() - start_time < timeout:
        messages = account.get_messages()
        for message in messages:
            match = re.search(r'Use the following code:\s*([A-Za-z0-9]+)', message.intro)
            if match:
                return match.group(1)
        time.sleep(2)
    return None

async def create_multiple_temp_mails(n):
    mail_tm = MailTm()
    accounts = [mail_tm.get_account() for _ in range(n)]
    return accounts

async def create_users():
    channel = grpc.insecure_channel(SERVER)
    stub = auth_service_pb2_grpc.AuthServiceStub(channel)

    users = []

    accounts = await create_multiple_temp_mails(3)

    for account in accounts:
        name = random_name()
        email = account.address
        password = account.password

        try:
            signup_request = rpc_signup_user_pb2.SignUpUserInput(
                name=name,
                email=email,
                password=password,
                passwordConfirm=password
            )
            stub.SignUpUser(signup_request)
            print(f"User signed up: {email}")

            # Espera o email chegar
            time.sleep(5)
            code = get_code(account)
            if code is None:
                print(f"Unable to get verification code for: {email}.")
                continue

            verify_request = auth_service_pb2.VerifyEmailRequest(
                verificationCode=code
            )
            stub.VerifyEmail(verify_request)
            print(f"User {email} verified.")

            users.append({"email": email, "password": password})

        except grpc.RpcError as e:
            print(f"Issue while trying to create/verify user {email}: {e}")

    channel.close()

    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

    print("All users have been created and saved in users.json.")


