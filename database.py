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
    id: int
    userId: str
    userRole: str
    lockId: int
    requestStatus: str
    time: datetime
    expireTime: datetime

# class for invitation
class Invitation( BaseModel ):
    id: int
    userId: str
    userCode : int
    userRole: str
    lockId: int
    lockLocation: str
    time: datetime
    expireTime: datetime

# class for warning
class Warning( BaseModel ):
    id: int
    userId: str
    userRole: str
    lockId: int
    lockLocation: str
    time: datetime
    securityStatus: str

# class for notification
class Notification( BaseModel ):
    id: int
    type: str
    userId: str
    userRole: str
    lockId: int
    time: datetime
    request: List[ Request ]
    warning: List[ Warning ]
    invitation: List[ Invitation ]

# class for users role
class UserRole( BaseModel ):
    userId: str
    userName: str
    userImage: str
    userRole: str
    datetime: datetime

# class for locks
class Lock( BaseModel ):
    lockId: int
    lockName: str
    lockStatus: str
    lockLocation: str
    securityStatus: str
    user: List[ UserRole ]
    invitation: List[ Invitation ]
    request: List[ Request ]
    history: List[ History ]
    time: datetime
    lockImage: str

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
    userRoleToLockListDict: Dict[ str, List[ LockDetails ] ] # userRole: LockList