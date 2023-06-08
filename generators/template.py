import pkgutil
import chevron

class Template:

    def __init__(self,path):
        self.data = pkgutil.get_data(__package__, path).decode('utf-8')
        self.context = {}
    
    def set_context(self,context):
        self.context = context

    def set(self,key,value):
        self.context[key] = value
        
    def content(self):
        return chevron.render(self.data, self.context)