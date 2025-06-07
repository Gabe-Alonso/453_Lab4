#!/usr/bin/env python3

import libTinyFS
import libDisk
import time
import datetime

def main():
    # Create a filesystem
    libTinyFS.tfs_mkfs("Filesystem", 10240)

    # Mount it
    assert libTinyFS.tfs_mount("Filesystem") == 0

    # Open files (first call will create them)
    fd1 = libTinyFS.tfs_open("text")  # Should create and return a valid fd
    fd2 = libTinyFS.tfs_open("text")  # Should reuse existing file
    fd3 = libTinyFS.tfs_open("text2") # Should create new
    assert fd1 != -1 and fd2 != -1 and fd3 != -1

    # Write >1 block of data to fd1 ("text")
    big_string = "A" * 300
    assert libTinyFS.tfs_write(fd1, big_string, len(big_string)) == 0

    # Read a single byte into a buffer from fd1
    buffer = bytearray([0x00])
    assert libTinyFS.tfs_readByte(fd1, buffer) == 0
    print("Read Byte:", buffer[0:1].decode('utf-8'))
    assert buffer[0:1].decode('utf-8') == 'A'

    # Write a byte to current position
    assert libTinyFS.tfs_writeByte(fd1, 'e') == 0

    # Sleep for 2 seconds to validate timestamp differences
    time.sleep(2)

    # View and verify file metadata
    print("\nFile Stat Output:")
    libTinyFS.tfs_stat(fd1)  # This prints formatted timestamps and updates access time

    # Close the file descriptor
    assert libTinyFS.tfs_close(fd1) == 0

    # Delete the file and verify removal
    fd_del = libTinyFS.tfs_open("deleteMe")
    assert fd_del != -1
    assert libTinyFS.tfs_write(fd_del, "delete this content", 19) == 0
    assert libTinyFS.tfs_delete(fd_del) == 0

    # Reopen the deleted file should recreate it
    fd_del2 = libTinyFS.tfs_open("deleteMe")
    assert fd_del2 != -1
    buffer3 = bytearray([0x00])
    assert libTinyFS.tfs_readByte(fd_del2, buffer3) == 0
    assert buffer3[0] == 0  # Should be null-padded empty file
    assert libTinyFS.tfs_close(fd_del2) == 0

    # Test read-only enforcement
    fd_ro = libTinyFS.tfs_open("readonly")
    assert libTinyFS.tfs_write(fd_ro, "can't touch this", 17) == 0
    libTinyFS.tfs_makeRO("readonly")
    assert libTinyFS.tfs_write(fd_ro, "new data", 8) == -1  # Should fail
    libTinyFS.tfs_makeRW("readonly")
    assert libTinyFS.tfs_write(fd_ro, "now writable", 13) == 0
    assert libTinyFS.tfs_close(fd_ro) == 0

    # Cleanly unmount the filesystem
    assert libTinyFS.tfs_umount() == 0

    # Remount and reopen the file to check persistence
    assert libTinyFS.tfs_mount("Filesystem") == 0
    fd4 = libTinyFS.tfs_open("text")
    assert fd4 != -1
    buffer2 = bytearray([0x00])
    assert libTinyFS.tfs_readByte(fd4, buffer2) == 0
    print("Post-unmount Read Byte:", buffer2[0:1].decode('utf-8'))
    assert buffer2[0:1].decode('utf-8') in ['A', 'e']  # depends on read pointer
    assert libTinyFS.tfs_close(fd4) == 0
    assert libTinyFS.tfs_umount() == 0

if __name__ == "__main__":
    main()

