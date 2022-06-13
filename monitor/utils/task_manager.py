"""
Module for task managing with file based system
"""


import os
from django.conf import settings
from typing import Tuple


class ErrorReadingFile(Exception):
    """
    Error reading file from file path
    """


class ErrorWritingFile(Exception):
    """
    Error writing file to file path
    """


class FileBasedManager:
    def __init__(
        self, directory: str = 'file-base-manager',
        file_name: str = 'file.log'
    ) -> None:
        self.__directory = os.path.join(settings.BASE_DIR, directory)
        self.__file_name = file_name
        self.create_paths()

    def create_paths(self):
        """
        Creates the manager file and directory
        """

        if os.path.isdir(self.__directory) is False:
            os.makedirs(self.__directory)
        if os.path.isfile(self.get_file_path()) is False:
            self.set_empty_file()

    def get_file_path(self):
        return os.path.join(self.__directory, self.__file_name)

    def read(self) -> list:
        try:
            with open(self.get_file_path()) as file:
                content = file.read()
                content = content.split(',')
                return content
        except Exception as e:
            raise ErrorReadingFile(e)

    def write(self, content: list):
        try:
            with open(self.get_file_path(), 'w') as file:
                content = ','.join(content)
                file.write(content)
        except Exception as e:
            raise ErrorWritingFile(e)

    def set_empty_file(self):
        self.write([])

    def delete_manager(self):
        if os.path.isdir(self.__directory):
            if os.path.isfile(self.get_file_path()):
                os.remove(self.get_file_path())
            os.rmdir(self.__directory)


class TaskAlreadyActive(Exception):
    """
    Task already active
    """


class Task:
    def __init__(self, task_id: str) -> None:
        self.__id = task_id

    def set_manager(self, manager: FileBasedManager):
        self.__manager = manager

    def add_task(self):
        active, tasks = self.is_task_active()
        if active:
            raise TaskAlreadyActive
        tasks.append(self.__id)
        self.__manager.write(tasks)

    def is_task_active(self) -> Tuple[bool, list]:
        tasks = self.__manager.read()
        is_active = self.__id in tasks
        return is_active, tasks

    def delete_task(self):
        active, tasks = self.is_task_active()
        if active:
            tasks.remove(self.__id)
            self.__manager.write(tasks)
