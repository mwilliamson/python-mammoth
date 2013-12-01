class Relationships(object):
    def __init__(self, relationships):
        self._relationships = relationships
    
    def __getitem__(self, key):
        return self._relationships[key]

class Relationship(object):
    def __init__(self, target):
        self.target = target
