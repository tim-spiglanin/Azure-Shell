import os
from msrestazure.azure_cloud import get_cloud_from_metadata_endpoint
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials

from cloudshell.cp.azure.common.singletons import SingletonByArgsMeta
from cloudshell.cp.azure.common.singletons import AbstractComparableInstance


class AzureClientsManager(AbstractComparableInstance):
    __metaclass__ = SingletonByArgsMeta

    azure_stack_dev_base_url = "https://management.local.azurestack.external"

    def check_params_equality(self, cloud_provider, *args, **kwargs):
        """Check if instance have the same attributes for initializing Azure session as provided in cloud_provider

        :param cloud_provider: AzureCloudProviderResourceModel instance
        :return: (bool) True/False whether attributes are same or not
        """
        subscription_id = self._get_subscription(cloud_provider)
        application_id = self._get_azure_application_id(cloud_provider)
        application_key = self._get_azure_application_key(cloud_provider)
        tenant = self._get_azure_tenant(cloud_provider)

        return all([
            subscription_id == self._subscription_id,
            application_id == self._application_id,
            application_key == self._application_key,
            tenant == self._tenant])

    def __init__(self, cloud_provider):
        """
        :param cloud_provider: AzureCloudProviderResourceModel instance
        :return
        """
        self.is_azure_stack = os.environ.get('AZURE_STACK', False)
        if self.is_azure_stack:
            os.environ['REQUESTS_CA_BUNDLE'] = 'c:\AzureStackRootSelfSignedCert.cer'

        self._subscription_id = self._get_subscription(cloud_provider)
        self._application_id = self._get_azure_application_id(cloud_provider)
        self._application_key = self._get_azure_application_key(cloud_provider)
        self._tenant = self._get_azure_tenant(cloud_provider)
        self.azure_stack_metadata = get_cloud_from_metadata_endpoint(self.azure_stack_dev_base_url) if self.is_azure_stack else None
        self._service_credentials = self._get_service_credentials()
        self._compute_client = None
        self._network_client = None
        self._storage_client = None
        self._resource_client = None
        self._subscription_client = None

    def _get_service_credentials(self):
        if self.is_azure_stack:
            temp = os.environ['REQUESTS_CA_BUNDLE']
            del os.environ['REQUESTS_CA_BUNDLE']
            sp = ServicePrincipalCredentials(client_id=self._application_id,
                                             secret=self._application_key,
                                             tenant=self._tenant,
                                             cloud_environment=self.azure_stack_metadata)
            os.environ['REQUESTS_CA_BUNDLE'] = temp
            return sp

        return ServicePrincipalCredentials(client_id=self._application_id,
                                           secret=self._application_key,
                                           tenant=self._tenant)

    def _get_subscription(self, cloud_provider_model):
        return cloud_provider_model.azure_subscription_id

    def _get_azure_application_id(self, cloud_provider_model):
        return cloud_provider_model.azure_application_id

    def _get_azure_application_key(self, cloud_provider_model):
        return cloud_provider_model.azure_application_key

    def _get_azure_tenant(self, cloud_provider_model):
        return cloud_provider_model.azure_tenant

    @property
    def compute_client(self):
        if self._compute_client is None:
            with SingletonByArgsMeta.lock:
                if self._compute_client is None:
                    self._compute_client = ComputeManagementClient(self._service_credentials,
                                                                   self._subscription_id,
                                                                   base_url=self.azure_stack_metadata.endpoints.resource_manager if self.is_azure_stack else None,
                                                                   api_version='2016-03-30' if self.is_azure_stack else '2017-03-01')

        return self._compute_client

    @property
    def network_client(self):
        if self._network_client is None:
            with SingletonByArgsMeta.lock:
                if self._network_client is None:
                    self._network_client = NetworkManagementClient(self._service_credentials,
                                                                   self._subscription_id,
                                                                   base_url=self.azure_stack_metadata.endpoints.resource_manager if self.is_azure_stack else None,
                                                                   api_version='2015-06-15' if self.is_azure_stack else '2017-03-01')

        return self._network_client

    @property
    def storage_client(self):
        if self._storage_client is None:
            with SingletonByArgsMeta.lock:
                if self._storage_client is None:
                    self._storage_client = StorageManagementClient(self._service_credentials,
                                                                   self._subscription_id,
                                                                   base_url=self.azure_stack_metadata.endpoints.resource_manager if self.is_azure_stack else None)

        return self._storage_client

    @property
    def resource_client(self):
        if self._resource_client is None:
            with SingletonByArgsMeta.lock:
                if self._resource_client is None:
                    self._resource_client = ResourceManagementClient(self._service_credentials,
                                                                     self._subscription_id,
                                                                     base_url=self.azure_stack_metadata.endpoints.resource_manager if self.is_azure_stack else None)

        return self._resource_client

    @property
    def subscription_client(self):
        if self._subscription_client is None:
            with SingletonByArgsMeta.lock:
                if self._subscription_client is None:
                    self._subscription_client = SubscriptionClient(self._service_credentials,
                                                                   base_url=self.azure_stack_metadata.endpoints.resource_manager if self.is_azure_stack else None)

        return self._subscription_client
