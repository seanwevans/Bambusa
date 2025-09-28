"""Utilities for converting Bambusa parse trees into typed AST nodes."""
from __future__ import annotations

from typing import List

from antlr4 import CommonTokenStream, InputStream, ParserRuleContext, Token
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Tree import TerminalNode

from ..ast import (
    ArrayType,
    Assignment,
    BinaryOp,
    Block,
    BOOL_TYPE,
    ConditionalExpr,
    ExprStmt,
    FLOAT_TYPE,
    ForStmt,
    FunctionDecl,
    GlobalDecl,
    Identifier,
    IfStmt,
    INT_TYPE,
    Literal,
    Program,
    Parameter,
    Range,
    ReturnStmt,
    SourceLocation,
    Statement,
    Type,
    UnaryOp,
    VarDecl,
    VOID_TYPE,
)
from .generated.BambusaLexer import BambusaLexer
from .generated.BambusaParser import BambusaParser
from .generated.BambusaVisitor import BambusaVisitor


class _ThrowingErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):  # type: ignore[override]
        raise SyntaxError(f"line {line}:{column} {msg}")


def _location_from_token(token: Token) -> SourceLocation:
    return SourceLocation(line=token.line, column=token.column)


def _location_from_ctx(ctx: ParserRuleContext) -> SourceLocation:
    return _location_from_token(ctx.start)


def _location_from_terminal(node: TerminalNode) -> SourceLocation:
    return _location_from_token(node.symbol)


