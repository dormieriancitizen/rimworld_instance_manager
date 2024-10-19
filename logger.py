from colorama import Fore, Back, Style
from colorama import init as colorama_init
colorama_init()

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class Logger(object):
    __metaclass__ = Singleton
    def info(self,log):
        print(Style.DIM+log+Style.RESET_ALL)

    def log(self,log):
        print(log)

    def error(self,log):
        print(log)

    def warn(self,log):
        print(log)