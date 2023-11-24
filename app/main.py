import sys
import os
import zlib


def cat_file(blob_sha):
    compressed_file = f".git/objects/{blob_sha[0:2]}/{blob_sha[2:]}"
    _, file = decompress(compressed_file).split(b"\x00")
    print(file.decode(), end="")


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
    if command == "cat-file":
        option = sys.argv[2]
        value = sys.argv[3]
        cat_file(value)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
