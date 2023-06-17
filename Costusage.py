'''
https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/download-cost-usage-report.htm
'''

import oci
import os
                               
# This script downloads all of the cost, usage, (or both) reports for a tenancy (specified in the config file).
#
# Pre-requisites: Create an IAM policy to endorse users in your tenancy to read cost reports from the OCI tenancy.
#
# Example policy:
# define tenancy reporting as ocid1.tenancy.oc1..aaaaaaaaned4fkpkisbwjlr56u7cj63lf3wffbilvqknstgtvzub7vhqkggq
# endorse group <group_name> to read objects in tenancy reporting
#
# Note - The only value you need to change is the <group_name> with your own value. Do not change the OCID in the first statement.
                               
reporting_namespace = 'bling'
                               
# Download all usage and cost files. You can comment out based on the specific need:
# prefix_file = ""                     #  For cost and usage files
prefix_file = "reports/cost-csv"   #  For cost
# prefix_file = "reports/usage-csv"  #  For usage
                               
# Update these values
destintation_path = 'downloaded_reports'
                               


# Make a directory to receive reports
if not os.path.exists(destintation_path):
    os.mkdir(destintation_path)
                               
# Get the list of reports
config = oci.config.from_file("~/.oci/config", "DEFAULT-HOMEREGION")



reporting_bucket = config['tenancy']
object_storage = oci.object_storage.ObjectStorageClient(config)
report_bucket_objects = oci.pagination.list_call_get_all_results(object_storage.list_objects, reporting_namespace, reporting_bucket, prefix=prefix_file)                          
# for o in report_bucket_objects.data.objects:
#     print('Found file ' + o.name)
#     object_details = object_storage.get_object(reporting_namespace, reporting_bucket, o.name)
#     filename = o.name.rsplit('/', 1)[-1]
                               
#     with open(destintation_path + '/' + filename, 'wb') as f:
#         for chunk in object_details.data.raw.stream(1024 * 1024, decode_content=False):
#             f.write(chunk)
                               
#     print('----> File ' + o.name + ' Downloaded')

k=[]
for i in report_bucket_objects.data.objects:

    k.append(i.name)

k.sort()

for sorted in k:
    print (sorted)




### Policies
# define tenancy usage-report as ocid1.tenancy.oc1..aaaaaaaamhmra7tjzxzaronywihwj4ibgnifs27nxr5nvemeemmwtrtatr2q
# endorse group Administrators to read objects in tenancy usage-report
