import ckanext.lodstatsext.model.store as store
import datetime
import dateutil.parser


class SubscriptionTime(EntityTime):
    def __init__(self):
        query = model.Session.query(model.Subscription)
        #query = query.filter(model.Subscription.owner_id == self.user.id)
        subscriptions = query.all()

        for subscription in subscriptions:
            extract_subscription_time(subscription)


    def extract_subscription_time(subscription):
        subscription_time = None
        if subscription.definition_type == 'semantic':
            subscription_time = extract_semantic_subscription_time(subscription)
        elif subscription.definition_type == 'sparql':
            subscription_time = extract_sparql_subscription_time(subscription)
        
        if subscription_time is not None:
            self.entities[subscription.id] = subscription_time


    def extract_semantic_subscription_time(subscription):
        subscription.parse_definition()
        time = subscription.definition['time']
        
        if time['type'] == 'span':
            return {'minTime': dateutil.parser.parse(time['min']), 'maxTime': dateutil.parser.parse(time['max'])}
        elif time['type'] == 'point':
            point = dateutil.parser.parse(semantic['time']['point'])
            variance = datetime.timedelta(days=int(semantic['time']['variance']))
            min_ = point - variance
            max_ = point + variance
            return {'minTime': min_, 'maxTime': max_}

        return None


    def extract_sparql_subscription_time(subscription):
        #TODO: find a way to extract time from a SPARQL query
        return None

