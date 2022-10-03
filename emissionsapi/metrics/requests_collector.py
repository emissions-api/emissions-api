from prometheus_client.core import CounterMetricFamily
from prometheus_client.registry import REGISTRY

import emissionsapi.db


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
        with emissionsapi.db.get_session() as session:
            for counter in session.query(emissionsapi.db.Counter).all():
                counters.add_metric([counter.function], counter.counter)

        yield counters
