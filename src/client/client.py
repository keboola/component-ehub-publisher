from keboola.http_client import HttpClient
from requests.exceptions import HTTPError

BASE_URL = "https://api.ehub.cz/v3/"

PUBLISHER_ENDPOINT = "publishers"

CAMPAIGN_LIST_ENDPOINT = "campaigns"
VOUCHER_LIST_ENDPOINT = "vouchers"
CREATIVE_LIST_ENDPOINT = "creatives"
TRANSACTION_LIST_ENDPOINT = "transactions"

DEFAULT_PAGE_SIZE = 50


class EHubClientException(Exception):
    pass


class EHubClient(HttpClient):
    def __init__(self, token):
        self.token = token
        super().__init__(BASE_URL)

    def get_single_publisher_campaign(self, publisher_id):
        parameters = {"apiKey": self.token, "perPage": 1, "page": 1}
        return self._get_endpoint(f"{PUBLISHER_ENDPOINT}/{publisher_id}/{CAMPAIGN_LIST_ENDPOINT}", parameters)

    def get_publisher_vouchers(self, publisher_id):
        return self._get_publisher_data(publisher_id, VOUCHER_LIST_ENDPOINT, "vouchers")

    def get_publisher_transactions(self, publisher_id):
        return self._get_publisher_data(publisher_id, TRANSACTION_LIST_ENDPOINT, "transactions")

    def get_publisher_creatives(self, publisher_id):
        return self._get_publisher_data(publisher_id, CREATIVE_LIST_ENDPOINT, "creatives")

    def get_publisher_campaigns(self, publisher_id):
        return self._get_publisher_data(publisher_id, CAMPAIGN_LIST_ENDPOINT, "campaigns")

    def _get_publisher_data(self, publisher_id, endpoint, object_name):
        endpoint_path = f"{PUBLISHER_ENDPOINT}/{publisher_id}/{endpoint}"
        # IMPORTANT PAGINATION STARTS AT 1 (for some reason)
        parameters = {"apiKey": self.token, "perPage": DEFAULT_PAGE_SIZE, "page": 1}
        return self._paginate_endpoint(endpoint_path, parameters, object_name)

    def _paginate_endpoint(self, endpoint, parameters, data_object):
        has_more = True
        while has_more:
            response = self._get_endpoint(endpoint, parameters)
            yield response.get(data_object)
            if response.get("totalItems") <= parameters.get("page") * 50:
                has_more = False
            parameters["page"] += 1

    def _get_endpoint(self, endpoint, parameters):
        try:
            return self.get(endpoint_path=endpoint, params=parameters)
        except HTTPError as http_err:
            raise EHubClientException(http_err) from http_err
