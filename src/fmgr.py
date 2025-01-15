import os
import shutil
from src.ui import ConsoleUI
from .futils import FileSelector, FileExplorer, FileSystem, FileManager


class StdFileSystem(FileSystem):
    def copy(src: str, dest: str) -> None:
        """Copy a file from src to dest"""
        if os.path.exists(src):
            shutil.copy2(src, dest)

    def move(src: str, dest: str) -> None:
        """Move a file from src to dest"""
        if os.path.exists(src):
            shutil.move(src, dest)

    def delete(path: str) -> None:
        """Delete a file"""
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)


def main_menu():
    file_selector = FileSelector()
    file_manager = FileManager(file_selector, StdFileSystem(), ConsoleUI())
    file_explorer = FileExplorer()
    
    while True:
        print("\n--- File Explorer ---")
        print("1. Display Directory")
        print("2. Navigate")
        print("3. Go to Parent Directory")
        print("4. Select Files")
        print("5. Copy")
        print("6. Move")
        print("7. Delete")
        print("8. Quit")
        
        choice = input("Your choice: ")
        
        try:
            if choice == '1':
                file_explorer.display_directory_contents()
            
            elif choice == '2':
                index = int(input("Enter navigation index: "))
                file_explorer.navigate(index)
            
            elif choice == '3':
                file_explorer.go_to_parent_directory()
            
            elif choice == '4':
                file_explorer.display_directory_contents()
                indices = input("Enter file indices to select (comma-separated): ")
                file_selector.select_files_by_indices(indices, file_explorer)
            
            elif choice == '5':
                dest = input("Enter destination path for copying: ")
                count = file_manager.copy_files(dest)
                print(f"{count} file(s) copied")

            elif choice == '6':
                dest = input("Enter destination path for moving: ")
                count = file_manager.move_files(dest)
                print(f"{count} file(s) moved")
            
            elif choice == '7':
                count = file_manager.delete_files()
                print(f"{count} file(s)/folder(s) deleted")
            
            elif choice == '8':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice")
        
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main_menu()