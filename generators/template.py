import pkgutil

class Template:

    def __init__(self,path):
        self.data = pkgutil.get_data(__package__, path).decode('utf-8')

    def replace(self,pattern,repl):
        
        if type(repl) is str:
            self.data = self.data.replace(pattern,repl)
            return
        
        if type(repl) is list:
            new_data = []
            for line in self.data.split("\n"):
                ix = line.find(pattern)
                if ix == -1:
                    new_data.append(line)
                    continue
                for r in repl:
                    new_data.append(f"{' ' * ix}{r}")

            self.data = '\n'.join(new_data)
            return
        
        raise ValueError(f"Unknown type for replacement {type(repl)}")

        
    def content(self):
        return self.data