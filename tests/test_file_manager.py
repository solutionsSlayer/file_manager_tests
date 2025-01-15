import pytest
from unittest.mock import MagicMock, call
from src.futils import FileManager, FileSelection, FileSystem
from src.ui import UserInterface, ErrorChoice

class MockFileSelection(FileSelection):
    def __init__(self, files_to_return=None):
        self.files_to_return = files_to_return or []

    def get_and_reset(self) -> list[str]:
        return self.files_to_return

class MockFileSystem(FileSystem):
    def copy(self, src: str, dest: str) -> None:
        pass
    
    def move(self, src: str, dest: str) -> None:
        pass
    
    def delete(self, path: str) -> None:
        pass

class MockUserInterface(UserInterface):
    def error(self, msg: str) -> None:
        pass

def test_file_manager_initialization():
    """Test the initialization of FileManager.
    
    Verifies that FileManager is properly initialized with the correct dependencies:
    - FileSelection
    - FileSystem
    - UserInterface
    """
    file_selection = MockFileSelection()
    file_system = MockFileSystem()
    user_interface = MockUserInterface()
    
    manager = FileManager(file_selection, file_system, user_interface)
    
    assert manager is not None
    assert manager.sel == file_selection
    assert manager.fs == file_system
    assert manager.ui == user_interface 

class TestFileManager:
    @pytest.fixture
    def setup_mocks(self):
        """Set up mock objects for testing.
        
        Returns:
            FileManager: A configured FileManager instance with mock dependencies.
        """
        self.test_files = ["file1.txt", "file2.txt"]
        self.selection = MockFileSelection(self.test_files)
        self.file_system = MockFileSystem()
        self.ui = MockUserInterface()
        
        self.file_system.copy = MagicMock()
        self.file_system.move = MagicMock()
        self.file_system.delete = MagicMock()
        self.ui.error = MagicMock()
        self.ui.error_choice = MagicMock(return_value=ErrorChoice.STOP)
        
        return FileManager(self.selection, self.file_system, self.ui)

    def test_delete_files_success(self, setup_mocks):
        """Test successful deletion of multiple files.
        
        Given:
            - A list of two files to delete
            - A properly configured file system
        When:
            - delete_files() is called
        Then:
            - Should return 2 (number of files deleted)
            - Should call delete() for each file
            - Should not report any errors
        """
        manager = setup_mocks
        
        result = manager.delete_files()
        
        assert result == 2
        assert self.file_system.delete.call_count == 2
        self.file_system.delete.assert_has_calls([
            call("file1.txt"),
            call("file2.txt")
        ])
        self.ui.error.assert_not_called()

    def test_delete_files_with_error(self, setup_mocks):
        """Test file deletion when an error occurs.
        
        Given:
            - A list of files to delete
            - File system throwing a permission error
        When:
            - delete_files() is called
        Then:
            - Should return 0 (no files deleted)
            - Should report the permission error
        """
        manager = setup_mocks
        self.file_system.delete.side_effect = OSError("Permission denied")
        
        result = manager.delete_files()
        
        assert result == 0
        assert call("Delete: Permission denied") in self.ui.error.call_args_list

    def test_copy_files_success(self, setup_mocks):
        """Test successful copying of multiple files.
        
        Given:
            - A list of two files to copy
            - A valid destination path
        When:
            - copy_files() is called with the destination
        Then:
            - Should return 2 (number of files copied)
            - Should call copy() for each file with correct destination
            - Should not report any errors
        """
        manager = setup_mocks
        destination = "/dest"
        
        result = manager.copy_files(destination)
        
        assert result == 2
        assert self.file_system.copy.call_count == 2
        self.file_system.copy.assert_has_calls([
            call("file1.txt", destination),
            call("file2.txt", destination)
        ])
        self.ui.error.assert_not_called()

    def test_copy_files_with_error(self, setup_mocks):
        """Test file copying when an error occurs.
        
        Given:
            - A list of files to copy
            - File system throwing a disk full error
        When:
            - copy_files() is called
        Then:
            - Should return 0 (no files copied)
            - Should report the disk full error
        """
        manager = setup_mocks
        destination = "/dest"
        self.file_system.copy.side_effect = OSError("Disk full")
        
        result = manager.copy_files(destination)
        
        assert result == 0
        assert call("Copy: Disk full") in self.ui.error.call_args_list

    def test_move_files_success(self, setup_mocks):
        manager = setup_mocks
        destination = "/dest"
        
        result = manager.move_files(destination)
        
        assert result == 2
        assert self.file_system.move.call_count == 2
        self.file_system.move.assert_has_calls([
            call("file1.txt", destination),
            call("file2.txt", destination)
        ])
        self.ui.error.assert_not_called()

    def test_move_files_with_error(self, setup_mocks):
        manager = setup_mocks
        destination = "/dest"
        self.file_system.move.side_effect = OSError("File locked")
        
        result = manager.move_files(destination)
        
        assert result == 0
        assert call("Move: File locked") in self.ui.error.call_args_list

    def test_empty_selection(self, setup_mocks):
        self.selection.files_to_return = []
        manager = setup_mocks
        
        assert manager.delete_files() == 0
        assert manager.copy_files("/dest") == 0
        assert manager.move_files("/dest") == 0
        
        self.file_system.delete.assert_not_called()
        self.file_system.copy.assert_not_called()
        self.file_system.move.assert_not_called() 

