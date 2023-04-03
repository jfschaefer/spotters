"""
    Import the annotations from the grounding dataset.
    As it is rather small, we do not need the parallelization etc. of a proper spotter and can keep things simple.
"""
from pathlib import Path

import json
import urllib.parse

from id_grounding_asa.document_corpus import DocumentCorpus
from id_grounding_asa.vocab import AsaGroundingBody, ASA
from spotterbase.anno_core.annotation import Annotation
from spotterbase.anno_core.tag_body import Tag, TagSet, SimpleTagBody
from spotterbase.anno_core.target import FragmentTarget
from spotterbase.rdf import TripleI, Uri, FileSerializer
from spotterbase.selectors.dom_range import DomPoint, DomRange
from spotterbase.utils import config_loader


def triple_gen() -> TripleI:
    known_args_type: dict[str, Tag] = {}

    tag_set = TagSet(
        uri=ASA.NS['argtype#'],
        label='Arguments Type Components'
    )
    yield from tag_set.to_triples()

    sog_tag = Tag(
        uri=ASA.NS['sog'],
        label='Source of Grounding'
    )

    known_sogs: dict[tuple[str, str], Uri] = {}

    for document in DocumentCorpus():
        print('processing', document.get_uri())
        tree = document.get_html_tree(cached=True)
        path = document.path
        with open(path.parent.parent/'data'/(path.name[:-len('.html')] + '_mcdict.json'), 'r') as fp:
            mcdict = json.load(fp)
        with open(path.parent.parent/'data'/(path.name[:-len('.html')] + '_anno.json'), 'r') as fp:
            anno = json.load(fp)

        concept_lookup = {}
        for c in mcdict['concepts'].values():
            text = c['surface']['text']
            assert text not in concept_lookup
            concept_lookup[text] = c['identifiers']

        for i, mi in enumerate(anno['mi_anno']):
            uri = document.get_uri() + '#groundingimport'

            # node = tree.xpath(f'//*[@id="{mi}"]')[0]
            node = document.get_node_for_id(mi)
            if anno['mi_anno'][mi]['concept_id'] is None:
                # not yet annotated
                continue

            dictionary = 'default'
            if 'mathvariant' in node.attrib and node.attrib['mathvariant'] == 'normal':
                dictionary = 'roman'
            concept = concept_lookup[node.text][dictionary][anno['mi_anno'][mi]['concept_id']]

            target = FragmentTarget(
                uri=uri + f'.target.{i}',
                source=document.get_uri(),
                selectors=document.get_selector_converter().dom_to_selectors(DomPoint(node).as_range())
            )
            yield from target.to_triples()
            body = AsaGroundingBody(
                uri=uri + f'.body.{i}',
                arity=concept['arity'],
                grounding=concept['description'],
                sog=[],
            )

            for sogids_list in anno['mi_anno'][mi]['sog']:
                sogids = tuple(sogids_list)
                if sogids not in known_sogs:
                    assert len(sogids) == 2
                    # print(f'//*[@id="{sogids[0]}"]')
                    # print(tree.xpath(f'//*[@id="{sogids[0]}"]'))
                    # start_node = tree.xpath(f'//*[@id="{sogids[0]}"]')[0]
                    # end_node = tree.xpath(f'//*[@id="{sogids[1]}"]')[0]
                    start_node = document.get_node_for_id(sogids[0])
                    end_node = document.get_node_for_id(sogids[1])
                    sog_target = FragmentTarget(
                        uri=uri + f'.target.sog.{i}',
                        source=document.get_uri(),
                        selectors=document.get_selector_converter().dom_to_selectors(
                            DomRange(DomPoint(start_node), DomPoint(end_node, after=True))
                        )
                    )
                    yield from sog_tag.to_triples()
                    sog_anno = Annotation(
                        uri=uri + f'.anno.sog.{i}',
                        target_uri=sog_target.uri,
                        body=SimpleTagBody(tag=sog_tag.uri)
                    )
                    yield from sog_anno.to_triples()

                    known_sogs[sogids] = sog_anno.uri
                body.sog.append(known_sogs[sogids])

            body.arg_types = []
            for arg_type in concept['args_type']:
                if arg_type not in known_args_type:
                    known_args_type[arg_type] = Tag(
                        uri=tag_set.uri + urllib.parse.unquote_plus(arg_type),
                        label=arg_type,
                        belongs_to=tag_set.uri,
                    )
                    yield from known_args_type[arg_type].to_triples()
                body.arg_types.append(known_args_type[arg_type].uri)

            annotation = Annotation(
                uri=uri + f'.anno.{i}',
                target_uri=target.uri,
                body=body
            )
            yield from annotation.to_triples()


config_loader.auto()


with FileSerializer(Path('/tmp/id-grounding-asa-import.ttl.gz')) as serializer:
    serializer.add_from_iterable(triple_gen())
