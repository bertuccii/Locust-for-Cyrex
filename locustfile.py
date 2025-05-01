
import uuid
import time
import datetime
from proto import auth_service_pb2_grpc
from proto import rpc_create_vacancy_pb2
from proto import rpc_signin_user_pb2
from proto import rpc_update_vacancy_pb2
from proto import vacancy_pb2
from proto import vacancy_service_pb2_grpc, vacancy_service_pb2
from locust import User, task, constant
from create_users import create_users
import grpc
import random
import json
import os
import asyncio
from grpc.experimental import gevent as grpc_gevent
from dotenv import load_dotenv


load_dotenv()
SERVER = os.getenv("SERVER")


# Global USERS list
USERS = []
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        USERS = json.load(f)
    print(f"{len(USERS)} users loaded.")
else:
    asyncio.run(create_users())
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            USERS = json.load(f)
        print(f"{len(USERS)} users loaded.")
    else:
        raise Exception("create_users() executed, but users.json was not created.")
        
# Enable grpc gevent support
grpc_gevent.init_gevent()

class MyUser(User):
    wait_time = constant(1)

    def on_start(self):
       
        options = [
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.enable_http_proxy', 0)
        ]
        self.channel = grpc.insecure_channel(SERVER, options=options)
        self.stub = auth_service_pb2_grpc.AuthServiceStub(self.channel)
        self.stub_vacancy = vacancy_service_pb2_grpc.VacancyServiceStub(self.channel)
   

        self.user = random.choice(USERS)
        self.email = self.user["email"]
        self.password = self.user["password"]
        self.access_token = self.login_user(self.email, self.password)

        if self.access_token:
            print(f"Successfull login: {self.email}")
        else:
            print(f"Failed to login: {self.email}")
        self.last_task_time = 0
        self.last_get_all_time = time.time()
        

    def on_stop(self):
        self.channel.close()

    def login_user(self, email, password):
        try:
            signin_request = rpc_signin_user_pb2.SignInUserInput(
                email=email,
                password=password
            )
            signin_response = self.stub.SignInUser(signin_request)
            return signin_response.access_token
        except grpc.RpcError as e:
            print(f"Erro logging in {email}: {e}")
            return None

   
    def create_vacancy(self):
        if not self.access_token or getattr(self, "vacancy_created", False):
            return

        vacancies = [
            ("Software Engineer", "Manage software development projects.", vacancy_pb2.Vacancy.DEVELOPMENT),
            ("Data Scientist", "Analyze and interpret data to provide insights.", vacancy_pb2.Vacancy.DEVELOPMENT),
            ("Product Manager", "Lead product development and management.", vacancy_pb2.Vacancy.OTHER),
            ("Marketing Specialist", "Create and execute marketing campaigns.", vacancy_pb2.Vacancy.SALES),
            ("UX Designer", "Design and develop user experiences.", vacancy_pb2.Vacancy.OTHER)
        ]
        
        jobs_dict = {
            f"{title} {uuid.uuid4().hex[:6]}": {
                "description": description,
                "division": division
            }
            for title, description, division in vacancies
        }

        unique_title = random.choice(list(jobs_dict.keys()))
        description = jobs_dict[unique_title]["description"]
        division = jobs_dict[unique_title]["division"]
        countries = ["Brazil", "USA", "Canada", "Australia", "Germany"]

        
        vacancy_request = rpc_create_vacancy_pb2.CreateVacancyRequest(
            Title=unique_title,
            Description=description,
            Division=division,
            Country=random.choice(countries)
        )


        metadata = [('authorization', self.access_token)]
        start_time = time.time()
        try:
            response = self.stub_vacancy.CreateVacancy(vacancy_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="gRPC",
                name="CreateVacancy",
                response_time=total_time,
                response_length=response.ByteSize(),
                exception=None
            )
            print(f"Vacancy created by {self.email}: {response.vacancy.Id}")
            self.last_created_vacancy_id = response.vacancy.Id
            self.vacancy_created = True
            self.vacancy_updated = False
        except grpc.RpcError as e:
            print(f"Error creating vacancy for {self.email}: {e}")


    
    def update_vacancy(self):
        if not self.access_token or not getattr(self, 'vacancy_created', False) or getattr(self, 'vacancy_updated', False):
            #print(f"User {self.email} has no token or no last created vacancy.")
            return

        vacancies = [
            ("Python Developer", "Develop python applications.", vacancy_pb2.Vacancy.DEVELOPMENT),
            ("Cyber Security Analyst", "Analyze and protect systems from cyber threats.", vacancy_pb2.Vacancy.SECURITY),
            ("Sales Manager", "Manage sales teams and processes.", vacancy_pb2.Vacancy.SALES),
            ("Technical Writer", "Write technical documentation.", vacancy_pb2.Vacancy.OTHER),
            ("Database Administrator", "Manage and maintain databases.", vacancy_pb2.Vacancy.DEVELOPMENT)
        ]
        jobs_dict = {
            f"{title} {uuid.uuid4().hex[:6]}": {
                "description": description,
                "division": division
            }
            for title, description, division in vacancies
        }
        unique_title = random.choice(list(jobs_dict.keys()))
        description = jobs_dict[unique_title]["description"]
        division = jobs_dict[unique_title]["division"]
                
        countries = ["Brazil", "USA", "Canada", "Australia", "Germany"]
        country = random.choice(countries)   
        update_fields = {
            "Title": unique_title,
            "Description": description,
            "Division": division,
            "Country": country
        }

        fields_to_update = random.sample(list(update_fields.keys()), k=random.randint(1, len(update_fields)))

        update_args = {"Id": self.last_created_vacancy_id}
        for field in fields_to_update:
            update_args[field] = update_fields[field]
        request = rpc_update_vacancy_pb2.UpdateVacancyRequest(**update_args)
        
        print("Atualizando os campos:", fields_to_update)
        print("Request:", request)
        metadata = [('authorization', self.access_token)]
        start_time = time.time()  
        try:
            response = self.stub_vacancy.UpdateVacancy(request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="gRPC",
                name="UpdateVacancy",
                response_time=total_time,
                response_length=response.ByteSize(),
                exception=None
            )
            print(f"Vacancy {self.last_created_vacancy_id} updated by {self.email}")
            self.vacancy_updated = True
        except grpc.RpcError as e:
            print(f"Error updating vacancy {self.last_created_vacancy_id} for {self.email}: {e}")


    
    def search_vacancy(self):
        if not self.access_token or not getattr(self, 'last_created_vacancy_id', False):
            return

        metadata = [('authorization', self.access_token)]
        start_time = time.time()
        try:
            search_request = vacancy_service_pb2.VacancyRequest(Id=self.last_created_vacancy_id)
            response = self.stub_vacancy.GetVacancy(search_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="gRPC",
                name="FetchVacancy",
                response_time=total_time,
                response_length=response.ByteSize(),
                exception=None
            )
            vacancy = response.vacancy
            print(f"Vacancy searched by {self.email}")
            print(f"Id: {vacancy.Id}")
            print(f"Title: {vacancy.Title}")
            print(f"Description: {vacancy.Description}")
            print(f"Division: {vacancy.Division}")
            print(f"Views: {vacancy.Views}")
            print(f"Country: {vacancy.Country}")
            print(f"CreatedAt: {datetime.datetime.fromtimestamp(vacancy.created_at.seconds).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"UpdatedAt: {datetime.datetime.fromtimestamp(vacancy.updated_at.seconds).strftime('%Y-%m-%d %H:%M:%S')}")
        except grpc.RpcError as e:
            print(f"Error searching vacancy {self.last_created_vacancy_id} for {self.email}: {e}")
   
    def delete_vacancy(self):
        if not self.access_token or not getattr(self, 'last_created_vacancy_id', False):
             return

        if not hasattr(self, 'last_created_vacancy_id'):
            print(f"User {self.email} has no last created vacancy.")
            return
        
        metadata = [('authorization', self.access_token)]
        vacancy_id = self.last_created_vacancy_id
        start_time = time.time()  
        try:
            delete_request = vacancy_service_pb2.VacancyRequest(Id=vacancy_id)
            response = self.stub_vacancy.DeleteVacancy(delete_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=total_time,
                response_length=response.ByteSize(),
                exception=None
            )
            
            print(f"Vacancy {vacancy_id} deleted by {self.email}: {response}")
            self.vacancy_created = False
            self.vacancy_updated = False
            del self.last_created_vacancy_id
        except grpc.RpcError as e:
            print(f"Error deleting vacancy {vacancy_id} for {self.email}: {e}")



 
    def get_all_vacancies(self):
        request = vacancy_service_pb2.GetVacanciesRequest(
            page=1,
            limit=10
        )

        start_time = time.time()
        try:
            stream = self.stub_vacancy.GetVacancies(request)
            vacancy_count = 0
            for vacancy in stream:
                vacancy_count += 1
                print(vacancy.Id)
                print(vacancy.Title)
            print(f"Total vacancies: {vacancy_count}")
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="gRPC",
                name="GetAllVacancies",
                response_time=total_time,
                response_length=vacancy_count,
                exception=None
            )

        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="gRPC",
                name="GetAllVacancies",
                response_time=total_time,
                response_length=0,
                exception=e
            )

    @task
    def run_vacancy_cycle(self):
        now = time.time()
        if now - self.last_task_time >= 30:
            self.create_vacancy()
            self.update_vacancy()
            self.search_vacancy()
            self.delete_vacancy()
            self.last_task_time = now
        
        if now - self.last_get_all_time >= 45:
            self.get_all_vacancies()

            self.last_get_all_time = now
    