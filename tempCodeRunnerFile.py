from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Dict
import requests
import os
import hashlib, uuid
from datetime import datetime
from database import User, Lock, History, Request, UserRole

app = FastAPI()

#   Load .env
load_dotenv( '.env' )
user = os.getenv( 'user' )
password = os.getenv( 'password' )
MY_VARIABLE = os.getenv('MY_VARIABLE')

#   Connect to MongoDB
client = MongoClient(f"mongodb+srv://{user}:{password}@cluster0.o068s.mongodb.net/")
db = client['EventBud']
# collection = db['Events']

#   CORS
origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*'],
)

##################################################
#
#   Helper Functions
#

def hash_password( password, salt = None ):
    '''
        Hash password with salt
        Input: password (str)
        Output: password_hash (str), salt (str)
    '''

    if not salt:
        salt = uuid.uuid4().hex
    password_salt = ( password + salt ).encode( 'utf-8' )
    password_hash = hashlib.sha512( password_salt ).hexdigest()
    return password_hash, salt
##################################################
#
#   API
#

# root
@app.get('/')
def read_root():
    return { "Hello": "World" }

# user signup
@app.post('/signup', tags=['Users'])   
def signup( user_signup: User_Signup ):
    '''
        normal sign up
        input: User_Signup
        output: dict
    '''

    # connect to database
    collection = db['Users']

    # check if email already exists
    if collection.find_one( { 'email': user.email }, { '_id': 0 } ):
        raise HTTPException( status_code = 400, detail = "Email already exists" )
    
    # hash password
    salt = uuid.uuid4().hex
    password_hash, salt = hash_password( user.password, salt )

    # create new user
    newUser = User(
        firstName = user.firstName, 
        lastName = user.lastName, 
        email = user.email, 
        password_hash = password_hash, 
        salt = salt 
    )

    # add user to database
    collection.insert_one( newUser.dict() )
    return { 'status': 'success' }

# user login
@app.post('/login', tags=['Users'])
def login( email: str, password: str ):

    # connect to database
    collection = db['Users']

    # check if email exists
    user = collection.find_one( { 'email': email } )
    if not user:
        raise HTTPException( status_code = 400, detail = "User not found" )
    
# get all lock
@app.get('/lock', tags=['Locks'])
def get_locks():
    '''
        get all locks
        input: None
        output: dict of locks 
            for example: {
                "lockId": "63B28CDF",
                "dataList": [
                    {
                        "userCode": 6392,
                        "img": null,
                        "userName": "Josephine",
                        "userSurname": "Smith"
                    },
                    {
                        "userCode": 1824,
                        "img": null,
                        "userName": "Taylor",
                        "userSurname": "Wang"
                    }
                ]
            }
    '''
    # connect to database
    collection = db['Locks']
    # get all locks
    locks = collection.find( {}, { '_id': 0 } )
    # return locks
    return { 'locks': locks }

    