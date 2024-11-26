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

# class for users role
class UserRole( BaseModel ):
    id: int
    roleName: str
    userLocks: List[ Lock ]

# class for users
class User( BaseModel ):
    id: int
    firstName: str
    lastName: str
    email: str
    password_hash: str
    salt: str
    userCode: str
    userRole: Dict[ str, str ] # userRole: lockId

# class for locks
class Lock( BaseModel ):
    id: int
    lockName: str
    lockStatus: str
    admin: List[ User ]
    members: List[ User ]
    guest: List[ User ]
    request: List[ Request ]
    history: List[ History ]
    time: datetime
    lockLocation: str
    image: str

# class for history
class History( BaseModel ):
    id: int
    userId: int
    lockId: int
    lockStatus: str
    time: datetime

# class for request
class Request( BaseModel ):
    id: int
    userId: int
    userRole: str
    lockId: int
    requestStatus: str
    time: datetime
    expireTime: datetime

# class for notification
class Notification( BaseModel ):
    id: int
    type: str
    userId: int
    userRole: str
    lockId: int
    time: datetime
    request: List[ Request ]
    warning: List[ Warning ]
    invitation: List[ Invitation ]

# class for invitation
class Invitation( BaseModel ):
    id: int
    userId: int
    userRole: str
    lockId: int
    lockLocation: str
    time: datetime
    expireTime: datetime

# class for warning
class Warning( BaseModel ):
    id: int
    userId: int
    userRole: str
    lockId: int
    lockLocation: str
    time: datetime
    securityStatus: str
