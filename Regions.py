'''
The script goes through all the Subscribed Regions and determines determines the availability domains
The script takes ONLY one command line argument, --profile_name , if none is provided DEFAULT is used
'''

try:
    import oci
    import argparse
    import sys
    from texttable import Texttable
except ModuleNotFoundError as err:
    print(err)
    exit (1)

def validate(profile_name):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()
    # Initialize service client with default config file
    identity_client = oci.identity.IdentityClient(config)
    tenancy_id = config["tenancy"]


    try:
        identity_client.list_region_subscriptions(tenancy_id = tenancy_id).data
    except oci.exceptions.ServiceError as s:
        print(f"ERR: failed to validate the Tenancy OCID '{s.message}'")
        sys.exit(1)


def summary(profile_name):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()

    # Initialize service client with default config file
    identity_client = oci.identity.IdentityClient(config)


    tenancy_id = config["tenancy"]
    list_regions_response = identity_client.list_regions()
    list_region_subscriptions_response = identity_client.list_region_subscriptions(tenancy_id=tenancy_id)
    tenancy = identity_client.get_tenancy(tenancy_id=tenancy_id)
    total_regions= (list_regions_response.data)
    regions=(list_region_subscriptions_response.data)

# Check for Default Region 
    for default in regions:
        if default.is_home_region == False:
            continue
        print ("Default Region for the Tenancy is: ", default.region_name)

    print("Tenancy Name: ",tenancy.data.name)
    print("Total OCI Commercial Regions",len(total_regions))
    print ("Number of Subscribed Regions:", len(regions),"\n")

    
t = Texttable()

def get_region (profile_name):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()

    # Initialize service client with default config file
    identity_client = oci.identity.IdentityClient(config)

    tenancy_id = config["tenancy"]
    list_region_subscriptions_response = identity_client.list_region_subscriptions(tenancy_id=tenancy_id)
    regions=(list_region_subscriptions_response.data)

    for j,region in enumerate(regions):
            identity_client.base_client.set_region(region.region_name)
            list_availability_domains_response = identity_client.list_availability_domains(compartment_id=tenancy_id)
            domains=(list_availability_domains_response.data )
            for i, ad in enumerate(domains):
                t.add_rows([['Number', 'Region', 'Region Key','AD #','Availability Domain'], [j+1, region.region_name, region.region_key,i+1, ad.name]])    
    return t


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile_name", dest="profile_name", type=str,
                        help="Specify the oci config profile name to be used, if none specified DEFAULT is used", required=False, default=None)
    args=parser.parse_args()

    validate(args.profile_name)
    summary(args.profile_name)

    get_region(args.profile_name)
    print (t.draw())