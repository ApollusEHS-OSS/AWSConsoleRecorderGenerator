import os
import json
import pprint
import math
import re

services = None
cfn_spec = None
occurances = []
skipped_ops = []
tf_resources = []
cfn_types = []
cfn_occurances = [
    "AWS::CloudFormation::CustomResource",
    "AWS::CloudFormation::WaitCondition",
    "AWS::CloudFormation::WaitConditionHandle",
    "AWS::SDB::Domain",
    "AWS::EC2::SecurityGroupEgress",
    "AWS::EC2::SecurityGroupIngress",
    "AWS::Redshift::ClusterSecurityGroup",
    "AWS::Redshift::ClusterSecurityGroupIngress",
    "AWS::ServiceDiscovery::PrivateDnsNamespace",
    "AWS::ServiceDiscovery::PublicDnsNamespace",
    "AWS::ServiceDiscovery::Service",
    "AWS::ServiceDiscovery::Instance",
    "AWS::SecretsManager::SecretTargetAttachment",
    "AWS::SecretsManager::ResourcePolicy",
    "AWS::RDS::DBSecurityGroup",
    "AWS::RDS::DBSecurityGroupIngress",
    "AWS::ElastiCache::SecurityGroup",
    "AWS::ElastiCache::SecurityGroupIngress",
    "Alexa::ASK::Skill",
    "AWS::EC2::EC2Fleet",
    "AWS::Kinesis::StreamConsumer",
    "AWS::CloudFormation::Macro",
    "AWS::CloudFormation::Transform",
    "AWS::CodePipeline::CustomActionType",
    "AWS::EC2::NetworkInterfacePermission",
    "AWS::EC2::TrunkInterfaceAssociation",
    "AWS::SES::Template",
    "AWS::Lambda::LayerVersionPermission",
    "AWS::Lambda::Permission",
    "AWS::Logs::Destination",
    "AWS::CDK::Metadata",
    "AWS::Route53::RecordSetGroup",
    "AWS::EMR::InstanceFleetConfig",
    "AWS::Glue::Partition",
    "AWS::KinesisAnalyticsV2::ApplicationCloudWatchLoggingOption"
]
'''
    "AWS::CloudFormation::Init",
    "AWS::SSM::MaintenanceWindowTarget",
    "AWS::CloudFormation::Authentication",
    "AWS::CloudFormation::Interface",
    "AWS::AutoScaling::Trigger"
'''

tf_occurances = [
    "aws_acm_certificate_validation",
    "aws_simpledb_domain",
    "aws_opsworks_custom_layer", # bad detection
    "aws_opsworks_ganglia_layer", # bad detection
    "aws_opsworks_haproxy_layer", # bad detection
    "aws_opsworks_java_app_layer", # bad detection
    "aws_opsworks_memcached_layer", # bad detection
    "aws_opsworks_mysql_layer", # bad detection
    "aws_opsworks_nodejs_app_layer", # bad detection
    "aws_opsworks_php_app_layer", # bad detection
    "aws_opsworks_rails_app_layer", # bad detection
    "aws_opsworks_static_web_layer", # bad detection
    "aws_appmesh_mesh",
    "aws_appmesh_route",
    "aws_appmesh_virtual_node",
    "aws_appmesh_virtual_router",
    "aws_alb",
    "aws_alb_listener",
    "aws_alb_listener_certificate",
    "aws_alb_listener_rule",
    "aws_alb_target_group",
    "aws_alb_target_group_attachment",
    "aws_iam_server_certificate",
    "aws_route53_delegation_set"
]

with open("combined.json", "r") as f:
    services = json.loads(f.read())

with open("cfnspec.json", "r") as f:
    cfn_spec = json.loads(f.read())['ResourceTypes']

with open("tf_resources.txt", "r") as f:
    lines = f.read().splitlines()
    for line in lines:
        tf_resources.append(line)

for cfntype, _ in cfn_spec.items():
    cfn_types.append(cfntype)

cfn_types.append("AWS::CloudFormation::Transform")
cfn_types.append("AWS::Lambda::LayerVersionPermission")
cfn_types.append("AWS::CDK::Metadata")
cfn_types.append("AWS::EC2::VPCEndpointService")
cfn_types.append("AWS::Lambda::LayerVersion")
cfn_types = set(cfn_types)

with open("bg.js", "r") as f:
    text = f.read()
    lines = text.splitlines()
    cfn_occurances += re.compile('(AWS\:\:[a-zA-Z0-9]+\:\:[a-zA-Z0-9]+)').findall(text)
    tf_occurances += re.compile('terraformType\'\:\ \'(aws(?:\_[a-zA-Z0-9]+)+)\'').findall(text)
    for line in lines:
        line = line.strip()
        if line.startswith("// autogen:") or line.startswith("// manual:"):
            lineparts = line.split(":")
            occurances.append(lineparts[2])

with open("skipped.txt", "r") as f:
    lines = f.read().splitlines()
    for line in lines:
        skipped_ops.append(line)

total_services = 0
total_operations = 0
total_unique_occurances = 0
with open("coverage.md", "w") as f:
    f.write("## CloudFormation Resource Coverage\n\n")
    f.write("**%s/%s (%s%%)** Resources Covered\n" % (
        len(set(cfn_occurances)),
        len(cfn_types),
        int(math.floor(len(set(cfn_occurances)) * 100 / len(cfn_types)))
    ))

    f.write("\n| Type | Coverage |\n")
    f.write("| --- | --- |\n")

    for cfntype in sorted(cfn_types):
        f.write("| *%s* | %s |\n" % (cfntype, cfn_occurances.count(cfntype)))

    f.write("\n## Terraform Coverage\n\n")
    f.write("**%s/%s (%s%%)** Resources Covered\n" % (
        len(set(tf_occurances)),
        len(tf_resources),
        int(math.floor(len(set(tf_occurances)) * 100 / len(tf_resources)))
    ))
    
    f.write("\n| Type | Coverage |\n")
    f.write("| --- | --- |\n")

    for tf_resource in sorted(tf_resources):
        f.write("| *%s* | %s |\n" % (tf_resource, tf_occurances.count(tf_resource)))

    f.write("\n## Service Coverage\n\n")
    f.write("| Service | Coverage |\n")
    f.write("| --- | --- |\n")

    for servicename in sorted(services):
        service = services[servicename]
        occurance_count = 0
        for operation in service['operations']:
            if servicename + "." + operation['name'] in occurances or servicename + "." + operation['name'] in skipped_ops:
                occurance_count += 1
        if occurance_count > 0:
            coverage_val = "%s/%s (%s%%)" % (occurance_count, len(service['operations']), int(math.floor(occurance_count * 100 / len(service['operations']))))
            f.write("| *%s* | %s |\n" % (servicename, coverage_val))
    
    f.write("\n## Operation Coverage\n\n")
    f.write("| Service | Operation | Occurances |\n")
    f.write("| --- | --- | --- |\n")
    for servicename in sorted(services):
        service = services[servicename]
        total_services += 1
        for operation in service['operations']:
            total_operations += 1
            occurance_count = occurances.count(servicename + "." + operation['name'])
            if occurance_count > 0:
                total_unique_occurances += 1
            f.write("| *%s* | `%s` | %s |\n" % (servicename, operation['name'], occurance_count))

    f.write("\n\n**Total Services: %s**\n\n**Total Operations: %s**\n\n**Total Unique Occurances: %s (%s%%)**\n"
        % (total_services, total_operations, total_unique_occurances, int(math.floor(total_unique_occurances * 100 / total_operations)))
    )
