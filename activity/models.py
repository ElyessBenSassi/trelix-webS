class Activity:
    def __init__(self, uri: str, activity_name: str, description: str = None, duration: int = None,
                 start_date: str = None, end_date: str = None, status: str = None, 
                 activity_type: str = None, instructor_uri: str = None, instructor_name: str = None):
        self.uri = uri
        self.activity_name = activity_name
        self.description = description
        self.duration = duration
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.type = activity_type
        self.instructor_uri = instructor_uri
        self.instructor_name = instructor_name
    
    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "activity_name": self.activity_name,
            "description": self.description,
            "duration": self.duration,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "type": self.type,
            "instructor_uri": self.instructor_uri,
            "instructor_name": self.instructor_name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Activity':
        return cls(
            uri=data.get("uri", ""),
            activity_name=data.get("activity_name", ""),
            description=data.get("description"),
            duration=data.get("duration"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            status=data.get("status"),
            activity_type=data.get("type"),
            instructor_uri=data.get("instructor_uri"),
            instructor_name=data.get("instructor_name")
        )
    
    def __str__(self):
        return f"Activity: {self.activity_name}"
    
    def __repr__(self):
        return f"Activity(uri='{self.uri}', activity_name='{self.activity_name}')"
