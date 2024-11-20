import json
import sys
import os
import datetime
from git import Repo
from graphviz import Digraph

def load_config(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def get_commits(repo_path, until_date):
    command = ['git', 'log', '--until={}'.format(until_date), '--pretty=format:%H']
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True, cwd=repo_path, check=True)
    commits = result.stdout.strip().split('\n')
    return commits

def get_commits_files(repo_path, commit_hash):
    command = ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True, cwd=repo_path)
    files = result.stdout.strip().split('\n')
    folders = set(os.path.dirname(f) for f in files if f)
    return files, list(folders)


def build_dependency_graph(repo_path, commits):
    graph = Digraph(comment='Dependency Graph')
    previous_commit = None
    for commit in commits:
        files, folders = get_commit_files(repo_path, commit)
        node_label = 'Commit: {}\nFiles:\n{}\nFolders:\n{}'.format(
            commit,
            '\n'.join(files),
            '\n'.join(folders)
        )
        graph.node(commit, label=node_label)
        if previous_commit:
            graph.edge(previous_commit, commit)
        previous_commit = commit
    return graph



def save_graph(graph, output_path):
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    graph.render(output_path, view=False, format='png')

def main(config_path):
    config = load_config(config_path)
    visualizer_path = config['visualizer_path']
    repo_path = config['repo_path']
    output_path = config['output_path']
    commit_date = config['commit_date']

    os.environ["PATH"] += os.pathsep + os.path.dirname(visualizer_path)

    commits = get_commits(repo_path, commit_date)
    graph = build_dependency_graph(commits)
    save_graph(graph, output_path)
    print("Граф зависимостей успешно сохранен в файле:", output_path + '.png')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python visualizer.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]
    main(config_path)
