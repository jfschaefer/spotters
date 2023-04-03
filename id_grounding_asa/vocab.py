from typing import Optional

from spotterbase.rdf import Vocabulary, NameSpace, Uri
from spotterbase.rdf.vocab import XSD
from spotterbase.records.jsonld_support import JsonLdContext
from spotterbase.records.record import Record, PredInfo, RecordInfo, AttrInfo


class ASA(Vocabulary):
    NS: NameSpace = NameSpace(Uri('https://sigmathling.kwarc.info/resources/grounding-dataset/'), 'asa:')

    corpus: Uri
    groundingBody: Uri
    hasGrounding: Uri
    hasSog: Uri
    hasArity: Uri
    hasArgsType: Uri


class ASA_PRED:
    # general-purpose
    hasGrounding = PredInfo(ASA.hasGrounding, json_ld_term='asa:hasGrounding', literal_type=XSD.string)
    hasSog = PredInfo(ASA.hasSog, json_ld_term='asa:hasSog', json_ld_type_is_id=True)
    hasArity = PredInfo(ASA.hasArity, json_ld_term='asa:hasArity', literal_type=XSD.nonNegativeInteger)
    hasArgsType = PredInfo(ASA.hasArgsType, json_ld_term='asa:hasArgsType', is_rdf_list=True, json_ld_type_is_id=True)


ASA_JSONLD_CONTEXT: JsonLdContext = JsonLdContext(
    uri=None,
    namespaces=[ASA.NS],
    pred_infos=list(p_info for p_info in ASA_PRED.__dict__.values() if isinstance(p_info, PredInfo)),
    terms=[
        ('asa:groundingBody', ASA.groundingBody),
    ]
)


class AsaGroundingBody(Record):
    record_info = RecordInfo(record_type=ASA.groundingBody,
                             attrs=[AttrInfo('grounding', ASA_PRED.hasGrounding),
                                    AttrInfo('sog', ASA_PRED.hasSog),
                                    AttrInfo('arity', ASA_PRED.hasArity),
                                    AttrInfo('args_type', ASA_PRED.hasArgsType),
                                    ])

    grounding: str
    arity: int
    args_type: list[Uri]
    sog: list[Uri]

    def __init__(self, uri: Optional[Uri] = None, *, arity: Optional[int] = None, args_type: Optional[list[Uri]] = None,
                 grounding: Optional[str] = None, sog: Optional[list[Uri]] = None):
        super().__init__(uri=uri, grounding=grounding, sog=sog, arity=arity, args_type=args_type)
