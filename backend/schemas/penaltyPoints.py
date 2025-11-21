import datetime
from backend.users.user import user

class PenaltyPoints:
    #class variables: 
    # points (int), user (user), reason (string), dateIssued (date)    
    def __init__(self, points: int, user: user, reason: str):
        self.points = points
        self.user = user
        self.reason = reason
        self.dateIssued = datetime.datetime.now()

    def __repr__(self):
        return (
            f"<PenaltyPoints user={self.user.username}, "
            f"points={self.points}, reason='{self.reason}'>"
        )
