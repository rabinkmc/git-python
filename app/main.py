import argparse
import hashlib
import os
import sys
import zlib
import time
from pathlib import Path

OBJECT_PATH = Path(".git/objects/")


def write_object(content):
    sha1 = hashlib.sha1(content).hexdigest()

    content = zlib.compress(content)
    os.makedirs(OBJECT_PATH / f"{sha1[:2]}", exist_ok=True)
    filepath = OBJECT_PATH / f"{sha1[:2]}" / f"{sha1[2:]}"
    if not filepath.exists():
        with open(filepath, "wb") as f:
            f.write(content)

    return sha1


def cat_file(blob_sha):
    path = Path(f".git/objects/{blob_sha[0:2]}/{blob_sha[2:]}")
    fp = open(path, "rb")
    content = zlib.decompress(fp.read())
    fp.close()
    _, file = content.split(b"\x00")
    print(file.decode(), end="")


def write_blob(path):
    # get the hash : requires path
    path = Path(path)
    fp = open(path, "rb")
    content = fp.read()
    fp.close()
    full_content = b"blob" + b" " + str(len(content)).encode() + b"\x00" + content
    return write_object(full_content)


def ls_tree(sha1):
    compressed_file = f".git/objects/{sha1[0:2]}/{sha1[2:]}"
    file = decompress(compressed_file)
    i = 0
    SHA_LENGTH = 20
    names = []
    while i < len(file) and file[i : i + 1] != b"\x00":
        i += 1

    i += 1
    while i < len(file):
        while i < len(file) and file[i : i + 1] != b" ":
            i += 1
        i += 1
        start = i
        while i < len(file) and file[i : i + 1] != b"\x00":
            i += 1
        filename = file[start:i].decode()
        i += 1 + SHA_LENGTH
        names.append(filename)

    print("\n".join(names))


def write_tree(path="."):
    out = b""
    files = sorted([file for file in os.listdir(path)])
    for file in files:
        filename = file
        if file == ".git":
            continue
        if path != ".":
            file = f"{path}/{file}"
        is_dir = os.path.isdir(file)
        mode = b"40000" if is_dir else b"100644"
        sha1 = write_tree(file) if is_dir else write_blob(file)
        result = mode + b" " + filename.encode() + b"\0" + bytes.fromhex(sha1)
        out += result

    out = b"tree" + b" " + str(len(out)).encode() + b"\0" + out
    return write_object(out)


def commit_tree(tree_id, parent_id, message):
    tree = f"tree {tree_id}"
    parent = f"parent {parent_id}"

    author = {
        "name": "Rabin Dhamala",
        "email": "rabinkmc@gmail.com",
    }

    now = int(time.time())
    author_info = f'author {author["name"]} <{author["email"]}> {now} +0545'
    committer_info = f'committer {author["name"]} <{author["email"]}> {now} +0545'
    commit_str = (
        "\n".join([tree, parent, author_info, committer_info]) + "\n\n" + message + "\n"
    )
    commit_str_with_header = (
        b"commit " + str(len(commit_str)).encode() + b"\0" + commit_str.encode()
    )

    return write_object(commit_str_with_header)


def decompress(compressed_file):
    path = Path(compressed_file)
    str_object1 = open(path, "rb").read()
    str_object2 = zlib.decompress(str_object1)
    return str_object2


def init():
    path = Path(".git")
    os.mkdir(path)
    os.mkdir(path / "objects")
    os.mkdir(path / "refs")
    with open(path / "HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")
    print("Initialized git directory")


def main():
    argparser = argparse.ArgumentParser(
        prog="Write your own git",
        description="Trying to learn git by building git itself",
    )
    argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
    argsubparsers.required = True

    # init
    init_sp = argsubparsers.add_parser(
        "init", help="Initialize a new, empty repository."
    )
    init_sp.add_argument(
        "path",
        metavar="directory",
        nargs="?",
        default=".",
        help="Where to create the repository.",
    )

    # cat-file
    cat_file_sp = argsubparsers.add_parser("cat-file", help="read the git object")
    cat_file_sp.add_argument("-p", action="store_true")
    cat_file_sp.add_argument("sha", help="hash of a git object")

    # hash-object
    hash_object_sp = argsubparsers.add_parser("hash-object", help="hash object")
    hash_object_sp.add_argument("-w", dest="file", help="file to hash")

    # ls-tree
    ls_tree_sp = argsubparsers.add_parser("ls-tree", help="read the git object")
    ls_tree_sp.add_argument("--name-only", action="store_true")
    ls_tree_sp.add_argument("sha", help="hash of a tree object")

    # write-tree
    argsubparsers.add_parser("write-tree", help="write tree")

    # commit-tree
    commit_tree_sp = argsubparsers.add_parser(
        "commit-tree", help="create a commit object"
    )
    commit_tree_sp.add_argument("tree", help="id of an existing tree object")
    commit_tree_sp.add_argument("-p", help="id of a parent commit object")
    commit_tree_sp.add_argument("-m", help="paragraph in the commit log message")

    clone_parser = argsubparsers.add_parser(
        "clone", help="Clone a repository into a new directory"
    )
    clone_parser.add_argument("url", help="url to clone from")

    # clone
    args = argparser.parse_args()
    match args.command:
        case "init":
            init()
        case "cat-file":
            cat_file(args.sha)
        case "hash-object":
            sha = write_blob(args.file)
            print(sha)
        case "ls-tree":
            ls_tree(args.sha)
        case "write-tree":
            sha = write_tree()
            print(sha)
        case "commit-tree":
            sha = commit_tree(args.tree, args.p, args.m)
            print(sha)
        case _:
            raise RuntimeError(f"Unknown command #{args.command}")


if __name__ == "__main__":
    main()
