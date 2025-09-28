grammar Bambusa;

// --- Parser rules ---

program
    : (functionDecl | globalDecl)* EOF
    ;

functionDecl
    : 'fn' Identifier '(' paramList? ')' returnType block
    ;

paramList
    : param (',' param)*
    ;

param
    : type Identifier
    ;

returnType
    : '->' type
    |               // void return
    ;

globalDecl
    : type Identifier '=' expression ';'
    ;

block
    : '{' statement* '}'
    ;

statement
    : varDecl ';'
    | assignment ';'
    | ifStmt
    | forStmt
    | returnStmt ';'
    | exprStmt ';'
    ;

varDecl
    : type Identifier ('=' expression)?
    ;

assignment
    : Identifier '=' expression
    ;

returnStmt
    : 'return' expression
    ;

exprStmt
    : expression
    ;

ifStmt
    : 'if' expression 'then' block ('else' block)?
    ;

forStmt
    : 'for' Identifier 'in' range block
    ;

range
    : expression '..' expression
    ;

expression
    : conditionalExpr
    ;

conditionalExpr
    : 'if' expression 'then' expression 'else' expression
    | logicalOrExpr
    ;

logicalOrExpr
    : logicalAndExpr ('||' logicalAndExpr)*
    ;

logicalAndExpr
    : equalityExpr ('&&' equalityExpr)*
    ;

equalityExpr
    : relationalExpr (('==' | '!=') relationalExpr)*
    ;

relationalExpr
    : additiveExpr (('<' | '>' | '<=' | '>=') additiveExpr)*
    ;

additiveExpr
    : multiplicativeExpr (('+' | '-') multiplicativeExpr)*
    ;

multiplicativeExpr
    : unaryExpr (('*' | '/' | '%') unaryExpr)*
    ;

unaryExpr
    : ('!' | '-') unaryExpr
    | primaryExpr
    ;

primaryExpr
    : IntegerLiteral
    | FloatLiteral
    | BoolLiteral
    | Identifier
    | '(' expression ')'
    ;

// --- Lexer rules ---

BoolLiteral
    : 'true'
    | 'false'
    ;

IntegerLiteral
    : [0-9]+
    ;

FloatLiteral
    : [0-9]+ '.' [0-9]+
    ;

Identifier
    : [a-zA-Z_][a-zA-Z_0-9]*
    ;

type
    : 'int'
    | 'float'
    | 'bool'
    | type '[' ']'        // arrays
    ;

WS
    : [ \t\r\n]+ -> skip
    ;

COMMENT
    : '//' ~[\r\n]* -> skip
    ;
