##############################################################
#
#   import section
#

from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from typing import Optional

##############################################################
#
#   Class OOP
#


class UserSignup( BaseModel ):
    email: str
    password: str
    firstName: str
    lastName: str
    userImage: str

# class for history
class History( BaseModel ):
    hisId: str
    userId: str
    lockId: str
    status: str
    datetime: datetime

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
    role: str
    lockId: str
    dateTime: Optional[datetime] = None

# class for invitation
class Invitation( BaseModel ):
    invId: str
    srcUserId: str
    desUserId: str
    role: str
    lockId: str
    datetime: datetime
    invStatus: str

# class for connection
class Connection( BaseModel ):
    conId: str
    userId: str
    userRole: str
    lockId: str
    datetime: datetime

# class for other
class Other( BaseModel ):
    otherId: str
    subMode: str
    amount: Optional[int] = None
    userId: str
    userRole: Optional[str] = None
    lockId: str
    datetime: datetime

# class for warning
class Warning( BaseModel ):
    warningId: str
    # subMode: str
    userId: str
    userRole: str
    lockId: str
    datetime: datetime
    securityStatus: str
    message: str

# # class for notification
# # NOTE: should it be have??? or 1. seperate to request invite warning 2. everything collect in notofication but seperate by mode
# class Notification( BaseModel ):
#     notiId: int
#     mode: str
#     datetime: datetime
#     subMode: str
#     amount: int
#     type: str
#     userId: str
#     userRole: str
#     lockId: str
#     lockLocation: str
#     lockName: str

# class for guest
class Guest( BaseModel ):
    userId: str
    lockId: str
    expireDatetime: datetime

# class for new lock
class NewLock( BaseModel ):
    userId: str
    lockId: str
    lockName: str
    lockLocation: str
    lockImage: str

# class for locks
class Lock( BaseModel ):
    lockId: str
    lockName: str
    lockImage: str
    lockLocation: str
    securityStatus: str
    admin: List[ str ]
    member: List[ str ]
    guest: List[ Guest ]
    invitation: List[ str ]
    request: List[ str ]
    history: List[ str ]
    connect: List[ str ]
    warning: List[ str ]
    other: List[ str ]

# class for lock details
class LockDetails( BaseModel ):
    lockId: str
    lockName: str
    lockLocation: str
    lockImage: str

# class for users
class User( BaseModel ):
    firstName: str
    lastName: str
    email: str
    userImage: str
    password_hash: str
    salt: str
    userId: str
    userCode: int
    lockLocationList: List[ str ]
    admin: List[ str ]
    member: List[ str ]
    guest: List[ Guest ]

# class for user edit profile
class UserEditProfile( BaseModel ):
    userId: str
    newEmail: str
    newFirstName: str
    newLastName: str