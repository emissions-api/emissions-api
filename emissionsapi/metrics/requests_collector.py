from prometheus_client.core import CounterMetricFamily
from prometheus_client.registry import REGISTRY

from emissionsapi.db import get_session, Metrics


class RequestsCollector(object):
    '''Collector for number of requests made to different functions.
    '''

    def __init__(self, registry=REGISTRY):
        registry.register(self)

    def collect(self):
        '''Collect the current number of requests made against different
        methods of the Emissions API.
        '''
        # Create counter metric
        counters = CounterMetricFamily(
                'requests_count',
                'Counted number of requests',
                labels=['method'])

        # Get requests count from database
        with get_session() as session:
            metrics = session\
                    .query(Metrics)\
                    .filter(Metrics.metric == 'request_count')\
                    .all()
            for metric in metrics:
                counters.add_metric([metric.label], metric.value)

        yield counters
