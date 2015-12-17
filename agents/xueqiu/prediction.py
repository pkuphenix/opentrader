import httplib2
from . import settings

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow 
from oauth2client.tools import run

client_id = settings.client_id
client_secret = settings.client_secret
scope = {'https://www.googleapis.com/auth/devstorage.full_control',
            'https://www.googleapis.com/auth/devstorage.read_only',
            'https://www.googleapis.com/auth/devstorage.read_write',
            'https://www.googleapis.com/auth/prediction'}
            
flow = OAuth2WebServerFlow(client_id, client_secret, scope)
            
storage = Storage("credentials.dat")
credentials = storage.get()
            
if credentials is None or credentials.invalid:
    credentials = run(flow, storage)
                
http = httplib2.Http()
http = credentials.authorize(http)
            
service = build('prediction', 'v1.6', http=http)

class TrainedModel(object):

    def __init__(self, project_id, model_name):
        self.p = project_id
        self.m = model_name
    
    #Train a Prediction API model
    def insert(self, storage_data_location=None, output_value=None, features=None):
        body= {
                "storageDataLocation": storage_data_location,
                "id": self.m,
                "trainingInstances": [
                            {"output": output_value,
                             "csvInstance": features
                             }
                           ]
             } 
        return service.trainedmodels().insert(project=self.p, body=body).execute()
        
    #Train a Prediction API model using a dataset
    def insert_dataset(self, training_data):
            body= {
                   "id": self.m,
                   "trainingInstances": training_data
                   }
            return service.trainedmodels().insert(project=self.p, body=body).execute()
            
    #Check training status of your model
    def get(self):
        return service.trainedmodels().get(project=self.p, id=self.m).execute()
    
    #Submit model id and request a prediction    
    def predict(self, features):
        body={
              "input": {
                "csvInstance": features
                }
            }
        return service.trainedmodels().predict(project=self.p, id=self.m, body=body).execute()
    
    #List available models    
    def list(self):
        return service.trainedmodels().list(project=self.p).execute()
    
    #Delete a trained model
    def delete(self):
        return service.trainedmodels().delete(project=self.p, id=self.m).execute()
     
    #Get analysis of the model and the data the model was trained on     
    def analyze(self):
        return service.trainedmodels().analyze(project=self.p, id=self.m).execute()
    
    #Add new data to a trained model    
    def update(self, output, features):
        body= {
               "output": output,
                "csvInstance":[
                features
                ]
              }
        return service.trainedmodels().update(project=self.p, id=self.m, body=body).execute()
        
class HostedModel(object):

    Hosted_model_id = 414649711441
    
    #Submit input and request an output against a hosted model
    def predict(self, model_name, csv_instances):
        body={
            "input":{
            "csvInstance": csv_instances
            }
        }
        return service.hostedmodels().predict()
