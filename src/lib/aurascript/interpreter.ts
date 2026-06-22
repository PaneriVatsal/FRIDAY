import { ASTNode, Program, VarDecl, Assign, IfStatement, RepeatStatement, WhileStatement, ExpressionStatement, BinaryExpression, Literal, Identifier, CallExpression } from './types';

export interface ExecutionStep {
  line: number;
  variables: Record<string, any>;
  action?: {
    type: 'move' | 'turn' | 'color' | 'width' | 'circle' | 'rect' | 'clear' | 'goto' | 'print';
    args: any[];
  };
}

export class Environment {
  private values: Map<string, any> = new Map();
  private parent: Environment | null = null;

  constructor(parent: Environment | null = null) {
    this.parent = parent;
  }

  public define(name: string, value: any) {
    this.values.set(name, value);
  }

  public get(name: string, line: number): any {
    if (this.values.has(name)) {
      return this.values.get(name);
    }
    if (this.parent) {
      return this.parent.get(name, line);
    }
    throw new Error(`[Line ${line}] Undefined variable '${name}'.`);
  }

  public assign(name: string, value: any, line: number) {
    if (this.values.has(name)) {
      this.values.set(name, value);
      return;
    }
    if (this.parent) {
      this.parent.assign(name, value, line);
      return;
    }
    throw new Error(`[Line ${line}] Undefined variable '${name}'.`);
  }

  public getAll(): Record<string, any> {
    const parentVars = this.parent ? this.parent.getAll() : {};
    const currentVars: Record<string, any> = {};
    this.values.forEach((value, key) => {
      currentVars[key] = value;
    });
    return { ...parentVars, ...currentVars };
  }
}

export class Interpreter {
  private program: Program;
  private environment: Environment;
  private steps: ExecutionStep[] = [];
  private logs: string[] = [];
  private stepLimit = 5000; // prevent infinite loops
  private stepCount = 0;

  constructor(program: Program) {
    this.program = program;
    this.environment = new Environment();
  }

  public run(): { steps: ExecutionStep[]; logs: string[]; error?: string } {
    this.steps = [];
    this.logs = [];
    this.stepCount = 0;
    this.environment = new Environment();

    try {
      this.evaluateBlock(this.program.body, this.environment);
      return { steps: this.steps, logs: this.logs };
    } catch (e: any) {
      return {
        steps: this.steps,
        logs: this.logs,
        error: e.message || 'Runtime execution error',
      };
    }
  }

  private evaluateBlock(statements: ASTNode[], env: Environment) {
    for (const statement of statements) {
      this.evaluate(statement, env);
    }
  }

  private evaluate(node: ASTNode, env: Environment): any {
    this.stepCount++;
    if (this.stepCount > this.stepLimit) {
      throw new Error(`Execution terminated: exceeded max step count (${this.stepLimit}). Check for infinite loops.`);
    }

    switch (node.type) {
      case 'Program':
        this.evaluateBlock(node.body, env);
        return null;

      case 'VarDecl': {
        const val = this.evaluate(node.value, env);
        env.define(node.name, val);
        this.logStep(node.line, env);
        return val;
      }

      case 'Assign': {
        const val = this.evaluate(node.value, env);
        env.assign(node.name, val, node.line);
        this.logStep(node.line, env);
        return val;
      }

      case 'ExpressionStatement':
        return this.evaluate(node.expression, env);

      case 'IfStatement': {
        const condition = this.evaluate(node.test, env);
        this.logStep(node.line, env);
        if (condition) {
          const ifEnv = new Environment(env);
          this.evaluateBlock(node.consequent, ifEnv);
        } else if (node.alternate) {
          const elseEnv = new Environment(env);
          this.evaluateBlock(node.alternate, elseEnv);
        }
        return null;
      }

      case 'RepeatStatement': {
        const count = this.evaluate(node.count, env);
        if (typeof count !== 'number' || count < 0) {
          throw new Error(`[Line ${node.line}] Repeat count must be a non-negative number.`);
        }
        this.logStep(node.line, env);
        for (let i = 0; i < count; i++) {
          const loopEnv = new Environment(env);
          this.evaluateBlock(node.body, loopEnv);
        }
        return null;
      }

      case 'WhileStatement': {
        this.logStep(node.line, env);
        let count = 0;
        while (true) {
          const condition = this.evaluate(node.test, env);
          if (!condition) break;

          count++;
          if (count > 2000) {
            throw new Error(`[Line ${node.line}] While loop exceeded 2000 iterations. Check for infinite loops.`);
          }

          const loopEnv = new Environment(env);
          this.evaluateBlock(node.body, loopEnv);
          this.logStep(node.line, env);
        }
        return null;
      }

      case 'BinaryExpression': {
        const left = this.evaluate(node.left, env);
        const right = this.evaluate(node.right, env);

        switch (node.operator) {
          case '+':
            return left + right;
          case '-':
            return left - right;
          case '*':
            return left * right;
          case '/':
            if (right === 0) throw new Error(`[Line ${node.line}] Division by zero.`);
            return left / right;
          case '%':
            return left % right;
          case '==':
            return left === right;
          case '!=':
            return left !== right;
          case '<':
            return left < right;
          case '>':
            return left > right;
          case '<=':
            return left <= right;
          case '>=':
            return left >= right;
          default:
            throw new Error(`[Line ${node.line}] Unknown operator: ${node.operator}`);
        }
      }

      case 'Literal':
        return node.value;

      case 'Identifier':
        return env.get(node.name, node.line);

      case 'CallExpression': {
        const args = node.args.map(arg => this.evaluate(arg, env));
        this.executeCall(node.callee, args, node.line, env);
        return null;
      }
    }
  }

  private executeCall(callee: string, args: any[], line: number, env: Environment) {
    const drawingFunctions = ['move', 'turn', 'color', 'width', 'circle', 'rect', 'clear', 'goto'];
    
    if (callee === 'print') {
      const output = args.join(' ');
      this.logs.push(output);
      this.steps.push({
        line,
        variables: env.getAll(),
        action: { type: 'print', args },
      });
      return;
    }

    if (drawingFunctions.includes(callee)) {
      // Validate drawing arguments
      if (callee === 'move' || callee === 'turn' || callee === 'width' || callee === 'circle') {
        if (args.length !== 1 || typeof args[0] !== 'number') {
          throw new Error(`[Line ${line}] Function '${callee}' expects 1 numeric argument.`);
        }
      }
      if (callee === 'color') {
        if (args.length !== 1 || typeof args[0] !== 'string') {
          throw new Error(`[Line ${line}] Function 'color' expects 1 string argument (e.g. "red" or "#ff00ff").`);
        }
      }
      if (callee === 'rect') {
        if (args.length !== 2 || typeof args[0] !== 'number' || typeof args[1] !== 'number') {
          throw new Error(`[Line ${line}] Function 'rect' expects 2 numeric arguments (width, height).`);
        }
      }
      if (callee === 'goto') {
        if (args.length !== 2 || typeof args[0] !== 'number' || typeof args[1] !== 'number') {
          throw new Error(`[Line ${line}] Function 'goto' expects 2 numeric arguments (x, y).`);
        }
      }

      this.steps.push({
        line,
        variables: env.getAll(),
        action: { type: callee as any, args },
      });
      return;
    }

    throw new Error(`[Line ${line}] Unknown function call '${callee}'.`);
  }

  private logStep(line: number, env: Environment) {
    this.steps.push({
      line,
      variables: env.getAll(),
    });
  }
}
