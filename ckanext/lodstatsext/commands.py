import ckan.lib.cli as cli
import ckan.model as model
import ckanext.lodstatsext.lib.helpers as h
import ckanext.lodstatsext.lib.personalization as personalization
import ckanext.lodstatsext.model.dataset_stats as mds
import ckanext.lodstatsext.model.vocabulary_stats as mvs
import ckanext.lodstatsext.model.similarity_stats as mvs
import ckanext.lodstatsext.model.triplestore as triplestore
import ckanext.lodstatsext.model.prefix as prefix
import datetime
import logging
import RDF
import sqlalchemy


log = logging.getLogger(__name__)


class LODStatsExtCommand(cli.CkanCommand):
    '''
    CKAN Example Extension

    Usage:
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__


    def command(self):
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print ExampleCommand.__doc__
            return
            

        self._load_config()
        getattr(self, self.args[0])(*(self.args[1:]))


    def test(self):
        pass
        
        
    def update_dataset_stats(self, dataset_uri=None):
        mds.DatasetStats.update(dataset_uri)


    def update_vocabulary_stats(self):
        mvs.VocabularyStats.update()
        
    
    def update_similarity_stats(self,
                                similarity_type,
                                element_uri,
                                element_type='dataset',
                                similar_element_type='dataset'):
        element_class = {'dataset': 'http://rdfs.org/ns/void#Dataset',
                         'user': 'http://xmlns.com/foaf/0.1/Person'}[element_type]
        similar_element_class = {'dataset': 'http://rdfs.org/ns/void#Dataset',
                                 'user': 'http://xmlns.com/foaf/0.1/Person'}[similar_element_type]
        similarities = mvs.SimilarityStats(mvs.SimilarityStats.type[similarity_type],
                                           element_class,
                                           element_uri,
                                           similar_element_class)
        similarities.update_and_commit()


    def load_similarity_stats(self,
                              similarity_type,
                              element_uri,
                              element_type='dataset',
                              similar_element_type='dataset'):
        element_class = {'dataset': 'http://rdfs.org/ns/void#Dataset',
                         'user': 'http://xmlns.com/foaf/0.1/Person'}[element_type]
        similar_element_class = {'dataset': 'http://rdfs.org/ns/void#Dataset',
                                 'user': 'http://xmlns.com/foaf/0.1/Person'}[similar_element_type]
        similarities = mvs.SimilarityStats(mvs.SimilarityStats.type[similarity_type],
                                           element_class,
                                           element_uri,
                                           similar_element_class) 
        similarities.load(5)
        for row in similarities.rows:
            print row



    def load_similarity_stats_from_store_only(self,
                                              similarity_type,
                                              element_uri,
                                              element_type='dataset',
                                              similar_element_type='dataset'):
        element_class = {'dataset': 'http://rdfs.org/ns/void#Dataset',
                         'user': 'http://xmlns.com/foaf/0.1/Person'}[element_type]
        similar_element_class = {'dataset': 'http://rdfs.org/ns/void#Dataset',
                                 'user': 'http://xmlns.com/foaf/0.1/Person'}[similar_element_type]
        similarities = mvs.SimilarityStats(mvs.SimilarityStats.type[similarity_type],
                                           element_class,
                                           element_uri,
                                           similar_element_class) 
        similarities.load(5, from_store_only=True)
        for row in similarities.rows:
            print row
            
    
    def get_datasets_matching_user_interest(self):
        for row in personalization.get_datasets_similar_to_user_interest(
                                                        h.user_to_uri('meier'),
                                                        'http://lodstats.org/similarity#topic'):
            print row


    def push_datasets_to_triplestore(self):
        serializer = RDF.Serializer(name='ntriples')
        rdf_model = RDF.Model()
        for dataset in model.Session.query(model.Package).all():
            dataset.rdf_uri = RDF.Uri(h.dataset_to_uri(dataset.name))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.owl.sameAs, RDF.Uri('urn:uuid:' + dataset.id)))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.rdf.type, prefix.dcat.Dataset))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.rdfs.label, dataset.name))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.dct.identifier, dataset.name))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.dct.title, dataset.title))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.dct.description, dataset.notes))
            # + license, author, maintainer
        triples = serializer.serialize_model_to_string(rdf_model)
        triplestore.ts.modify('clear graph <http://ckan.org/datasets>')
        triplestore.ts.modify('''
                           insert into graph <http://ckan.org/datasets>
                           {
                           ''' + triples + '''
                           }
                           ''')


    def push_users_to_triplestore(self):
        serializer = RDF.Serializer(name='ntriples')
        rdf_model = RDF.Model()
        
        
        for user in model.Session.query(model.User).all():
            user.rdf_uri = RDF.Uri(h.user_to_uri(user.name))
            rdf_model.append(RDF.Statement(user.rdf_uri, prefix.owl.sameAs, RDF.Uri("urn:uuid:" + user.id)))
            rdf_model.append(RDF.Statement(user.rdf_uri, prefix.rdf.type, prefix.foaf.Person))
            
            for follow in model.Session.query(model.UserFollowingDataset).filter(model.UserFollowingDataset.follower_id == user.id).all():
                dataset = model.Session.query(model.Package).get(follow.object_id)
                dataset.rdf_uri = RDF.Uri(h.dataset_to_uri(dataset.name))
                rdf_model.append(RDF.Statement(user.rdf_uri, prefix.foaf.interest, dataset.rdf_uri))
            
            for follow in model.Session.query(model.UserFollowingUser).filter(model.UserFollowingUser.follower_id == user.id).all():
                followee = model.Session.query(model.User).get(follow.object_id)
                followee.rdf_uri = RDF.Uri(h.user_to_uri(followee.name))
                rdf_model.append(RDF.Statement(user.rdf_uri, prefix.foaf.interest, followee.rdf_uri))

        triples = serializer.serialize_model_to_string(rdf_model)
        triplestore.ts.modify('clear graph <http://ckan.org/users>')
        triplestore.ts.modify('''
                           insert into graph <http://ckan.org/users>
                           {
                           ''' + triples + '''
                           }
                           ''')

    def push_lodstats_datasets_to_triplestore(self):
        serializer = RDF.Serializer(name='ntriples')
        rdf_model = RDF.Model()
        for dataset in model.Session.query(model.Package).all():
            dataset.rdf_uri = RDF.Uri(h.dataset_to_uri(dataset.name))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.rdf.type, prefix.void.Dataset))
            rdf_model.append(RDF.Statement(dataset.rdf_uri, prefix.dstats.evaluated, 'false'))
        triples = serializer.serialize_model_to_string(rdf_model)
        triplestore.ts.modify('clear graph <http://lodstats.org/datasets>')
        triplestore.ts.modify('''
                               insert into graph <http://lodstats.org/datasets>
                               {
                               ''' + triples + '''
                               }
                               ''')

