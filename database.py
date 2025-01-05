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
    userImage: Optional[str] = None

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
    lockName: str
    lockLocation: str
    lockImage: str
    requestStatus: str
    datetime: datetime

# class for new request
class NewRequest( BaseModel ):
    userId: str
    lockId: str
    lockName: str
    lockLocation: str
    lockImage: str

# class for accept request
class AcceptRequest( BaseModel ):
    reqId: str
    expireDatetime: datetime

# class for accept request
class AcceptAllRequest( BaseModel ):
    lockId: str
    expireDatetime: datetime

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

# class for accept invitation
class AcceptInvitation( BaseModel ):
    invId: str
    lockName: str
    lockLocation: str
    lockImage: str

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

# class for new warning
class NewWarning( BaseModel ):
    userId: str
    userRole: Optional[str] = None
    lockId: str

# class for guest
class Guest( BaseModel ):
    userId: str
    lockId: str
    lockName: str
    lockLocation: str
    lockImage: str
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
    securityStatus: str
    admin: List[ str ]
    member: List[ str ]
    guest: List[ Guest ]
    invitation: List[ str ]
    request: List[ str ]
    history: List[ str ]
    connect: List[ str ]
    warning: List[ str ]

# class for lock details
class LockDetail( BaseModel ):
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
    admin: List[ LockDetail ]
    member: List[ LockDetail ]
    guest: List[ Guest ]

# class for user edit profile
class UserEditProfile( BaseModel ):
    userId: str
    newEmail: Optional[str] = None
    newFirstName: Optional[str] = None
    newLastName: Optional[str] = None
    newImage: Optional[str] = None

# class for user change password
class UserChangePassword( BaseModel ):
    userId: str
    currentPassword: str
    newPassword: str