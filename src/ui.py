from enum import IntEnum

class ErrorChoice(IntEnum):
    IGNORE = 0
    IGNORE_ALL = 1
    STOP = 2

class UserInterface:
    def error(self, msg: str) -> None:
        pass
    
    def error_choice(self, msg: str) -> ErrorChoice:
        pass

class ConsoleUI(UserInterface):
    def error(self, msg: str) -> None:
        print(msg)
        
    def error_choice(self, msg: str) -> ErrorChoice:
        print(f"Error: {msg}")
        print("0: Ignore and continue")
        print("1: Always ignore errors")
        print("2: Stop operation")
        while True:
            try:
                choice = int(input("Your choice: "))
                return ErrorChoice(choice)
            except ValueError:
                print("Please enter a valid number (0-2)")
