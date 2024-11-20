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

def get_commits(repo_path, date):
    repo = Repo(repo_path)
    commits = []
    for commit in repo.iter_commits():
        if commit.committed_datetime < datetime.datetime.strptime(date, '%Y-%m-%d'):
            commits.append(commit)
    return commits

def build_dependency_graph(commits):
    graph = Digraph(format='png')
    for commit in commits:
        files = commit.stats.files.keys()
        label = f"Commit: {commit.hexsha[:7]}\n" + "\n".join(files)
        graph.node(commit.hexsha, label=label)
        for parent in commit.parents:
            graph.edge(parent.hexsha, commit.hexsha)
    return graph

def save_graph(graph, output_path):
    graph.render(output_path, cleanup=True)

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
