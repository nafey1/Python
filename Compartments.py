################################################################################################################################
## The script goes through all the Subscribed Regions and determines determines the availability domains
## The script takes ONLY one command like argument, i.e; tenancy_ocid
## Redirect the output to a tsv file as it can generate a tab-delimited file, for viewing in Excel
###############################################################################################################################
try:
    import oci
    import argparse
    import sys
    from prettytable import PrettyTable
    from treelib import Node, Tree
except ModuleNotFoundError as err:
    print (err)
    exit(1)

config = oci.config.from_file("~/.oci/config","DEFAULT")

# Initialize service client with default config file
identity_client = oci.identity.IdentityClient(config)
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


# Check for Default Region 
for default in regions:
    if default.is_home_region == False:
        continue
    print ("Default Region for the Tenancy is: ", default.region_name)

print("Tenancy Name: ",tenancy.data.name)
print ("Number of Subscribed Regions:", len(regions),"\n")
    

list_compartments_response = identity_client.list_compartments(compartment_id=tenancy_id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
list_compartments = (list_compartments_response.data)

tree = Tree()

x = PrettyTable()
x.field_names  = ["Root", "Level 1", "Level 2", "Level 3" ,"Level 4" ,"Level 5"]


root_compartment = identity_client.get_compartment(compartment_id=tenancy_id)

def tree_root_compartment ():
    tree.create_node(root_compartment.data.name, root_compartment.data.name) # root compartment
    x.add_row([root_compartment.data.name, "", "", "", "",""])

def tree_child_compartments(list_compartments):
    for i, root in enumerate(list_compartments):
        # if root.name != "ISV":
        #     continue
        # print (f'{i+1} {root.name} ')
        tree.create_node(root.name, root.id,  parent=root_compartment.data.name)
        x.add_row([root.name, "", "", "", "",""])
        list_compartments_response = identity_client.list_compartments(compartment_id=root.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
        list_compartments = (list_compartments_response.data)
        for j, one in enumerate(list_compartments):
            # print (f'\t\t{j+1} {one.name}  ')
            tree.create_node(one.name, one.id,  parent=root.id)
            x.add_row([root.name, one.name, "", "", "",""])
            list_compartments_response = identity_client.list_compartments(compartment_id=one.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
            list_compartments = (list_compartments_response.data)
            for k, two in enumerate(list_compartments):
                # print (f'\t\t\t{k+1 } {two.name}')
                tree.create_node(two.name, two.id,  parent=one.id)
                x.add_row([root.name, one.name, two.name, "", "",""])
                list_compartments_response = identity_client.list_compartments(compartment_id=two.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
                list_compartments = (list_compartments_response.data)
                for l, three in enumerate(list_compartments):
                    # print (f'\t\t\t\t{l+1} {three.name}')
                    tree.create_node(three.name, three.id,  parent=two.id)
                    x.add_row([root.name, one.name, two.name, three.name, "",""])
                    list_compartments_response = identity_client.list_compartments(compartment_id=three.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
                    list_compartments = (list_compartments_response.data)
                    for m, four in enumerate(list_compartments):
                        # print (f'\t\t\t\t\t{m+1} {four.name}')
                        tree.create_node(four.name, four.id,  parent=three.id)
                        x.add_row([root.name, one.name, two.name, three.name, four.name,""])
                        list_compartments_response = identity_client.list_compartments(compartment_id=four.id, compartment_id_in_subtree=False, sort_by="NAME", sort_order="ASC", lifecycle_state="ACTIVE")
                        list_compartments = (list_compartments_response.data)
                        for n, five in enumerate(list_compartments):
                            # print (f'\t\t\t\t\t\t{n+1} {five.name}')
                            tree.create_node(five.name, five.id,  parent=four.id)
                            x.add_row([root.name, one.name, two.name, three.name, four.name, five.name])
    return x, tree

if __name__ == "__main__":
    tree_root_compartment ()
    tree_child_compartments(list_compartments)

    # Create a tabular Compartment Structure
    x.align = "l"
    print(x)
    # Create a Tree like structure for compartments
    tree.show()





