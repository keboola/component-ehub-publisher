import copy
import logging
import contextlib
import dateparser
import warnings
import sys
from functools import wraps
import json

from typing import Callable, List, Dict

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException
from keboola.csvwriter import ElasticDictWriter
from keboola.utils.helpers import comma_separated_values_to_list

from client import EHubClient, EHubClientException
from json_parser_multi import MulitCsvJsonParser

KEY_API_TOKEN = '#api_token'
KEY_PUBLISHER_IDS = "publisher_ids"

KEY_FETCH_CAMPAIGNS = "fetch_campaigns"
KEY_FETCH_VOUCHERS = "fetch_vouchers"
KEY_FETCH_CREATIVES = "fetch_creatives"
KEY_FETCH_TRANSACTIONS = "fetch_transactions"

KEY_TRANSACTION_OPTIONS = "transaction_options"
KEY_TRANSACTION_OPTIONS_FETCH_MODE = "fetch_mode"
KEY_TRANSACTION_OPTIONS_DATE_FROM = "date_from"
KEY_TRANSACTION_OPTIONS_DATE_TO = "date_to"

KEY_DESTINATION = "destination_settings"
KEY_LOAD_MODE = "load_mode"

REQUIRED_PARAMETERS = [KEY_API_TOKEN, KEY_PUBLISHER_IDS]
REQUIRED_IMAGE_PARS = []

DEFAULT_LOAD_MODE = "incremental_load"
DEFAULT_DATE_FROM = "1 week ago"
DEFAULT_DATE_TO = "now"

_SYNC_ACTIONS = dict()

# Ignore dateparser warnings regarding pytz
warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)


def sync_action(action_name: str):
    def decorate(func):
        # to allow pythonic names / action name mapping
        _SYNC_ACTIONS[action_name] = func.__name__

        @wraps(func)
        def action_wrapper(self, *args, **kwargs):
            # override when run as sync action, because it could be also called normally within run
            is_sync_action = self.configuration.action != 'run'

            # do operations with func
            if is_sync_action:
                stdout_redirect = None
                # mute logging just in case
                logging.getLogger().setLevel(logging.FATAL)
            else:
                stdout_redirect = sys.stdout
            try:
                # when success, only specified message can be on output, so redirect stdout before.
                with contextlib.redirect_stdout(stdout_redirect):
                    result = func(self, *args, **kwargs)

                if is_sync_action:
                    # sync action expects valid JSON in stdout on success.
                    if result:
                        # expect array or object:
                        sys.stdout.write(json.dumps(result))
                    else:
                        sys.stdout.write(json.dumps({'status': 'success'}))

                return result

            except Exception as e:
                if is_sync_action:
                    # sync actions expect stderr
                    sys.stderr.write(str(e))
                    exit(1)
                else:
                    raise e

        return action_wrapper

    return decorate


