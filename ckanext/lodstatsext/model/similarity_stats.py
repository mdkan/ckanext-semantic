import ckanext.lodstatsext.model.prefix as prefix
import ckanext.lodstatsext.model.triplestore as triplestore
import datetime
import RDF


class SimilarityStats:
    graph = 'http://lodstats.org/similarities'
    
    @classmethod
    def update_similarities(cls, similarity_uri_string, element_uri_string, element_class_uri_string):
        if similarity_uri_string == 'http://lodstats.org/similarity#topic' and \
           element_class_uri_string == 'http://rdfs.org/ns/void#Dataset':
            result = triplestore.ts.query('''
                                       prefix xs: <http://www.w3.org/2001/XMLSchema#>
                                       prefix vstats: <http://lodstats.org/vocabulary#>
                                       prefix void: <http://rdfs.org/ns/void#>
                                       
                                       select ?dataset2 (sum(xs:decimal(?specificity)) as ?similarity)
                                       where
                                       {
                                           <''' + element_uri_string + '''> void:vocabulary ?vocabulary1.
                                           ?dataset2 void:vocabulary ?vocabulary2.
                                           
                                           ?vocabulary1 vstats:cosSpecificity ?specificity.
                                           filter(?vocabulary1=?vocabulary2)
                                       }
                                       group by ?dataset2
                                       order by desc(?similarity)
                                       ''')       

            similarity_stats = SimilarityStats(element_uri_string)
                                                      
            for row in result['results']['bindings']:
                similarity_stats.append(element_uri_string, row['dataset2']['value'], row['similarity']['value'], similarity_uri_string)
            
            similarity_stats.commit()
            
        elif similarity_uri_string == 'http://lodstats.org/similarity#vocabulary':
            pass
        elif similarity_uri_string == 'http://lodstats.org/similarity#location':
            pass
        elif similarity_uri_string == 'http://lodstats.org/similarity#time':
            pass
            
            
    @classmethod
    def get_and_cache_similarities(cls, similarity_uri_string, element_uri_string, similar_element_class_uri_string, count_limit):
        count1 = int(triplestore.ts.query('''
                                        prefix sim: <http://purl.org/ontology/similarity/>
                                        select (count(distinct ?element1) as ?count)
                                        where
                                        {
                                            ?similarity a sim:Similarity.
                                            ?similarity sim:method <''' + similarity_uri_string + '''>.
                                            ?similarity sim:element ?element1.
                                            ?similarity sim:element ?element2.
                                            ?element1 a <''' + similar_element_class_uri_string + '''>.
                                            filter(?element2=<''' + element_uri_string + '''> and ?element1!=?element2)
                                        }
                                        ''')['results']['bindings'][0]['count']['value'])
        count2 = int(triplestore.ts.query('''
                                        prefix sim: <http://purl.org/ontology/similarity/>
                                        select (count(distinct ?element) as ?count)
                                        where
                                        {
                                            ?element a <''' + similar_element_class_uri_string + '''>.
                                        }
                                        ''')['results']['bindings'][0]['count']['value'])
                                        
                                        
        if float(count1) / float(count2) < 0.4:
            SimilarityStats.update_similarities(similarity_uri_string, element_uri_string, 'http://rdfs.org/ns/void#Dataset')
            
        return SimilarityStats.get_similaries(similarity_uri_string, element_uri_string, similar_element_class_uri_string, count_limit)


    @classmethod
    def get_similaries(cls, similarity_uri_string, element_uri_string, similar_element_class_uri_string, count_limit):
        result = triplestore.ts.query('''
                                    prefix sim: <http://purl.org/ontology/similarity/>
                                    select distinct ?element1 ?similarity_weight
                                    where
                                    {
                                        ?similarity a sim:Similarity.
                                        ?similarity sim:method <''' + similarity_uri_string + '''>.
                                        ?similarity sim:element ?element1.
                                        ?similarity sim:element ?element2.
                                        ?similarity sim:weight ?similarity_weight.
                                        ?element1 a <''' + similar_element_class_uri_string + '''>.
                                        filter(?element2=<''' + element_uri_string + '''> and ?element1!=?element2)
                                    }
                                    order by desc(?similarity_weight)
                                    limit ''' + str(count_limit) + '''
                                    ''')
        #owl:Thing problem to determine class of element1
        
        return [(row['element1']['value'], row['similarity_weight']['value']) for row in result['results']['bindings']]


    def __init__(self, element):
        self.element = element
        self.rdf = RDF.Model()
        
        
    def append(self, element1_uri_string, element2_uri_string, weight, method_uri_string):
        similarity_node = RDF.Node()
        self.rdf.append(RDF.Statement(similarity_node, prefix.rdf.type, prefix.sim.Similarity))
        self.rdf.append(RDF.Statement(similarity_node, prefix.sim.element, RDF.Uri(element1_uri_string)))
        self.rdf.append(RDF.Statement(similarity_node, prefix.sim.element, RDF.Uri(element2_uri_string)))
        self.rdf.append(RDF.Statement(similarity_node, prefix.sim.weight, str(weight)))
        self.rdf.append(RDF.Statement(similarity_node, prefix.sim.method, RDF.Uri(method_uri_string)))
        self.rdf.append(RDF.Statement(similarity_node, prefix.dct.created, RDF.Node(literal=datetime.datetime.now().isoformat(), datatype=prefix.xs.dateTime.uri)))
        

    def commit(self):
        serializer = RDF.Serializer(name="ntriples")
        triples = serializer.serialize_model_to_string(self.rdf)
        triplestore.ts.modify('''
                           delete from graph <''' + SimilarityStats.graph + '''>
                           {
                               ?similarity ?predicate ?object.
                           }
                           where
                           {
                               ?similarity a <http://purl.org/ontology/similarity/Similarity>.
                               ?similarity <http://purl.org/ontology/similarity/element> <''' + self.element + '''>.
                               ?similarity ?predicate ?object.
                           }
                           
                           insert in graph <''' + SimilarityStats.graph + '''>
                           {
                           ''' + triples + '''
                           }
                           ''')
                           
    def load(self):
        pass        

    def clear_rdf(self):
        self.rdf = RDF.Model()

