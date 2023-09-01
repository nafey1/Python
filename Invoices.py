'''
The script goes through all the Subscribed Regions and determines the Limits for Regional and AD Specific Resources.
The script takes ONLY one command line argument, --profile_name , if none is provided DEFAULT is used
Redirect the output to a tsv file as it can generate a tab-delimited file, for viewing in Excel
'''

try:
    import oci
    import argparse
    import sys
    from datetime import date
except ModuleNotFoundError as err:
    # Error handling
    print(err)
    exit (1)


def summary(profile_name):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()

    

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
        return default.region_name

    print("Tenancy Name: ",tenancy.data.name)
    print("Total OCI Commercial Regions",len(total_regions))
    print ("Number of Subscribed Regions:", len(regions),"\n")
    print (f'Script Executed on: {date.today()}')



def invoices(profile_name):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()

    osp_gateway_client = oci.osp_gateway.InvoiceServiceClient(config)
    tenancy_id = config["tenancy"]
    list_invoices_response = osp_gateway_client.list_invoices(
    osp_home_region="us-ashburn-1",
    compartment_id=tenancy_id,
    sort_by="TYPE",
    sort_order="ASC")

    print(list_invoices_response.data)




if __name__ =="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile_name", dest="profile_name", type=str,
                        help="Specify the oci config profile name to be used", required=False, default=None)
    args=parser.parse_args()

    summary(args.profile_name)
    invoices(args.profile_name)
