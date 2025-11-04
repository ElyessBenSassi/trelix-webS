class Person:
    def __init__(self, uri: str, name: str, email: str, age: int = None, role: str = None, role_uri: str = None, role_label: str = None):
        self.uri = uri
        self.name = name
        self.email = email
        self.age = age
        self.role = role
        self.role_uri = role_uri
        self.role_label = role_label
    
    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "role": self.role
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Person':
        return cls(
            uri=data.get("uri", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            age=data.get("age"),
            role=data.get("role") or data.get("role_uri"),  # Support both
            role_uri=data.get("role_uri"),
            role_label=data.get("role_label")
        )
    
    def __str__(self):
        return f"Person: {self.name}"
    
    def __repr__(self):
        return f"Person(uri='{self.uri}', name='{self.name}', email='{self.email}', age={self.age}, role='{self.role}')"
