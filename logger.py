from colorama import Fore, Back, Style, init
init()

LOG_LEVELS = {
    "error": 0,
    "warn": 1,
    "log": 2,
    "info": 3,
    "debug": 4
}

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class Logger(object):
    __metaclass__ = Singleton

    def __init__(self,log_level=3):
        self.log_level = log_level

    def info(self,log):
        if self.log_level >= LOG_LEVELS["info"]:
            print(Style.DIM+log+Style.RESET_ALL)

    def log(self,log):
        if self.log_level >= LOG_LEVELS["log"]:
            print(log)

    def error(self,log):
        if self.log_level >= LOG_LEVELS["error"]:
            print(Fore.RED+log+Style.RESET_ALL)

    def warn(self,log):
        if self.log_level >= LOG_LEVELS["warn"]:
            print(Fore.YELLOW+log+Style.RESET_ALL)
