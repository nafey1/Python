################################################################################################################################
## The script goes through all the compartments in the Subscribed Regions and gathers the Instance Information
## If the value of an instance in the column "Maintenance Reboot Due Date" is anything other than None, please refer to instance for maintenance info
## The script takes ONLY one command line argument, i.e; tenancy_ocid
###############################################################################################################################


try:
    import oci
    import argparse
    import sys
    from prettytable import PrettyTable
except ModuleNotFoundError as err:
    # Error handling
    print(err)
    exit (1)

config = oci.config.from_file("~/.oci/config","DEFAULT")

# Initialize service client with default config file
identity_client = oci.identity.IdentityClient(config)
core_client = oci.core.ComputeClient(config)
oci.config.validate_config(config)

# Define Variables
parser = argparse.ArgumentParser(
    prog = "Subscribed Region / Availability Scanner",
    description = "List Subscribed Regions, and the respective Availability Domains"
)

parser.add_argument(
    "tenancy_ocid",
    help="the tenancy OCID to be scanned"
)

args = parser.parse_args()
tenancy_id = args.tenancy_ocid


## Tenancy Check
try:
    tenancy_check = identity_client.list_region_subscriptions(
        tenancy_id = tenancy_id
    ).data
except oci.exceptions.ServiceError as s:
    print(f"ERR: failed to validate the Tenancy OCID '{s.message}'")
    sys.exit(1)

# Check for Subscribed Regions
list_region_subscriptions_response = identity_client.list_region_subscriptions(tenancy_id=tenancy_id)
tenancy = identity_client.get_tenancy(tenancy_id=tenancy_id)
regions=(list_region_subscriptions_response.data)


compute = 0
ocpus   = 0.0
memory  = 0.0

# Check for Default Region 
for default in regions:
    if default.is_home_region == False:
        continue
    print ("Default Region for the Tenancy is: ", default.region_name)

print("Tenancy Name: ",tenancy.data.name)
print ("Number of Subscribed Regions:", len(regions),"\n")
    

root_compartment = identity_client.get_compartment(compartment_id=tenancy_id)


x = PrettyTable()
x.field_names  = ["Compartment", "Region", "Display Name", "Availability Domain" ,"Fault Domain" ,"State", "Shape", "OCPUs", "Memory", "Maintenance Reboot Due Date"]

# Get the compute instances from the ROOT compartment
for region in regions:
    identity_client.base_client.set_region(region.region_name)
    core_client.base_client.set_region(region.region_name)
    list_instances_response = core_client.list_instances(compartment_id=root_compartment.data.id)
    list_instances = (list_instances_response.data)
    for a, instance in enumerate(list_instances):
        # print (f'{region.region_name} {root_compartment.data.name} {instance.display_name} {instance.availability_domain} {instance.fault_domain} {instance.lifecycle_state} {instance.shape} {instance.shape_config.ocpus} {instance.shape_config.memory_in_gbs} {instance.time_maintenance_reboot_due}')
        x.add_row([ root_compartment.data.name, region.region_name, instance.display_name, instance.availability_domain, instance.fault_domain, instance.lifecycle_state, instance.shape, instance.shape_config.ocpus, instance.shape_config.memory_in_gbs, instance.time_maintenance_reboot_due   ])
        if instance.lifecycle_state in ("TERMINATING","TERMINATED"):
            continue
        compute = a + 1
        ocpus  = ocpus  + instance.shape_config.ocpus
        memory = memory + instance.shape_config.memory_in_gbs



