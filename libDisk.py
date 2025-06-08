#!/usr/bin/env python3

import errors

BLOCKSIZE = 256

disks = {}
closed_disks = {}
disk_num_counter = 0

def showDisk():
    disk = disks[0]
    disk.seek(0)
    block = disk.read(10240)
    for i in range(0, 10240):
        print(f"{block[i]:08X}", end='\\')
    print()

def openDisk(filename, nBytes):
    print("openDisk")
    global disk_num_counter
    global disks
    if nBytes < 0:
        return errors.ERR_INVALID_PARAMETERS
    if nBytes > 0:
        disk = open(filename, "wb+")
        disk.write(b'\0' * nBytes)
        disks[disk_num_counter] = disk
        disk_num_counter += 1
        print(disks)
        print(closed_disks)
        return disk_num_counter - 1
    elif nBytes == 0:
        disk = open(filename, "rb+")
        newDiskNum = closed_disks[filename]
        disks[newDiskNum] = disk
        print(disks)
        print(closed_disks)
        return newDiskNum
    else:
        return errors.ERR_INVALID_PARAMETERS

def readBlock(disk, bNum, block: bytearray):
    print("readBlock")
    if disk not in disks:
        return errors.ERR_DISK_NOT_MOUNTED
    curDisk = disks[disk]
    curDisk.seek(bNum * BLOCKSIZE)
    block[:] = curDisk.read(BLOCKSIZE)
    for i in range(0, len(block)):
        chunk = block[i]
        print(f"{chunk:08X}", end='\\')
    print()
    return errors.ERR_OK

def writeBlock(disk, bNum, block: bytearray):
    print("writeBlock")
    for i in range(0, len(block)):
        chunk = block[i]
        print(f"{chunk:08X}", end='\\')
    print()
    if disk not in disks:
        return errors.ERR_DISK_NOT_MOUNTED
    curDisk = disks[disk]
    curDisk.seek(bNum * BLOCKSIZE)
    curDisk.write(block)
    return errors.ERR_OK


def closeDisk(diskNum):
    print("closeDisk")
    if diskNum not in disks:
        return errors.ERR_DISK_NOT_MOUNTED
    disk = disks[diskNum]
    closed_disks[disk.name] = diskNum
    disk.close()
    print("Disks: ")
    print(disks)
    print("Closed Disks: ")
    print(closed_disks)
    return errors.ERR_OK
