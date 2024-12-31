from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Dict
import requests
import os
import hashlib, uuid
from datetime import datetime
from api.database import User, Lock, History, Request, User_Signup, NewLock, NewRequest, NewInvitation, Invitation, Other
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
    requestId = 'req' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if request id already exists
    while collection.find_one( { 'requestId' : requestId }, { '_id' : 0 } ):
        requestId = 'req' + str( collection.count_documents( {} ) + number ).zfill( 5 )
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
    invitationId = 'invite' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if invitation id already exists
    while collection.find_one( { 'invitationId' : invitationId }, { '_id' : 0 } ):
        invitationId = 'invite' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return invitationId

# generate connect id
def generate_connect_id():
    '''
        Generate connect id
        Input: None
        Output: connect id (str)
    '''

    # Connect to database
    collection = db['Connect']

    # Generate connect id
    connectId = 'con' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if connect id already exists
    while collection.find_one( { 'connectId' : connectId }, { '_id' : 0 } ):
        connectId = 'con' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return connectId

# generate other id
def generate_other_id():
    '''
        Generate other id
        Input: None
        Output: other id (str)
    '''

    # Connect to database
    collection = db['Other']

    # Generate other id
    otherId = 'other' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if other id already exists
    while collection.find_one( { 'otherId' : otherId }, { '_id' : 0 } ):
        otherId = 'other' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return otherId

# generate warning id
def generate_warning_id():
    '''
        Generate warning id
        Input: None
        Output: warning id (str)
    '''

    # Connect to database
    collection = db['Warning']

    # Generate warning id
    warningId = 'warning' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if warning id already exists
    while collection.find_one( { 'warningId' : warningId }, { '_id' : 0 } ):
        warningId = 'warning' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return warningId

# generate history id
def generate_history_id():
    '''
        Generate history id
        Input: None
        Output: history id (str)
    '''

    # Connect to database
    collection = db['History']

    # Generate history id
    historyId = 'his' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if history id already exists
    while collection.find_one( { 'historyId' : historyId }, { '_id' : 0 } ):
        historyId = 'his' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return historyId

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
def get_admin_lock( lockId: str ):
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
            for userId in lock['admin']
            for user in userCollection.find( { 'userId': userId }, { '_id': 0 } )
        ]
    }

    return adminLock

