##############################################################
#
#   import section
#

from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

##############################################################
#
#   Class OOP
#


class User_Signup( BaseModel ):
    email: str
    password: str
    firstName: str
    lastName: str

# class for history
class History( BaseModel ):
    id: int
    userId: str
    lockId: int
    lockStatus: str
    time: datetime

# class for request
class Request( BaseModel ):
    reqId: str
    userId: str
    lockId: str
    requestStatus: str
    datetime: datetime

# class for new request
class NewRequest( BaseModel ):
    userId: str
    lockId: str

# class for new invitation
class NewInvitation( BaseModel ):
    srcUserId: str
    desUserId: str
    userRole: str
    lockId: str
    dateTime: datetime

# class for invitation
class Invitation( BaseModel ):
    id: str
    userId: str
    userCode : int
    userRole: str
    lockId: str
    lockLocation: str
    time: datetime
    expireTime: datetime

# class for connection
class Connection( BaseModel ):
    conId: str
    userId: str
    userRole: str
    lockId: str
    datetime: datetime

# class for other
class Other( BaseModel ):
    otherId: int
    subMode: str
    userId: str
    userRole: str
    lockId: str
    datetime: datetime

# class for warning
class Warning( BaseModel ):
    warningId: int
    subMode: str
    userId: str
    userRole: str
    lockId: str
    lockLocation: str
    datetime: datetime
    securityStatus: str

# class for notification
# NOTE: should it be have??? or 1. seperate to request invite warning 2. everything collect in notofication but seperate by mode
class Notification( BaseModel ):
    notiId: int
    mode: str
    datetime: datetime
    subMode: str
    amount: int
    type: str
    userId: str
    userRole: str
    lockId: str
    lockLocation: str
    lockName: str

# class for users role
class UserRole( BaseModel ):
    userId: str
    userName: str
    userImage: str
    userRole: str
    datetime: datetime

# class for new lock
class NewLock( BaseModel ):
    userId: str
    lockId: int
    lockName: str
    lockLocation: str
    lockImage: str

# class for locks
class Lock( BaseModel ):
    lockId: int
    lockName: str
    lockImage: str
    lockStatus: str
    lockLocation: str
    securityStatus: str
    roleToUserIdListDict: Dict[ str, List[ str ] ] # role : userIdList
    invitation: List[ Invitation ]
    request: List[ Request ]
    history: List[ History ]
    warning: List[ Warning ]

# class for lock details
class LockDetails( BaseModel ):
    lockId: int
    lockName: str
    lockLocation: str
    lockImage: str

# class for users
class User( BaseModel ):
    id: int
    firstName: str
    lastName: str
    email: str
    userImage: str
    password_hash: str
    salt: str
    userId: str
    userCode: int
    lockLocationList: List[ str ]
    userRoleToLockIdListDict: Dict[ str, List[ str ] ] # userRole: LockIdList
