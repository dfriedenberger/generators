import chevron

class Template:

    def __init__(self,path):
        with open(path,'r',encoding="UTF-8") as f:
            self.data = f.read()
        self.context = {}
    
    def set_context(self,context):
        self.context = context

    def set(self,key,value):
        self.context[key] = value
        
    def content(self):
        return chevron.render(self.data, self.context)