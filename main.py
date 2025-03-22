from xml.dom import minidom
import xml.etree.ElementTree as ET
import libvirt
import os

def lookupdom(conn, id):
    return conn.lookupByID(id)

def getxml(dom):
    raw_xml = dom.XMLDesc()
    return minidom.parseString(raw_xml)

def get_disk_size(file_path):
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)  
        return round(size_mb, 2)
    except Exception as e:
        return f"Error: {e}"

conn = libvirt.open("qemu:///system")
if not conn:
    raise SystemExit("Failed to open connection to qemu:///system")

try:
    dom = lookupdom(conn, 1)
    xml = getxml(dom)

    print("=== VM Information ===")

    domainTypes = xml.getElementsByTagName("type")
    for domainType in domainTypes:
        print(f"Machine: {domainType.getAttribute('machine')}")
        print(f"Arch: {domainType.getAttribute('arch')}")

    root = ET.fromstring(dom.XMLDesc())

    memory_element = root.find("memory")
    if memory_element is None:
        memory_element = root.find("currentMemory")

    if memory_element is not None:
        memory_kib = int(memory_element.text)
        memory_mb = memory_kib // 1024  
        print(f"Memory: {memory_mb} MB")

    vcpu_element = root.find("vcpu")
    if vcpu_element is not None:
        print(f"vCPUs: {vcpu_element.text}")

    os_element = root.find(".//{http://libosinfo.org/xmlns/libvirt/domain/1.0}os")
    if os_element is not None:
        os_id = os_element.attrib.get("id", "Unknown OS")
        print(f"OS: {os_id}")
    else:
        print("OS: Unknown (no metadata found)")

    print("\n=== Network Interfaces ===")
    for interface in root.findall("./devices/interface"):
        mac = interface.find("mac")
        source = interface.find("source")
        if mac is not None:
            print(f"MAC Address: {mac.attrib.get('address')}")
        if source is not None:
            print(f"Network Source: {source.attrib.get('network', 'N/A')}")

    print("\n=== Disk Devices ===")
    for disk in root.findall("./devices/disk"):
        disk_source = disk.find("source")
        if disk_source is not None:
            disk_file = disk_source.attrib.get("file", "N/A")
            print(f"Disk Source: {disk_file}")
            if disk_file != "N/A":
                print(f"Disk Size: {get_disk_size(disk_file)} MB")

finally:
    conn.close()
