################################################################################################################################
## The script goes through all the tenancy level Active announcements
## The script takes ONLY one command line argument, i.e; tenancy_ocid
###############################################################################################################################

try:
    import oci
    import argparse
    import sys
    from texttable import Texttable
except ModuleNotFoundError as err:
    print (err)
    exit(1)
except ImportError as imp:
    print(imp)
    exit(1)

config = oci.config.from_file("~/.oci/config","DEFAULT")


# Initialize service client with default config file
announcements_service_client = oci.announcements_service.AnnouncementClient(config)

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
    tenancy_check = announcements_service_client.list_announcements(
        compartment_id = tenancy_id
    ).data
except oci.exceptions.ServiceError as s:
    print(f"ERR: failed to validate the Tenancy OCID '{s.message}'")
    sys.exit(1)


list_announcements_response = announcements_service_client.list_announcements(
    compartment_id= tenancy_id,
    sort_by = "timeOneValue",
    lifecycle_state="ACTIVE",
    is_banner= False)

list_announcements = (list_announcements_response.data.items)


t = Texttable( max_width= 170)

def get_tenancy_announcements():
    for i, announcement in enumerate(list_announcements):
        # if announcement.id != "ocid1.announcement.oc1..aaaaaaaamq3ifotzunhecukfdjqdkyokhc2yr2p67khk3w4xkkzvwwcnjcga":
        #     continue
        get_announcement_response = announcements_service_client.get_announcement(announcement_id=announcement.id)
        a=(get_announcement_response.data)
        t.add_rows([['#','Platform', 'Announcement Type', 'State','Ticket Number', 'Affected Service(s)', 'Summary', 'Description' ,'Created','Action Required by'],  [i+1,a.platform_type, a.announcement_type, a.lifecycle_state, a.reference_ticket_number, ', '.join(a.services), a.summary, a.description ,a.time_created, a.time_one_value]])
    return t

## Execute the function
if __name__ == "__main__":
    get_tenancy_announcements()
    print (t.draw())