#!/usr/bin/env python3

import libTinyFS
import libDisk

def main():
    libTinyFS.tfs_mkfs("Filesystem", 10240)
    libTinyFS.tfs_mount("Filesystem")
    libTinyFS.tfs_open("text")
    libTinyFS.tfs_open("text")
    libTinyFS.tfs_open("text2")
    libTinyFS.tfs_write(1, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                           "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                           "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                           , 300)
    libTinyFS.tfs_stat(1)
    libTinyFS.tfs_close(1)
    libTinyFS.tfs_umount()

if __name__ == "__main__":
    main()

