import unittest
import os
import json
import tempfile
import shutil
import subprocess
from datetime import datetime, timezone
from task import (
    load_config,
    parse_loose_object,
    get_commit_objects,
    parse_commit,
    build_commit_graph,
    save_graph
)

class TestVisualizer(unittest.TestCase):
    def setUp(self):
        # Сохраняем текущую рабочую директорию
        self.original_cwd = os.getcwd()
        
        # Создаем временный тестовый репозиторий
        self.test_repo_dir = tempfile.mkdtemp()
        
        # Инициализируем репозиторий
        subprocess.run(['git', 'init'], cwd=self.test_repo_dir, check=True)
        
        # Создаем несколько коммитов
        test_file_path = os.path.join(self.test_repo_dir, 'test_file.txt')
        with open(test_file_path, 'w') as f:
            f.write('Initial commit')
        
        subprocess.run(['git', 'add', 'test_file.txt'], cwd=self.test_repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit', '--date=2023-01-01T12:00:00'], cwd=self.test_repo_dir, check=True)
        
        with open(test_file_path, 'a') as f:
            f.write('\nSecond commit')
        
        subprocess.run(['git', 'add', 'test_file.txt'], cwd=self.test_repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Second commit', '--date=2023-01-02T12:00:00'], cwd=self.test_repo_dir, check=True)
        
        # Создаем конфигурационный файл
        self.config = {
            "visualizer_path": "dot",
            "repo_path": self.test_repo_dir,
            "output_path": os.path.join(self.test_repo_dir, 'dependency_graph'),
            "commit_date": "2023-01-03"
        }
        self.config_path = os.path.join(self.test_repo_dir, 'config.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f)
        self.git_dir = os.path.join(self.config['repo_path'], '.git')

    def tearDown(self):
        # Возвращаемся в исходную рабочую директорию
        os.chdir(self.original_cwd)
        
        # Удаляем временный репозиторий
        def handle_remove_readonly(func, path, exc):
            import stat
            os.chmod(path, stat.S_IWRITE)
            func(path)
        
        shutil.rmtree(self.test_repo_dir, onerror=handle_remove_readonly)

    def test_load_config(self):
        config = load_config(self.config_path)
        self.assertEqual(config, self.config)

    def test_parse_loose_object(self):
        # Получаем любой объект из репозитория
        objects_dir = os.path.join(self.git_dir, 'objects')
        for root, dirs, files in os.walk(objects_dir):
            for file in files:
                object_path = os.path.join(root, file)
                try:
                    obj_type, content = parse_loose_object(object_path)
                    self.assertIn(obj_type, ['commit', 'tree', 'blob'])
                    self.assertIsInstance(content, bytes)
                    return  # Тест пройден после успешной проверки одного объекта
                except Exception:
                    continue
        self.fail("Не удалось найти и проверить объект Git")

    def test_get_commit_objects(self):
        commit_objects = get_commit_objects(self.git_dir)
        self.assertGreater(len(commit_objects), 0)
        for commit_hash, content in commit_objects:
            self.assertEqual(len(commit_hash), 40)
            self.assertIsInstance(content, bytes)

    def test_parse_commit(self):
        commit_objects = get_commit_objects(self.git_dir)
        for commit_hash, content in commit_objects:
            headers, message = parse_commit(content)
            self.assertIn('tree', headers)
            self.assertIn('author', headers)
            self.assertIsInstance(message, str)
            return  # Тест пройден после успешной проверки одного коммита
        self.fail("Не удалось найти и проверить коммит")

    def test_build_commit_graph(self):
        graph = build_commit_graph(self.git_dir, self.config['commit_date'])
        self.assertIsNotNone(graph)
        # Проверяем, что граф содержит узлы
        self.assertGreaterEqual(len(graph.body), 1)

    def test_save_graph(self):
        graph = build_commit_graph(self.git_dir, self.config['commit_date'])
        output_path = self.config['output_path']
        save_graph(graph, output_path)
        self.assertTrue(os.path.isfile(output_path + '.png'))

if __name__ == '__main__':
    unittest.main()
