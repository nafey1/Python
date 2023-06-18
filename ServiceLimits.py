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

## Define Variables
service_scope_type=['REGION', 'AD']


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

    print("Tenancy Name: ",tenancy.data.name)
    print("Total OCI Commercial Regions",len(total_regions))
    print ("Number of Subscribed Regions:", len(regions),"\n")
    print (f'Script Executed on: {date.today()}')


def regional_limits(profile_name, scope):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()


    identity_client = oci.identity.IdentityClient(config)
    tenancy_id = config["tenancy"]
    list_region_subscriptions_response = identity_client.list_region_subscriptions(tenancy_id=tenancy_id)
    regions=(list_region_subscriptions_response.data)
    limits_client = oci.limits.LimitsClient(config)

    for region in regions:
            identity_client.base_client.set_region(region.region_name)
            limits_client.base_client.set_region(region.region_name)

            list_services_response = limits_client.list_services(compartment_id=tenancy_id, sort_by="name",sort_order="ASC")
            services=(list_services_response.data)
            for svc in services:
                # if svc.name != "database":
                #     continue
                for svc_scope_type in service_scope_type:     
                    if svc_scope_type != scope:
                        continue
                    list_limit_values_response = limits_client.list_limit_values(compartment_id=tenancy_id,service_name=svc.name, scope_type=svc_scope_type)
                    svc_limits=(list_limit_values_response.data)            
                    for limits in svc_limits:
                        
                        list_limit_definitions_response = limits_client.list_limit_definitions(compartment_id=tenancy_id,service_name=svc.name, name=limits.name)
                        limit_definition=(list_limit_definitions_response.data)

                        get_resource_availability_response = limits_client.get_resource_availability(compartment_id=tenancy_id, service_name=svc.name, limit_name=limits.name)
                        svc_availability = (get_resource_availability_response.data)

                        print (f"{region.region_name}\t {svc.name}\t {svc.description}\t {limit_definition[0].description!r}\t  {limits.name}\t {limits.scope_type}\t {limits.availability_domain}\t {limits.value}\t {svc_availability.available}\t {svc_availability.used}\t {'n/a' if isinstance(svc_availability.used, type(None))  or isinstance(limits.value, type(None))  or limits.value == 0 else svc_availability.used/limits.value*100} ")


def ad_limits(profile_name, scope):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()

    # Initialize service client with default config file
    identity_client = oci.identity.IdentityClient(config)
    tenancy_id = config["tenancy"]
    list_region_subscriptions_response = identity_client.list_region_subscriptions(tenancy_id=tenancy_id)
    regions=(list_region_subscriptions_response.data)
    limits_client = oci.limits.LimitsClient(config)

    for region in regions:
            identity_client.base_client.set_region(region.region_name)
            limits_client.base_client.set_region(region.region_name)

            list_services_response = limits_client.list_services(compartment_id=tenancy_id, sort_by="name",sort_order="ASC")
            services=(list_services_response.data)
            for svc in services:
                # if svc.name != "database":
                #     continue
                for svc_scope_type in service_scope_type:     
                    if svc_scope_type != scope:
                        continue
                    
                    list_availability_domains_response = identity_client.list_availability_domains(compartment_id=tenancy_id)
                    domains=(list_availability_domains_response.data )
                    for ad in domains:

                        list_limit_values_response = limits_client.list_limit_values(compartment_id=tenancy_id,service_name=svc.name, availability_domain=ad.name,scope_type=svc_scope_type)
                        svc_limits=(list_limit_values_response.data)    

                        for limits in svc_limits:

                            list_limit_definitions_response = limits_client.list_limit_definitions(compartment_id=tenancy_id,service_name=svc.name, name=limits.name)
                            limit_definition=(list_limit_definitions_response.data)

                            get_resource_availability_response = limits_client.get_resource_availability(compartment_id=tenancy_id, service_name=svc.name, availability_domain=ad.name, limit_name=limits.name)
                            svc_availability = (get_resource_availability_response.data)

                            print (f"{region.region_name}\t {svc.name}\t {svc.description}\t {limit_definition[0].description!r}\t  {limits.name}\t {limits.scope_type}\t {limits.availability_domain}\t {limits.value}\t {svc_availability.available}\t {svc_availability.used}\t {'n/a' if isinstance(svc_availability.used, type(None))  or isinstance(limits.value, type(None))  or limits.value == 0 else svc_availability.used/limits.value*100}  ")

if __name__ =="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile_name", dest="profile_name", type=str,
                        help="Specify the oci config profile name to be used", required=False, default=None)
    args=parser.parse_args()

    summary(args.profile_name)
    print (f" {'Region'}\t {'Service'}\t {'Service Description'}\t {'Limit Description'}\t {'Limit Name'}\t {'Scope'}\t {'Availability Domain'}\t {'Service Limit'}\t {'Limit Available'}\t {'Limit Used'}\t {'% of Limit Used'} ")

    regional_limits (args.profile_name, service_scope_type[0])
    ad_limits (args.profile_name, service_scope_type[1])