from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Dict
import requests
import os
import hashlib, uuid
from datetime import datetime
from database import User, Lock, History, Request, UserRole, User_Signup, NewLock, NewRequest, NewInvitation, Invitation
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

# generate request id
def generate_request_id():
    '''
        Generate request id
        Input: None
        Output: request id (str)
    '''

    # Connect to database
    collection = db['Request']

    # Generate request id
    requestId = 'RQ' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if request id already exists
    while collection.find_one( { 'requestId' : requestId }, { '_id' : 0 } ):
        requestId = 'EV' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return requestId

# generate invitation id
def generate_invitation_id():
    '''
        Generate invitation id
        Input: None
        Output: invitation id (str)
    '''

    # Connect to database
    collection = db['Invitation']

    # Generate invitation id
    invitationId = 'IV' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if invitation id already exists
    while collection.find_one( { 'invitationId' : invitationId }, { '_id' : 0 } ):
        invitationId = 'IV' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return invitationId


##################################################
#
#   API
#

##################################################
#   Login/Register
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
    
##################################################
#   Lock Mangement
#

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
    userCollection = db['Users']

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
            for userId in lock['roleToUserIdListDict']['admin']
            for user in userCollection.find( { 'userId': userId }, { '_id': 0 } )
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
    lockCollection = db['Locks']

    # get user
    user = collection.find_one( { 'userId': userId }, { '_id': 0 } )
    if not user:
        raise HTTPException( status_code = 404, detail = "User not found" )

    lockLocationList = user['lockLocationList']

    # if lock location active is none
    if not lockLocationActiveStr:
        # set lock loaction active is first element of lock location list
        lockLocationActiveStr = lockLocationList[0]

    dataList = list()

    for lockIdList in user['userRoleToLockListDict'].values():
        for lockId in lockIdList:
            lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
            if lockLocationActiveStr == lock['lockLocation']:
                dataList.append( {
                    'lockId': lock['lockId'],
                    'lockImage': lock['lockImage'],
                    'lockName': lock['lockName'],
                } )
       
    # get user lock
    userLock = {
        'userId': user['userId'],
        'userName': user['firstName'],
        'lockLocation': lockLocationActiveStr,
        'dataList': dataList,
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
    lockCollection = db['Locks']
    userCollection = db['Users']

    # get lock
    lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
    if not lock:
        raise HTTPException( status_code = 404, detail = "Lock not found" )
    
    # check if user is admin then set isAdmin to True
    isAdmin = False
    for role, userIdList in lock['roleToUserIdListDict'].items():
        if userId in userIdList and role == 'admin':
            isAdmin = True

    dataList = list()

    for userIdList in lock['roleToUserIdListDict'].values:
        for userId in userIdList:
            user = userCollection.find_one( { 'userId': userId }, { '_id': 0 } )
            dataList.append( {
                'userId': user['userId'],
                'userName': user['firstName'],
                'userImage': user['userImage'],
                'role': user['userRole'],
            } )
        

    # get dict of lock detail
    lockDetail = {
        'lockId': lock['lockId'],
        'lockName': lock['lockName'],
        'lockLocation': lock['lockLocation'],
        'lockImage': lock['lockImage'],
        'securityStatus': lock['securityStatus'],
        'isAdmin': isAdmin,
        'dataList': dataList
    }

    return lockDetail

# get user of this lock by lockId and interested role
# userId???
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
    lockCollection = db['Locks']
    userCollection = db['Users']

    # get lock
    lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
    if not lock:
        raise HTTPException( status_code = 404, detail = "Lock not found" )
    
    dataList = list()

    # get user of lock by role
    for userIdList in lock['roleToUserIdListDict'][role]:
        for userId in userIdList:
            user = userCollection.find_one( { 'userId': userId }, { '_id': 0 } )
            dataList.append( {
                'userId': user['userId'],
                'userName': user['firstName'],
                'userSurname': user['lastName'],
                'userImage': user['userImage'],
                'role': user['userRole'],
                'dateTime': user['datetime'],
            } )

    # get dict of user by role
    userByRole = {
        'lockId': lock['lockId'],
        'lockName': lock['lockName'],
        'lockLocation': lock['lockLocation'],
        'dataList': dataList
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

# get history by lockId
@app.get('/history/{lockId}', tags=['History'])
def get_history_by_lockId( lockId: int ):
    '''
        get history by lockId
        input: lockId (int)
        output: dict of history
        for example:
        {
            "lockId": "12345",
            "lockName": "Front Door",
            "lockLocation": "Home",
            "dataList": [
                {
                    "userImage": null,
                    "dateTime": "2024-10-23T02:33:15",
                    "userName": null,
                    "status": "risk"
                },
                {
                    "userImage": "https://i.postimg.cc/3rBxMwmj/james-Corner.png",
                    "dateTime": "2024-10-23T08:57:52",
                    "userName": "James Corner",
                    "status": "connect"
                },
                {
                    "userImage": "https://i.postimg.cc/Fzgf8gm0/anna-House.png",
                    "dateTime": "2024-10-23T17:55:52",
                    "userName": "Anna House",
                    "status": "req"
                },
                {
                    "userImage": "https://i.postimg.cc/BQnQJGBr/taylor-Wang.png",
                    "dateTime": "2024-10-22T07:15:05",
                    "userName": "Taylor Wang",
                    "status": "connect"
                },
                {
                    "userImage": "https://i.postimg.cc/jdtLgPgX/jonathan-Smith.png",
                    "dateTime": "2024-10-22T15:05:47",
                    "userName": "Jonathan Smith",
                    "status": "connect"
                },
                {
                    "userImage": "https://i.postimg.cc/BQnQJGBr/taylor-Wang.png",
                    "dateTime": "2024-10-18T18:41:12",
                    "userName": "Taylor Wang",
                    "status": "connect"
                },
                {
                    "userImage": "https://i.postimg.cc/jdtLgPgX/jonathan-Smith.png",
                    "dateTime": "2024-10-18T21:26:33",
                    "userName": "Jonathan Smith",
                    "status": "connect"
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
    
    # get dict of history by lockId
    historyByLockId = {
        'lockId': lock['lockId'],
        'lockName': lock['lockName'],
        'lockLocation': lock['lockLocation'],
        'dataList': lock['history']
    }

    return historyByLockId

# post new lock
@app.post('/newLock', tags=['Create New Lock'])
def post_new_lock( new_lock: NewLock ):
    '''
        post new lock to Lock format
        update lock location list and user role to lock id list dict in user
        input: NewLock
        output: dict of new lock
        for example:
        {
            "userId": "js7694",
            "lockId": "12345",
            "message": "Create new lock successfully"
        }
    '''
    # if lock is already exists
    if collection.find_one( { 'lockId': new_lock.lockId } ):
        raise HTTPException( status_code = 400, detail = "Lock already exists" )
    
    # if user is already have this lockId
    if userCollection.find_one( { 'userId': new_lock.userId, 'userRoleToLockIdListDict.admin': new_lock.lockId } ):
        raise HTTPException( status_code = 400, detail = "User already have this lock" )

    # connect to database
    collection = db['Locks']
    userCollection = db['Users']

    # create new lock
    newLock = Lock(
        lockId = new_lock.lockId,
        lockName = new_lock.lockName,
        lockLocation = new_lock.lockLocation,
        lockImage = new_lock.lockImage,
        lockStatus = 'secure',
        securityStatus = 'secure',
        roleToUserIdListDict = {
            'admin': [ new_lock.userId ],
            'member': [],
        },
        invitation = [],
        request = [],
        history = [],
    )

    # add new lock to database
    collection.insert_one( newLock.dict() )

    # update lock location list in user
    # NOTE: add new lock location to lock location list
    userCollection.update_one( { 'userId': new_lock.userId }, { '$push': { 'lockLocationList': new_lock.lockLocation } } )
    
    # update user role to lock id list dict
    # NOTE: add new lock to admin role by append new lock id to admin list
    userCollection.update_one( { 'userId': new_lock.userId }, { '$push': { 'userRoleToLockIdListDict.admin': new_lock.lockId } } )

    return { 'userId': new_lock.userId, 'lockId': new_lock.lockId, 'message': 'Create new lock successfully' }

# post new request
@app.post('/request', tags=['Create New Lock'])
def post_new_request( new_request: NewRequest ):
    '''
        post new request to Request format
        post new request to lock
        input: NewRequest
        output: dict of new request
        for example:
        {
            "lockId": "12345",
            "userId": "tw8769",
            "message": "Send request successfully"
        }
    '''

    # connect to database
    collection = db['Request']
    lockCollection = db['Locks']

    # if request is already exists and request status is not expired
    if collection.find_one( { 'lockId': new_request.lockId, 'userId': new_request.userId, 'requestStatus': { '$ne': 'expired' } } ):
        raise HTTPException( status_code = 400, detail = "Request already exists" )

    # create new request
    newRequest = Request(
        requestId = generate_request_id(),
        lockId = new_request.lockId,
        userId = new_request.userId,
        requestType = new_request.requestType,
        requestStatus = new_request.requestStatus,
        requestDateTime = datetime.now(),
    )

    # add new request to database
    collection.insert_one( newRequest.dict() )

    # update request to lock
    # NOTE: add new request to lock by append new request to request list
    lockCollection.update_one( { 'lockId': new_request.lockId }, { '$push': { 'request': newRequest.dict() } } )

    return { 'lockId': new_request.lockId, 'userId': new_request.userId, 'message': 'Send request successfully' }

# post new invitation
@app.post('/invitation', tags=['Add New People'])
def post_new_invitation( new_invitation: Invitation ):
    '''
        post new invitation to Invitation format
        post new invitation to lock
        input: Invitation
        output: dict of new invitation
        for example:
        {
            "lockId": "12345",
            "userId": "tw8769",
            "message": "Send invitation successfully"
        }
    '''

    # connect to database
    collection = db['Invitation']
    lockCollection = db['Locks']

    # create new invitation
    newInvitation = Invitation(
        invitationId = generate_invitation_id(),
        lockId = new_invitation.lockId,
        userId = new_invitation.userId,
        invitationStatus = new_invitation.invitationStatus,
        invitationDateTime = datetime.now(),
    )

    # add new invitation to database
    collection.insert_one( newInvitation.dict() )

    # update invitation to lock
    # NOTE: add new invitation to lock by append new invitation to invitation list
    lockCollection.update_one( { 'lockId': new_invitation.lockId }, { '$push': { 'invitation': newInvitation.dict() } } )

    return { 'lockId': new_invitation.lockId, 'userId': new_invitation.userId, 'message': 'Send invitation successfully' }
    
# post lock location
@app.post('/lockLocation/{userId}', tags=['Locks Setting'])
def post_lock_location( userId: str, lockLocation: str ):
    '''
        post lock location to User format
        and append lock location to lock location list
        input: userId (str) and lockLocation (str)
        output: dict of lock location
        for example:
        {
            "userId": "js7694",
            "locationName": "Home"
            "message": "Create lock location successfully"
        }
    '''

    # connect to database
    collection = db['Users']

    # update lock location
    collection.update_one( { 'userId': userId }, { '$push': { 'lockLocationList': lockLocation } } )

    return { 'userId': userId, 'message': 'Update lock location successfully' }
