################################################################################################################################
## The script goes through all the Subscribed Regions and determines the Limits for Regional and AD Specific Resources.
## The script takes ONLY one command line argument, i.e; tenancy_ocid
## Redirect the output to a tsv file as it can generate a tab-delimited file, for viewing in Excel
###############################################################################################################################

try:
    import oci
    import argparse
    import sys
    from datetime import date
except ModuleNotFoundError as err:
    # Error handling
    print(err)
    exit (1)

# Read the OCI CLI configuration file from the default location
config = oci.config.from_file("~/.oci/config","DEFAULT")

# Initialize service client with default config file
identity_client = oci.identity.IdentityClient(config)
limits_client = oci.limits.LimitsClient(config)

oci.config.validate_config(config)


###### Define Variables
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
service_scope_type=['REGION', 'AD']


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

# Print Execution Time
print (f'Script Executed on: {date.today()}')


# Check for Default Region 
for default in regions:
    if default.is_home_region == False:
        continue
    print ("Default Region for the Tenancy: ", default.region_name)

print("Tenancy Name: ",tenancy.data.name)

print ("Number of Subscribed Regions:", len(regions))



print (f" {'Region'}\t {'Service'}\t {'Service Description'}\t {'Limit Description'}\t {'Limit Name'}\t {'Scope'}\t {'Availability Domain'}\t {'Service Limit'}\t {'Limit Available'}\t {'Limit Used'}\t {'% of Limit Used'} ")

def regional_limits(tenancy_id, scope):
    for region in regions:
            identity_client.base_client.set_region(region.region_name)
            limits_client.base_client.set_region(region.region_name)

            list_services_response = limits_client.list_services(compartment_id=tenancy_id, sort_by="name",sort_order="ASC")
            services=(list_services_response.data)
            for svc in services:
                # if svc.name != "compute":
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

                        print (f"{region.region_name}\t {svc.name}\t {svc.description}\t {limit_definition[0].description}\t  {limits.name}\t {limits.scope_type}\t {limits.availability_domain}\t {limits.value}\t {svc_availability.available}\t {svc_availability.used}\t {'n/a' if isinstance(svc_availability.used, type(None))  or isinstance(limits.value, type(None))  or limits.value == 0 else svc_availability.used/limits.value*100} ")


def ad_limits(tenancy_id, scope):
    for region in regions:
            identity_client.base_client.set_region(region.region_name)
            limits_client.base_client.set_region(region.region_name)

            list_services_response = limits_client.list_services(compartment_id=tenancy_id, sort_by="name",sort_order="ASC")
            services=(list_services_response.data)
            for svc in services:
                # if svc.name != "compute":
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

                            print (f"{region.region_name}\t {svc.name}\t {svc.description}\t {limit_definition[0].description}\t  {limits.name}\t {limits.scope_type}\t {limits.availability_domain}\t {limits.value}\t {svc_availability.available}\t {svc_availability.used}\t {'n/a' if isinstance(svc_availability.used, type(None))  or isinstance(limits.value, type(None))  or limits.value == 0 else svc_availability.used/limits.value*100}  ")

if __name__ =="__main__":
    regional_limits (tenancy_id, "REGION")
    ad_limits (tenancy_id, "AD")