from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Dict
import requests
import os
import hashlib, uuid
from datetime import datetime
from database import User, Lock, History, Request, UserRole, User_Signup
import random

app = FastAPI()

#   Load .env
load_dotenv( '.env' )
user = os.getenv( 'user' )
password = os.getenv( 'password' )
MY_VARIABLE = os.getenv('MY_VARIABLE')

#   Connect to MongoDB
client = MongoClient(f"mongodb+srv://{user}:{password}@cluster0.o068s.mongodb.net/")
db = client['Fido']
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

# hash password
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

# genrate user code 
def generate_user_code():
    '''
        Generate user code by random number 4 digits
        Input: None
        Output: user code (int)
    '''

    # connect to database
    collection = db['Users']

    # get all users
    users = list( collection.find( {}, { '_id': 0 } ) )

    # get user code
    userCodes = [ user['userCode'] for user in users ]

    # cgeck if user code limit reached
    if len( userCodes ) == 9999:
        raise HTTPException( status_code = 400, detail = "User code limit reached" )
    
    # generate user code
    userCode = random.randint( 1000, 9999 )

    # check if user code already exists
    while userCode in userCodes:
        userCode = random.randint( 1000, 9999 )

    return userCode

# generate user id by first name and last name and 4 digits random unique number
def generate_user_id( firstName, lastName ):
    '''
        Generate user id
        Input: first name (str), last name (str)
        Output: user id (str)
        for example: firstName = 'Josephine', lastName = 'Smith' => userId = 'js7694'
    '''

    # connect to database
    collection = db['Users']

    # get all users
    users = list( collection.find( {}, { '_id': 0 } ) )

    # get 4 digits of user id
    userIDs = [ user['userId'] for user in users ]
        
    # generate user id
    userId = firstName[0].lower() + lastName[0].lower() + str( random.randint( 1000, 9999 ) )

    # check if user id already exists
    while userId in userIDs:
        userId = firstName[0].lower() + lastName[0].lower() + str( random.randint( 1000, 9999 ) )

    return userId



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
    
    # generate user code
    userCode = generate_user_code()

    # generate user id
    userId = generate_user_id( user.firstName, user.lastName )

    # hash password
    salt = uuid.uuid4().hex
    password_hash, salt = hash_password( user.password, salt )

    # create new user
    newUser = User(
        firstName = user.firstName, 
        lastName = user.lastName, 
        email = user.email, 
        password_hash = password_hash, 
        salt = salt,
        userId = userId,
        userCode = userCode,
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
        raise HTTPException( status_code = 404, detail = "User not found" )
    
# get admin lock
@app.get('/admin/lock/{lockId}', tags=['Create New Lock'])
def get_admin_lock( lockId: int ):
    '''
        get all admin of this lock by lockId
        input: lockId (int)
        output: dict of lock
        for example:
        {
            "lockId":"63B28CDF",
            "dataList": [
                { 
                    "userCode": 6392,
                    "userImage": null,
                    "userId": "js7694",
                    "userName": "Josephine",
                    "userSurname": "Smith"
                },
                { 
                    "userCode": 1824,
                    "userImage": null,
                    "userId": "tw7634",
                    "userName": "Taylor",
                    "userSurname": "Wang"
                }
            ]
        }
    '''

    # connect to database
    collection = db['Locks']

    # get lock
    lock = collection.find_one( { 'lockId': lockId }, { '_id': 0 } )
    if not lock:
        raise HTTPException( status_code = 404, detail = "Lock not found" )
    
    # get admin lock
    adminLock = {
        'lockId': lock['lockId'],
        'dataList': [
            {
                'userCode': user['userCode'],
                'userImage': user['userImage'],
                'userId': user['userId'],
                'userName': user['firstName'],
                'userSurname': user['lastName'],
            }
            for user in lock['user']
            if user['userRole'] == 'admin'
        ]
    }

    return adminLock

# get list of lock location by userId
@app.get('/lockList/user/{userId}', tags=['Locks List'])
def get_lock_location( userId: str ):
    '''
        get list of lock location by userId
        input: userId (str)
        output: dict of lock location
        for example:
        {
            "userId": "js8974"
            "dataList": ["Home", "Office"],
        }
    '''

    # connect to database
    collection = db['Users']

    # get user
    user = collection.find_one( { 'userId': userId }, { '_id': 0 } )
    if not user:
        raise HTTPException( status_code = 404, detail = "User not found" )
    
    # get dict of lock location
    lockLocation = {
        'userId': user['userId'],
        'dataList': user['lockLocationList'],
    }

    return lockLocation

# get user lock by userId
# NOTE: if lockLocationActiveStr is None, set lockLocationActiveStr to first element of lockLocationList
# NOTE: if lockLocationActiveStr is None, set path to /lockList/{userId}/None
@app.get('/lockList/{userId}', tags=['Locks List'])
@app.get('/lockList/{userId}/{lockLocationActiveStr}', tags=['Locks List'])
def get_user_lock(userId: str, lockLocationActiveStr: str = None):
    '''
        get all user lock
        input: userId (str)
        output: dict of lock
        for example:
        {
            "userId": "js8974"
            "userName":"Jonathan",
            "lockLocationList": ["Home", "Office"],
            "lockLocationActive": "Home",
            "dataList": [
                { 
                    "lockId": "12345",
                    "lockImage": null,
                    "lockName": "Front Door"
                },
                { 
                    "lockId": "12345",
                    "lockImage": null,
                    "lockName": "Back Door"
                }
            ]
        }
    '''

    # connect to database
    collection = db['Users']

    # get user
    user = collection.find_one( { 'userId': userId }, { '_id': 0 } )
    if not user:
        raise HTTPException( status_code = 404, detail = "User not found" )

    lockLocationList = user['lockLocationList']

    # if lock location active is none
    if not lockLocationActiveStr:
        # set lock loaction active is first element of lock location list
        lockLocationActiveStr = lockLocationList[0]
       
    # get user lock
    userLock = {
        'userId': user['userId'],
        'userName': user['firstName'],
        'lockLocation': lockLocationActiveStr,
        'dataList': [
            {
                'lockId': lock['lockId'],
                'lockImage': lock['lockImage'],
                'lockName': lock['lockName'],
            }
            for lockList in user['userRoleToLockListDict'].values()
            for lock in lockList
            if lockLocationActiveStr == lock['lockLocation']
        ]
    }

    return userLock

# get lock detail by lockId
@app.get('/lockDetail/{lockId}/{userId}', tags=['Locks Detail'])
def get_lock_detail( lockId: int, userId: str ):
    '''
        get lock detail by lockId
        input: lockId (int) and userId (str)
        output: dict of lock
        for example:
        {
            "lockId": "12345",
            "lockName": "Front Door",
            "lockLocation": "Home",
            "lockImage": null,
            "securityStatus": "secure",
            "isAdmin": true,
            "dataList": [
                {
                "userId": "js8974",
                "userName": "Jonathan",
                "userImage": "jonathan.jpg",
                "role": "admin"
                },
                {
                "userId": "tw7634",
                "userName": "Taylor",
                "userImage": "jonathan.jpg",
                "role": "member"
                },
            ]
        }
    '''

    # connect to database
    collection = db['Locks']

    # get lock
    lock = collection.find_one( { 'lockId': lockId }, { '_id': 0 } )
    if not lock:
        raise HTTPException( status_code = 404, detail = "Lock not found" )
    
    # check if user is admin then set isAdmin to True
    isAdmin = False
    for user in lock['user']:
        if user['userId'] == userId and user['userRole'] == 'admin':
            isAdmin = True

    # get dict of lock detail
    lockDetail = {
        'lockId': lock['lockId'],
        'lockName': lock['lockName'],
        'lockLocation': lock['lockLocation'],
        'lockImage': lock['lockImage'],
        'securityStatus': lock['securityStatus'],
        'isAdmin': isAdmin,
        'dataList': [
            {
                'userId': user['userId'],
                'userName': user['firstName'],
                'userImage': user['userImage'],
                'role': user['userRole'],
            }
            for user in lock['user']
        ]
    }

    return lockDetail

# get user of this lock by lockId and interested role
@app.get('/lock/role/{lockId}/{role}', tags=['Role Setting'])
def get_user_by_lockId_role( lockId: int, role: str ):
    '''
        get user of this lock by lockId and interested role
        input: lockId (int) and role (str)
        output: dict of user of this lock by role
        for example:
        {
            "lockId": "12345",
            "lockName": "Front Door",
            "lockLocation": "Home",
            "dataList": [
                {
                "userId": "js8974",
                "userName": "Jonathan",
                "userSurname": "Smith",
                "userImage": "jonathan.jpg",
                "role": "admin",
                "dateTime": null
                },
            ]
        }
    '''

    # connect to database
    collection = db['Locks']

    # get lock
    lock = collection.find_one( { 'lockId': lockId }, { '_id': 0 } )
    if not lock:
        raise HTTPException( status_code = 404, detail = "Lock not found" )
    
    # get user by role
    userList = [
        {
            'userId': user['userId'],
            'userName': user['firstName'],
            'userSurname': user['lastName'],
            'userImage': user['userImage'],
            'role': user['userRole'],
            'dateTime': user['dateTime'] if 'dateTime' in user else None,
        }
        for user in lock['user']
        if user['userRole'] == role
    ]

    # get dict of user by role
    userByRole = {
        'lockId': lock['lockId'],
        'lockName': lock['lockName'],
        'lockLocation': lock['lockLocation'],
        'dataList': userList
    }

    return userByRole

# get user by userCode
@app.get('/user/{userCode}', tags=['Add New User'])
def get_user_by_userCode( userCode: int ):
    '''
        get user by userCode
        input: userCode (int)
        output: dict of user
        for example:
        {
            "userCode": 6783,
            "dataList": [
                {
                "userId": "tc9820",
                "userCode": 6783,
                "userName": "Tylor",
                "userSurname": "Chang",
                "userImage": "Tylor.jpg"
                },
            ]
        }
    '''

    # connect to database
    collection = db['Users']

    # get user
    user = collection.find_one( { 'userCode': userCode }, { '_id': 0 } )
    if not user:
        raise HTTPException( status_code = 404, detail = "User not found" )
    
    # get dict of user by userCode
    userByUserCode = {
        'userCode': user['userCode'],
        'dataList': [
            {
                'userId': user['userId'],
                'userCode': user['userCode'],
                'userName': user['firstName'],
                'userSurname': user['lastName'],
                'userImage': user['userImage'],
            }
        ]
    }

    return userByUserCode


