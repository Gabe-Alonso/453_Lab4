#!/usr/bin/env python3

import libTinyFS
import libDisk

def main():
    libTinyFS.tfs_mkfs("Filesystem", 10240)

if __name__ == "__main__":
    main()

