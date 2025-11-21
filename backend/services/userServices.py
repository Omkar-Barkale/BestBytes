import json
from pathlib import Path

def saveUserToDB(username, email, passwordHash,path: Path):
        newUser ={
            username:{
            "email": email,
            "password":passwordHash}
        }

        path.mkdir(parents= True, exist_ok= True)
        path = path/"users.json"


        print(newUser)
        data = {}
        if path.exists():
            with open(path, 'r') as jsonFile:
                try:
                    data = json.load(jsonFile)
                except json.JSONDecodeError:
                    data = {}
                
        data.update(newUser)
        with open(path,'w') as jsonFile:
            json.dump(data,jsonFile, indent = 2)
            jsonFile.truncate()