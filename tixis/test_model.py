import pytest
from common.db import db
from program import Program

def test_program():
    Program.remove()
    assert Program.list() == []
    prog = Program.new(name='NewProgram', desc='This is the new program', target_type='percent', target_value=0)
    assert prog.desc == 'This is the new program'
    assert prog.target_type == 'percent'

    assert len(Program.list()) == 1
    the_prog = Program.find_one({'name':'NewProgram'})
    assert the_prog is not None
    assert the_prog.desc == 'This is the new program'
    assert True