class ASTBuilder(BambusaVisitor):
    """Visitor that lowers parse trees into strongly typed AST nodes."""

    def visitProgram(self, ctx: BambusaParser.ProgramContext) -> Program:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        globals_: List[GlobalDecl] = []
        functions: List[FunctionDecl] = []
        for child in ctx.getChildren():
            if isinstance(child, BambusaParser.GlobalDeclContext):
                globals_.append(self.visit(child))
            elif isinstance(child, BambusaParser.FunctionDeclContext):
                functions.append(self.visit(child))
        return Program(location=location, globals=globals_, functions=functions)

    def visitGlobalDecl(self, ctx: BambusaParser.GlobalDeclContext) -> GlobalDecl:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        type_node = self.visit(ctx.type_())
        name = ctx.Identifier().getText()
        value = self.visit(ctx.expression())
        return GlobalDecl(location=location, type=type_node, name=name, value=value)

    def visitFunctionDecl(self, ctx: BambusaParser.FunctionDeclContext) -> FunctionDecl:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        name = ctx.Identifier().getText()
        params = []
        if ctx.paramList():
            params = [self.visit(param_ctx) for param_ctx in ctx.paramList().param()]
        return_type = VOID_TYPE
        return_ctx = ctx.returnType()
        if return_ctx is not None and return_ctx.type_() is not None:
            return_type = self.visit(return_ctx.type_())
        body = self.visit(ctx.block())
        return FunctionDecl(location=location, name=name, params=params, return_type=return_type, body=body)

    def visitParam(self, ctx: BambusaParser.ParamContext) -> Parameter:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        type_node = self.visit(ctx.type_())
        name = ctx.Identifier().getText()
        return Parameter(location=location, type=type_node, name=name)

    def visitType(self, ctx: BambusaParser.TypeContext) -> Type:  # type: ignore[override]
        if ctx.getChildCount() == 1:
            text = ctx.getText()
            if text == "int":
                return INT_TYPE
            if text == "float":
                return FLOAT_TYPE
            if text == "bool":
                return BOOL_TYPE
            raise ValueError(f"unexpected primitive type '{text}'")
        element = self.visit(ctx.type_())
        return ArrayType(element_type=element)

    def visitBlock(self, ctx: BambusaParser.BlockContext) -> Block:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        statements = [self.visit(stmt_ctx) for stmt_ctx in ctx.statement()]
        return Block(location=location, statements=statements)

    def visitStatement(self, ctx: BambusaParser.StatementContext) -> Statement:  # type: ignore[override]
        if ctx.varDecl():
            return self.visit(ctx.varDecl())
        if ctx.assignment():
            return self.visit(ctx.assignment())
        if ctx.ifStmt():
            return self.visit(ctx.ifStmt())
        if ctx.forStmt():
            return self.visit(ctx.forStmt())
        if ctx.returnStmt():
            return self.visit(ctx.returnStmt())
        if ctx.exprStmt():
            return self.visit(ctx.exprStmt())
        raise NotImplementedError("unknown statement form")

    def visitVarDecl(self, ctx: BambusaParser.VarDeclContext) -> VarDecl:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        type_node = self.visit(ctx.type_())
        name = ctx.Identifier().getText()
        initializer = self.visit(ctx.expression()) if ctx.expression() else None
        return VarDecl(location=location, type=type_node, name=name, initializer=initializer)

    def visitAssignment(self, ctx: BambusaParser.AssignmentContext) -> Assignment:  # type: ignore[override]
        identifier = ctx.Identifier()
        location = _location_from_token(identifier.symbol)
        value = self.visit(ctx.expression())
        return Assignment(location=location, name=identifier.getText(), value=value)

    def visitIfStmt(self, ctx: BambusaParser.IfStmtContext) -> IfStmt:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        condition = self.visit(ctx.expression())
        then_block = self.visit(ctx.block(0))
        else_block = self.visit(ctx.block(1)) if ctx.block(1) else None
        return IfStmt(location=location, condition=condition, then_block=then_block, else_block=else_block)

    def visitForStmt(self, ctx: BambusaParser.ForStmtContext) -> ForStmt:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        iterator = ctx.Identifier().getText()
        range_node = self.visit(ctx.range_())
        body = self.visit(ctx.block())
        return ForStmt(location=location, iterator=iterator, range=range_node, body=body)

    def visitRange(self, ctx: BambusaParser.RangeContext) -> Range:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        start_expr = self.visit(ctx.expression(0))
        end_expr = self.visit(ctx.expression(1))
        return Range(location=location, start=start_expr, end=end_expr)

    def visitReturnStmt(self, ctx: BambusaParser.ReturnStmtContext) -> ReturnStmt:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        value = self.visit(ctx.expression())
        return ReturnStmt(location=location, value=value)

    def visitExprStmt(self, ctx: BambusaParser.ExprStmtContext) -> ExprStmt:  # type: ignore[override]
        location = _location_from_ctx(ctx)
        value = self.visit(ctx.expression())
        return ExprStmt(location=location, value=value)

    def visitExpression(self, ctx: BambusaParser.ExpressionContext):  # type: ignore[override]
        return self.visit(ctx.conditionalExpr())

    def visitConditionalExpr(self, ctx: BambusaParser.ConditionalExprContext):  # type: ignore[override]
        if ctx.getChildCount() == 1:
            return self.visit(ctx.logicalOrExpr())
        location = _location_from_ctx(ctx)
        condition = self.visit(ctx.expression(0))
        then_expr = self.visit(ctx.expression(1))
        else_expr = self.visit(ctx.expression(2))
        return ConditionalExpr(location=location, condition=condition, then_expr=then_expr, else_expr=else_expr)

    def visitLogicalOrExpr(self, ctx: BambusaParser.LogicalOrExprContext):  # type: ignore[override]
        return self._fold_left(ctx)

    def visitLogicalAndExpr(self, ctx: BambusaParser.LogicalAndExprContext):  # type: ignore[override]
        return self._fold_left(ctx)

    def visitEqualityExpr(self, ctx: BambusaParser.EqualityExprContext):  # type: ignore[override]
        return self._fold_left(ctx)

    def visitRelationalExpr(self, ctx: BambusaParser.RelationalExprContext):  # type: ignore[override]
        return self._fold_left(ctx)

    def visitAdditiveExpr(self, ctx: BambusaParser.AdditiveExprContext):  # type: ignore[override]
        return self._fold_left(ctx)

    def visitMultiplicativeExpr(self, ctx: BambusaParser.MultiplicativeExprContext):  # type: ignore[override]
        return self._fold_left(ctx)

    def visitUnaryExpr(self, ctx: BambusaParser.UnaryExprContext):  # type: ignore[override]
        if ctx.getChildCount() == 1:
            return self.visit(ctx.primaryExpr())
        operator_node = ctx.getChild(0)
        operand = self.visit(ctx.unaryExpr())
        location = _location_from_terminal(operator_node)
        return UnaryOp(location=location, operator=operator_node.getText(), operand=operand)

    def visitPrimaryExpr(self, ctx: BambusaParser.PrimaryExprContext):  # type: ignore[override]
        if ctx.IntegerLiteral():
            token = ctx.IntegerLiteral().getSymbol()
            return Literal(location=_location_from_token(token), value=int(token.text))
        if ctx.FloatLiteral():
            token = ctx.FloatLiteral().getSymbol()
            return Literal(location=_location_from_token(token), value=float(token.text))
        if ctx.BoolLiteral():
            token = ctx.BoolLiteral().getSymbol()
            return Literal(location=_location_from_token(token), value=token.text == "true")
        if ctx.Identifier():
            token = ctx.Identifier().getSymbol()
            return Identifier(location=_location_from_token(token), name=token.text)
        return self.visit(ctx.expression())

    def _fold_left(self, ctx: ParserRuleContext):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))
        node = self.visit(ctx.getChild(0))
        for i in range(1, ctx.getChildCount(), 2):
            operator_node = ctx.getChild(i)
            right_ctx = ctx.getChild(i + 1)
            right = self.visit(right_ctx)
            node = BinaryOp(
                location=_location_from_terminal(operator_node),
                operator=operator_node.getText(),
                left=node,
                right=right,
            )
        return node


def parse_program(source: str) -> Program:
    """Parse Bambusa source code into an AST."""

    input_stream = InputStream(source)
    lexer = BambusaLexer(input_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(_ThrowingErrorListener())

    token_stream = CommonTokenStream(lexer)
    parser = BambusaParser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(_ThrowingErrorListener())

    tree = parser.program()
    builder = ASTBuilder()
    return builder.visit(tree)
