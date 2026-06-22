import { Token, TokenType, ASTNode, Program, VarDecl, Assign, IfStatement, RepeatStatement, WhileStatement, ExpressionStatement, BinaryExpression, Literal, Identifier, CallExpression } from './types';

export class Parser {
  private tokens: Token[];
  private current: number = 0;
  public errors: string[] = [];

  constructor(tokens: Token[]) {
    this.tokens = tokens;
  }

  private peek(): Token {
    return this.tokens[this.current];
  }

  private peekNext(): Token {
    if (this.current + 1 >= this.tokens.length) return this.tokens[this.tokens.length - 1];
    return this.tokens[this.current + 1];
  }

  private isAtEnd(): boolean {
    return this.peek().type === 'EOF';
  }

  private advance(): Token {
    if (!this.isAtEnd()) this.current++;
    return this.tokens[this.current - 1];
  }

  private match(...types: TokenType[]): boolean {
    for (const type of types) {
      if (this.check(type)) {
        this.advance();
        return true;
      }
    }
    return false;
  }

  private check(type: TokenType): boolean {
    if (this.isAtEnd()) return false;
    return this.peek().type === type;
  }

  private consume(type: TokenType, message: string): Token {
    if (this.check(type)) return this.advance();
    
    const token = this.peek();
    const errMsg = `[Line ${token.line}, Col ${token.column}] Error at '${token.value || 'EOF'}': ${message}`;
    this.errors.push(errMsg);
    throw new Error(errMsg);
  }

  public parse(): Program {
    const body: ASTNode[] = [];
    while (!this.isAtEnd()) {
      try {
        const stmt = this.statement();
        if (stmt) body.push(stmt);
      } catch (e) {
        this.synchronize();
      }
    }
    return { type: 'Program', body, line: 1 };
  }

  private synchronize() {
    this.advance();
    while (!this.isAtEnd()) {
      if (this.tokens[this.current - 1].type === 'SEMICOLON') return;

      switch (this.peek().type) {
        case 'LET':
        case 'IF':
        case 'REPEAT':
        case 'WHILE':
          return;
      }
      this.advance();
    }
  }

  private statement(): ASTNode {
    if (this.match('LET')) return this.varDeclaration();
    if (this.match('IF')) return this.ifStatement();
    if (this.match('REPEAT')) return this.repeatStatement();
    if (this.match('WHILE')) return this.whileStatement();

    // Assignment or expression statement
    return this.assignmentOrExpressionStatement();
  }

  private varDeclaration(): VarDecl {
    const nameToken = this.consume('IDENTIFIER', 'Expect variable name.');
    const line = nameToken.line;
    this.consume('ASSIGN', "Expect '=' after variable name.");
    const value = this.expression();
    this.consume('SEMICOLON', "Expect ';' after variable declaration.");
    return { type: 'VarDecl', name: nameToken.value, value, line };
  }

  private ifStatement(): IfStatement {
    const line = this.tokens[this.current - 1].line;
    const test = this.expression();
    this.consume('LBRACE', "Expect '{' before if branch.");
    const consequent = this.block();
    
    let alternate: ASTNode[] | undefined = undefined;
    if (this.match('ELSE')) {
      this.consume('LBRACE', "Expect '{' before else branch.");
      alternate = this.block();
    }

    return { type: 'IfStatement', test, consequent, alternate, line };
  }

  private repeatStatement(): RepeatStatement {
    const line = this.tokens[this.current - 1].line;
    const count = this.expression();
    this.consume('LBRACE', "Expect '{' before repeat block body.");
    const body = this.block();
    return { type: 'RepeatStatement', count, body, line };
  }

  private whileStatement(): WhileStatement {
    const line = this.tokens[this.current - 1].line;
    const test = this.expression();
    this.consume('LBRACE', "Expect '{' before while block body.");
    const body = this.block();
    return { type: 'WhileStatement', test, body, line };
  }

