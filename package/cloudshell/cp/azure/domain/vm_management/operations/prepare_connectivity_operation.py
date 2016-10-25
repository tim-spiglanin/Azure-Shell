from platform import machine

from cloudshell.cp.azure.common.operations_helper import OperationsHelper
from cloudshell.cp.azure.domain.services.tags import TagNames
from cloudshell.cp.azure.models.prepare_connectivity_action_result import PrepareConnectivityActionResult

INVALID_REQUEST_ERROR = 'Invalid request: {0}'


class PrepareConnectivityOperation(object):
    def __init__(self,
                 logger,
                 vm_service,
                 network_service,
                 storage_service,
                 tags_service,
                 key_pair_service):
        """

        :param logger:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.key_pair.KeyPairService key_pair_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service
        self.key_pair_service = key_pair_service

    def prepare_connectivity(self,
                             reservation,
                             cloud_provider_model,
                             storage_client,
                             resource_client,
                             network_client,
                             logger,
                             request):
        """

        :param logging.Logger logger:
        :param request:
        :param network_client:
        :param storage_client:
        :param resource_client:
        :param cloudshell.cp.azure.models.reservation_model.ReservationModel reservation:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :return:
        """

        resource_name = OperationsHelper.generate_name("base")
        reservation_id = reservation.reservation_id
        group_name = str(reservation_id)
        vnet = cloud_provider_model.azure_mgmt_vnet
        tags = self.tags_service.get_tags(reservation=reservation)
        result = []
        action_result = PrepareConnectivityActionResult()

        for action in request.actions:
            cidr = self._extract_cidr(action)
            logger.info("Received CIDR {0} from server".format(cidr))
            # 1. Create a resource group
            self.vm_service.create_resource_group(resource_management_client=resource_client, group_name=group_name,
                                                  region=cloud_provider_model.region, tags=tags)

            storage_account_name = OperationsHelper.generate_name(reservation_id[0:8])
            # 2. Create a storage account
            action_result.storage_name = self.storage_service.create_storage_account(storage_client=storage_client,
                                                                                     group_name=group_name,
                                                                                     region=cloud_provider_model.region,
                                                                                     storage_account_name=storage_account_name,
                                                                                     tags=tags)
            # 3 Create a Key pair for the sandbox
            key_pair = self.key_pair_service.generate_key_pair()

            account_key = self.storage_service.get_storage_account_key(storage_client=storage_client,
                                                                       group_name=group_name,
                                                                       storage_name=storage_account_name)
            self.key_pair_service.save_key_pair(account_key=account_key,
                                                key_pair=key_pair,
                                                group_name=group_name,
                                                storage_name=storage_account_name)

            # 4. Create the network interface
            # todo: change that to create a subnet
            action_result.subnet_name = self.network_service.create_virtual_network(management_group_name=group_name,
                                                                                    network_client=network_client,
                                                                                    network_name=resource_name,
                                                                                    region=cloud_provider_model.region,
                                                                                    subnet_name=resource_name,
                                                                                    tags=tags,
                                                                                    subnet_cidr=cidr,
                                                                                    vnet_cidr=vnet).name

            # 5.Create the NSG object
            # todo: crete the subnet


            result.append(action_result)
        return result

    @staticmethod
    def _extract_cidr(action):
        cidrs = [custom_attribute.attributeValue
                 for custom_attribute in action.customActionAttributes
                 if custom_attribute.attributeName == 'Network']
        if not cidrs:
            raise ValueError(INVALID_REQUEST_ERROR.format('CIDR is missing'))
        if len(cidrs) > 1:
            raise ValueError(INVALID_REQUEST_ERROR.format('Too many CIDRs parameters were found'))
        return cidrs[0]
