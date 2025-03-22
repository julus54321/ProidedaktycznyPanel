import libvirt
from xml.dom import minidom
import xml.etree.ElementTree as ET
import os
import json

def get_vm_info(dom):
    xml = minidom.parseString(dom.XMLDesc())
    root = ET.fromstring(dom.XMLDesc())

    vm_info = {
        "name": dom.name(),
        "uuid": dom.UUIDString(),
        "state": "Running" if dom.isActive() else "Stopped",
        "autostart": "Enabled" if dom.autostart() else "Disabled"
    }

    domain_type = xml.getElementsByTagName("type")
    for dt in domain_type:
        vm_info["machine"] = dt.getAttribute("machine")
        vm_info["architecture"] = dt.getAttribute("arch")

    memory_element = root.find("memory")
    if memory_element is None:
        memory_element = root.find("currentMemory")
    if memory_element is not None:
        vm_info["memory_mb"] = int(memory_element.text) // 1024

    vcpu_element = root.find("vcpu")
    if vcpu_element is not None:
        vm_info["vcpus"] = int(vcpu_element.text)

    os_element = root.find(".//{http://libosinfo.org/xmlns/libvirt/domain/1.0}os")
    if os_element is not None:
        vm_info["os"] = os_element.attrib.get("id", "Unknown OS")
    else:
        vm_info["os"] = "Unknown (no metadata found)"

    conn = libvirt.open("qemu:///system")
    default_network = conn.networkLookupByName("default")
    network_xml = default_network.XMLDesc()
    network_root = ET.fromstring(network_xml)

    dhcp_info = {}
    for host in network_root.findall(".//dhcp/host"):
        mac = host.attrib.get("mac")
        ip = host.attrib.get("ip")
        if mac and ip:
            dhcp_info[mac.lower()] = ip

    conn.close()

    vm_info["network_interfaces"] = []
    for interface in root.findall("./devices/interface"):
        mac = interface.find("mac")
        source = interface.find("source")
        net_info = {
            "mac": mac.attrib.get("address") if mac is not None else "N/A",
            "network_source": source.attrib.get("network", "N/A") if source is not None else "N/A",
            "ip": "N/A"
        }

        if mac is not None:
            mac_address = mac.attrib.get("address").lower()
            if mac_address in dhcp_info:
                net_info["ip"] = dhcp_info[mac_address]

        vm_info["network_interfaces"].append(net_info)

    vm_info["disks"] = []
    for disk in root.findall("./devices/disk"):
        disk_source = disk.find("source")
        if disk_source is not None:
            disk_file = disk_source.attrib.get("file", "N/A")
            disk_info = {"source": disk_file}
            if disk_file != "N/A":
                try:
                    disk_info["size_mb"] = round(os.path.getsize(disk_file) / (1024 * 1024), 2)
                except FileNotFoundError:
                    disk_info["size_mb"] = "File not found"
            vm_info["disks"].append(disk_info)

    return vm_info


def print_all_vms():
    conn = libvirt.open("qemu:///system")
    if not conn:
        raise SystemExit("Failed to open connection to qemu:///system")

    try:
        vm_ids = conn.listDomainsID()
        vm_names = conn.listDefinedDomains()

        vms = []
        for vm_id in vm_ids:
            dom = conn.lookupByID(vm_id)
            vms.append(get_vm_info(dom))

        for vm_name in vm_names:
            dom = conn.lookupByName(vm_name)
            vms.append(get_vm_info(dom))

        return vms

    finally:
        conn.close()