# get list of lock location by userId
@app.get('/lockLocation/user/{userId}', tags=['Locks List'])
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
# NOTE: if lockLocationActiveStr is None, lockLocationActiveStr = lockLocationList[0] and set path to /lockList/{userId}
@app.get('/lockList/{userId}', tags=['Locks List'])
@app.get('/lockList/{userId}/{lockLocationActiveStr}', tags=['Locks List'])
def get_user_lock( userId: str, lockLocationActiveStr: str = None):
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

    # get lock of this lock location active
    # loop for admin and member
    for lockId in user['admin']+user['member']:
        lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
        if lock:
            if lockLocationActiveStr == lock['lockLocation']:
                dataList.append( {
                    'lockId': lock['lockId'],
                    'lockImage': lock['lockImage'],
                    'lockName': lock['lockName'],
                } )

    # loop for guest
    for guest in user['guest']:
        lockId = guest['lockId']
        lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
        if lock:
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
def get_lock_detail( lockId: str, userId: str ):
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
    
    # if user is not in lock
    if userId not in lock['admin'] and userId not in lock['member'] and not any(guest["userId"] == userId for guest in lock['guest']):
        raise HTTPException( status_code = 403, detail = "User is not in lock" )
    
    # check if user is admin then set isAdmin to True
    isAdmin = False
    if userId in lock['admin']:
        isAdmin = True

    dataList = list()

    # loop for get admin user
    for userIdStr in lock['admin']:
        user = userCollection.find_one( { 'userId': userIdStr }, { '_id': 0 } )
        if user:
            dataList.append( {
                'userId': user['userId'],
                'userName': user['firstName'],
                'userImage': user['userImage'],
                'role': 'admin'
            } )

    # loop for get member user
    for userIdStr in lock['member']:
        user = userCollection.find_one( { 'userId': userIdStr }, { '_id': 0 } )
        if user:
            dataList.append( {
                'userId': user['userId'],
                'userName': user['firstName'],
                'userImage': user['userImage'],
                'role': 'member'
            } )

    # loop for get guest user
    for guest in lock['guest']:
        user = userCollection.find_one( { 'userId': guest['userId'] }, { '_id': 0 } )
        if user:
            dataList.append( {
                'userId': user['userId'],
                'userName': user['firstName'],
                'userImage': user['userImage'],
                'role': 'guest',
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
def get_user_by_lockId_role( lockId: str, role: str ):
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
    for userIdStr in lock[role]:
        if role == 'guest':
            guest = userIdStr
            user = userCollection.find_one( { 'userId': guest['userId'] }, { '_id': 0 } )
            datetime = guest['expirationDatetime']
        else:
            user = userCollection.find_one( { 'userId': userIdStr }, { '_id': 0 } )
            datetime = None
        if user:
            dataList.append( {
                'userId': user['userId'],
                'userName': user['firstName'],
                'userSurname': user['lastName'],
                'userImage': user['userImage'],
                'role': role,
                'dateTime': datetime
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
def get_history_by_lockId( lockId: str ):
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
    userCollection = db['Users']
    historyCollection = db['History']

    # get lock
    lock = collection.find_one( { 'lockId': lockId }, { '_id': 0 } )
    if not lock:
        raise HTTPException( status_code = 404, detail = "Lock not found" )
    
    # get history by lockId
    dataList = list()
    for historyId in lock['history']:
        history = historyCollection.find_one( { 'hisId': historyId }, { '_id': 0 } )
        if history:
            user = userCollection.find_one( { 'userId': history['userId'] }, { '_id': 0 } )
            dataList.append( {
                'userImage': user['userImage'],
                'dateTime': history['datetime'],
                'userName': user['firstName'] + ' ' + user['lastName'],
                'status': history['status'],
            } )
    
    # get dict of history by lockId
    historyByLockId = {
        'lockId': lock['lockId'],
        'lockName': lock['lockName'],
        'lockLocation': lock['lockLocation'],
        'dataList': dataList
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

    # connect to database
    collection = db['Locks']
    userCollection = db['Users']
    
    # if user is already have this lockId and return message error
    if userCollection.find_one( { 'userId': new_lock.userId, 'admin': { '$in': [new_lock.lockId] } } ):
        raise HTTPException( status_code = 400, detail = "Lock ID Already Exists" )

    # create new lock
    newLock = Lock(
        lockId = new_lock.lockId,
        lockName = new_lock.lockName,
        lockLocation = new_lock.lockLocation,
        lockImage = new_lock.lockImage,
        lockStatus = 'secure',
        securityStatus = 'secure',
        admin = [ new_lock.userId ],
        member = [],
        guest = [],
        invitation = [],
        request = [],
        history = [],
        warning = [],
    )

    # add new lock to database
    collection.insert_one( newLock.dict() )

    # update lock location list in user
    # NOTE: add new lock location to lock location list
    userCollection.update_one( { 'userId': new_lock.userId }, { '$push': { 'lockLocationList': new_lock.lockLocation } } )
    
    # add new lock to admin by append new lock id to list
    userCollection.update_one( { 'userId': new_lock.userId }, { '$push': { 'admin': new_lock.lockId } })

    return { 'userId': new_lock.userId, 'lockId': new_lock.lockId, 'message': 'Create new lock successfully' }

# post new request
@app.post('/request', tags=['Create New Lock'])
def post_new_request( new_request: NewRequest ):
    '''
        post new request to Request format
        post new request to lock
        post send request to Other( subMode = sent )
        post send request to History
        post history to lock
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
    otherCollection = db['Other']
    historyCollection = db['History']

    # if request is already exists
    if collection.find_one( { 'lockId': new_request.lockId, 'userId': new_request.userId } ):
        raise HTTPException( status_code = 400, detail = "Request already exists" )

    # generate request id
    requestId = generate_request_id()

    # create new request
    newRequest = Request(
        reqId = requestId,
        lockId = new_request.lockId,
        userId = new_request.userId,
        requestStatus = 'sent',
        datetime = datetime.now(),
    )

    # add new request to database
    collection.insert_one( newRequest.dict() )

    # update request to lock
    # NOTE: add new request to lock by append new request to request list
    lockCollection.update_one( { 'lockId': new_request.lockId }, { '$push': { 'request': requestId } } )

    # create new other
    # NOTE: create new other with subMode = sent
    newOther = Other(
        otherId = generate_other_id(),
        subMode = 'sent',
        amount = None,
        userId = new_request.userId,
        userRole = None,
        lockId = new_request.lockId,
        datetime = datetime.now(),
    )

    # add new other to database
    otherCollection.insert_one( newOther.dict() )

    # generate new history id
    historyId = generate_history_id()

    # create new history
    # NOTE: create new history with status = req
    newHistory = History(
        hisId = historyId,
        userId = new_request.userId,
        lockId = new_request.lockId,
        status = 'req',
        datetime = datetime.now(),
    )

    # add new history to database
    historyCollection.insert_one( newHistory.dict() )

    # post history to lock
    # NOTE: add new history to lock by append new history to history list
    lockCollection.update_one( { 'lockId': new_request.lockId }, { '$push': { 'history': historyId } } )

    return { 'lockId': new_request.lockId, 'userId': new_request.userId, 'message': 'Send request successfully' }

# post new invitation
@app.post('/invitation', tags=['Add New People'])
def post_new_invitation( new_invitation: NewInvitation ):
    '''
        post new invitation to Invitation format
        post new invitation to lock
        post new invitation to other
        input: Invitation
        output: dict of new invitation
        for example:
        {
            "srcUserId": "js7694",
            "desUserId": "tw8769",
            "role": "member",
            "dateTime": null,
            "message": "Send invitation successfully"
        }
    '''

    # connect to database
    otherCollection = db['Other']
    lockCollection = db['Locks']
    inviteCollection = db['Invitation']

    # if invitation is already exists
    if inviteCollection.find_one( { 'srcUserId': new_invitation.srcUserId, 'desUserId': new_invitation.desUserId, 'lockId': new_invitation.lockId } ):
        raise HTTPException( status_code = 400, detail = "Invitation already exists" )

    # generate invitation id
    invitationId = generate_invitation_id()

    # create new invitation
    newInvitation = Invitation(
        invId = invitationId,
        srcUserId = new_invitation.srcUserId,
        desUserId = new_invitation.desUserId,
        role = new_invitation.role,
        lockId = new_invitation.lockId,
        invStatus = 'invite',
        datetime = new_invitation.datetime if new_invitation.datetime else datetime.now(),
    )

    # add new invitation to database
    inviteCollection.insert_one( newInvitation.dict() )

    # update invitation to lock
    # NOTE: add new invitation to lock by append invitation id to invitation list
    lockCollection.update_one( { 'lockId': new_invitation.lockId }, { '$push': { 'invitation': invitationId } } )

    # create new other
    # NOTE: create new other with subMode = invite
    newOther = Other(
        otherId = generate_other_id(),
        subMode = 'invite',
        amount = None,
        userId = new_invitation.desUserId,
        userRole = new_invitation.role,
        lockId = new_invitation.lockId,
        datetime = new_invitation.datetime if new_invitation.datetime else datetime.now(),
    )

    # add new other to database
    otherCollection.insert_one( newOther.dict() )

    return { 'srcUserId': new_invitation.srcUserId, 'desUserId': new_invitation.desUserId, 'role': new_invitation.role, 'dateTime': new_invitation.datetime, 'message': 'Send invitation successfully' }
    
# post lock location
@app.post('/lockLocation/{userId}/{lockLocationStr}', tags=['Locks Setting'])
def post_lock_location( userId: str, lockLocationStr: str ):
    '''
        post lock location to lock location list of user
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

    # if lock location is already exists
    if collection.find_one( { 'userId': userId, 'lockLocationList': lockLocationStr } ):
        raise HTTPException( status_code = 400, detail = "Lock location already exists" )

    # update lock location
    collection.update_one( { 'userId': userId }, { '$push': { 'lockLocationList': lockLocationStr } } )

    return { 'userId': userId, 'message': 'Update lock location successfully' }

# get notofication request mode list by userId
@app.get('/notification/req/{userId}', tags=['Notifications'])
def get_request_notification_list( userId: str ):
    '''
        get request list in notification format by userId and order by date time
        input: userId (str)
        output: dict of notification list
        for example of request mode:
        {
            "userId": "js8974",
            "mode": "req",
            "dataList": [
            {
                "notiId": "req01",
                "dateTime": "2024-10-25T19:47:10",
                "subMode": null,
                "amount": 3, (for count amount of request of lock)
                "lockId": "12345",
                "lockLocation": "Home",
                "lockName": "Front Door",
                "userName": "Alice",
                "userSurname": "Johnson",
                "role": null
            },
            {
                "notiId": "req02",
                "dateTime": "2024-10-25T16:33:22",
                "subMode": null,
                "amount": 7,
                "lockId": "67890",
                "lockLocation": "Home",
                "lockName": "Garage",
                "userName": "Michael",
                "userSurname": "Smith",
                "role": null
            },
            {
                "notiId": "req03",
                "dateTime": "2024-10-25T13:58:47",
                "subMode": null,
                "amount": 2,
                "lockId": "23456",
                "lockLocation": "Home",
                "lockName": "Backdoor",
                "userName": "Emma",
                "userSurname": "Brown",
                "role": null
            },
            {
                "notiId": "req04",
                "dateTime": "2024-10-25T11:24:15",
                "subMode": null,
                "amount": 9,
                "lockId": "34567",
                "lockLocation": "Office",
                "lockName": "Office Lock",
                "userName": "David",
                "userSurname": "Wilson",
                "role": null
            },
            {
                "notiId": "req05",
                "dateTime": "2024-10-25T09:12:30",
                "subMode": null,
                "amount": 5,
                "lockId": "45678",
                "lockLocation": "Office",
                "lockName": "Storage",
                "userName": "Olivia",
                "userSurname": "Garcia",
                "role": null
            }
        ]
    }
    '''

    # connect to database
    collection = db['Request']
    userCollection = db['Users']
    lockCollection = db['Locks']

    # get user
    user = userCollection.find_one( { 'userId': userId }, { '_id': 0 } )

    # get lockId list that user is admin
    lockIdList = user['admin']

    requestList = list()

    # get request in notification format
    for lockId in lockIdList:
        requests = list( collection.find( { 'lockId': lockId }, { '_id': 0 } ) )
        lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
        for request in requests:
            requestList.append(
                {
                    'notiId': request['reqId'],
                    'dateTime': request['datetime'],
                    'subMode': None,
                    'amount': len( lock['request'] ),
                    'lockId': lockId,
                    'lockLocation': lock['lockLocation'],
                    'lockName': lock['lockName'],
                    'userName': user['firstName'],
                    'userSurname': user['lastName'],
                    'role': None,
                }
            )

    # order by date time
    requestList = sorted( requestList, key = lambda x: x['dateTime'], reverse = True )

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'req',
        'dataList': requestList
    }

    return notificationList

# get notification connect mode list by userId
app.get('/notification/connect/{userId}', tags=['Notifications'])
def get_connect_notification_list( userId: str ):
    '''
        get connect list in notification format by userId and order by date time
        input: userId (str)
        output: dict of notification list
        for example of connection mode:
        {
            "userId": "js8974",
            "mode": "connect",
            "dataList": [
            {
                "notiId": "con01",
                "dateTime": "2024-10-25T14:25:09",
                "subMode": null,
                "amount": null,
                "lockId": "12345",
                "lockLocation": "Home",
                "lockName": "Front Door",
                "userName": "Liam",
                "userSurname": "Martinez",
                "role": null
            },
            {
                "notiId": "con02",
                "dateTime": "2024-10-25T10:50:32",
                "subMode": null,
                "amount": null,
                "lockId": "13458",
                "lockLocation": "Office",
                "lockName": "Server Room",
                "userName": "Sophia",
                "userSurname": "Davis",
                "role": null
            },
            {
                "notiId": "con03",
                "dateTime": "2024-10-25T08:15:45",
                "subMode": null,
                "amount": null,
                "lockId": "12349",
                "lockLocation": "Home",
                "lockName": "Reception Door Lock",
                "userName": "James",
                "userSurname": "Taylor",
                "role": null
            }
        ]
    }
    '''

    # connect to database
    conCollection = db['Connect']
    userCollection = db['Users']
    lockCollection = db['Locks']

    # get user
    user = userCollection.find_one( { 'userId': userId }, { '_id': 0 } )

    # get lockId list that user is admin
    lockIdList = user['admin']

    connectList = list()

    # get request in notification format
    for lockId in lockIdList:
        connects = list( conCollection.find( { 'lockId': lockId }, { '_id': 0 } ) )
        lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
        for connect in connects:
            connectList.append(
                {
                    'notiId': connect['reqId'],
                    'dateTime': connect['datetime'],
                    'subMode': None,
                    'amount': None,
                    'lockId': lockId,
                    'lockLocation': lock['lockLocation'],
                    'lockName': lock['lockName'],
                    'userName': user['firstName'],
                    'userSurname': user['lastName'],
                    'role': None,
                }
            )

    # order by date time
    connectList = sorted( connectList, key = lambda x: x['dateTime'], reverse = True )

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'connect',
        'dataList': connectList
    }

    return notificationList

# get notification(mode = other and submode = invite) list by userId
@app.get('/notification/other/invite/{userId}', tags=['Notifications'])
def get_other_invite_notification_list( userId: str ):
    '''
        get other list (mode = other and submode = invite) in notification format by userId and order by date time
        input: userId (str)
        output: dict of notification list
        for example of other mode:
        {
            "userId": "js8974",
            "mode": "other",
            "dataList": [
            {
                "notiId": "other01",
                "dateTime": "2024-10-25T18:30:25",
                "subMode": "invite",
                "amount": null,
                "lockId": "12345",
                "lockLocation": "Home",
                "lockName": "Front Door",
                "userName": "Mason",
                "userSurname": "Johnson",
                "role": "admin"
            },
            {
                "notiId": "other04",
                "dateTime": "2024-10-25T12:05:35",
                "subMode": "invite",
                "amount": null,
                "lockId": "78457",
                "lockLocation": "",
                "lockName": "Backyard",
                "userName": "Ella",
                "userSurname": "Brown",
                "role": "member"
            },
        ]
    }
    '''

    # connect to database
    otherCollection = db['Other']
    lockCollection = db['Locks']
    userCollection = db['Users']

    # get submode = sent
    others = list( otherCollection.find( { 'userId': userId, 'subMode': 'invite' }, { '_id': 0 } ) )

    notificationList = {
        'userId': userId,
        'mode': 'other',
        'dataList': [
            {
                'notiId': other['otherId'],
                'dateTime': other['datetime'],
                'subMode': 'invite',
                'amount': None,
                'lockId': other['lockId'],
                'lockLocation': lock['lockLocation'],
                'lockName': lock['lockName'],
                'userName': user['firstName'],
                'userSurname': user['lastName'],
                'role': other['userRole'],
            }
            for other in others
            for lock in lockCollection.find( { 'lockId': other['lockId'] }, { '_id': 0 } )
            for user in userCollection.find( { 'userId': other['userId'] }, { '_id': 0 } )
        ]
    }

    return notificationList

# get notification(mode = other and submode = sent) list by userId
@app.get('/notification/other/sent/{userId}', tags=['Notifications'])
def get_other_sent_notification_list( userId: str ):
    '''
        get other list (mode = other and submode = sent) in notification format by userId and order by date time
        input: userId (str)
        output: dict of notification list
        for example of other mode:
        {
            "userId": "js8974",
            "mode": "other",
            "dataList": [
            {
                "notiId": "other02",
                "dateTime": "2024-10-25T16:15:50",
                "subMode": "sent",
                "amount": null,
                "lockId": "67890",
                "lockLocation": "Home",
                "lockName": "Garage",
                "userName": "",
                "userSurname": ""
                "role": ""
            },
            {
                "notiId": "other05",
                "dateTime": "2024-10-25T09:45:20",
                "subMode": "sent",
                "amount": null,
                "lockId": "90356",
                "lockLocation": "Office",
                "lockName": "Storage",
                "userName": "",
                "userSurname": "",
                "role": ""
            }
        ]
    }
    '''

    # connect to database
    otherCollection = db['Other']
    lockCollection = db['Locks']

    # get submode = sent
    others = list( otherCollection.find( { 'userId': userId, 'subMode': 'sent' }, { '_id': 0 } ) )

    notificationList = {
        'userId': userId,
        'mode': 'other',
        'dataList': [
            {
                'notiId': other['otherId'],
                'dateTime': other['datetime'],
                'subMode': 'sent',
                'amount': None,
                'lockId': other['lockId'],
                'lockLocation': lock['lockLocation'],
                'lockName': lock['lockName'],
                'userName': None,
                'userSurname': None,
                'role': None,
            }
            for other in others
            for lock in lockCollection.find( { 'lockId': other['lockId'] }, { '_id': 0 } )
        ]
    }

    return notificationList

# get notification(mode = other and submode = accepted) list by userId
@app.get('/notification/other/accepted/{userId}', tags=['Notifications'])
def get_other_accepted_notification_list( userId: str ):
    '''
        get other list (mode = other and submode = accepted) in notification format by userId and order by date time
        input: userId (str)
        output: dict of notification list
        for example of other mode:
        {
            "userId": "js8974",
            "mode": "other",
            "dataList": [
            {
                "notiId": "other03",
                "dateTime": "2024-10-25T14:10:05",
                "subMode": "accepted",
                "amount": null,
                "lockId": "89046",
                "lockLocation": "Office",
                "lockName": "Office Door",
                "userName": "",
                "userSurname": "",
                "role": ""
            }
        ]
    }
    '''

    # connect to database
    otherCollection = db['Other']
    lockCollection = db['Locks']

    # get submode = sent
    others = list( otherCollection.find( { 'userId': userId, 'subMode': 'accepted' }, { '_id': 0 } ) )

    notificationList = {
        'userId': userId,
        'mode': 'other',
        'dataList': [
            {
                'notiId': other['otherId'],
                'dateTime': other['datetime'],
                'subMode': 'accepted',
                'amount': None,
                'lockId': other['lockId'],
                'lockLocation': lock['lockLocation'],
                'lockName': lock['lockName'],
                'userName': None,
                'userSurname': None,
                'role': None,
            }
            for other in others
            for lock in lockCollection.find( { 'lockId': other['lockId'] }, { '_id': 0 } )
        ]
    }

    return notificationList

# get notification(mode = warning and submode = main) list by userId
@app.get('/notification/warning/main/{userId}', tags=['Notifications'])
def get_warning_main_notification_list( userId: str ):
    '''
        get warning list(mode = warning and submode = main) in notification format by userId and order by datetime
        input: userId (str)
        output: dict of notification list
        for example of warning mode:
        {
            "userId": "js8974",
            "mode": "warning",
            "subMode": "main",
            "dataList": [
            {
                "dateTime": "2024-10-25T18:45:03",
                "amount": 2,
                "lockId": "12345",
                "lockLocation": "Home",
                "lockName": "Front Door",
                "error": null,
            },
            {
                "dateTime": "2024-10-25T15:27:18",
                "amount": 7,
                "lockId": "12345",
                "lockLocation": "Home",
                "lockName": "Garage",
                "error": null,
            },
            {
                "dateTime": "2024-10-25T12:34:56",
                "amount": 3,
                "lockId": "12345",
                "lockLocation": "Office",
                "lockName": "Office Door",
                "error": null,
            }
        ]
    }
    '''

    # connect to database
    warningCollection = db['Warning']
    lockCollection = db['Locks']
    userCollection = db['Users']

     # get user
    user = userCollection.find_one( { 'userId': userId }, { '_id': 0 } )

    # get lockId list that user is admin
    lockIdList = user['admin']

    warningList = list()

    # get request in notification format
    for lockId in lockIdList:
        lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
        latestWarning = warningCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
        warningList.append(
            {
                'dateTime': latestWarning['datetime'],
                'amount': len( lock['warning'] ),
                'lockId': lockId,
                'lockLocation': lock['lockLocation'],
                'lockName': lock['lockName'],
                'error': None,
            }
        )

    # order by date time
    warningList = sorted( warningList, key = lambda x: x['dateTime'], reverse = True )

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'warning',
        'subMode': 'main',
        'dataList': notificationList
    }

    return notificationList

# get notification(mode = warning and submode = view) list by userId 
@app.get('/notification/warning/view/{userId}', tags=['Notifications'])
def get_warning_view_notification_list( userId: str ):
    '''
        get warning list(mode = warning and submode = view) in notification format by userId and order by date time
        input: userId (str)
        output: dict of notification list
        for example of warning mode:
        {
            "userId": "js8974",
            "mode": "warning",
            "subMode": "view",
            "dataList": [
            {
                "dateTime": "2024-10-25T18:45:03",
                "amount": null,
                "lockId": "12345",
                "lockLocation": "Home",
                "lockName": "Front Door",
                "error": "Attempt to access without permission"
            },
            {
                "dateTime": "2024-10-25T15:27:18",
                "amount": null,
                "lockId": "12345",
                "lockLocation": "Home",
                "lockName": "Front Door",
                "error": "Authentication failed"
            },
            ]
        }
    '''

    # connect to database
    warningCollection = db['Warning']
    lockCollection = db['Locks']
    userCollection = db['Users']

    # get user
    user = userCollection.find_one( { 'userId': userId }, { '_id': 0 } )

    # get lockId list that user is admin
    lockIdList = user['admin']

    warningList = list()

    # get warning in notification format
    for lockId in lockIdList:
        lock = lockCollection.find_one( { 'lockId': lockId }, { '_id': 0 } )
        warnings = list( warningCollection.find( { 'lockId': lockId }, { '_id': 0 } ) )
        for warning in warnings:
            warningList.append(
                {
                    'dateTime': warning['datetime'],
                    'amount': None,
                    'lockId': lockId,
                    'lockLocation': lock['lockLocation'],
                    'lockName': lock['lockName'],
                    'error': warning['error'],
                }
            )

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'warning',
        'subMode': 'view',
        'dataList': warningList
    }

    return notificationList

# Ignore risk attempt by delete warning by lockid
@app.delete('/delete/notification/warning/{lockId}', tags=['Notifications'])
@app.delete('/delete/notification/warning/{lockId}/{notiId}', tags=['Notifications'])
def delete_warning_notification( lockId: str, notiId: str = None ):
    '''
        delete warning notification by notiId and lockId
        if not sent notiId = delete all warning by lockId
        if sent notiId = delete warning by notiId and lockId
        input: lockId (int) and notiId (str)(optional)
        output: dict of notification
        for example:
        {
            "notiId": "req01",
            "lockId": "12345",
            "message": "Delete notification successfully"
        }
    '''

    # connect to database
    lockCollection = db['Locks']

    # delete warning notification of lock
    # in case notiId is None
    if not notiId:
        # delete all of warningId in warning list
        lockCollection.update_one( { 'lockId': lockId }, { '$set': { 'warning': [] } } )

        return { 'lockId': lockId, 'message': 'Delete all notification successfully' }

    # in case notiId is not None
    else:
        # delete warningId of warning list of lock
        lockCollection.update_one( { 'lockId': lockId }, { '$pull': { 'warning': { 'reqId': notiId } } } )

        return { 'notiId': notiId, 'lockId': lockId, 'message': 'Delete notification successfully' }

# delete notification of invitation by lockId
# change invitation status to declined
@app.delete('/delete/notification/invitation/{lockId}', tags=['Notifications'])
def delete_invitation_notification( lockId: str ):
    '''
        delete invitation notification by lockId and change invitation status to declined
        post new history to lock?
        change status of invitation to declined

        input: lockId (int)
        output: dict of invitation notification
        for example:
        {
            "lockId": "12345",
            "message": "Delete invitation notification successfully"
        }
    '''

    # connect to database
    inviteCollection = db['Invitation']

    # delete invitation notification by lockId
    inviteCollection.update_many( { 'lockId': lockId }, { '$set': { 'invStatus': 'declined' } } )

    return { 'lockId': lockId, 'message': 'Delete invitation notification successfully' }


# accept request 
@app.put('/acceptRequest/{reqId}', tags=['Accept Request'])
def accept_request( reqId: str ):
    '''
        accept request by update request status to accepted and 
        add user to lock by append user to member role
        add location to lock location list
        input: reqId (str)
        output: dict of request
        for example:
        {
            "reqId": "req01",
            "message": "Accept request successfully"
        }
    '''

    # connect to database
    collection = db['Request']
    lockCollection = db['Locks']
    userCollection = db['Users']

    # get request by reqId
    request = collection.find_one( { 'reqId': reqId }, { '_id': 0 } )
    if not request:
        raise HTTPException( status_code = 404, detail = "Request not found" )

    # update request status to accepted
    collection.update_one( { 'reqId': reqId }, { '$set': { 'requestStatus': 'accepted' } } )

    # add user to lock
    # NOTE: add user to lock by append user to guest role
    lockCollection.update_one( { 'lockId': request['lockId'] }, { '$push': { 'roleToUserIdListDict.guest': request['userId'] } } )
    userCollection.update_one( { 'userId': request['userId'] }, { '$push': { 'userRoleToLockIdListDict.guest': request['lockId'] } } )

    # add location to lock location list in user
    # NOTE: add location to lock location list
    userCollection.update_one( { 'userId': request['userId'] }, { '$push': { 'lockLocationList': request['lockLocation'] } } )

    return { 'reqId': reqId, 'message': 'Accept request successfully' }