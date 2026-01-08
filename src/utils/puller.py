from dataclasses import dataclass
from typing import Any, Optional, Literal

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from src.utils.logger import get_logger
from src.utils.errors import (
    BorderAPIError,
    DataNotFoundError,
    InvalidTransportTypeError,
)


logger = get_logger(__name__)


@dataclass
class BorderConfig:
    domain: str = "https://belarusborder.by"
    monitoring_endpoint: str = "/info/monitoring-new"
    stat_endpoint: str = "/info/monitoring/statistics"
    token: str = "test"
    timeout: int = 10
    max_retries: int = 3


class DataPuller:

    def __init__(self, checkpoint_id: str):
        self.checkpoint_id = checkpoint_id
        self.config = BorderConfig()
        self.data: dict[str, Any] = {}
        self._session = self._create_session()

    def _create_session(self):
        session = requests.Session()

        retry = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods="GET",
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        return session

    def _pull(self, endpoint: str) -> Optional[dict[str, Any]]:
        url = f"{self.config.domain}{endpoint}"
        params = {
            "checkpointId": self.checkpoint_id,
            "token": self.config.token,
        }

        try:
            logger.info(f"Fetching data from {endpoint}")
            response = self._session.get(
                url=url,
                params=params,
                timeout=self.config.timeout,
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched data from {endpoint}")
            return data

        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching {endpoint}")
            raise BorderAPIError(f"Request timeout for {endpoint}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {endpoint}")
            raise BorderAPIError(f"HTTP {e.response.status_code} error for {endpoint}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise BorderAPIError(f"Failed to fetch {endpoint}: {str(e)}")

        except ValueError:
            logger.error(f"Invalid JSON response from {endpoint}")
            raise BorderAPIError(f"Invalid JSON from {endpoint}")

    def fetch_data(self) -> dict[str, Any]:
        self.data = {
            "monitoring": self._pull(self.config.monitoring_endpoint),
            "statistics": self._pull(self.config.stat_endpoint),
        }
        return self.data

    def fetch_monitoring(self) -> Optional[dict[str, Any]]:
        monitoring_data = self._pull(self.config.monitoring_endpoint)
        self.data["monitoring"] = monitoring_data
        return monitoring_data

    def fetch_statistics(self) -> Optional[dict[str, Any]]:
        stats_data = self._pull(self.config.stat_endpoint)
        self.data["statistics"] = stats_data
        return stats_data

    def close(self):
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DataFilter:

    TRANSPORT_TYPES = Literal["car", "bus"]
    TRANSPORT_KEYS = {"car": "carLiveQueue", "bus": "busLiveQueue"}

    def __init__(
        self, data: dict[str, Any], regnum: str, transport_type: TRANSPORT_TYPES
    ):
        if not regnum:
            raise ValueError("regnum cannot be empty")

        self.data = data
        self.transport_type = transport_type.lower()
        self.regnum = regnum.upper().strip()

        self._validate_transport_type()

    def _validate_transport_type(self):
        if self.transport_type not in self.TRANSPORT_KEYS:
            valid_types = ", ".join(self.TRANSPORT_KEYS.keys())
            raise InvalidTransportTypeError(self.transport_type, valid_types)

    def filter_by_regnum(self) -> Optional[dict[str, Any]]:
        monitoring_data = self.data.get("monitoring")

        if not monitoring_data:
            raise DataNotFoundError("No monitoring data available")

        queue_key = self.TRANSPORT_KEYS[self.transport_type]

        if queue_key not in monitoring_data:
            logger.warning(f"Queue key '{queue_key}' not found in monitoring data")
            raise DataNotFoundError(f"No {self.transport_type} queue data available")

        queue = monitoring_data[queue_key]

        if not isinstance(queue, list):
            raise DataNotFoundError(
                f"Invalid queue data format for {self.transport_type}"
            )

        for vehicle in queue:
            if vehicle.get("regnum") == self.regnum:
                logger.info(
                    f"Found vehicle {self.regnum} in {self.transport_type} queue"
                )
                return vehicle

        logger.info(f"Vehicle {self.regnum} not found in queue")
        return None


# def main():
#     try:
#         with DataPuller('a9173a85-3fc0-424c-84f0-defa632481e4') as puller:
#             puller.fetch_data()
#
#             data_filter = DataFilter(
#                 data=puller.data,
#                 regnum='6710MB1',
#                 transport_type='car'
#             )
#
#             vehicle_data = data_filter.filter_by_regnum()
#
#             if vehicle_data:
#                 print(f"Vehicle found: {vehicle_data}")
#             else:
#                 print("Vehicle not found in queue")
#
#     except BorderAPIError as e:
#         logger.error(f"API error: {e}")
#     except (InvalidTransportTypeError, DataNotFoundError) as e:
#         logger.error(f"Data error: {e}")
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}", exc_info=True)
#
#
# if __name__ == '__main__':
#     main()
