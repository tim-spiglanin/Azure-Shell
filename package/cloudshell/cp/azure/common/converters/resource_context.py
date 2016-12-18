import jsonpickle

from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMFromCustomImageResourceModel


class ResourceContextConverter(object):

    def _get_attribute_by_name(self, attr_name, attrs):
        """Get attribute value by it's name from the attributes list

        :param attr_name: str name of the attribute
        :param attrs: list of attribute dictionaries: [{"name": "some_attr", "value": "some_value"}, ...]
        :return:
        """
        return next(attr["value"] for attr in attrs if attr["name"] == attr_name)

    def _set_base_deploy_azure_vm_model_params(self, deployed_resource, resource):
        """Convert all basic parameters for VM deploy models

        :param deployed_resource: deploy_azure_vm_resource_models.BaseDeployAzureVMResourceModel subclass instance
        :param resource: The context of the resource
        :return:
        """
        deployed_resource.group_name = ""  # needs to be auto generated
        deployed_resource.vm_name = ""  # needs to be auto generated
        deployed_resource.cloud_provider = resource.attributes['Cloud Provider']
        deployed_resource.instance_type = resource.attributes['Instance Type']
        deployed_resource.wait_for_ip = self._convert_to_bool(resource.attributes['Wait for IP'])
        deployed_resource.autoload = self._convert_to_bool(resource.attributes['Autoload'])
        deployed_resource.add_public_ip = self._convert_to_bool(resource.attributes['Add Public IP'])
        deployed_resource.inbound_ports = resource.attributes['Inbound Ports']
        deployed_resource.public_ip_type = resource.attributes['Public IP Type']
        deployed_resource.extension_script_file = resource.attributes['Extension Script file']
        deployed_resource.extension_script_configurations = resource.attributes['Extension Script Configurations']

        app_request = jsonpickle.decode(resource.app_context.app_request_json)
        attrs = app_request["logicalResource"]["attributes"]
        deployed_resource.username = self._get_attribute_by_name("User", attrs)
        deployed_resource.password = self._get_attribute_by_name("Password", attrs)

    def resource_context_to_deploy_azure_vm_from_custom_image_model(self, resource, deployment_credentials):
        """Converts context to a DeployAzureVMFromCustomImageResourceModel model

        :param resource: The context of the resource
        :param deployment_credentials:
        :return: cloudshell.cp.azure.models.deploy_azure_vm_resource_models.DeployAzureVMFromCustomImageResourceModel
        """
        deployed_resource = DeployAzureVMFromCustomImageResourceModel()
        self._set_base_deploy_azure_vm_model_params(deployed_resource=deployed_resource, resource=resource)
        deployed_resource.image_urn = resource.attributes['Image URN']
        deployed_resource.image_os_type = resource.attributes['Image OS Type']

        return deployed_resource

    def resource_context_to_deploy_azure_vm_model(self, resource, deployment_credentials):
        """Converts context to a DeployAzureVMResourceModel model

        :param resource : The context of the resource
        :param deployment_credentials:
        :return: cloudshell.cp.azure.models.deploy_azure_vm_resource_models.DeployAzureVMResourceModel
        """
        deployed_resource = DeployAzureVMResourceModel()
        self._set_base_deploy_azure_vm_model_params(deployed_resource=deployed_resource, resource=resource)

        deployed_resource.image_publisher = resource.attributes['Image Publisher']
        deployed_resource.image_offer = resource.attributes['Image Offer']
        deployed_resource.image_sku = resource.attributes['Image SKU']
        deployed_resource.image_version = resource.attributes['Image Version']

        return deployed_resource

    def _convert_to_bool(self, string):
        """Converts string to bool

        :param string: (str) incoming string
        :return: (boolean) True or False
        """
        return string in ['true', 'True', '1']
