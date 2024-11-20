import json
import sys
import os
import zlib
import struct
from datetime import datetime
from graphviz import Digraph

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def parse_loose_object(object_path):
    with open(object_path, 'rb') as f:
        compressed_data = f.read()
    try:
        decompressed_data = zlib.decompress(compressed_data)
    except zlib.error as e:
        print(f"Ошибка при распаковке объекта {object_path}: {e}")
        raise
    header, _, content = decompressed_data.partition(b'\x00')
    obj_type, size = header.decode().split()
    return obj_type, content


def get_commit_objects(git_dir):
    objects_dir = os.path.join(git_dir, 'objects')
    commit_objects = []
    for root, dirs, files in os.walk(objects_dir):
        # Исключаем директории 'info' и 'pack'
        dirs[:] = [d for d in dirs if d not in ['info', 'pack']]
        for file in files:
            # Проверяем, что имя файла состоит из 38 шестнадцатеричных символов
            if len(file) != 38 or not all(c in '0123456789abcdef' for c in file.lower()):
                continue
            object_path = os.path.join(root, file)
            try:
                obj_type, content = parse_loose_object(object_path)
                if obj_type == 'commit':
                    commit_hash = os.path.relpath(object_path, objects_dir).replace('\\', '').replace('/', '')
                    commit_objects.append((commit_hash, content))
            except Exception as e:
                print(f"Ошибка при обработке файла {object_path}: {e}")
    return commit_objects



def parse_commit(content):
    lines = content.decode().split('\n')
    headers = {}
    i = 0
    while lines[i]:
        key, value = lines[i].split(' ', 1)
        headers[key] = value
        i += 1
    i += 1  # Пропустить пустую строку
    message = '\n'.join(lines[i:])
    return headers, message

def build_commit_graph(git_dir, until_date):
    commit_objects = get_commit_objects(git_dir)
    graph = Digraph(format='png')
    commits_info = {}

    for object_path, content in commit_objects:
        headers, message = parse_commit(content)
        commit_hash = os.path.basename(os.path.dirname(object_path)) + os.path.basename(object_path)
        author_info = headers.get('author', '')
        date_str = author_info.split('>')[-1].strip()
        try:
            timestamp = int(date_str.split()[0])
        except ValueError:
            continue
        commit_date = datetime.utcfromtimestamp(timestamp)
        if commit_date >= datetime.strptime(until_date, '%Y-%m-%d'):
            continue

        tree_hash = headers.get('tree')
        parent_hashes = headers.get('parent', '').split()
        commits_info[commit_hash] = {
            'tree': tree_hash,
            'parents': parent_hashes,
            'date': commit_date,
            'message': message
        }

    for commit_hash, info in commits_info.items():
        label = f"Commit: {commit_hash[:7]}\nDate: {info['date']}\nMessage: {info['message']}"
        graph.node(commit_hash, label=label)
        for parent_hash in info['parents']:
            if parent_hash in commits_info:
                graph.edge(parent_hash, commit_hash)

    return graph

def save_graph(graph, output_path):
    graph.render(output_path, cleanup=True)

def main():
    if len(sys.argv) != 2:
        print("Usage: python visualizer.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]
    config = load_config(config_path)
    visualizer_path = config['visualizer_path']
    repo_path = config['repo_path']
    output_path = config['output_path']
    commit_date = config['commit_date']

    git_dir = os.path.join(repo_path, '.git')

    os.environ["PATH"] += os.pathsep + os.path.dirname(visualizer_path)

    graph = build_commit_graph(git_dir, commit_date)
    save_graph(graph, output_path)
    print("Граф зависимостей успешно сохранен в файле:", output_path + '.png')

if __name__ == "__main__":
    main()
