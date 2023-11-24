import sys
import os
import zlib
import hashlib


def cat_file(blob_sha):
    compressed_file = f".git/objects/{blob_sha[0:2]}/{blob_sha[2:]}"
    _, file = decompress(compressed_file).split(b"\x00")
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


def hash_object(filename):
    fr = open(filename, "r")
    file_content = fr.read()
    fr.close()
    content = f"blob {len(file_content)}\x00{file_content}".encode()
    checksum = hashlib.sha1(content).hexdigest()
    dir = checksum[:2]
    file_hash = checksum[2:]
    content = zlib.compress(content)
    if not os.path.isdir(f".git/objects/{dir}"):
        os.mkdir(f".git/objects/{dir}")
    f = open(f".git/objects/{dir}/{file_hash}", "wb")
    f.write(content)
    f.close()
    print(checksum, end="")


def decompress(compressed_file):
    str_object1 = open(compressed_file, "rb").read()
    str_object2 = zlib.decompress(str_object1)
    return str_object2


def init():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")
    print("Initialized git directory")


def main():
    command = sys.argv[1]
    if command == "init":
        init()
    elif command == "cat-file":
        _ = sys.argv[2]
        sha1 = sys.argv[3]
        cat_file(sha1)
    elif command == "hash-object":
        _ = sys.argv[2]
        filename = sys.argv[3]
        hash_object(filename)
    elif command == "ls-tree":
        _ = sys.argv[2]
        sha1 = sys.argv[3]
        ls_tree(sha1)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
