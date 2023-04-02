import os
import logging
import shutil

class IgnoreFilesAndTmpFolder():
    def ignore_folder(self,path : str):
        _, name = os.path.split(path)
        if name.lower() in ["tmp","temp"]:
            return True
        return False
    def ignore_file(self,_ : str):
        return True
    
class IgnorePythonIgnores():
    def ignore_folder(self,_ : str):
        return False
    def ignore_file(self,path : str):
        _, name = os.path.split(path)
        if name.lower() in ["__pycache__"]:
            return True
        return False


class ProjectCopier:

    def __init__(self,source_path : str,target_path : str):
        self.source_path = source_path
        self.target_path = target_path

    def create_path(self,path : str):
        if not os.path.exists(path):
            os.makedirs(path)

    def copy(self):
        self.copy_folder(s_path = self.source_path,t_path = self.target_path,ignore = IgnoreFilesAndTmpFolder())

    def copy_folder(self,s_path : str,t_path : str,ignore):

        logging.info(f"Copy {s_path} to {t_path} {type(ignore)}")

        for file in os.listdir(s_path):
            source = os.path.join(s_path,file)
            target = os.path.join(t_path,file)

            if os.path.isdir(source):
                if ignore.ignore_folder(source): continue
                # Copy folder
                self.create_path(target)
                self.copy_folder(source,target,ignore = IgnorePythonIgnores())

            if os.path.isfile(source):
                if ignore.ignore_file(source): continue
                # Copy file
                shutil.copyfile(source, target)



