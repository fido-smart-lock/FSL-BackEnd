from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Dict
import requests
import os
import hashlib, uuid
from datetime import datetime
from database import User, Lock, History, Request, User_Signup, NewLock, NewRequest, NewInvitation, Invitation, Other
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
# NOTE: if lockLocationActiveStr is None, set lockLocationActiveStr to first element of lockLocationList
# NOTE: if lockLocationActiveStr is None, set path to /lockList/{userId}/None
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

    # get lock
    lock = collection.find_one( { 'lockId': lockId }, { '_id': 0 } )
    if not lock:
        raise HTTPException( status_code = 404, detail = "Lock not found" )
    
    # get dict of history by lockId
    historyByLockId = {
        'lockId': lock['lockId'],
        'lockName': lock['lockName'],
        'lockLocation': lock['lockLocation'],
        'dataList': [
            {
                'userImage': user['userImage'] if user else None,
                'dateTime': history['datetime'],
                'userName': user['firstName'] + ' ' + user['lastName'] if user else None,
                'status': history['status']
            }
            for history in lock['history']
            for user in userCollection.find( { 'userId': history['userId'] }, { '_id': 0 } )
        ]
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

    # if lock is already exists
    if collection.find_one( { 'lockId': new_lock.lockId } ):
        raise HTTPException( status_code = 400, detail = "Lock already exists" )
    
    # if user is already have this lockId
    if userCollection.find_one( { 'userId': new_lock.userId, 'userRoleToLockIdListDict.admin': new_lock.lockId } ):
        raise HTTPException( status_code = 400, detail = "User already have this lock" )

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
@app.get('/notification/request/{userId}', tags=['Notifications'])
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

    # get all request
    requests = list( collection.find( { 'userId': userId }, { '_id': 0 } ) )

    # get request in notificaton format
    requestList = [
        {
            'notiId': request['reqId'],
            'dateTime': request['datetime'],
            'subMode': None,
            'amount': len( lock['request'] ),
            'lockId': request['lockId'],
            'lockLocation': lock['lockLocation'],
            'lockName': lock['lockName'],
            'userName': user['firstName'],
            'userSurname': user['lastName'],
            'role': None,
        }
        for request in requests
        for user in userCollection.find( { 'userId': request['userId'] }, { '_id': 0 } )
        for lock in lockCollection.find( { 'lockId': request['lockId'] }, { '_id': 0 } )
    ]

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'req',
        'dataList': requestList
    }

    return notificationList

# get notification connection mode list by userId
app.get('/notification/connection/{userId}', tags=['Notifications'])
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
    collection = db['Connect']
    userCollection = db['Users']
    lockCollection = db['Locks']

    # get all connect
    connects = list( collection.find( { 'userId': userId }, { '_id': 0 } ) )

    # get connect in notificaton format
    connectList = [
        {
            'notiId': connect['connectId'],
            'dateTime': connect['datetime'],
            'subMode': None,
            'amount': None,
            'lockId': connect['lockId'],
            'lockLocation': lock['lockLocation'],
            'lockName': lock['lockName'],
            'userName': user['firstName'],
            'userSurname': user['lastName'],
            'role': None,
        }
        for connect in connects
        for user in userCollection.find( { 'userId': connect['userId'] }, { '_id': 0 } )
        for lock in lockCollection.find( { 'lockId': connect['lockId'] }, { '_id': 0 } )
    ]

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'connect',
        'dataList': connectList
    }

    return notificationList

# # get notification other mode list by userId
# @app.get('/notification/other/{userId}', tags=['Notifications'])
# def get_other_notification_list( userId: str ):
    '''
        get other list in notification format by userId and order by date time
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

# get notification warning mode list by userId
@app.get('/notification/warning/view/{userId}', tags=['Notifications'])
def get_warning_main_notification_list( userId: str ):
    '''
        get warning list in notification format by userId and order by date time
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
    collection = db['Warning']
    lockCollection = db['Locks']

    # get all warning
    warnings = list( collection.find( { 'userId': userId }, { '_id': 0 } ) )

    # get warning in notificaton format
    warningList = [
        {
            'dateTime': warning['datetime'],
            'amount': len( lock['warning'] ),
            'lockId': warning['lockId'],
            'lockLocation': lock['lockLocation'],
            'lockName': lock['lockName'],
            'error': warning['error'],
        }
        for warning in warnings
        for lock in lockCollection.find( { 'lockId': warning['lockId'] }, { '_id': 0 } )
    ]

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'warning',
        'subMode': 'main',
        'dataList': warningList
    }

    return notificationList

# get notification warning mode list by userId 
@app.get('/notification/warning/view/{userId}', tags=['Notifications'])
def get_warning_view_notification_list( userId: str ):
    '''
        get warning list in notification format by userId and order by date time
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
    collection = db['Warning']
    lockCollection = db['Locks']

    # get all warning
    warnings = list( collection.find( { 'userId': userId }, { '_id': 0 } ) )

    # get warning in notificaton format
    warningList = [
        {
            'dateTime': warning['datetime'],
            'amount': None,
            'lockId': warning['lockId'],
            'lockLocation': lock['lockLocation'],
            'lockName': lock['lockName'],
            'error': warning['error'],
        }
        for warning in warnings
        for lock in lockCollection.find( { 'lockId': warning['lockId'] }, { '_id': 0 } )
    ]

    # get dict of notification list
    notificationList = {
        'userId': userId,
        'mode': 'warning',
        'subMode': 'view',
        'dataList': warningList
    }

    return notificationList

# delete notification by notiId in interested lockid
@app.delete('/notification/{notiId}/{lockId}', tags=['Notifications'])
def delete_notification( notiId: str, lockId: str ):
    '''
        delete notification by notiId and lockId
        input: notiId (str) and lockId (int)
        output: dict of notification
        for example:
        {
            "notiId": "req01",
            "lockId": "12345",
            "message": "Delete notification successfully"
        }
    '''

    # connect to database
    collection = db['Request']
    lockCollection = db['Locks']

    # delete notification by notiId
    collection.delete_one( { 'reqId': notiId } )

    # delete notification to lock
    # NOTE: delete notification in request list of lock
    lockCollection.update_one( { 'lockId': lockId }, { '$pull': { 'request': { 'reqId': notiId } } } )

    return { 'notiId': notiId, 'lockId': lockId, 'message': 'Delete notification successfully' }

# Ignore all risk attempt by delete warning by lockid
@app.delete('/warning/ignore/{lockId}', tags=['Notifications'])
def Ignore_all_risk_attempt( lockId: str ):
    '''
        Ignore all risk attempt by delete warning by lockId
        input: lockId (int)
        output: dict of warning
        for example:
        {
            "lockId": "12345",
            "message": "Ignore warning successfully"
        }
    '''

    # connect to database
    collection = db['Warning']
    lockCollection = db['Locks']

    # delete warning by warningId
    collection.delete_one( { 'lockId': lockId } )

    # delete warning to lock
    # NOTE: delete warning in warning list of lock
    lockCollection.update_one( { 'lockId': lockId }, { '$pull': { 'warning': { 'lockId': lockId } } } )

    return { 'lockId': lockId, 'message': 'Ignore warning successfully' }

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