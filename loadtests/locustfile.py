from locust import HttpUser,task,between
import os
class ChatUser(HttpUser):
    wait_time=between(1,3)
    @task
    def chat(self):
        token=os.getenv('LOADTEST_JWT','')
        headers={'Authorization':'Bearer '+token} if token else {}
        self.client.post('/api/v1/chat',json={'message':'What is the battery life of iPhone?'},headers=headers,name='/api/v1/chat')
