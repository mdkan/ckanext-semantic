import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import ckanext.semantic.lib.helpers as h
import ckanext.semantic.model.prefix as prefix
import ckanext.semantic.model.similarity.methods as similarity_methods
import ckanext.semantic.model.recommendation as r
import datetime
import lodstats.stats as stats
import logging
import RDF


log = logging.getLogger(__name__)


class RecommendationController(base.BaseController):
    def read(self, type_=None):
        context = {'model': model,
                   'session': model.Session,
                   'user': base.c.user or base.c.author}
        data_dict = {'id': base.c.user,
                     'user_obj': base.c.userobj}

        try:
            user_dict = logic.get_action('user_show')(context, data_dict)
        except NotFound:
            base.h.redirect_to(controller='user', action='login', id=None)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))
        base.c.user_dict = user_dict
        base.c.is_myself = user_dict['name'] == base.c.user
        

        recommendation = r.Recommendation(base.c.userobj)
        recommendation.set_recommended_entity_class(str(prefix.void.Dataset.uri))


        dataset_interests = set()
        subscription_query = model.Session.query(model.Subscription).filter(model.Subscription.owner_id==base.c.user_dict['id'])
        for subscription in subscription_query.all():
            dataset_list = logic.get_action('subscription_dataset_list')(context, {'subscription_id': subscription.id})
            for dataset in dataset_list:
                dataset_interests.add(h.dataset_to_uri(dataset['name']))
        recommendation.set_additional_interests(dataset_interests)

         
        if type_ == None:
           types = ['topic', 'location', 'time']
           recommendation.set_count_limit(2)
        else:
            types = [type_]
            recommendation.set_count_limit(10)
        

        base.c.recommendation = {}
        for type_ in types:
            recommendation.set_type(type_)
            recommendation.load()
            for dataset, reasons in recommendation.entities.iteritems():
                dataset_dict = model_dictize.package_dictize(dataset, context)
                dataset_dict['dataset_reasons'] = [reason for reason in reasons if reason.class_uri == str(prefix.void.Dataset)]
                dataset_dict['dataset_reasons_count'] = len(dataset_dict['dataset_reasons'])
                dataset_dict['subscription_reasons'] = [reason for reason in reasons if reason.class_uri == str(prefix.ckan.Subscription)]
                dataset_dict['subscription_reasons_count'] = len(dataset_dict['subscription_reasons'])
                dataset_dict['multiple_reasons'] = dataset_dict['dataset_reasons_count'] + dataset_dict['subscription_reasons_count'] > 1

                if base.c.recommendation.has_key(type_):
                    base.c.recommendation[type_].append(dataset_dict)
                else:
                    base.c.recommendation[type_] = [dataset_dict]

        return base.render('recommendation.html')