class TestFileManagerErrorHandling:
    @pytest.fixture
    def setup_mocks(self):
        self.test_files = ["file1.txt", "file2.txt", "file3.txt"]
        self.selection = MockFileSelection(self.test_files)
        self.file_system = MockFileSystem()
        self.ui = MockUserInterface()
        
        self.file_system.copy = MagicMock()
        self.file_system.move = MagicMock()
        self.file_system.delete = MagicMock()
        self.ui.error = MagicMock()
        self.ui.error_choice = MagicMock()
        
        return FileManager(self.selection, self.file_system, self.ui)

    def test_delete_files_ignore_error(self, setup_mocks):
        """Test file deletion with error ignoring behavior.
        
        Given:
            - Three files to delete
            - First file causes an error
            - User chooses to ignore the error
        When:
            - delete_files() is called
        Then:
            - Should return 2 (successful deletions)
            - Should attempt to delete all files
            - Should show error choice dialog once
        """
        manager = setup_mocks
        self.file_system.delete.side_effect = [
            OSError("Error with file1"),
            None,
            None 
        ]
        self.ui.error_choice.return_value = ErrorChoice.IGNORE
        
        result = manager.delete_files()
        
        assert result == 2
        assert self.file_system.delete.call_count == 3
        self.ui.error_choice.assert_called_once()

    def test_delete_files_ignore_all_errors(self, setup_mocks):
        """Test file deletion with ignore-all errors behavior.
        
        Given:
            - Three files to delete
            - All operations cause errors
            - User chooses to ignore all errors
        When:
            - delete_files() is called
        Then:
            - Should return 0 (no successful deletions)
            - Should attempt to delete all files
            - Should show error choice dialog once
        """
        manager = setup_mocks
        self.file_system.delete.side_effect = [
            OSError("Error 1"),
            OSError("Error 2"),
            OSError("Error 3")
        ]
        self.ui.error_choice.return_value = ErrorChoice.IGNORE_ALL
        
        result = manager.delete_files()
        
        assert result == 0
        assert self.file_system.delete.call_count == 3
        self.ui.error_choice.assert_called_once()

    def test_delete_files_stop_on_error(self, setup_mocks):
        manager = setup_mocks
        self.file_system.delete.side_effect = [
            None,
            OSError("Error with file2"),
            None
        ]
        self.ui.error_choice.return_value = ErrorChoice.STOP
        
        result = manager.delete_files()
        
        assert result == 1
        assert self.file_system.delete.call_count == 2
        self.ui.error_choice.assert_called_once() 

    def test_copy_files_with_special_characters(self, setup_mocks):
        manager = setup_mocks
        self.test_files = ["file with spaces.txt", "file#with#hash.txt"]
        self.selection.files_to_return = self.test_files
        destination = "/path/with spaces/dest"
        
        result = manager.copy_files(destination)
        
        assert result == 2
        self.file_system.copy.assert_has_calls([
            call("file with spaces.txt", destination),
            call("file#with#hash.txt", destination)
        ]) 

