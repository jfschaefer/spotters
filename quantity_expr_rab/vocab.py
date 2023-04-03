from typing import Optional

from spotterbase.rdf import Vocabulary, NameSpace, Uri
from spotterbase.rdf.vocab import XSD
from spotterbase.records.jsonld_support import JsonLdContext
from spotterbase.records.record import Record, PredInfo, RecordInfo, AttrInfo


class RAB(Vocabulary):
    NS: NameSpace = NameSpace(Uri('https://sigmathling.kwarc.info/resources/quantity-expressions/'), 'rab:')

    corpus: Uri

    quantBody: Uri

    hasScalar: Uri
    hasUnit: Uri


class RAB_PRED:
    # general-purpose
    hasScalar = PredInfo(RAB.hasScalar, json_ld_term='rab:hasScalar', literal_type=XSD.double)
    hasUnit = PredInfo(RAB.hasUnit, json_ld_term='rab:hasUnit', json_ld_type_is_id=True)


RAB_JSONLD_CONTEXT: JsonLdContext = JsonLdContext(
    uri=None,
    namespaces=[RAB.NS],
    pred_infos=list(p_info for p_info in RAB_PRED.__dict__.values() if isinstance(p_info, PredInfo)),
    terms=[
        ('rab:quantBody', RAB.quantBody),
    ]
)


class RabQuantBody(Record):
    record_info = RecordInfo(record_type=RAB.quantBody,
                             attrs=[AttrInfo('scalar', RAB_PRED.hasScalar), AttrInfo('unit', RAB_PRED.hasUnit)])

    scalar: float
    unit: Uri

    def __init__(self, uri: Optional[Uri] = None, scalar: Optional[float] = None, unit: Optional[Uri] = None):
        super().__init__(uri=uri, scalar=scalar, unit=unit)