  private block(): ASTNode[] {
    const statements: ASTNode[] = [];
    while (!this.check('RBRACE') && !this.isAtEnd()) {
      try {
        const stmt = this.statement();
        if (stmt) statements.push(stmt);
      } catch (e) {
        this.synchronize();
      }
    }
    this.consume('RBRACE', "Expect '}' after block.");
    return statements;
  }

  private assignmentOrExpressionStatement(): ASTNode {
    const startToken = this.peek();
    
    // Check if it's an assignment (e.g. `x = ...`)
    if (startToken.type === 'IDENTIFIER' && this.peekNext().type === 'ASSIGN') {
      const name = this.advance().value; // consume identifier
      this.advance(); // consume '='
      const value = this.expression();
      this.consume('SEMICOLON', "Expect ';' after assignment.");
      return { type: 'Assign', name, value, line: startToken.line };
    }

    // Standard expression statement
    const expr = this.expression();
    this.consume('SEMICOLON', "Expect ';' after expression.");
    return { type: 'ExpressionStatement', expression: expr, line: startToken.line };
  }

  private expression(): ASTNode {
    return this.equality();
  }

  private equality(): ASTNode {
    let expr = this.comparison();

    while (this.match('EQ', 'NEQ')) {
      const operator = this.tokens[this.current - 1].value;
      const right = this.comparison();
      expr = {
        type: 'BinaryExpression',
        operator,
        left: expr,
        right,
        line: this.tokens[this.current - 1].line,
      };
    }

    return expr;
  }

  private comparison(): ASTNode {
    let expr = this.term();

    while (this.match('LT', 'LTE', 'GT', 'GTE')) {
      const operator = this.tokens[this.current - 1].value;
      const right = this.term();
      expr = {
        type: 'BinaryExpression',
        operator,
        left: expr,
        right,
        line: this.tokens[this.current - 1].line,
      };
    }

    return expr;
  }

  private term(): ASTNode {
    let expr = this.factor();

    while (this.match('PLUS', 'MINUS')) {
      const operator = this.tokens[this.current - 1].value;
      const right = this.factor();
      expr = {
        type: 'BinaryExpression',
        operator,
        left: expr,
        right,
        line: this.tokens[this.current - 1].line,
      };
    }

    return expr;
  }

  private factor(): ASTNode {
    let expr = this.primary();

    while (this.match('STAR', 'SLASH', 'MODULO')) {
      const operator = this.tokens[this.current - 1].value;
      const right = this.primary();
      expr = {
        type: 'BinaryExpression',
        operator,
        left: expr,
        right,
        line: this.tokens[this.current - 1].line,
      };
    }

    return expr;
  }

  private primary(): ASTNode {
    const token = this.peek();

    if (this.match('FALSE')) return { type: 'Literal', value: false, line: token.line };
    if (this.match('TRUE')) return { type: 'Literal', value: true, line: token.line };

    if (this.match('NUMBER')) {
      const val = parseFloat(token.value);
      return { type: 'Literal', value: isNaN(val) ? token.value : val, line: token.line };
    }

    if (this.match('STRING')) {
      return { type: 'Literal', value: token.value, line: token.line };
    }

    if (this.match('IDENTIFIER')) {
      // Check if it's a function call (e.g. `print(...)`)
      if (this.match('LPAREN')) {
        const args: ASTNode[] = [];
        if (!this.check('RPAREN')) {
          do {
            args.push(this.expression());
          } while (this.match('COMMA'));
        }
        this.consume('RPAREN', "Expect ')' after arguments.");
        return { type: 'CallExpression', callee: token.value, args, line: token.line };
      }
      return { type: 'Identifier', name: token.value, line: token.line };
    }

    if (this.match('LPAREN')) {
      const expr = this.expression();
      this.consume('RPAREN', "Expect ')' after expression.");
      return expr;
    }

    const errMsg = `[Line ${token.line}, Col ${token.column}] Expect expression, found '${token.value || 'EOF'}'.`;
    this.errors.push(errMsg);
    throw new Error(errMsg);
  }
}