class TestFileManagerEdgeCases:
    @pytest.fixture
    def setup_mocks(self):
        """Set up mock objects for testing edge cases.
        
        Returns:
            FileManager: A configured FileManager instance with mock dependencies.
        """
        self.test_files = ["file1.txt", "file2.txt"]
        self.selection = MockFileSelection(self.test_files)
        self.file_system = MockFileSystem()
        self.ui = MockUserInterface()
        
        self.file_system.copy = MagicMock()
        self.file_system.move = MagicMock()
        self.file_system.delete = MagicMock()
        self.ui.error = MagicMock()
        self.ui.error_choice = MagicMock()
        
        return FileManager(self.selection, self.file_system, self.ui)

    def test_very_long_path_handling(self, setup_mocks):
        """Test handling of extremely long file paths.
        
        Given:
            - A file path that exceeds typical OS limits (> 255 characters)
            - A valid destination path
            - File system configured to throw OSError for long paths
        When:
            - copy_files() is called
        Then:
            - Should return 0 (no files copied)
            - Should report a path too long error
        """
        manager = setup_mocks
        very_long_name = "a" * 300 + ".txt"
        self.selection.files_to_return = [very_long_name]
        destination = "/dest"
        
        # Configure le mock pour lever une erreur lors de chemins trop longs
        self.file_system.copy.side_effect = OSError("File name too long")
        
        result = manager.copy_files(destination)
        
        assert result == 0
        assert "too long" in str(self.ui.error.call_args_list).lower()

    def test_handle_unicode_filenames(self, setup_mocks):
        """Test handling of files with Unicode characters in names.
        
        Given:
            - Files with emoji, accents, and special characters
            - A valid destination path
        When:
            - move_files() is called
        Then:
            - Should handle Unicode characters correctly
            - Should successfully move files with special characters
        """
        manager = setup_mocks
        unicode_files = ["🎉file.txt", "éèà.txt", "文件.txt", "файл.txt"]
        self.selection.files_to_return = unicode_files
        destination = "/dest"
        
        result = manager.move_files(destination)
        
        assert result == len(unicode_files)
        assert self.file_system.move.call_count == len(unicode_files)

    def test_handle_readonly_files(self, setup_mocks):
        """Test handling of read-only files.
        
        Given:
            - A read-only file
            - Attempt to delete the file
        When:
            - delete_files() is called
        Then:
            - Should handle permission error appropriately
            - Should show proper error message
        """
        manager = setup_mocks
        self.file_system.delete.side_effect = PermissionError("Read-only file")
        
        result = manager.delete_files()
        
        assert result == 0
        assert "read-only" in str(self.ui.error.call_args_list).lower()

    def test_handle_network_path(self, setup_mocks):
        """Test handling of network paths and timeouts.
        
        Given:
            - A network path destination
            - Network operation timing out
        When:
            - copy_files() is called
        Then:
            - Should handle network timeout gracefully
            - Should show appropriate error message
        """
        manager = setup_mocks
        destination = "//network/share/path"
        self.file_system.copy.side_effect = TimeoutError("Network timeout")
        
        result = manager.copy_files(destination)
        
        assert result == 0
        assert "timeout" in str(self.ui.error.call_args_list).lower()

    def test_handle_special_files(self, setup_mocks):
        """Test handling of special file types.
        
        Given:
            - Special files (symlinks, pipes, device files)
            - Attempt to copy these files
        When:
            - copy_files() is called
        Then:
            - Should handle special files appropriately
            - Should show relevant warnings or errors
        """
        manager = setup_mocks
        self.selection.files_to_return = [
            "symlink.lnk",
            "pipe",
            "device"
        ]
        self.file_system.copy.side_effect = [
            OSError("Invalid file type"),
            None,
            OSError("Device not supported")
        ]
        
        result = manager.copy_files("/dest")
        
        assert result == 1  # Only one successful copy
        assert self.ui.error.call_count == 2

    def test_concurrent_file_access(self, setup_mocks):
        """Test handling of files being accessed by other processes.
        
        Given:
            - A file that is locked by another process
            - Attempt to move the file
        When:
            - move_files() is called
        Then:
            - Should handle file lock gracefully
            - Should show appropriate error message
        """
        manager = setup_mocks
        self.file_system.move.side_effect = OSError("File is in use by another process")
        
        result = manager.move_files("/dest")
        
        assert result == 0
        assert "in use" in str(self.ui.error.call_args_list).lower() 