#!/usr/bin/env python3

import libTinyFS
import libDisk
import errors
import time

def main():
    print("Creating filesystem")
    assert libTinyFS.tfs_mkfs("Filesystem", 10240) == errors.ERR_OK

    print("Mounting filesystem")
    assert libTinyFS.tfs_mount("Filesystem") == errors.ERR_OK

    print("Opening files")
    fd1 = libTinyFS.tfs_open("text")
    fd2 = libTinyFS.tfs_open("text")
    fd3 = libTinyFS.tfs_open("text2")
    assert fd1 >= 0 and fd2 >= 0 and fd3 >= 0

    print("Testing invalid filename")
    assert libTinyFS.tfs_open("toolongname") == errors.ERR_INVALID_FILENAME

    print("Writing large block to fd1")
    big_string = "A" * 300
    assert libTinyFS.tfs_write(fd1, big_string, len(big_string)) == errors.ERR_OK

    print("Reading a byte from fd1")
    buffer = bytearray([0x00])
    assert libTinyFS.tfs_readByte(fd1, buffer) == errors.ERR_OK
    print("Buffer read:", buffer[0:1].decode('utf-8'))
    assert buffer[0:1].decode('utf-8') == 'A'

    print("Writing a byte to fd1")
    assert libTinyFS.tfs_writeByte(fd1, 'e') == errors.ERR_OK

    print("Sleeping to validate timestamp differences")
    time.sleep(2)

    print("Stat file:")
    result = libTinyFS.tfs_stat(fd1)
    print("Stat:", result)
    assert "Read" in result

    print("Closing fd1")
    assert libTinyFS.tfs_close(fd1) == errors.ERR_OK

    print("Deleting file deleteMe")
    fd_del = libTinyFS.tfs_open("deleteMe")
    assert fd_del >= 0
    assert libTinyFS.tfs_write(fd_del, "delete this content", 19) == errors.ERR_OK
    assert libTinyFS.tfs_delete(fd_del) == errors.ERR_OK

    print("Reopening deleted file")
    fd_del2 = libTinyFS.tfs_open("deleteMe")
    assert fd_del2 >= 0
    buffer3 = bytearray([0x00])
    assert libTinyFS.tfs_readByte(fd_del2, buffer3) == errors.ERR_OK
    assert buffer3[0] == 0
    assert libTinyFS.tfs_close(fd_del2) == errors.ERR_OK

    print("Testing read-only enforcement")
    fd_ro = libTinyFS.tfs_open("readonly")
    assert fd_ro >= 0
    assert libTinyFS.tfs_write(fd_ro, "can't touch this", 17) == errors.ERR_OK
    libTinyFS.tfs_makeRO("readonly")
    assert libTinyFS.tfs_write(fd_ro, "fail write", 10) == errors.ERR_FILE_READ_ONLY
    libTinyFS.tfs_makeRW("readonly")
    assert libTinyFS.tfs_write(fd_ro, "success write", 13) == errors.ERR_OK
    assert libTinyFS.tfs_close(fd_ro) == errors.ERR_OK

    print("Unmounting filesystem")
    assert libTinyFS.tfs_umount() == errors.ERR_OK

    print("Testing write while unmounted (should fail)")
    assert libTinyFS.tfs_write(fd3, "nope", 4) == errors.ERR_DISK_NOT_MOUNTED

    print("Remounting filesystem")
    assert libTinyFS.tfs_mount("Filesystem") == errors.ERR_OK

    print("Testing reopen after remount")
    fd4 = libTinyFS.tfs_open("text")
    assert fd4 >= 0
    buffer2 = bytearray([0x00])
    assert libTinyFS.tfs_readByte(fd4, buffer2) == errors.ERR_OK
    print("Read after remount:", buffer2[0:1].decode('utf-8'))
    assert buffer2[0:1].decode('utf-8') in ['A', 'e']
    assert libTinyFS.tfs_close(fd4) == errors.ERR_OK

    print("Testing invalid FD")
    assert libTinyFS.tfs_close(999) == errors.ERR_INVALID_FD
    assert libTinyFS.tfs_readByte(999, bytearray([0x00])) == errors.ERR_INVALID_FD
    assert libTinyFS.tfs_write(999, "test", 4) == errors.ERR_INVALID_FD

    print("Final unmount")
    assert libTinyFS.tfs_umount() == errors.ERR_OK

if __name__ == "__main__":
    main()
