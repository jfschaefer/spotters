from spotterbase.corpora.arxiv import ArxivCategory
from spotterbase.model_core.sb import SB
from spotterbase.rdf.vocab import OA, RDF
from spotterbase.sparql.endpoint import Virtuoso
from spotterbase.utils import config_loader

config_loader.auto()
endpoint = Virtuoso()

for row in endpoint.query(f'''
{OA.NS:sparql}
{RDF.NS:sparql}
{SB.NS:sparql}
SELECT DISTINCT ?paper WHERE {{
  # make sure that ?paper is about category theory
  ?paper sb:isBasedOn/^oa:hasTarget/oa:hasBody/rdf:value {ArxivCategory('math.GR').as_uri():<>} .
  # find theorems in ?paper and look up their offsets
   ?theorem_anno oa:hasBody/rdf:value <http://sigmathling.kwarc.info/spotterbase/para-class#Theorem> .
   ?theorem_anno oa:hasTarget [
     oa:hasSource ?paper ;
     oa:hasSelector [ a sb:OffsetSelector ; oa:start ?t_start ; oa:end ?t_end ; ]
   ] .
   # Same with mentions of rational numbers (offsets ?q_start, ?q_end)
   ?q_anno oa:hasBody/rdf:value <http://www.wikidata.org/entity/Q1244890> .
   ?q_anno oa:hasTarget [
     oa:hasSource ?paper  ;
     oa:hasSelector [ a sb:OffsetSelector ; oa:start ?q_start ; oa:end ?q_end ; ]
   ] .
   #  # make sure that mention is inside theorem
   FILTER (?t_start < ?q_start && ?t_end > ?q_end)
}} LIMIT 100
'''):
    print(row)
