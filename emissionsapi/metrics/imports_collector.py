from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import REGISTRY

from emissionsapi.db import get_session, Metrics


class ImportsCollector(object):
    '''Collector for statistics related to data imports.
    '''

    def __init__(self, registry=REGISTRY):
        registry.register(self)

    def collect(self):
        '''Collect the current number of active imports.
        '''
        # Create counter metric
        imports = GaugeMetricFamily(
                'active_imports',
                'Number of active imports',
                labels=['product'])

        # Get number of active imports from database
        with get_session() as session:
            metrics = session\
                    .query(Metrics)\
                    .filter(Metrics.metric == 'active_imports')\
                    .all()
            for metric in metrics:
                imports.add_metric([metric.label], metric.value)

        yield imports
