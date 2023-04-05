from .data_property import DataProperty
class DataStruct:

    def __init__(self,name : str):
        self.data_properties = []
        self.name = name

    def add_data_property(self,data_property : DataProperty):
        self.data_properties.append(data_property)

    def get_name(self):
        return self.name
    
    def get_data_properties(self):
        return self.data_properties

    def __repr__(self):
        return f"({self.name}, {self.data_properties})"
