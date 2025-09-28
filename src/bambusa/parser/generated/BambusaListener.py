# Generated from Bambusa.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .BambusaParser import BambusaParser
else:
    from BambusaParser import BambusaParser

# This class defines a complete listener for a parse tree produced by BambusaParser.
class BambusaListener(ParseTreeListener):

    # Enter a parse tree produced by BambusaParser#program.
    def enterProgram(self, ctx:BambusaParser.ProgramContext):
        pass

    # Exit a parse tree produced by BambusaParser#program.
    def exitProgram(self, ctx:BambusaParser.ProgramContext):
        pass


    # Enter a parse tree produced by BambusaParser#functionDecl.
    def enterFunctionDecl(self, ctx:BambusaParser.FunctionDeclContext):
        pass

    # Exit a parse tree produced by BambusaParser#functionDecl.
    def exitFunctionDecl(self, ctx:BambusaParser.FunctionDeclContext):
        pass


    # Enter a parse tree produced by BambusaParser#paramList.
    def enterParamList(self, ctx:BambusaParser.ParamListContext):
        pass

    # Exit a parse tree produced by BambusaParser#paramList.
    def exitParamList(self, ctx:BambusaParser.ParamListContext):
        pass


    # Enter a parse tree produced by BambusaParser#param.
    def enterParam(self, ctx:BambusaParser.ParamContext):
        pass

    # Exit a parse tree produced by BambusaParser#param.
    def exitParam(self, ctx:BambusaParser.ParamContext):
        pass


    # Enter a parse tree produced by BambusaParser#returnType.
    def enterReturnType(self, ctx:BambusaParser.ReturnTypeContext):
        pass

    # Exit a parse tree produced by BambusaParser#returnType.
    def exitReturnType(self, ctx:BambusaParser.ReturnTypeContext):
        pass


    # Enter a parse tree produced by BambusaParser#globalDecl.
    def enterGlobalDecl(self, ctx:BambusaParser.GlobalDeclContext):
        pass

    # Exit a parse tree produced by BambusaParser#globalDecl.
    def exitGlobalDecl(self, ctx:BambusaParser.GlobalDeclContext):
        pass


    # Enter a parse tree produced by BambusaParser#block.
    def enterBlock(self, ctx:BambusaParser.BlockContext):
        pass

    # Exit a parse tree produced by BambusaParser#block.
    def exitBlock(self, ctx:BambusaParser.BlockContext):
        pass


    # Enter a parse tree produced by BambusaParser#statement.
    def enterStatement(self, ctx:BambusaParser.StatementContext):
        pass

    # Exit a parse tree produced by BambusaParser#statement.
    def exitStatement(self, ctx:BambusaParser.StatementContext):
        pass


    # Enter a parse tree produced by BambusaParser#varDecl.
    def enterVarDecl(self, ctx:BambusaParser.VarDeclContext):
        pass

    # Exit a parse tree produced by BambusaParser#varDecl.
    def exitVarDecl(self, ctx:BambusaParser.VarDeclContext):
        pass


    # Enter a parse tree produced by BambusaParser#assignment.
    def enterAssignment(self, ctx:BambusaParser.AssignmentContext):
        pass

    # Exit a parse tree produced by BambusaParser#assignment.
    def exitAssignment(self, ctx:BambusaParser.AssignmentContext):
        pass


    # Enter a parse tree produced by BambusaParser#returnStmt.
    def enterReturnStmt(self, ctx:BambusaParser.ReturnStmtContext):
        pass

    # Exit a parse tree produced by BambusaParser#returnStmt.
    def exitReturnStmt(self, ctx:BambusaParser.ReturnStmtContext):
        pass


    # Enter a parse tree produced by BambusaParser#exprStmt.
    def enterExprStmt(self, ctx:BambusaParser.ExprStmtContext):
        pass

    # Exit a parse tree produced by BambusaParser#exprStmt.
    def exitExprStmt(self, ctx:BambusaParser.ExprStmtContext):
        pass


    # Enter a parse tree produced by BambusaParser#ifStmt.
    def enterIfStmt(self, ctx:BambusaParser.IfStmtContext):
        pass

    # Exit a parse tree produced by BambusaParser#ifStmt.
    def exitIfStmt(self, ctx:BambusaParser.IfStmtContext):
        pass


    # Enter a parse tree produced by BambusaParser#forStmt.
    def enterForStmt(self, ctx:BambusaParser.ForStmtContext):
        pass

    # Exit a parse tree produced by BambusaParser#forStmt.
    def exitForStmt(self, ctx:BambusaParser.ForStmtContext):
        pass


    # Enter a parse tree produced by BambusaParser#range.
    def enterRange(self, ctx:BambusaParser.RangeContext):
        pass

    # Exit a parse tree produced by BambusaParser#range.
    def exitRange(self, ctx:BambusaParser.RangeContext):
        pass


    # Enter a parse tree produced by BambusaParser#expression.
    def enterExpression(self, ctx:BambusaParser.ExpressionContext):
        pass

    # Exit a parse tree produced by BambusaParser#expression.
    def exitExpression(self, ctx:BambusaParser.ExpressionContext):
        pass


    # Enter a parse tree produced by BambusaParser#conditionalExpr.
    def enterConditionalExpr(self, ctx:BambusaParser.ConditionalExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#conditionalExpr.
    def exitConditionalExpr(self, ctx:BambusaParser.ConditionalExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#logicalOrExpr.
    def enterLogicalOrExpr(self, ctx:BambusaParser.LogicalOrExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#logicalOrExpr.
    def exitLogicalOrExpr(self, ctx:BambusaParser.LogicalOrExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#logicalAndExpr.
    def enterLogicalAndExpr(self, ctx:BambusaParser.LogicalAndExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#logicalAndExpr.
    def exitLogicalAndExpr(self, ctx:BambusaParser.LogicalAndExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#equalityExpr.
    def enterEqualityExpr(self, ctx:BambusaParser.EqualityExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#equalityExpr.
    def exitEqualityExpr(self, ctx:BambusaParser.EqualityExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#relationalExpr.
    def enterRelationalExpr(self, ctx:BambusaParser.RelationalExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#relationalExpr.
    def exitRelationalExpr(self, ctx:BambusaParser.RelationalExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#additiveExpr.
    def enterAdditiveExpr(self, ctx:BambusaParser.AdditiveExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#additiveExpr.
    def exitAdditiveExpr(self, ctx:BambusaParser.AdditiveExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#multiplicativeExpr.
    def enterMultiplicativeExpr(self, ctx:BambusaParser.MultiplicativeExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#multiplicativeExpr.
    def exitMultiplicativeExpr(self, ctx:BambusaParser.MultiplicativeExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#unaryExpr.
    def enterUnaryExpr(self, ctx:BambusaParser.UnaryExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#unaryExpr.
    def exitUnaryExpr(self, ctx:BambusaParser.UnaryExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#primaryExpr.
    def enterPrimaryExpr(self, ctx:BambusaParser.PrimaryExprContext):
        pass

    # Exit a parse tree produced by BambusaParser#primaryExpr.
    def exitPrimaryExpr(self, ctx:BambusaParser.PrimaryExprContext):
        pass


    # Enter a parse tree produced by BambusaParser#type.
    def enterType(self, ctx:BambusaParser.TypeContext):
        pass

    # Exit a parse tree produced by BambusaParser#type.
    def exitType(self, ctx:BambusaParser.TypeContext):
        pass



del BambusaParser