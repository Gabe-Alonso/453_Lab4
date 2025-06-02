#!/usr/bin/env python3

import time
import libDisk

BLOCKSIZE = 256
DEFAULT_DISK_SIZE = 10240
DEFAULT_DISK_NAME = "tinyFSDISK"

cur_disk = 0


def tfs_mkfs(filename, nBytes):
    print("Make Filesystem")

    disk_num = libDisk.openDisk(filename, nBytes)
    data = bytearray([0x0] * BLOCKSIZE )
    libDisk.readBlock(disk_num, 0, data)
    # Write superblock
    # First byte is Magic Number
    # Next byte is block number of root directory inode (should be index 1, with data in next block)
    # next byte contains a type of block (0 = free, 1 = used)
    # Index of block is block num + 1 (marking blocks 0, 1, and 2 as used for
    # superblock, special inode, and root dir data)
    # giving the system an upper limit of 255 blocks should more space be allocated

    data[0] = 0x5A
    data[1] = 0x1
    data[2] = 0x1
    data[3] = 0x1

    libDisk.writeBlock(disk_num, 0, data)
    data = bytearray()
    libDisk.readBlock(disk_num, 1, data)
    # Inodes will hold: 1 byte perms (0 if RO, 1 if RW), 4 byte creation time, 4 byte access time,
    # 4 byte modification time, and then a list of data block indices, null terminating (as super block
    # is at 0, never accessed in this way)
    t = time.time()
    print(int(t))
    print(int(t).to_bytes(8, byteorder='big'))


    libDisk.writeBlock(disk_num, 1, data)
    # Add dir data block
    # Each name takes 8 bytes max, and then 1 byte for holding inode location
    # limits total amount of files to 256 if more space was given, but allows
    # for more files in scope of TinyFS

    data = bytearray()
    libDisk.readBlock(disk_num, 2, data)

    libDisk.writeBlock(disk_num, 2, data)

def tfs_mount(filename):
    print("Mount Filesystem")

def tfs_umount():
    print("Unmount Filesystem")

def tfs_open(filename):
    print("Open File")

def tfs_close(fd):
    print("Close File")

def tfs_write(fd, buffer, size):
    print("Write File")

def tfs_delete(fd):
    print("Delete File")

def tfs_readByte(fd, buffer):
    print("Read Byte from File")

def tfs_seek(fd, offset):
    print("Seek File")

def tfs_stat(fd):
    print("Stat File")

def tfs_makeRO(filename):
    print("Make file Read only")

def tfs_makeRW(filename):
    print("Make file Readable and writable")

def tfs_writeByte(fd, buffer):
    print("Write Byte from File")
