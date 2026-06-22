export type TokenType =
  | 'LET'          // let
  | 'IF'           // if
  | 'ELSE'         // else
  | 'REPEAT'       // repeat
  | 'WHILE'        // while
  | 'TRUE'         // true
  | 'FALSE'        // false
  | 'IDENTIFIER'   // variable/function names
  | 'NUMBER'       // numbers (e.g. 5, 3.14)
  | 'STRING'       // strings (e.g. "red")
  | 'PLUS'         // +
  | 'MINUS'        // -
  | 'STAR'         // *
  | 'SLASH'        // /
  | 'MODULO'       // %
  | 'ASSIGN'       // =
  | 'EQ'           // ==
  | 'NEQ'          // !=
  | 'LT'           // <
  | 'GT'           // >
  | 'LTE'          // <=
  | 'GTE'          // >=
  | 'LPAREN'       // (
  | 'RPAREN'       // )
  | 'LBRACE'       // {
  | 'RBRACE'       // }
  | 'COMMA'        // ,
  | 'SEMICOLON'    // ;
  | 'EOF'          // end of file
  | 'ERROR';       // error token

export interface Token {
  type: TokenType;
  value: string;
  line: number;
  column: number;
}

export type ASTNode =
  | Program
  | VarDecl
  | Assign
  | IfStatement
  | RepeatStatement
  | WhileStatement
  | ExpressionStatement
  | BinaryExpression
  | Literal
  | Identifier
  | CallExpression;

export interface Program {
  type: 'Program';
  body: ASTNode[];
  line?: number;
}

export interface VarDecl {
  type: 'VarDecl';
  name: string;
  value: ASTNode;
  line: number;
}

export interface Assign {
  type: 'Assign';
  name: string;
  value: ASTNode;
  line: number;
}

export interface IfStatement {
  type: 'IfStatement';
  test: ASTNode;
  consequent: ASTNode[];
  alternate?: ASTNode[];
  line: number;
}

export interface RepeatStatement {
  type: 'RepeatStatement';
  count: ASTNode;
  body: ASTNode[];
  line: number;
}

export interface WhileStatement {
  type: 'WhileStatement';
  test: ASTNode;
  body: ASTNode[];
  line: number;
}

export interface ExpressionStatement {
  type: 'ExpressionStatement';
  expression: ASTNode;
  line: number;
}

export interface BinaryExpression {
  type: 'BinaryExpression';
  operator: string;
  left: ASTNode;
  right: ASTNode;
  line: number;
}

export interface Literal {
  type: 'Literal';
  value: string | number | boolean;
  line: number;
}

export interface Identifier {
  type: 'Identifier';
  name: string;
  line: number;
}

export interface CallExpression {
  type: 'CallExpression';
  callee: string;
  args: ASTNode[];
  line: number;
}
