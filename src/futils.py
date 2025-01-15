import os
from typing import Callable
from src.ui import UserInterface, ErrorChoice
from pathlib import Path

class FileListProvider:
    def subset(indices: list[int]) -> list[str]:
        pass


class FileSelection:
    def get_and_reset() -> list[str]:
        pass


class FileSystem:
    def copy(src: str, dest: str) -> None:
        pass

    def move(src: str, dest: str) -> None:
        pass

    def delete(path: str) -> None:
        pass


class FileSelector(FileSelection):
    def __init__(self):
        self.selected_files = []
    
    def select_files_by_indices(self, indices: list[int], file_explorer: FileListProvider) -> list[str]:
        """Select files based on indices"""
        try:
            self.selected_files = file_explorer.subset(indices)
            
            print("Selected files:")
            for file in self.selected_files:
                print(f" - {os.path.basename(file)}")
            
            return self.selected_files
        except Exception as e:
            print(f"Error selecting files: {e}")
            return []
 
    def get_and_reset(self) -> list[str]:
        """Return the list of currently selected files"""
        res = self.selected_files.copy()
        self.selected_files.clear()
        return res


class FileExplorer(FileListProvider):
    def __init__(self):
        self._set_current_path(os.path.expanduser('~'))

    def _set_current_path(self, path: str) -> None:
        """Set current path and update the contents of the current directory"""
        self.current_path = path
        self.current_directory_contents = os.listdir(self.current_path)

    def display_directory_contents(self) -> None:
        """Display contents of the current directory"""
        try:
            print(f"\nCurrent Directory: {self.current_path}")
            print("-" * 50)
            for index, element in enumerate(self.current_directory_contents):
                full_path = os.path.join(self.current_path, element)
                element_type = "📁 Folder" if os.path.isdir(full_path) else "📄 File"
                print(f"{index}. {element_type}: {element}")
        except PermissionError:
            print("Access denied to this directory.")
        except Exception as e:
            print(f"Error: {e}")

    def navigate(self, index: int) -> None:
        """Navigate to a subdirectory"""
        try:
            selected_element = self.current_directory_contents[index]
            full_path = os.path.join(self.current_path, selected_element)
            
            if os.path.isdir(full_path):
                self._set_current_path(full_path)
                self.display_directory_contents()
            else:
                print(f"Cannot open file {selected_element}")
        except Exception as e:
            print(f"Navigation error: {e}")

    def go_to_parent_directory(self) -> None:
        """Move to the parent directory"""
        self._set_current_path(os.path.dirname(self.current_path))
        self.display_directory_contents()

    def subset(self, indices: list[int]) -> list[str]:
        """Return a subset of the current directory contents"""
        selected_files = []
        for index in indices:
            if 0 <= index < len(self.current_directory_contents):
                full_path = os.path.join(self.current_path, self.current_directory_contents[index])
                selected_files.append(full_path)
        return selected_files


class FileManager:
    def __init__(self, file_selection: FileSelection, file_system: FileSystem, user_interface: UserInterface):
        self.sel = file_selection
        self.fs = file_system
        self.ui = user_interface
        self.ignore_all_errors = False

    def _validate_path(self, path: str) -> bool:
        """Validate if a path is acceptable.
        
        Args:
            path: The path to validate
            
        Returns:
            bool: True if path is valid, False otherwise
        """
        try:
            # Vérifie la longueur du chemin
            if len(str(Path(path))) > 255:  # ou utilisez os.pathconf('/', 'PC_PATH_MAX') sur Unix
                raise OSError("Path too long")
                
            # Vérifie si le chemin contient des caractères valides
            Path(path).resolve()
            
            return True
        except (OSError, ValueError) as e:
            self.ui.error(f"Invalid path: {str(e)}")
            return False

    def _handle_operation_error(self, operation: str, error: Exception) -> ErrorChoice:
        """Handle file operation errors.
        
        Args:
            operation: The operation being performed ('Copy', 'Move', 'Delete')
            error: The exception that occurred
            
        Returns:
            ErrorChoice: User's decision on how to handle the error
        """
        error_msg = f"{operation}: {str(error)}"
        self.ui.error(error_msg)
        
        if not self.ignore_all_errors:
            return self.ui.error_choice(error_msg)
        return ErrorChoice.IGNORE_ALL

    def copy_files(self, destination: str) -> int:
        """Copy selected files to destination.
        
        Args:
            destination: Destination path for the files
            
        Returns:
            int: Number of successfully copied files
        """
        if not self._validate_path(destination):
            return 0
            
        success_count = 0
        files = self.sel.get_and_reset()
        
        for file in files:
            if not self._validate_path(file):
                continue
                
            try:
                self.fs.copy(file, destination)
                success_count += 1
            except Exception as e:
                choice = self._handle_operation_error("Copy", e)
                
                if choice == ErrorChoice.STOP:
                    break
                elif choice == ErrorChoice.IGNORE_ALL:
                    self.ignore_all_errors = True
                    
        return success_count

    def move_files(self, destination: str) -> int:
        """Move selected files to destination.
        
        Args:
            destination: Destination path for the files
            
        Returns:
            int: Number of successfully moved files
        """
        if not self._validate_path(destination):
            return 0
            
        success_count = 0
        files = self.sel.get_and_reset()
        
        for file in files:
            if not self._validate_path(file):
                continue
                
            try:
                self.fs.move(file, destination)
                success_count += 1
            except Exception as e:
                choice = self._handle_operation_error("Move", e)
                
                if choice == ErrorChoice.STOP:
                    break
                elif choice == ErrorChoice.IGNORE_ALL:
                    self.ignore_all_errors = True
                    
        return success_count

    def delete_files(self) -> int:
        """Delete selected files.
        
        Returns:
            int: Number of successfully deleted files
        """
        success_count = 0
        files = self.sel.get_and_reset()
        
        for file in files:
            if not self._validate_path(file):
                continue
                
            try:
                self.fs.delete(file)
                success_count += 1
            except Exception as e:
                choice = self._handle_operation_error("Delete", e)
                
                if choice == ErrorChoice.STOP:
                    break
                elif choice == ErrorChoice.IGNORE_ALL:
                    self.ignore_all_errors = True
                    
        return success_count
