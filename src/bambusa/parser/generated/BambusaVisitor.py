# Generated from Bambusa.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .BambusaParser import BambusaParser
else:
    from BambusaParser import BambusaParser

# This class defines a complete generic visitor for a parse tree produced by BambusaParser.

class BambusaVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by BambusaParser#program.
    def visitProgram(self, ctx:BambusaParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#functionDecl.
    def visitFunctionDecl(self, ctx:BambusaParser.FunctionDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#paramList.
    def visitParamList(self, ctx:BambusaParser.ParamListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#param.
    def visitParam(self, ctx:BambusaParser.ParamContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#returnType.
    def visitReturnType(self, ctx:BambusaParser.ReturnTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#globalDecl.
    def visitGlobalDecl(self, ctx:BambusaParser.GlobalDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#block.
    def visitBlock(self, ctx:BambusaParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#statement.
    def visitStatement(self, ctx:BambusaParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#varDecl.
    def visitVarDecl(self, ctx:BambusaParser.VarDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#assignment.
    def visitAssignment(self, ctx:BambusaParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#returnStmt.
    def visitReturnStmt(self, ctx:BambusaParser.ReturnStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#exprStmt.
    def visitExprStmt(self, ctx:BambusaParser.ExprStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#ifStmt.
    def visitIfStmt(self, ctx:BambusaParser.IfStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#forStmt.
    def visitForStmt(self, ctx:BambusaParser.ForStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#range.
    def visitRange(self, ctx:BambusaParser.RangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#expression.
    def visitExpression(self, ctx:BambusaParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#conditionalExpr.
    def visitConditionalExpr(self, ctx:BambusaParser.ConditionalExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#logicalOrExpr.
    def visitLogicalOrExpr(self, ctx:BambusaParser.LogicalOrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#logicalAndExpr.
    def visitLogicalAndExpr(self, ctx:BambusaParser.LogicalAndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#equalityExpr.
    def visitEqualityExpr(self, ctx:BambusaParser.EqualityExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#relationalExpr.
    def visitRelationalExpr(self, ctx:BambusaParser.RelationalExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#additiveExpr.
    def visitAdditiveExpr(self, ctx:BambusaParser.AdditiveExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#multiplicativeExpr.
    def visitMultiplicativeExpr(self, ctx:BambusaParser.MultiplicativeExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#unaryExpr.
    def visitUnaryExpr(self, ctx:BambusaParser.UnaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#primaryExpr.
    def visitPrimaryExpr(self, ctx:BambusaParser.PrimaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BambusaParser#type.
    def visitType(self, ctx:BambusaParser.TypeContext):
        return self.visitChildren(ctx)



del BambusaParser