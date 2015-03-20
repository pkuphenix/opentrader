import sys
import ply.lex as lex
import ply.yacc as yacc


# -----------------------------------------------------------------------------
# calc.py
#
# A simple calculator with variables.   This is from O'Reilly's
# "Lex and Yacc", p. 63.
# -----------------------------------------------------------------------------

if sys.version_info[0] >= 3:
    raw_input = input

class OTLexer:
    tokens = (
        'METHOD','FUNCTION','STRING','NUMBER'
        )

    literals = ['.', '(', ')', ',']

    # Tokens
    t_METHOD = r'filter|orderby|groupby|limit'
    t_FUNCTION = r'merge|plus|minus|mul|div|max|min|avr'

    def t_NUMBER(self, t):
        r'-?\d+(\.\d+)?'
        t.value = float(t.value)
        return t

    def t_STRING(self, t):
        r'\".*?\"'
        t.value = t.value[1:-1]
        return t

    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")
        
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer
    def build(self,**kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
    
    # Test it output
    def test(self,data):
        self.lexer.input(data)
        while True:
             tok = self.lexer.token()
             if not tok: break
             print tok

    def __init__(self):
        self.base_obj = None
        self.base_module = None
    
# Build the lexer
#m = OTLexer()
#m.build()
#m.test("filter()")

# Parsing rules

#precedence = (
#    ('left','+','-'),
#    ('left','*','/'),
#    ('right','UMINUS'),
#    )



# dictionary of names
class OTYacc:
    tokens = (
        'METHOD','FUNCTION','STRING','NUMBER'
        )

    def p_script(self, p):
        """
        expression : method_expr
                   | function_expr
        """
        p[0] = p[1]

    def p_method_call(self, p):
        """
        method_expr : METHOD '(' parameters ')'
                    | expression '.' METHOD '(' parameters ')'
        """
        if len(p) == 5:
            p[0] = getattr(self.obj, p[1])(*p[3])
        else:
            p[0] = getattr(p[1], p[3])(*p[5])

    def p_function_call(self, p):
        "function_expr : FUNCTION '(' parameters ')'"
        p[0] = getattr(self.ctx, p[1])(*p[3])

    def p_parameters(self, p):
        """
        parameters : param
                   | parameters ',' param
        """
        rtn = []
        if len(p) == 4:
            p[1].extend([p[3]])
            p[0] = p[1]
        else:
            p[0] = [p[1]]

    def p_param(self, p):
        """
        param : method_expr
              | function_expr
              | STRING
              | NUMBER
        """
        p[0] = p[1]

    def p_error(self, p):  
        if p:
            print("Syntax error at '%s'" % p.value)  
        else:
            print("Syntax error at EOF")  

    def build(self, **kwargs):
        self.yacc = yacc.yacc(module=self, **kwargs)
        self.lexer = OTLexer()
        self.lexer.build()

    def parse(self, text):
        return self.yacc.parse(text, lexer=self.lexer.lexer)

    def __init__(self, obj, ctx):
        self.yacc = None
        self.lexer = None
        self.obj = obj
        self.ctx = ctx

    @classmethod
    def filter(cls, a, b): # just for local test
        print a+b
        return cls

    @staticmethod
    def merge(a): # just for local test
        print a

if __name__ == "__main__":
    parser = OTYacc(OTYacc, OTYacc)
    parser.build()
    parser.parse('merge(filter(3,4).filter(3,4))')