# Get the compute instances from the Other compartments
list_compartments_response = identity_client.list_compartments(compartment_id=tenancy_id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
list_compartments = (list_compartments_response.data)


for root in list_compartments:
    if root.name != 'ISV':
        continue
    list_compartments_response = identity_client.list_compartments(compartment_id=root.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
    list_compartments = (list_compartments_response.data)
    for region in regions:
        identity_client.base_client.set_region(region.region_name)
        core_client.base_client.set_region(region.region_name)
        list_instances_response = core_client.list_instances(compartment_id=root.id)
        list_instances = (list_instances_response.data)
        for i, instances in enumerate(list_instances):
            x.add_row([ root.name, region.region_name, instances.display_name, instances.availability_domain, instances.fault_domain, instances.lifecycle_state, instances.shape, instances.shape_config.ocpus, instances.shape_config.memory_in_gbs, instances.time_maintenance_reboot_due   ])
            # print (f'\t\t {root.name} {region.region_name} {instances.display_name} {instances.availability_domain}, {instances.fault_domain}, {instances.lifecycle_state}, {instances.shape}, {instances.shape_config.ocpus}, {instances.shape_config.memory_in_gbs}, {instances.time_maintenance_reboot_due}')
            if instances.lifecycle_state in ("TERMINATING","TERMINATED"):
                continue
            compute = compute + 1
            ocpus  = ocpus  + instances.shape_config.ocpus
            memory = memory + instances.shape_config.memory_in_gbs
#### Level ONE
    for one in list_compartments:
        if one.name != 'SA':
            continue
        list_compartments_response = identity_client.list_compartments(compartment_id=one.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
        list_compartments = (list_compartments_response.data)
        for region in regions:
            identity_client.base_client.set_region(region.region_name)
            core_client.base_client.set_region(region.region_name)
            list_instances_response = core_client.list_instances(compartment_id=one.id)
            list_instances = (list_instances_response.data)
            for j, instances in enumerate(list_instances):
                x.add_row([ root.name+' > '+one.name, region.region_name, instances.display_name, instances.availability_domain, instances.fault_domain, instances.lifecycle_state, instances.shape, instances.shape_config.ocpus, instances.shape_config.memory_in_gbs, instances.time_maintenance_reboot_due   ])
                # print (f'\t\t {one.name} {region.region_name} {instances.display_name} {instances.availability_domain}, {instances.fault_domain}, {instances.lifecycle_state}, {instances.shape}, {instances.shape_config.ocpus}, {instances.shape_config.memory_in_gbs}, {instances.time_maintenance_reboot_due}')                
                if instances.lifecycle_state in ("TERMINATING","TERMINATED"):
                    continue
                compute = compute + 1
                ocpus  = ocpus  + instances.shape_config.ocpus
                memory = memory + instances.shape_config.memory_in_gbs
#### Level TWO                
        for two in list_compartments:
            if two.name not in ("farooqnafey"):
                continue
            list_compartments_response = identity_client.list_compartments(compartment_id=two.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
            list_compartments = (list_compartments_response.data)
            for region in regions:
                identity_client.base_client.set_region(region.region_name)
                core_client.base_client.set_region(region.region_name)
                list_instances_response = core_client.list_instances(compartment_id=two.id)
                list_instances = (list_instances_response.data)
                for k, instances in enumerate(list_instances):
                    x.add_row([ root.name+'>'+one.name+'>'+two.name, region.region_name, instances.display_name, instances.availability_domain, instances.fault_domain, instances.lifecycle_state, instances.shape, instances.shape_config.ocpus, instances.shape_config.memory_in_gbs, instances.time_maintenance_reboot_due   ])
                    # print (f'\t\t\t {two.name} {region.region_name} {instances.display_name} {instances.availability_domain}, {instances.fault_domain}, {instances.lifecycle_state}, {instances.shape}, {instances.shape_config.ocpus}, {instances.shape_config.memory_in_gbs}, {instances.time_maintenance_reboot_due}')
                    if instances.lifecycle_state in ("TERMINATING","TERMINATED"):
                        continue
                    compute = compute + 1
                    ocpus  = ocpus  + instances.shape_config.ocpus
                    memory = memory + instances.shape_config.memory_in_gbs
#### Level Three
            for three in list_compartments:
                list_compartments_response = identity_client.list_compartments(compartment_id=three.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
                list_compartments = (list_compartments_response.data)
                for region in regions:
                    identity_client.base_client.set_region(region.region_name)
                    core_client.base_client.set_region(region.region_name)
                    list_instances_response = core_client.list_instances(compartment_id=three.id)
                    list_instances = (list_instances_response.data)
                    for l, instances in enumerate(list_instances):
                        x.add_row([ root.name+'>'+one.name+'>'+two.name+'>'+three.name, region.region_name, instances.display_name, instances.availability_domain, instances.fault_domain, instances.lifecycle_state, instances.shape, instances.shape_config.ocpus, instances.shape_config.memory_in_gbs, instances.time_maintenance_reboot_due   ])
                        # print (f'\t\t\t {three.name} {region.region_name} {instances.display_name} {instances.availability_domain}, {instances.fault_domain}, {instances.lifecycle_state}, {instances.shape}, {instances.shape_config.ocpus}, {instances.shape_config.memory_in_gbs}, {instances.time_maintenance_reboot_due}')
                        if instances.lifecycle_state in ("TERMINATING","TERMINATED"):
                            continue
                        compute = compute + 1
                        ocpus  = ocpus  + instances.shape_config.ocpus
                        memory = memory + instances.shape_config.memory_in_gbs
#### Level FOUR
                for four in list_compartments:
                    list_compartments_response = identity_client.list_compartments(compartment_id=four.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
                    list_compartments = (list_compartments_response.data)
                    for region in regions:
                        identity_client.base_client.set_region(region.region_name)
                        core_client.base_client.set_region(region.region_name)
                        list_instances_response = core_client.list_instances(compartment_id=four.id)
                        list_instances = (list_instances_response.data)
                        for m, instances in enumerate(list_instances):
                            x.add_row([ root.name+'>'+one.name+'>'+two.name+'>'+three.name+'>'+four.name, region.region_name, instances.display_name, instances.availability_domain, instances.fault_domain, instances.lifecycle_state, instances.shape, instances.shape_config.ocpus, instances.shape_config.memory_in_gbs, instances.time_maintenance_reboot_due   ])
                            # print (f'\t\t\t {four.name} {region.region_name} {instances.display_name} {instances.availability_domain}, {instances.fault_domain}, {instances.lifecycle_state}, {instances.shape}, {instances.shape_config.ocpus}, {instances.shape_config.memory_in_gbs}, {instances.time_maintenance_reboot_due}')
                            if instances.lifecycle_state in ("TERMINATING","TERMINATED"):
                                continue
                            compute = compute + 1
                            ocpus  = ocpus  + instances.shape_config.ocpus
                            memory = memory + instances.shape_config.memory_in_gbs
#### Level FIVE
                    for five in list_compartments:
                        list_compartments_response = identity_client.list_compartments(compartment_id=five.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
                        list_compartments = (list_compartments_response.data)
                        for region in regions:
                            identity_client.base_client.set_region(region.region_name)
                            core_client.base_client.set_region(region.region_name)
                            list_instances_response = core_client.list_instances(compartment_id=five.id)
                            list_instances = (list_instances_response.data)
                            for n, instances in enumerate(list_instances):
                                x.add_row([ root.name+'>'+one.name+'>'+two.name+'>'+three.name+'>'+four.name+'>'+five.name, region.region_name, instances.display_name, instances.availability_domain, instances.fault_domain, instances.lifecycle_state, instances.shape, instances.shape_config.ocpus, instances.shape_config.memory_in_gbs, instances.time_maintenance_reboot_due   ])
                                # print (f'\t\t\t {five.name} {region.region_name} {instances.display_name} {instances.availability_domain}, {instances.fault_domain}, {instances.lifecycle_state}, {instances.shape}, {instances.shape_config.ocpus}, {instances.shape_config.memory_in_gbs}, {instances.time_maintenance_reboot_due}')
                                if instances.lifecycle_state in ("TERMINATING","TERMINATED"):
                                    continue
                                compute = compute  +1
                                ocpus  = ocpus  + instances.shape_config.ocpus
                                memory = memory + instances.shape_config.memory_in_gbs





x.align = "l"
print(x)

print (f'\x1B[3mTerminating / Terminated Instances are not counted in the Summary \x1B[0m')
print (f'Total Server: {compute}, Total OCPUs: {ocpus}, Total Memory (in GBs): {memory}')


# list_instances_response = core_client.list_instances(compartment_id="ocid1.compartment.oc1..aaaaaaaaiaujpsq7v42fhc7vd3neinxzxsvbyi4rcm7y4dfp2hix6uwuioba", display_name="Bastion")            
# print (list_instances_response.data)