class Component(ComponentBase):

    def __init__(self):
        self.client = None
        self.result_writers = {}
        self.incremental = None
        self.publisher_ids = None
        super().__init__()

    def run(self):
        self.validate_configuration_parameters(REQUIRED_PARAMETERS)
        self.validate_image_parameters(REQUIRED_IMAGE_PARS)
        params = self.configuration.parameters

        self.init_client()
        self.init_publisher_ids()

        destination_settings = params.get(KEY_DESTINATION, {})
        load_mode = destination_settings.get(KEY_LOAD_MODE, DEFAULT_LOAD_MODE)
        self.incremental = load_mode != "full_load"

        if not self.publisher_ids:
            raise UserException("No publisher IDs set")

        if params.get(KEY_FETCH_CAMPAIGNS):
            logging.info("Fetching publisher campaign data")
            self.fetch_and_save_campaigns()
        if params.get(KEY_FETCH_VOUCHERS):
            logging.info("Fetching publisher voucher  data")
            self.fetch_and_save_vouchers()
        if params.get(KEY_FETCH_CREATIVES):
            logging.info("Fetching publisher creative data")
            self.fetch_and_save_creatives()
        if params.get(KEY_FETCH_TRANSACTIONS):
            logging.info("Fetching publisher transaction data")
            self.fetch_and_save_transactions()

        self._close_all_result_writers()

    def init_client(self):
        params = self.configuration.parameters
        api_key = params.get(KEY_API_TOKEN)
        self.client = EHubClient(api_key)

    def init_publisher_ids(self):
        params = self.configuration.parameters
        self.publisher_ids = comma_separated_values_to_list(params.get(KEY_PUBLISHER_IDS))

    @sync_action('testConnection')
    def test_connection(self):
        self.init_client()
        self.init_publisher_ids()

        failed_publishers = []
        for publisher_id in self.publisher_ids:
            try:
                self.client.get_single_publisher_campaign(publisher_id)
            except EHubClientException:
                failed_publishers.append(publisher_id)
        if failed_publishers:
            raise UserException(
                f"Failed to authorize the connection with the following Publisher IDs {failed_publishers}. "
                f"Either API Key is Invalid, or the Publisher ID")
        if not self.publisher_ids:
            raise UserException("Cannot test connection without any publisher IDs")

    def fetch_and_save_campaigns(self) -> None:
        self._initialize_result_writer("campaign")
        self._initialize_result_writer("campaign_categories")
        self._initialize_result_writer("campaign_commission_groups")
        self._initialize_result_writer("campaign_restrictions")
        parser = MulitCsvJsonParser(dont_parse_list=['commissions'])
        for publisher_id in self.publisher_ids:
            try:
                for page in self.client.get_publisher_campaigns(publisher_id):
                    parsed = parser.parse_data(page, "campaign")
                    for table in parsed:
                        parsed[table] = self._add_key_value_to_data(parsed[table], "publisherId", publisher_id)
                    self._get_result_writer("campaign").writerows(parsed["campaign"])
                    self._get_result_writer("campaign_categories").writerows(parsed["categories"])
                    self._get_result_writer("campaign_commission_groups").writerows(parsed["commissionGroups"])
                    self._get_result_writer("campaign_restrictions").writerows(parsed["restrictions"])
            except EHubClientException as ehub_exc:
                raise UserException(
                    "Fetching data from eHUB failed, check your API Key and Publisher IDs") from ehub_exc

    def fetch_and_save_vouchers(self) -> None:
        try:
            self._fetch_and_save_data_for_all_publishers("voucher", self.client.get_publisher_vouchers)
        except EHubClientException as ehub_exc:
            raise UserException("Fetching data from eHUB failed, check your API Key and Publisher IDs") from ehub_exc

    def fetch_and_save_creatives(self) -> None:
        try:
            self._fetch_and_save_data_for_all_publishers("creative", self.client.get_publisher_creatives)
        except EHubClientException as ehub_exc:
            raise UserException("Fetching data from eHUB failed, check your API Key and Publisher IDs") from ehub_exc

    def fetch_and_save_transactions(self) -> None:
        params = self.configuration.parameters
        transaction_options = params.get(KEY_TRANSACTION_OPTIONS)
        fetch_mode = transaction_options.get(KEY_TRANSACTION_OPTIONS_FETCH_MODE)

        if fetch_mode == "full_fetch":
            self._fetch_and_save_transactions_full()
        else:
            date_from = transaction_options.get(KEY_TRANSACTION_OPTIONS_DATE_FROM)
            date_to = transaction_options.get(KEY_TRANSACTION_OPTIONS_DATE_TO)
            self._fetch_and_save_transactions_incremental(date_from, date_to)

    def _fetch_and_save_transactions_full(self):
        try:
            self._fetch_and_save_data_for_all_publishers("transaction", self.client.get_publisher_transactions)
        except EHubClientException as ehub_exc:
            raise UserException("Fetching data from eHUB failed, check your API Key and Publisher IDs") from ehub_exc

    def _fetch_and_save_transactions_incremental(self, date_from: str = DEFAULT_DATE_FROM,
                                                 date_to: str = DEFAULT_DATE_TO):
        parsed_date_from = self._parse_date(date_from)
        parsed_date_to = self._parse_date(date_to)
        logging.info(
            f"Fetching transaction data incrementally based on the Insert Date ; "
            f"from {parsed_date_from} till {parsed_date_to}")
        try:
            self._fetch_and_save_data_for_all_publishers("transaction", self.client.get_publisher_transactions,
                                                         date_from=parsed_date_from, date_to=parsed_date_to)
        except EHubClientException as ehub_exc:
            raise UserException("Fetching data from eHUB failed, check your API Key and Publisher IDs") from ehub_exc

    def _fetch_and_save_data_for_all_publishers(self, object_name: str, fetcher_function: Callable, **kwargs) -> None:
        self._initialize_result_writer(object_name)
        for publisher_id in self.publisher_ids:
            self._fetch_and_save_data(object_name, fetcher_function, publisher_id, **kwargs)

    def _fetch_and_save_data(self, object_name: str, fetcher_function: Callable, publisher_id: str, **kwargs) -> None:
        for page in fetcher_function(publisher_id, **kwargs):
            page = self._add_key_value_to_data(page, "publisherId", publisher_id)
            self._get_result_writer(object_name).writerows(page)

    @staticmethod
    def _add_key_value_to_data(data: List[Dict], key: str, value: str) -> List[Dict]:
        for i, row in enumerate(data):
            data[i][key] = value
        return data

    def _initialize_result_writer(self, object_name: str) -> None:
        if object_name not in self.result_writers:
            table_schema = self.get_table_schema_by_name(object_name)
            table_definition = self.create_out_table_definition_from_schema(table_schema, incremental=self.incremental)
            writer = ElasticDictWriter(table_definition.full_path, table_definition.columns)
            self.result_writers[object_name] = {"table_definition": table_definition, "writer": writer}

    def _get_result_writer(self, object_name: str) -> ElasticDictWriter:
        return self.result_writers.get(object_name).get("writer")

    def _close_all_result_writers(self) -> None:
        for writer_name in self.result_writers:
            self._close_result_writer(writer_name)

    def _close_result_writer(self, writer_name: str) -> None:
        writer = self._get_result_writer(writer_name)
        table_definition = self.result_writers.get(writer_name).get("table_definition")
        writer.close()
        table_definition.columns = copy.deepcopy(writer.fieldnames)
        self.write_manifest(table_definition)

    @staticmethod
    def _parse_date(date_to_parse: str) -> str:
        try:
            parsed = dateparser.parse(date_to_parse)
            return parsed.strftime("%Y-%m-%dT%H:%M:%S.%f")
        except (AttributeError, TypeError) as err:
            raise UserException(f"Failed to parse date {date_to_parse}, make sure the date is either in YYYY-MM-DD "
                                f"format or relative date i.e. 5 days ago, 1 month ago, yesterday, etc.") from err

    # overriden base
    def execute_action(self):
        """
        Executes action defined in the configuration.
        The default action is 'run'.
        """
        action = self.configuration.action
        if not action:
            logging.warning("No action defined in the configuration, using the default run action.")
            action = 'run'

        try:
            # apply action mapping
            if action != 'run':
                action = _SYNC_ACTIONS[action]

            action_method = getattr(self, action)
        except (AttributeError, KeyError) as e:
            raise AttributeError(f"The defined action {action} is not implemented!") from e
        return action_method()


"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
