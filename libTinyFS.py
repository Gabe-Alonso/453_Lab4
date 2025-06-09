#!/usr/bin/env python3

import time
import libDisk
import datetime
import errors

BLOCKSIZE = 256
DEFAULT_DISK_SIZE = 10240
DEFAULT_DISK_NAME = "tinyFSDISK"

cur_disk = -1
fd_counter = 1
res_tab = {}

# Error Num Guide
# 0: Normal Behavior
# -1: No such file/directory


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
    data[13] = 2


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
    return errors.ERR_OK

def tfs_mount(filename):
    print("Mount Filesystem")
    global cur_disk
    global fd_counter
    fd_counter = 1
    res_tab[0] = {"inode": 1, "fp": 9, "filename": "root", "d_blocks": [2]}
    if cur_disk != -1:
        print("Another filesystem is already mounted")
        return errors.ERR_DISK_ALREADY_MOUNTED
    disk_num = libDisk.openDisk(filename, 0)
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(disk_num, 0, data)
    print("Magic Number")
    print(data[0])
    if data[0] != 0x5A:
        print("Invalid Magic Number")
        return errors.ERR_NOT_SUPERBLOCK
    else:
        cur_disk = disk_num
        return errors.ERR_OK

def tfs_umount():
    print("Unmount Filesystem")
    global cur_disk
    global fd_counter
    if cur_disk == -1:
        print("No disk currently mounted")
        return errors.ERR_DISK_NOT_MOUNTED
    else:
        libDisk.closeDisk(cur_disk)
        res_tab.clear()
        fd_counter = 0
        cur_disk -= 1
    return errors.ERR_OK

def tfs_open(filename):
    print("Open File")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if len(filename) > 8:
        print("Filename cannot be longer than 8 characters")
        return errors.ERR_INVALID_FILENAME
    global res_tab
    print(res_tab)
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, 2, data)
    i = 0
    inode_location = -1
    new_data = -1
    data_blocks = None
    while i < 256 and data[i] != 0x0:
        name_bytes = data[i:i + 8]
        new_fn = name_bytes.split(b'\x00', 1)[0].decode('utf-8')
        if new_fn == filename:
            print("File Matches")
            inode_location = data[i + 8]
            print("Inode location")
            print(inode_location)
            for i, b in res_tab.items():
                if b["inode"] == inode_location:
                    data_blocks = b["d_blocks"]
            break
        i += 9
    if inode_location == -1:
        print("File does not exist, creating file " + filename)
        data = bytearray([0x0] * BLOCKSIZE)
        libDisk.readBlock(cur_disk, 0, data)
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
        data[13] = new_data
        libDisk.writeBlock(cur_disk, inode_location, data)

        # Update access time for root inode
        data = bytearray([0x0] * BLOCKSIZE)
        libDisk.readBlock(cur_disk, 1, data)
        t = int(time.time()).to_bytes(4, byteorder='big')
        print("New Dir Inode access time")
        print(t)
        data[1:5] = t
        libDisk.writeBlock(cur_disk, 1, data)
    elif inode_location > -1 and data_blocks is None:
        data = bytearray([0x0] * BLOCKSIZE)
        libDisk.readBlock(cur_disk, inode_location, data)
        t = int(time.time()).to_bytes(4, byteorder='big')
        print("New Inode access time")
        print(t)
        data[1:5] = t
        i = 13
        data_blocks = []
        while data[i] != 0x0:
            data_blocks.append(data[i])
            i += 1
        libDisk.writeBlock(cur_disk, inode_location, data)


    global fd_counter
    fd = fd_counter
    fd_counter += 1
    if data_blocks is not None:
        res_tab[fd] = {"inode": inode_location, "fp": 0, "filename": filename, "d_blocks": data_blocks}
    else:
        res_tab[fd] = {"inode": inode_location, "fp": 0, "filename": filename, "d_blocks": [new_data]}
    print(res_tab)
    return fd


def tfs_close(fd):
    print("Close File")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if fd not in res_tab:
        return errors.ERR_INVALID_FD

    print("Closing file: " + res_tab[fd]["filename"])
    del res_tab[fd]
    return errors.ERR_OK

