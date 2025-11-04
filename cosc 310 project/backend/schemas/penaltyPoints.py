import datetime
from backend.schemas.user import user

class penaltyPoints:
    
    #class variables: 
    # points (int), user (user), reason (string), dateIssued (date)
    def __init__ (self, points: int, user: user, reason: str):
        self.points = points
        self.user = user
        self.reason = reason
        self.dateIssued = datetime.datetime.now
    
    def __repr__(self):
        return f"<penaltyPoints user={self.user.username}, points={self.points}, reason='{self.reason}'>"

