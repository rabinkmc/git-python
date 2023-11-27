import sys
import os
import zlib
import hashlib
import argparse
from pathlib import Path

object_path = Path(".git/objects/")


def cat_file(blob_sha):
    path = Path(f".git/objects/{blob_sha[0:2]}/{blob_sha[2:]}")
    fp = open(path, "rb")
    content = zlib.decompress(fp.read())
    fp.close()
    _, file = content.split(b"\x00")
    print(file.decode(), end="")


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
    sha1 = hashlib.sha1(out).hexdigest()

    out = zlib.compress(out)
    os.makedirs(object_path / f"{sha1[:2]}", exist_ok=True)
    filepath = object_path / f"{sha1[:2]}" / f"{sha1[2:]}"
    if not filepath.exists():
        with open(filepath, "wb") as f:
            f.write(out)

    return sha1


def write_blob(path):
    # get the hash : requires path
    path = Path(path)
    fp = open(path, "rb")
    content = fp.read()
    fp.close()
    full_content = b"blob" + b" " + str(len(content)).encode() + b"\x00" + content
    sha1 = hashlib.sha1(full_content).hexdigest()

    # compress and save in git object
    content = zlib.compress(full_content)
    os.makedirs(object_path / f"{sha1[:2]}", exist_ok=True)
    filepath = object_path / f"{sha1[:2]}" / f"{sha1[2:]}"
    if not filepath.exists():
        with open(filepath, "wb") as f:
            f.write(content)
    return sha1


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
    command = sys.argv[1]
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

    args = argparser.parse_args(sys.argv[1:])
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
        case _:
            raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
