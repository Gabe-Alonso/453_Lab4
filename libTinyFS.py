#!/usr/bin/env python3

import time
import libDisk

BLOCKSIZE = 256
DEFAULT_DISK_SIZE = 10240
DEFAULT_DISK_NAME = "tinyFSDISK"

cur_disk = -1
fd_counter = 1
res_tab = {0: {"inode": 1, "fp": 9, "filename": "root"}}


def tfs_mkfs(filename, nBytes):
    print("Make Filesystem")

    disk_num = libDisk.openDisk(filename, nBytes)
    data = bytearray([0x0] * BLOCKSIZE)
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
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(disk_num, 1, data)
    # Inodes will hold: 1 byte perms (0 if RO, 1 if RW (default)), 4 byte access time, 4 byte modification time,
    # 4 byte creation time, and then a list of data block indices, null terminating (as super block
    # is at 0, never accessed in this way), which also allows new blocks to be added (not indefinitely
    # but within reason)
    data[0] = 0x1

    # Creating 3 repeated 4 byte chunks for creation, access, and mod times
    t = int(time.time()).to_bytes(4, byteorder='big')
    t3 = t * 3
    data[1:13] = t3
    print(t3)
    data[14] = 2


    libDisk.writeBlock(disk_num, 1, data)
    # Add dir data block
    # Each name takes 8 bytes max, and then 1 byte for holding inode location
    # limits total amount of files to 256 if more space was given, but allows
    # for more files in scope of TinyFS
    # Each 9 byte chunk is indexable as a file descriptor

    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(disk_num, 2, data)
    data[0:8] = b'root' + b'\x00' * 4
    data[8] = 0x1
    libDisk.writeBlock(disk_num, 2, data)


    libDisk.closeDisk(disk_num)

def tfs_mount(filename):
    print("Mount Filesystem")
    global cur_disk
    if cur_disk != -1:
        print("Another filesystem is already mounted")
        return -1
    disk_num = libDisk.openDisk(filename, 0)
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(disk_num, 0, data)
    print("Magic Number")
    print(data[0])
    if data[0] != 0x5A:
        print("Invalid Magic Number")
        return -1
    else:
        cur_disk = disk_num
        return 0

def tfs_umount():
    print("Unmount Filesystem")
    global cur_disk
    global fd_counter
    if cur_disk == -1:
        print("No disk currently mounted")
        return -1
    else:
        libDisk.closeDisk(cur_disk)
        res_tab.clear()
        fd_counter = 0
        cur_disk -= 1


def tfs_open(filename):
    print("Open File")

    if len(filename) > 8:
        print("Filename cannot be longer than 8 characters")
        return -1
    global res_tab
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, 2, data)
    i = 0
    inode_location = -1
    while i < 256 and data[i] != 0x0:
        name_bytes = data[i:i + 8]
        new_fn = name_bytes.split(b'\x00', 1)[0].decode('utf-8')
        if new_fn == filename:
            print("File Matches")
            inode_location = data[i + 8]
            print("Inode location")
            print(inode_location)
        i += 9
    if inode_location == -1:
        print("File does not exist, creating file " + filename)
        data = bytearray([0x0] * BLOCKSIZE)
        libDisk.readBlock(cur_disk, 0, data)
        inode_location = -1
        new_data = -1
        index = 3
        while new_data == -1 or inode_location == -1:
            print(data[index])
            if inode_location == -1 and data[index] == 0:
                inode_location = index - 1
                data[index] = 1
            elif new_data == -1 and data[index] == 0:
                new_data = index - 1
                data[index] = 1
            index = index + 1
        libDisk.writeBlock(cur_disk, 0, data)
        data = bytearray([0x0] * BLOCKSIZE)
        libDisk.readBlock(cur_disk, 2, data)
        i = 0
        global res_tab
        fp = res_tab[0]["fp"]
        data[fp: fp+ len(filename)] = filename.encode('utf-8')
        data[fp + 8] = inode_location
        res_tab[0]["fp"] += 9
        libDisk.writeBlock(cur_disk, 2, data)

        # Create the inode for the new file
        data = bytearray([0x0] * BLOCKSIZE)
        libDisk.readBlock(cur_disk, inode_location, data)
        # Inodes will hold: 1 byte perms (0 if RO, 1 if RW (default)), 4 byte access time, 4 byte modification time,
        # 4 byte creation time, and then a list of data block indices, null terminating (as super block
        # is at 0, never accessed in this way), which also allows new blocks to be added (not indefinitely
        # but within reason)
        data[0] = 0x1

        # Creating 3 repeated 4 byte chunks for creation, access, and mod times
        t = int(time.time()).to_bytes(4, byteorder='big')
        print("New File Inode access time")
        print(t)
        t3 = t * 3
        data[1:13] = t3
        data[14] = new_data
        libDisk.writeBlock(cur_disk, inode_location, data)

        # Update access time for root inode
        data = bytearray([0x0] * BLOCKSIZE)
        libDisk.readBlock(cur_disk, 1, data)
        t = int(time.time()).to_bytes(4, byteorder='big')
        print("New Dir Inode access time")
        print(t)
        data[1:5] = t
        libDisk.writeBlock(cur_disk, 1, data)

    global fd_counter
    fd = fd_counter
    fd_counter += 1
    res_tab[fd] = {"inode": inode_location, "fp": 0, "filename": filename}


    print(res_tab)


def tfs_close(fd):
    print("Close File")
    print("Closing file: " + res_tab[fd]["filename"])
    del res_tab[fd]

def tfs_write(fd, buffer, size):
    print("Write File")

def tfs_delete(fd):
    print("Delete File")
    print("Deleting file: " + res_tab[fd]["filename"])

    # Deallocate and reformat all data associated blocks and inode
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    index = 14
    deleted_blocks = []
    while data[index] != 0x0:
        data2 = bytearray([0x0] * BLOCKSIZE)
        libDisk.writeBlock(cur_disk, data[index], data2)
        deleted_blocks.append(data[index])
        index = index + 1
    deleted_blocks.append(res_tab[fd]["inode"])
    data2 = bytearray([0x0] * BLOCKSIZE)
    libDisk.writeBlock(cur_disk, res_tab[fd]["inode"], data2)

    # Remove file from directory
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, 2, data)
    i = 0
    while i < 256 and data[i] != 0x0:
        name_bytes = data[i:i + 8]
        new_fn = name_bytes.split(b'\x00', 1)[0].decode('utf-8')
        if new_fn == res_tab[fd]["filename"]:
            print("File Matches")
            data[i:i+10] = [0x0] * 9
            break
        i += 9

    libDisk.writeBlock(cur_disk, 2, data)

    # Update directory inode access time
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, 1, data)
    t = int(time.time()).to_bytes(4, byteorder='big')
    print("New Dir Inode access time")
    print(t)
    data[1:5] = t
    libDisk.writeBlock(cur_disk, 1, data)

    # Update super block, freeing newly deleted blocks
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, 1, data)
    print(deleted_blocks)
    for index in deleted_blocks:
        data[index + 1] = 0x0
    libDisk.writeBlock(cur_disk, 2, data)

    del res_tab[fd]

def tfs_readByte(fd, buffer):
    print("Read Byte from File")

def tfs_seek(fd, offset):
    print("Seek File")
    res_tab[fd]["fp"] = offset
    return 0


def tfs_stat(fd):
    print("Stat File")

def tfs_makeRO(filename):
    print("Make file Read only")

def tfs_makeRW(filename):
    print("Make file Readable and writable")

def tfs_writeByte(fd, buffer):
    print("Write Byte from File")
