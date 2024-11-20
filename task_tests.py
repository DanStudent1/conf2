import unittest
import os
import json
import tempfile
from task import load_config, get_commits, build_dependency_graph

class TestVisualizer(unittest.TestCase):
    def setUp(self):
        self.config = {
            "visualizer_path": "/usr/bin/dot",
            "repo_path": "/путь/к/тестовому/репозиторию",
            "output_path": "test_dependency_graph",
            "commit_date": "2023-01-01"
        }
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f)

    def tearDown(self):
        os.remove(self.config_path)
        os.rmdir(self.temp_dir)

    def test_load_config(self):
        config = load_config(self.config_path)
        self.assertEqual(config, self.config)

    def test_get_commits(self):
        commits = get_commits(self.config['repo_path'], self.config['commit_date'])
        self.assertIsInstance(commits, list)

    def test_build_dependency_graph(self):
        commits = get_commits(self.config['repo_path'], self.config['commit_date'])
        graph = build_dependency_graph(commits)
        self.assertIsNotNone(graph)

if __name__ == '__main__':
    unittest.main()
