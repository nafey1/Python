#!/usr/bin/python3
#
# blogpost.py
# 
# A small python script demonstrating how to iterate over the
# API response in Python-OCI SDK.
#
# This example lists the public IP address for any given compute
# VM along its display name, lifecycle state and OCID
# 
# Usage:
# ./blogpost.py <COMPARTMENT OCID
#
import sys
import oci
import argparse
from terminaltables import AsciiTable

# -------------------------------------------------- global variables

all_instance_metadata = [];

# -------------------------------------------------- parsing command line arguments
parser = argparse.ArgumentParser(
    prog = "python3 blogpost.py",
    description = "List name, OCID, lifecycle state and public IP for every compute VM in a compartment"
)

parser.add_argument(
    "compartment_ocid",
    help="the compartment OCID to be scanned"
)

args = parser.parse_args()
compartment_ocid = args.compartment_ocid

# step 1) load the config. In this example API-key authentication is used. 
# Alternative authentication methods exist as well, have a look at
# https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm
# for more details
config = oci.config.from_file()
oci.config.validate_config(config)

# step 2) list all the compute instances in a compartment. Many additional
# filter options exist, see 
# https://docs.oracle.com/en-us/iaas/tools/python/2.93.1/api/core/client/oci.core.ComputeClient.html#oci.core.ComputeClient.list_instances
# for more details
compute_client = oci.core.ComputeClient(config)
try:
    vm_instances = compute_client.list_instances(
        compartment_id = compartment_ocid
    ).data
except oci.exceptions.ServiceError as s:
    print(f"ERR: failed to obtain a list of compute VM instances due to '{s.message}'")
    sys.exit(1)

if len(vm_instances) == 0:
    print (f"ERR: no compute VMs found in compartment {compartment_ocid}")
    sys.exit(2)


# step 3) Public IP addresses are part of the instance virtual network
# interface card (NIC). Each vNIC is attached to a compute instance
# by means of a vNIC attachement. These must be obtained using a virtual
# network client
virtual_network_client = oci.core.VirtualNetworkClient(config)

# iterate over all the instances found in step 2
for vm in vm_instances:

    # this dict stores the relevant instance details
    instance_info = {
        "display_name": vm.display_name,
        "id": vm.id,
        "lifecycle_state": vm.lifecycle_state,
        "public_ips": [ ]
    }

    # skip terminated instances
    if vm.lifecycle_state == "TERMINATED":
        continue
    
    # get the VM's vNIC attachements. You could add a check for an error in this
    # call but this isn't done for the sake of readability.
    vnic_attachments = compute_client.list_vnic_attachments(
        compartment_id=vm.compartment_id,
        instance_id=vm.id
    ).data

    # get a list of vNICs from the vNIC attachement. Most often you
    # find a single vNIC, but it's possible to have multiple.
    vnics = [virtual_network_client.get_vnic(va.vnic_id).data for va in vnic_attachments]
    for vnic in vnics:
        if vnic.public_ip:
            instance_info["public_ips"].append(vnic.public_ip) 
    
    all_instance_metadata.append(instance_info)


# step 4) construct the output table
table_data = [
    [ "Display Name", "Lifecycle Status", "Public IPs", "Instance OCID"]
]

for row in all_instance_metadata:
    table_data.append(
        [row["display_name"], row["lifecycle_state"], ", ".join(row["public_ips"]), row["id"]]
    )

# step 5: print the table
print(AsciiTable(table_data).table)