def tfs_write(fd, buffer, size):
    print("Write File")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if fd not in res_tab:
        return errors.ERR_INVALID_FD


    # Check if file is writable
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    if data[0] == 0x0:
        return errors.ERR_FILE_READ_ONLY
    print("Is block writable?")
    print(data[0])
    if data[0] == 0x0:
        print("File is read only")
        return errors.ERR_FILE_READ_ONLY

    # Check if size is bigger than one block
    if size <= BLOCKSIZE:
        # If not, write straight to already allocated data block
        new_data = buffer.encode('utf-8')
        padding = BLOCKSIZE - (len(new_data) % BLOCKSIZE)
        if padding != BLOCKSIZE:
            new_data += b'\x00' * padding
        libDisk.writeBlock(cur_disk, res_tab[fd]["d_blocks"][0], new_data)
    else:
        # If it is, allocate as many new blocks as necessary and write each block's worth to the new blocks
        # Keeping track of what new blocks you use
        # Remember to add new files to directory file, updating inode access time, and adding new
        # / removing unnecessary data blocks from superblock

        # Make sure enough blocks are allocated, allocate them and update superblock
        needed_blocks = (size // BLOCKSIZE) + 1
        if needed_blocks > len(res_tab[fd]["d_blocks"]):
            new_blocks = needed_blocks - len(res_tab[fd]["d_blocks"])
            data = bytearray([0x0] * BLOCKSIZE)
            libDisk.readBlock(cur_disk, 0, data)
            i = 0
            blocks_added = 0
            while new_blocks > blocks_added:
                if data[i] == 0x0:
                    blocks_added = new_blocks
                    res_tab[fd]["d_blocks"].append(i - 1)
                    data[i] = 0x1
                i += 1
                if i >= BLOCKSIZE:
                    return errors.ERR_NO_FREE_BLOCKS
                libDisk.writeBlock(cur_disk, 0, data)

            libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
            i = 13
            # Add new entries to inode
            for block in res_tab[fd]["d_blocks"]:
                data[i] = block
                i += 1
            while i < 256:
                data[i] = 0x0
                i += 1
            libDisk.writeBlock(cur_disk, res_tab[fd]["inode"], data)

        new_data = buffer.encode('utf-8')
        padding = BLOCKSIZE - (len(new_data) % BLOCKSIZE)
        if padding != BLOCKSIZE:
            new_data += b'\x00' * padding
        i = 0
        db = 0
        while i < size:
            libDisk.writeBlock(cur_disk, res_tab[fd]["d_blocks"][db], new_data[i:i + BLOCKSIZE])
            db += 1
            i += BLOCKSIZE

    # Update inode
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    t = int(time.time()).to_bytes(4, byteorder='big')
    print("New Inode access time")
    print(t)
    data[1:5] = t
    libDisk.writeBlock(cur_disk, res_tab[fd]["inode"], data)
    blocks = res_tab[fd]["d_blocks"]

    # Make sure other version of this open are up to date on what data block are referenced, update file pointer to 0
    for i, b in res_tab.items():
        if b["inode"] == res_tab[fd]["inode"]:
            b["d_blocks"] = blocks
            b["fp"] = 0
    print(res_tab)
    return errors.ERR_OK


def tfs_delete(fd):
    print("Delete File")
    print("Deleting file: " + res_tab[fd]["filename"])
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if fd not in res_tab:
        return errors.ERR_INVALID_FD

    # Deallocate and reformat all data associated blocks and inode
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    index = 13
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
    libDisk.readBlock(cur_disk, 0, data)
    print(deleted_blocks)
    for index in deleted_blocks:
        data[index + 1] = 0x0
    libDisk.writeBlock(cur_disk, 0, data)

    del res_tab[fd]
    return errors.ERR_OK

def tfs_readByte(fd, buffer):
    print("Read Byte from File")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if fd not in res_tab:
        return errors.ERR_INVALID_FD

    data = bytearray([0x0] * BLOCKSIZE)
    fp = res_tab[fd]["fp"] % BLOCKSIZE
    block = fp // BLOCKSIZE
    if block > len(res_tab[fd]["d_blocks"]):
        print("Cannot read past end of file")
        return errors.ERR_EOF
    libDisk.readBlock(cur_disk, res_tab[fd]["d_blocks"][block], data)
    buffer[0] = data[res_tab[fd]["fp"]]
    # Update inode
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    t = int(time.time()).to_bytes(4, byteorder='big')
    print("New Inode access time")
    print(t)
    data[1:5] = t
    libDisk.writeBlock(cur_disk, res_tab[fd]["inode"], data)
    return errors.ERR_OK

def tfs_seek(fd, offset):
    print("Seek File")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if fd not in res_tab:
        return errors.ERR_INVALID_FD

    res_tab[fd]["fp"] = offset
    return errors.ERR_OK

def tfs_stat(fd):
    print("Stat File")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if fd not in res_tab:
        return errors.ERR_INVALID_FD

    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    access = int(time.time())
    t_bytes = access.to_bytes(4, byteorder='big')
    print("New Inode access time")
    readability = ""
    if data[0] == 0x0:
        readability = "Read Only"
    else:
        readability = "Read and Write"
    data[1:5] = t_bytes
    acc_form = datetime.datetime.fromtimestamp(access).strftime("%Y-%m-%d %H:%M:%S")
    mod = int.from_bytes(data[5:9], byteorder='big')
    mod_form = datetime.datetime.fromtimestamp(mod).strftime("%Y-%m-%d %H:%M:%S")
    cre = int.from_bytes(data[9:13], byteorder='big')
    cre_form = datetime.datetime.fromtimestamp(cre).strftime("%Y-%m-%d %H:%M:%S")
    print(acc_form, mod_form, cre_form)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    return readability + " " + acc_form + " " + mod_form + " " + cre_form

def tfs_makeRO(filename):
    print("Make file Read only")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    inode = -1
    for i, b in res_tab.items():
        if b["filename"] == filename:
            inode = b["inode"]
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, inode, data)
    data[0] = 0x0
    t = int(time.time()).to_bytes(4, byteorder='big')
    print("New Inode access time")
    print(t)
    data[1:5] = t
    libDisk.writeBlock(cur_disk, inode, data)
    return errors.ERR_OK

