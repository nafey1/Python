import oci
from oci.exceptions import ServiceError
import argparse
from tabulate import tabulate
import concurrent.futures
import logging
import os
import inspect

script_directory = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

logging.basicConfig(filename=f"{script_directory}/log.txt", filemode="w", format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
logger.setLevel(logging.INFO)    

def write_to_file (region, data, scope_type):
    logger.info("Entered write_to_file function.")
    columns = ['Region', 'Service', 'Service Description', 'Limit Description', 'Limit Name', 'Scope', 'Availability Domain', 'Service Limit', 'Limit Available', 'Limit Used', '% of Limit Used']
    file_path = f"{script_directory}/limits/{region}/limits-{scope_type}.txt"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "w") as f:
        f.write(tabulate(data, headers=columns, tablefmt='simple'))
        logger.info(f"Finished writing file for region {region}.")

def get_limit_percentage (resource_availability, limit_value):
    if resource_availability.used is None or limit_value.value is None or limit_value.value == 0:
        limit_percentage = "n/a"
    else:
        limit_percentage = "{:.2f}".format(resource_availability.used / limit_value.value * 100)
    
    return limit_percentage

def get_regions (profile_name):
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()

    identity_client = oci.identity.IdentityClient(config)
    tenancy_id = config["tenancy"]

    # Get subscribed regions
    region_subscriptions = identity_client.list_region_subscriptions(tenancy_id).data
    regions = [region_subscription.region_name for region_subscription in region_subscriptions]
    logger.info("Finished getting the regions.")    
    return regions

def process_oci_limits(profile_name, region):
    # Load the default configuration
    if profile_name:
        config = oci.config.from_file(profile_name=profile_name)
    else:
        config = oci.config.from_file()

    identity_client = oci.identity.IdentityClient(config)
    limits_client = oci.limits.LimitsClient(config)
    tenancy_id = config["tenancy"]

    region_limits = []
    ad_limits = []
    identity_client.base_client.set_region(region)
    limits_client.base_client.set_region(region)

    # Get service and limit names
    services = limits_client.list_services(tenancy_id).data
    logger.info(f"Starting limits processing for region {region}")  
    for service in services:
        service_name = service.name
        limit_definitions = limits_client.list_limit_definitions(tenancy_id, service_name=service_name).data        
        limits_values = limits_client.list_limit_values(tenancy_id, service_name).data
        for limit_value in limits_values:
            for limit_definition in limit_definitions:
                if limit_definition.name == limit_value.name:
                    limit_description = limit_definition.description
            if limit_value.scope_type == "AD":
                ad_name = limit_value.availability_domain
                try:
                    resource_availability=limits_client.get_resource_availability(compartment_id=tenancy_id, service_name=service_name, availability_domain=ad_name, limit_name=limit_value.name).data
                except Exception as e:
                    logger.exception(f"Encountered error for {service_name} {limit_value.name} {limit_value.scope_type} {limit_value}: {e}")
                limit_percentage = get_limit_percentage(resource_availability, limit_value)
                ad_limits.append([region, service_name, service.description, limit_description, limit_value.name, limit_value.scope_type, limit_value.availability_domain, limit_value.value, resource_availability.available, resource_availability.used, limit_percentage])
            elif limit_value.scope_type == "REGION":
                try:
                    resource_availability=limits_client.get_resource_availability(compartment_id=tenancy_id, service_name=service_name, limit_name=limit_value.name).data
                except ServiceError as e:
                    logger.exception(f"Error getting usage for {service_name} {limit_definition.name} {limit_value.name} {limit_value.scope_type}: {e}")
                limit_percentage = get_limit_percentage(resource_availability, limit_value)
                region_limits.append([region, service_name, service.description, limit_description, limit_value.name, limit_value.scope_type, limit_value.availability_domain, limit_value.value, resource_availability.available, resource_availability.used, limit_percentage])
        logger.info(f"Finished with service {service.name} in {region}")    
    write_to_file(region=region, data=ad_limits,scope_type="AD")
    write_to_file(region=region, data=region_limits,scope_type="REGION")

def check_oci_limits(profile):
    regions = get_regions(profile)

    with concurrent.futures.ThreadPoolExecutor(max_workers=26) as executor:
        futures = []
        for region in regions:
            logger.info(f"Created thread for region {region}")
            future = executor.submit(process_oci_limits, profile, region)
            futures.append(future)

    concurrent.futures.wait(futures)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile-name", dest="profile_name", type=str,
                        help="Specify the oci config profile name to be used", required=False, default=None)
    args=parser.parse_args()
    profile = args.profile_name

    retry_strategy_builder = oci.retry.RetryStrategyBuilder(
        max_attempts_check = True,
        max_attempts = 10,
        total_elapsed_time_check = True,
        total_elapsed_time_seconds = 300,
        retry_base_sleep_time_seconds = 2,
        service_error_check=True,
        service_error_retry_on_any_5xx=True,
        service_error_retry_config={
            400: ['QuotaExceeded', 'LimitExceeded'],
            429: []
        },
        backoff_type=oci.retry.BACKOFF_FULL_JITTER_EQUAL_ON_THROTTLE_VALUE
    )

    custom_retry_strategy = retry_strategy_builder.get_retry_strategy()
    oci.retry.GLOBAL_RETRY_STRATEGY = custom_retry_strategy

    check_oci_limits (profile)
