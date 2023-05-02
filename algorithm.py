class Algorithm:
    def __init__(self, id, name, location, description, author, link, outcomes, code):
        self.id = id
        self.name = name
        self.location = location
        self.description = description
        self.author = author
        self.link = link
        self.outcomes = outcomes
        self.code = code

    def get_info(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "author": self.author,
            "link": self.link,
            "outcomes": self.outcomes
        }

    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id
    
    def get_description(self):
        return self.description
    
    def get_location(self):
        return self.location
    
    def execute(self, data):
        return self.code(data)