def tfs_makeRW(filename):
    print("Make file Readable and writable")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    inode = -1
    for i, b in res_tab.items():
        if b["filename"] == filename:
            inode = b["inode"]
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, inode, data)
    data[0] = 0x1
    t = int(time.time()).to_bytes(4, byteorder='big')
    print("New Inode access time")
    print(t)
    data[1:5] = t
    libDisk.writeBlock(cur_disk, inode, data)
    return errors.ERR_OK

def tfs_writeByteAtOffset(fd, offset, char):
    print("Write Byte to File")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    # Check if file is writable
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    if data[0] == 0x0:
        print("File is read only")
        return errors.ERR_FILE_READ_ONLY

    data = bytearray([0x0] * BLOCKSIZE)
    fp = offset % BLOCKSIZE
    block = offset // BLOCKSIZE
    if block > len(res_tab[fd]["d_blocks"]):
        print("Cannot add another byte to file, use other write instead")
        return errors.ERR_WRITE_BYTE_AT_EOF
    libDisk.readBlock(cur_disk, res_tab[fd]["d_blocks"][block], data)
    data[fp] = char
    libDisk.writeBlock(cur_disk, res_tab[fd]["d_blocks"][block], data)

    # Update inode
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    t = int(time.time()).to_bytes(4, byteorder='big')
    print("New Inode access time")
    print(t)
    data[1:5] = t
    libDisk.writeBlock(cur_disk, res_tab[fd]["inode"], data)
    return errors.ERR_OK

def tfs_writeByte(fd, char):
    print("Write Byte to File (Using Current File Pointer)")
    if cur_disk == -1:
        return errors.ERR_DISK_NOT_MOUNTED
    if fd not in res_tab:
        return errors.ERR_INVALID_FD
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    if data[0] == 0x0:
        print("File is read only")
        return errors.ERR_FILE_READ_ONLY

    data = bytearray([0x0] * BLOCKSIZE)
    fp = res_tab[fd]["fp"] % BLOCKSIZE
    block = fp // BLOCKSIZE
    if block > len(res_tab[fd]["d_blocks"]):
        print("Cannot add another byte to file, use other write instead")
        return errors.ERR_WRITE_BYTE_AT_EOF
    libDisk.readBlock(cur_disk, res_tab[fd]["d_blocks"][block], data)

    data[fp] = ord(char)
    libDisk.writeBlock(cur_disk, res_tab[fd]["d_blocks"][block], data)

    # Update inode
    data = bytearray([0x0] * BLOCKSIZE)
    libDisk.readBlock(cur_disk, res_tab[fd]["inode"], data)
    t = int(time.time()).to_bytes(4, byteorder='big')
    print("New Inode access time")
    print(t)
    data[1:5] = t
    libDisk.writeBlock(cur_disk, res_tab[fd]["inode"], data)
    return errors.ERR_OK