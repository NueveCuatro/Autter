from utils.utils_c2 import foo

class Content():
    def __init__(self):
        self.requires_data = False
        print("content class instanciated=================")
    
    def run(self):
        test = foo()
        return("This is the content ===============")