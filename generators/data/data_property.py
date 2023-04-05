
class DataProperty:

    def __init__(self,name : str,data_type : str,items : str):
        self.name = name
        self.data_type = data_type
        self.items = items
  
    def get_data_type(self):
        return self.data_type
    
    def get_items(self):
        return self.items
    
    def get_name(self):
        return self.name

    def __repr__(self):
        return f'({self.name}, {self.data_type}, {self.items})'