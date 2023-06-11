import oci

# Create a default config using DEFAULT profile in default location
# Refer to
# https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File
# for more info
config = oci.config.from_file()


# Initialize service client with default config file
monitoring_client = oci.monitoring.MonitoringClient(config)


# Send the request to service, some parameters are not required, see API
# doc for more info
summarize_metrics_data_response = monitoring_client.summarize_metrics_data(
    compartment_id="ocid1.compartment.oc1..aaaaaaaaebfcvucovsujhajrikjge63w333hirsdsop7yrr6uehti24kecpa",
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query="CpuUtilization[1m].mean()"

        ),

    compartment_id_in_subtree=False)

# Get the data from response
# print(summarize_metrics_data_response.data)

metrics_data = (summarize_metrics_data_response.data)

for i in metrics_data:
    # print (f'{i.dimensions}')
    for j,k in i.dimensions.items():
        if j != 'resourceDisplayName':
            continue
        print (j,k)


a=[]
b=[]


for i in metrics_data:
    # print (f'{i.dimensions}')
    for j in i.aggregated_datapoints:
        a.append(j.timestamp)
        b.append(j.value)

print (f'{a}')        