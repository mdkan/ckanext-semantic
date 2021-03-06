from . import EntityTime
from . import SubscriptionExtractor
import ckan.model as model
import ckanext.semantic.lib.helpers as h
import ckanext.semantic.lib.time as ht
import datetime
import dateutil.parser


class SubscriptionTime(EntityTime, SubscriptionExtractor):
    def __init__(self):
        super(SubscriptionTime, self).__init__()


    def _extract(self):
        query = model.Session.query(model.Subscription)
        subscriptions = query.all()
        self.entities = {}
        
        for subscription in subscriptions:
            self.extract_subscription_time(subscription)
            
        self._extracted = True


    def extract_subscription_time(self, subscription):
        time = None
        type_ = subscription.definition['type']
        if type_ == 'search':
            time = self.extract_search_subscription_time(subscription)
        elif type_ == 'sparql':
            time = self.extract_sparql_subscription_time(subscription)
        
        if time is not None:
            key = h.subscription_to_uri(h.user_id_to_object(subscription.owner_id).name, subscription.name)
            self.entities[key] = time


    def extract_search_subscription_time(self, subscription):
        filters = subscription.definition['filters']
        if 'time_min' in filters and 'time_max' in filters:
            return {'min_time': ht.to_naive_utc(ht.min_datetime(filters['time_min'][0])),
                    'max_time': ht.to_naive_utc(ht.max_datetime(filters['time_max'][0]))}


        return None


    def extract_sparql_subscription_time(self, subscription):
        #TODO: find a way to extract time from a SPARQL query
        return None

