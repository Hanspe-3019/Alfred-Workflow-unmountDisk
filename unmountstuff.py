''' workflow code in separate module
it is python 2.7
'''
import os
import plistlib
import json

def diskutil_list_external(physical=True):
    '''
        "diskutil list -plist external physical"

    '''
    disk_type = "physical" if physical else "virtual"
    diskutil = "diskutil list -plist external " + disk_type

    plist = os.popen(diskutil).read().encode()
    loads = plistlib.readPlistFromString # Python 2.7
    return loads(plist)

def get_all_disks():
    '''
    Strategie: Wir holen uns zuerst die physische Sicht.
    Jedes physische Device hat ein Partitionsschema und dementsprechend
    eine oder mehrere Partionen.
    '''
    devs = []
    disks = diskutil_list_external()['AllDisksAndPartitions']
    for disk in disks:
        disk_dev = disk['DeviceIdentifier']
        volumes = get_volumes_from_partitions(disk['Partitions'])
        disk_size = int(disk['Size'])//1000**3
        vols = 'Volumes ' +  ', '.join("'" + vol + "'" for vol in volumes)
        icon_path = get_icon_path(volumes)
        dev = {
            "title": vols,
            "subtitle": '{:s} {:d} MB'.format(disk_dev, disk_size),
            "arg": disk_dev,
            "icon": { "path": icon_path },
        }
        devs.append(dev)
    return json.dumps( { "items": devs } )

def get_volumes_from_partitions(partitions):
    ''' Hole VolumeName aus der Partition,
    EFI bei GUID-Schema interessiert nicht.
    Sonderfall einer Partition ist APFS-Container. Aus diesem werden
    die APFS-Volumes synthetisiert.
    '''
    volumes = []
    for partition in partitions:
        content = partition['Content']
        if content == 'EFI':
            continue
        try:
            volumes.append(partition['VolumeName'])
        except KeyError:
            container_dev = partition['DeviceIdentifier']
            volumes.extend(get_volumes_from_container_device(container_dev))


    return volumes

def get_volumes_from_container_device(dev):
    ''' Die Volumes eines Containers
    '''
    containers = diskutil_list_external(physical=False)['AllDisksAndPartitions']
    for container in containers:
        apfs_phys = container['APFSPhysicalStores']
        # Array of Dict
        for phys in apfs_phys:
            if phys['DeviceIdentifier'] != dev:
                continue
            volumes = container['APFSVolumes']
            return [vol['VolumeName'] for vol in volumes]

    return []
def get_icon_path(volumes):
    ''' Existiert png zu einem der Volumes?
    '''
    home = os.getenv('HOME')
    icon_dir = home + '/' + os.getenv('ICONDIR', '.')
    for vol in volumes:
        icon_path = icon_dir + '/' + vol + '.png'
        if not os.path.isfile(icon_path):
            continue

        return icon_path
    return 'default.png'
