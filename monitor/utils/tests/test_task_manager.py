"""
Task and file manager test
"""

import os

from django.conf import settings
from django.test import SimpleTestCase
from utils.task_manager import (ErrorReadingFile, ErrorWritingFile,
                                FileBasedManager, Task)


class UtilityMixin:
    directory_path = 'test_file_manager'
    file_name = 'test.txt'

    def setUp(self) -> None:
        manager = FileBasedManager(
            directory=self.directory_path,
            file_name=self.file_name
        )
        self.manager = manager

    @property
    def manager_directory(self):
        return os.path.join(settings.BASE_DIR, self.directory_path)

    @property
    def file_path(self):
        return os.path.join(self.manager_directory, self.file_name)

    def tearDown(self) -> None:
        os.remove(self.file_path)
        os.rmdir(self.manager_directory)


class FileManagerTest(UtilityMixin, SimpleTestCase):
    def test_create_paths_delete_manager(self):
        self.manager.delete_manager()
        self.manager.create_paths()

    def test_get_file_path(self):
        computed = self.manager.get_file_path()
        self.assertEqual(self.file_path, computed)

    def test_write(self):
        self.manager.write(['a', 'b', 'c'])
        with open(self.file_path) as file:
            computed = file.read()
        self.assertEqual('a,b,c', computed)

        self.manager.write([''])
        with open(self.file_path) as file:
            computed = file.read()
        self.assertEqual('', computed)

        self.manager.write([])
        with open(self.file_path) as file:
            computed = file.read()
        self.assertEqual('', computed)

    def test_write_error(self):
        self.manager.delete_manager()
        with self.assertRaises(ErrorWritingFile):
            self.manager.write(['a', 'b'])
        self.manager.create_paths()

    def test_read_error(self):
        self.manager.delete_manager()
        with self.assertRaises(ErrorReadingFile):
            self.manager.read()
        self.manager.create_paths()

    def test_read(self):
        with open(self.file_path, 'w') as file:
            file.write('a,b,c')
        computed = self.manager.read()
        self.assertListEqual(computed, ['a', 'b', 'c'])

        with open(self.file_path, 'w') as file:
            file.write('')
        computed = self.manager.read()
        self.assertListEqual(computed, [])

    def test_set_empty_file(self):
        with open(self.file_path, 'w') as file:
            file.write('a,b,c,d,e,f,s,a,d,d,f')
        self.manager.set_empty_file()
        with open(self.file_path) as file:
            computed = file.read()
        self.assertEqual('', computed)


class TaskTest(UtilityMixin, SimpleTestCase):
    task_id = 'test_00_id'

    def setUp(self) -> None:
        super().setUp()
        self.task = Task(
            task_id=self.task_id,
            manager=self.manager)

    def test_get_task_id(self):
        computed = self.task.get_task_id()
        self.assertEqual(computed, self.task_id)

    def test_get_manager(self):
        computed = self.task.get_manager()
        self.assertEqual(computed, self.manager)

    def test_add_task(self):
        self.task.add_task()
        with open(self.file_path) as file:
            computed = file.read()
        self.assertEqual(computed, self.task_id)

    def test_is_task_active_false(self):
        active, tasks = self.task.is_task_active()
        self.assertFalse(active)
        self.assertListEqual(tasks, [])

    def test_is_task_active_true(self):
        self.task.add_task()
        active, tasks = self.task.is_task_active()
        self.assertTrue(active)
        self.assertListEqual(tasks, [self.task_id])

    def test_delete_task(self):
        self.task.delete_task()
        active, tasks = self.task.is_task_active()
        self.assertFalse(active)
        self.assertListEqual(tasks, [])
