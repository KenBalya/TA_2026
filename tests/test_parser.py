# tests/test_parser.py

from core.query.parser import parse_query_to_ir1
from core.query.ir import IntentType

def test_parser_precondition_reinstall_die_roller():
    q = "Sebelum memasang kembali die roller, apa yang harus dilakukan?"
    ir1 = parse_query_to_ir1(q)
    assert ir1.intent == IntentType.PRECONDITION
    assert ir1.anchor_object == "die roller"
    assert ir1.temporal_relation == "BEFORE"
