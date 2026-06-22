import { Token, TokenType } from './types';

const KEYWORDS: Record<string, TokenType> = {
  let: 'LET',
  if: 'IF',
  else: 'ELSE',
  repeat: 'REPEAT',
  while: 'WHILE',
  true: 'TRUE',
  false: 'FALSE',
};

export class Lexer {
  private input: string;
  private position: number = 0;
  private line: number = 1;
  private column: number = 1;

  constructor(input: string) {
    this.input = input;
  }

  private peek(): string {
    if (this.position >= this.input.length) return '';
    return this.input[this.position];
  }

  private peekNext(): string {
    if (this.position + 1 >= this.input.length) return '';
    return this.input[this.position + 1];
  }

  private advance(): string {
    const char = this.peek();
    this.position++;
    if (char === '\n') {
      this.line++;
      this.column = 1;
    } else {
      this.column++;
    }
    return char;
  }

  private isAlpha(char: string): boolean {
    return /[a-zA-Z_]/.test(char);
  }

  private isDigit(char: string): boolean {
    return /[0-9]/.test(char);
  }

  private isAlphaNumeric(char: string): boolean {
    return this.isAlpha(char) || this.isDigit(char);
  }

  public tokenize(): Token[] {
    const tokens: Token[] = [];

    while (this.position < this.input.length) {
      const char = this.peek();

      // Skip whitespace
      if (/\s/.test(char)) {
        this.advance();
        continue;
      }

      // Skip single line comments
      if (char === '/' && this.peekNext() === '/') {
        // Read until end of line
        while (this.peek() !== '\n' && this.position < this.input.length) {
          this.advance();
        }
        continue;
      }

      const tokenLine = this.line;
      const tokenColumn = this.column;

      // Group Operators and Punctuation
      switch (char) {
        case '+':
          this.advance();
          tokens.push({ type: 'PLUS', value: '+', line: tokenLine, column: tokenColumn });
          break;
        case '-':
          this.advance();
          tokens.push({ type: 'MINUS', value: '-', line: tokenLine, column: tokenColumn });
          break;
        case '*':
          this.advance();
          tokens.push({ type: 'STAR', value: '*', line: tokenLine, column: tokenColumn });
          break;
        case '/':
          this.advance();
          tokens.push({ type: 'SLASH', value: '/', line: tokenLine, column: tokenColumn });
          break;
        case '%':
          this.advance();
          tokens.push({ type: 'MODULO', value: '%', line: tokenLine, column: tokenColumn });
          break;
        case ';':
          this.advance();
          tokens.push({ type: 'SEMICOLON', value: ';', line: tokenLine, column: tokenColumn });
          break;
        case ',':
          this.advance();
          tokens.push({ type: 'COMMA', value: ',', line: tokenLine, column: tokenColumn });
          break;
        case '(':
          this.advance();
          tokens.push({ type: 'LPAREN', value: '(', line: tokenLine, column: tokenColumn });
          break;
        case ')':
          this.advance();
          tokens.push({ type: 'RPAREN', value: ')', line: tokenLine, column: tokenColumn });
          break;
        case '{':
          this.advance();
          tokens.push({ type: 'LBRACE', value: '{', line: tokenLine, column: tokenColumn });
          break;
        case '}':
          this.advance();
          tokens.push({ type: 'RBRACE', value: '}', line: tokenLine, column: tokenColumn });
          break;
        case '=':
          this.advance();
          if (this.peek() === '=') {
            this.advance();
            tokens.push({ type: 'EQ', value: '==', line: tokenLine, column: tokenColumn });
          } else {
            tokens.push({ type: 'ASSIGN', value: '=', line: tokenLine, column: tokenColumn });
          }
          break;
        case '!':
          this.advance();
          if (this.peek() === '=') {
            this.advance();
            tokens.push({ type: 'NEQ', value: '!=', line: tokenLine, column: tokenColumn });
          } else {
            tokens.push({ type: 'ERROR', value: '!', line: tokenLine, column: tokenColumn });
          }
          break;
        case '<':
          this.advance();
          if (this.peek() === '=') {
            this.advance();
            tokens.push({ type: 'LTE', value: '<=', line: tokenLine, column: tokenColumn });
          } else {
            tokens.push({ type: 'LT', value: '<', line: tokenLine, column: tokenColumn });
          }
          break;
        case '>':
          this.advance();
          if (this.peek() === '=') {
            this.advance();
            tokens.push({ type: 'GTE', value: '>=', line: tokenLine, column: tokenColumn });
          } else {
            tokens.push({ type: 'GT', value: '>', line: tokenLine, column: tokenColumn });
          }
          break;
        case '"':
        case "'": {
          const quote = this.advance();
          let value = '';
          while (this.peek() !== quote && this.position < this.input.length) {
            value += this.advance();
          }
          if (this.peek() === quote) {
            this.advance(); // consume closing quote
            tokens.push({ type: 'STRING', value, line: tokenLine, column: tokenColumn });
          } else {
            tokens.push({ type: 'ERROR', value: 'Unterminated string: ' + value, line: tokenLine, column: tokenColumn });
          }
          break;
        }
        default:
          if (this.isDigit(char)) {
            let numStr = '';
            while (this.isDigit(this.peek())) {
              numStr += this.advance();
            }
            if (this.peek() === '.' && this.isDigit(this.peekNext())) {
              numStr += this.advance(); // consume '.'
              while (this.isDigit(this.peek())) {
                numStr += this.advance();
              }
            }
            tokens.push({ type: 'NUMBER', value: numStr, line: tokenLine, column: tokenColumn });
          } else if (this.isAlpha(char)) {
            let identStr = '';
            while (this.isAlphaNumeric(this.peek())) {
              identStr += this.advance();
            }
            const type = KEYWORDS[identStr] || 'IDENTIFIER';
            tokens.push({ type, value: identStr, line: tokenLine, column: tokenColumn });
          } else {
            this.advance();
            tokens.push({ type: 'ERROR', value: `Unknown character: ${char}`, line: tokenLine, column: tokenColumn });
          }
          break;
      }
    }

    tokens.push({ type: 'EOF', value: '', line: this.line, column: this.column });
    return tokens;
  }
}
