'use client';

import { useState, useEffect, useRef } from 'react';
import { Lexer } from '@/lib/aurascript/lexer';
import { Parser } from '@/lib/aurascript/parser';
import { Interpreter, ExecutionStep } from '@/lib/aurascript/interpreter';
import { Token, ASTNode } from '@/lib/aurascript/types';
import { 
  Play, 
  Square, 
  ChevronRight, 
  Terminal as TerminalIcon, 
  Code, 
  Database, 
  Eye, 
  HelpCircle, 
  ArrowLeft, 
  RotateCcw, 
  Layers, 
  Cpu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

// Predefined Code Presets
const PRESETS = {
  glowingSpiral: `// AuraScript - Glowing Spiral
let size = 2;
color("#ff007f"); // Neon Pink
width(2);

repeat 120 {
  move(size);
  turn(45);
  size = size + 1.5;
  
  if (size > 60) {
    color("#00f0ff"); // Switch to Neon Cyan
  }
  if (size > 120) {
    color("#ffcc00"); // Switch to Neon Amber
  }
}`,
  flowerDesign: `// AuraScript - Flower Grid
width(2);
let count = 0;

repeat 36 {
  // Rainbow-ish colors using branches
  if (count < 12) {
    color("#ff0055");
  }
  if (count >= 12) {
    if (count < 24) {
      color("#00ffcc");
    }
  }
  if (count >= 24) {
    color("#ffff00");
  }

  // Draw a square leaf
  repeat 4 {
    move(60);
    turn(90);
  }
  
  turn(10);
  count = count + 1;
}`,
  starburst: `// AuraScript - Star Burst
width(1.5);
color("#a020f0"); // Purple

repeat 50 {
  move(120);
  turn(144);
  
  if (color == "#a020f0") {
    color("#00ff66");
  } else {
    color("#a020f0");
  }
}`,
  fibonacciFractal: `// AuraScript - Math & Movement
let a = 1;
let b = 1;
let temp = 0;
color("#ff5500");
width(2.5);

repeat 9 {
  print("Fibonacci number:", b);
  move(b * 3);
  turn(90);
  
  // Update variables
  temp = a + b;
  a = b;
  b = temp;
}`,
  customShapes: `// AuraScript - Triangles and Circles
color("#00ff66");
width(3);

// Draw a neon green triangle
repeat 3 {
  move(80);
  turn(120);
}

// Relocate without drawing
goto(0, -60);
color("#ff00bb");

// Draw circles
circle(30);
circle(50);
circle(70);
`
};

export default function Playground() {
  const [code, setCode] = useState(PRESETS.glowingSpiral);
  const [activePreset, setActivePreset] = useState<keyof typeof PRESETS>('glowingSpiral');
  
  // Interpreter & Execution State
  const [tokens, setTokens] = useState<Token[]>([]);
  const [ast, setAst] = useState<ASTNode | null>(null);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [executionSteps, setExecutionSteps] = useState<ExecutionStep[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  
  // Animation State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [playbackSpeed, setPlaybackSpeed] = useState(50); // ms per step
  const [highlightedLine, setHighlightedLine] = useState<number | null>(null);
  const [currentScope, setCurrentScope] = useState<Record<string, any>>({});
  
  // Debug Panels Tabs
  const [activeTab, setActiveTab] = useState<'console' | 'ast' | 'scope' | 'tokens'>('console');
  
  // Refs
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Trigger Lexer & Parser on code change
  useEffect(() => {
    try {
      const lexer = new Lexer(code);
      const scannedTokens = lexer.tokenize();
      setTokens(scannedTokens);

      const parser = new Parser(scannedTokens);
      const parsedAst = parser.parse();
      setAst(parsedAst);
      setParseErrors(parser.errors);
    } catch (err: any) {
      // Errors are already handled inside parser.errors, but catch syntax crashes
      setParseErrors([err.message || 'Syntax parsing error.']);
    }
  }, [code]);

  // Handle preset selection
  const selectPreset = (key: keyof typeof PRESETS) => {
    setActivePreset(key);
    setCode(PRESETS[key]);
    resetExecution();
  };

  // Compile & Interpreter
  const runProgram = (instant: boolean = false) => {
    resetExecution();
    
    // Scan & Parse
    const lexer = new Lexer(code);
    const scannedTokens = lexer.tokenize();
    const parser = new Parser(scannedTokens);
    
    let parsedAst: ASTNode | null = null;
    try {
      parsedAst = parser.parse();
      if (parser.errors.length > 0) {
        setParseErrors(parser.errors);
        setActiveTab('console');
        return;
      }
    } catch (err: any) {
      setParseErrors([err.message || 'Parsing error.']);
      setActiveTab('console');
      return;
    }

    // Interpret
    const interpreter = new Interpreter(parsedAst);
    const result = interpreter.run();
    
    setExecutionSteps(result.steps);
    setLogs(result.logs);
    setRuntimeError(result.error || null);

    if (result.error) {
      setActiveTab('console');
    }

    if (result.steps.length > 0) {
      if (instant) {
        // Draw entire program immediately
        setCurrentStepIndex(result.steps.length - 1);
        setIsPlaying(false);
      } else {
        // Start playing step-by-step
        setIsPlaying(true);
        setCurrentStepIndex(0);
      }
    }
  };

  // Reset Execution state
  const resetExecution = () => {
    stopPlayback();
    setExecutionSteps([]);
    setCurrentStepIndex(-1);
    setLogs([]);
    setRuntimeError(null);
    setHighlightedLine(null);
    setCurrentScope({});
    
    // Clear Canvas
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawGrid(canvas, ctx);
      }
    }
  };

  // Stop playback loop
  const stopPlayback = () => {
    setIsPlaying(false);
    if (animationTimerRef.current) {
      clearInterval(animationTimerRef.current);
      animationTimerRef.current = null;
    }
  };

  // Playback timer loop
  useEffect(() => {
    if (isPlaying && executionSteps.length > 0) {
      if (animationTimerRef.current) clearInterval(animationTimerRef.current);
      
      animationTimerRef.current = setInterval(() => {
        setCurrentStepIndex(prev => {
          if (prev >= executionSteps.length - 1) {
            stopPlayback();
            return prev;
          }
          return prev + 1;
        });
      }, playbackSpeed);
    }
    
    return () => {
      if (animationTimerRef.current) clearInterval(animationTimerRef.current);
    };
  }, [isPlaying, executionSteps, playbackSpeed]);

  // Update canvas, active line and variables whenever currentStepIndex changes
  useEffect(() => {
    if (currentStepIndex >= 0 && currentStepIndex < executionSteps.length) {
      const currentStep = executionSteps[currentStepIndex];
      setHighlightedLine(currentStep.line);
      setCurrentScope(currentStep.variables);
      
      // Render canvas state up to this step
      drawCanvasUpTo(currentStepIndex);
    } else {
      setHighlightedLine(null);
      setCurrentScope({});
    }
  }, [currentStepIndex, executionSteps]);

  // Canvas Grid Rendering helper
  const drawGrid = (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) => {
    ctx.strokeStyle = 'rgba(139, 92, 246, 0.05)';
    ctx.lineWidth = 1;
    
    // Draw horizontal lines
    const gridSpacing = 40;
    for (let y = 0; y < canvas.height; y += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
    // Draw vertical lines
    for (let x = 0; x < canvas.width; x += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }

    // Draw central axis lines
    ctx.strokeStyle = 'rgba(139, 92, 246, 0.15)';
    ctx.lineWidth = 1.5;
    
    ctx.beginPath();
    ctx.moveTo(0, canvas.height / 2);
    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();
  };

  // Redraw Canvas up to index 'stepIndex'
  const drawCanvasUpTo = (stepIndex: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear and Redraw background/grid
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGrid(canvas, ctx);

    // Initial Turtle State
    const startX = canvas.width / 2;
    const startY = canvas.height / 2;
    
    let x = startX;
    let y = startY;
    let angle = -90; // point upwards initially (standard turtle)
    let color = '#bc34fa'; // neon purple default
    let width = 2;

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Walk all steps up to stepIndex
    for (let i = 0; i <= stepIndex; i++) {
      const step = executionSteps[i];
      if (!step.action) continue;

      const { type, args } = step.action;

      if (type === 'move') {
        const dist = args[0] as number;
        const rad = (angle * Math.PI) / 180;
        const newX = x + dist * Math.cos(rad);
        const newY = y + dist * Math.sin(rad);

        // Drawing path
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(newX, newY);
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        
        // Add neon glow
        ctx.shadowBlur = 12;
        ctx.shadowColor = color;

        ctx.stroke();
        
        // Reset shadow for next operations
        ctx.shadowBlur = 0;

        x = newX;
        y = newY;
      } else if (type === 'turn') {
        const deg = args[0] as number;
        angle += deg;
      } else if (type === 'color') {
        color = args[0] as string;
      } else if (type === 'width') {
        width = args[0] as number;
      } else if (type === 'circle') {
        const radius = args[0] as number;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.shadowBlur = 10;
        ctx.shadowColor = color;
        ctx.stroke();
        ctx.shadowBlur = 0;
      } else if (type === 'rect') {
        const w = args[0] as number;
        const h = args[1] as number;
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.shadowBlur = 10;
        ctx.shadowColor = color;
        // Centered around turtle
        ctx.strokeRect(x - w / 2, y - h / 2, w, h);
        ctx.shadowBlur = 0;
      } else if (type === 'goto') {
        const targetX = args[0] as number;
        const targetY = args[1] as number;
        // Translate from our (0,0) center space to canvas pixel coordinate space
        x = startX + targetX;
        y = startY + targetY;
      } else if (type === 'clear') {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawGrid(canvas, ctx);
      }
    }

    // Render Turtle cursor
    drawTurtle(ctx, x, y, angle, color);
  };

  // Draw glowing visual turtle cursor
  const drawTurtle = (ctx: CanvasRenderingContext2D, x: number, y: number, angle: number, color: string) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate((angle * Math.PI) / 180);

    // Glowing Cursor Triangle
    ctx.beginPath();
    ctx.moveTo(12, 0);   // Tip pointing forward
    ctx.lineTo(-8, -8);  // Left wing
    ctx.lineTo(-4, 0);   // Center indentation
    ctx.lineTo(-8, 8);   // Right wing
    ctx.closePath();

    ctx.fillStyle = color;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1.5;
    ctx.shadowBlur = 15;
    ctx.shadowColor = color;

    ctx.fill();
    ctx.stroke();
    
    ctx.restore();
  };

  // Redraw initial empty grid on mount
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      // Set high resolution canvas
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (ctx) {
        drawGrid(canvas, ctx);
        drawTurtle(ctx, width / 2, height / 2, -90, '#bc34fa');
      }
    }
  }, []);

  // AST Visualizer Component (Recursive)
  const RenderAST = ({ node, label }: { node: any; label?: string }) => {
    const [isExpanded, setIsExpanded] = useState(true);

    if (!node || typeof node !== 'object') {
      return (
        <span className="text-amber-300 font-mono text-xs">{JSON.stringify(node)}</span>
      );
    }

    const keys = Object.keys(node).filter(k => k !== 'line');

    return (
      <div className="pl-4 border-l border-violet-500/10 my-0.5">
        <div 
          className="flex items-center gap-1.5 cursor-pointer hover:bg-white/5 py-0.5 px-1 rounded text-violet-300 select-none"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="text-[10px] text-white/30 font-bold">{isExpanded ? '▼' : '▶'}</span>
          <span className="text-xs font-mono font-semibold">
            {label ? `${label}: ` : ''}
            <span className="text-violet-400 font-bold">{node.type || 'Object'}</span>
          </span>
        </div>
        
        {isExpanded && (
          <div className="pl-3 mt-0.5 space-y-1">
            {keys.map(key => {
              const val = node[key];
              if (Array.isArray(val)) {
                return (
                  <div key={key} className="pl-2">
                    <span className="text-[11px] text-white/40 font-mono">{key}: [</span>
                    <div className="space-y-1">
                      {val.map((item, idx) => (
                        <RenderAST key={idx} node={item} label={`${idx}`} />
                      ))}
                    </div>
                    <span className="text-[11px] text-white/40 font-mono">]</span>
                  </div>
                );
              }
              return (
                <div key={key} className="flex flex-row items-baseline gap-1">
                  <span className="text-[11px] text-white/40 font-mono">{key}:</span>
                  <RenderAST node={val} />
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <main className="min-h-screen flex flex-col bg-[#05000b] text-white overflow-hidden font-sans">
      {/* Header */}
      <header className="border-b border-violet-950/40 bg-black/40 backdrop-blur-md px-6 py-4 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/">
            <button className="flex items-center gap-1.5 text-xs text-white/60 hover:text-violet-400 font-medium tracking-wide transition-colors">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to FRIDAY
            </button>
          </Link>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-violet-500 animate-pulse" />
            <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
              AuraScript Playground
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/40 font-mono mr-2">Presets:</span>
          <div className="flex bg-white/5 border border-white/10 p-0.5 rounded-lg text-xs">
            {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map(key => (
              <button
                key={key}
                onClick={() => selectPreset(key)}
                className={`px-3 py-1 rounded-md transition-colors ${
                  activePreset === key 
                    ? 'bg-violet-600/80 text-white shadow-sm font-semibold' 
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Workspace Workspace */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Panel: Editor & Instructions */}
        <div className="w-full md:w-[45%] flex flex-col border-r border-violet-950/40 bg-black/20 overflow-hidden shrink-0">
          
          {/* Action Bar */}
          <div className="px-4 py-3 border-b border-violet-950/40 flex items-center justify-between bg-black/40 shrink-0">
            <div className="flex gap-2">
              <button 
                onClick={() => runProgram(false)}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-medium text-xs shadow-lg shadow-violet-500/25 transition-all active:scale-95"
              >
                <Play className="w-3.5 h-3.5 fill-current" /> Animate Run
              </button>
              <button 
                onClick={() => runProgram(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white text-xs transition-colors"
              >
                <Cpu className="w-3.5 h-3.5 text-violet-400" /> Instant Draw
              </button>
              {isPlaying ? (
                <button 
                  onClick={stopPlayback}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/50 hover:bg-red-900/50 border border-red-500/30 text-red-300 text-xs transition-colors"
                >
                  <Square className="w-3.5 h-3.5 fill-current" /> Pause
                </button>
              ) : currentStepIndex >= 0 && currentStepIndex < executionSteps.length - 1 ? (
                <button 
                  onClick={() => setIsPlaying(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/50 hover:bg-emerald-900/50 border border-emerald-500/30 text-emerald-300 text-xs transition-colors"
                >
                  <Play className="w-3.5 h-3.5 fill-current" /> Resume
                </button>
              ) : null}
              <button 
                onClick={resetExecution}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white text-xs transition-colors"
                title="Reset Workspace"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Animation Speed Slider */}
            <div className="flex items-center gap-2 text-[10px] text-white/50">
              <span>Delay: {playbackSpeed}ms</span>
              <input 
                type="range" 
                min="5" 
                max="250" 
                step="5"
                value={playbackSpeed} 
                onChange={(e) => setPlaybackSpeed(parseInt(e.target.value))}
                className="w-16 h-1 rounded bg-violet-950/80 appearance-none cursor-pointer accent-violet-500"
              />
            </div>
          </div>

          {/* Code Editor Container */}
          <div className="flex-1 relative overflow-hidden font-mono flex">
            {/* Gutter / Line Numbers */}
            <div className="w-12 bg-[#080210] border-r border-violet-950/30 py-4 flex flex-col text-right pr-3 text-white/20 select-none text-xs leading-6">
              {code.split('\n').map((_, idx) => {
                const lineNum = idx + 1;
                const isCurrent = highlightedLine === lineNum;
                return (
                  <div 
                    key={idx} 
                    className={`transition-colors duration-100 ${
                      isCurrent 
                        ? 'text-violet-400 font-bold bg-violet-500/10 border-r-2 border-violet-500 pr-2.5' 
                        : ''
                    }`}
                  >
                    {lineNum}
                  </div>
                );
              })}
            </div>

            {/* Code Textarea */}
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="flex-1 bg-transparent text-white/90 p-4 border-0 outline-none focus:ring-0 resize-none font-mono text-xs leading-6 overflow-y-auto"
              spellCheck="false"
              placeholder="// Write your AuraScript code here..."
            />
          </div>

          {/* Quick Syntax Documentation Banner */}
          <div className="p-4 bg-[#080212] border-t border-violet-950/30 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 text-violet-400 text-xs">
              <HelpCircle className="w-4 h-4" />
              <span>Built-ins: <code>move(d)</code>, <code>turn(a)</code>, <code>color("hex")</code>, <code>width(w)</code>, <code>circle(r)</code>, <code>rect(w,h)</code>, <code>goto(x,y)</code></span>
            </div>
          </div>
        </div>

        {/* Right Panel: Canvas & Diagnostics */}
        <div className="flex-1 flex flex-col overflow-hidden">
          
          {/* Canvas Window (Visualizer) */}
          <div className="h-[55%] border-b border-violet-950/40 relative bg-black/60 overflow-hidden flex items-center justify-center">
            {/* Grid Coordinates Label */}
            <div className="absolute top-3 left-4 text-[10px] font-mono text-white/30 pointer-events-none uppercase tracking-wider">
              Viewport: 2D Canvas (0, 0 at center)
            </div>
            
            {/* Live Playback Step Pointer */}
            {currentStepIndex >= 0 && (
              <div className="absolute top-3 right-4 bg-violet-950/60 border border-violet-800/40 rounded px-2 py-0.5 text-[9px] font-mono text-violet-300">
                Step {currentStepIndex + 1} / {executionSteps.length}
              </div>
            )}

            <canvas 
              ref={canvasRef} 
              className="w-full h-full bg-transparent"
            />
          </div>

          {/* Diagnostics Panel (Tabs) */}
          <div className="flex-1 flex flex-col bg-[#05000c]/60 overflow-hidden">
            {/* Diagnostic Tabs */}
            <div className="flex border-b border-violet-950/40 bg-black/40 text-xs shrink-0 select-none">
              <button 
                onClick={() => setActiveTab('console')}
                className={`px-4 py-2.5 flex items-center gap-1.5 border-b-2 font-medium transition-colors ${
                  activeTab === 'console' 
                    ? 'border-violet-500 bg-white/5 text-white' 
                    : 'border-transparent text-white/40 hover:text-white/70'
                }`}
              >
                <TerminalIcon className="w-3.5 h-3.5 text-violet-400" /> Console Logs {(logs.length > 0 || parseErrors.length > 0 || runtimeError) && (
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                )}
              </button>
              <button 
                onClick={() => setActiveTab('ast')}
                className={`px-4 py-2.5 flex items-center gap-1.5 border-b-2 font-medium transition-colors ${
                  activeTab === 'ast' 
                    ? 'border-violet-500 bg-white/5 text-white' 
                    : 'border-transparent text-white/40 hover:text-white/70'
                }`}
              >
                <Layers className="w-3.5 h-3.5 text-violet-400" /> AST Tree
              </button>
              <button 
                onClick={() => setActiveTab('scope')}
                className={`px-4 py-2.5 flex items-center gap-1.5 border-b-2 font-medium transition-colors ${
                  activeTab === 'scope' 
                    ? 'border-violet-500 bg-white/5 text-white' 
                    : 'border-transparent text-white/40 hover:text-white/70'
                }`}
              >
                <Database className="w-3.5 h-3.5 text-violet-400" /> State Variables ({Object.keys(currentScope).length})
              </button>
              <button 
                onClick={() => setActiveTab('tokens')}
                className={`px-4 py-2.5 flex items-center gap-1.5 border-b-2 font-medium transition-colors ${
                  activeTab === 'tokens' 
                    ? 'border-violet-500 bg-white/5 text-white' 
                    : 'border-transparent text-white/40 hover:text-white/70'
                }`}
              >
                <Code className="w-3.5 h-3.5 text-violet-400" /> Lexer Tokens
              </button>
            </div>

            {/* Diagnostic Content */}
            <div className="flex-1 p-4 overflow-y-auto font-mono text-xs text-white/75 bg-black/20">
              
              {/* CONSOLE LOG TAB */}
              {activeTab === 'console' && (
                <div className="space-y-2">
                  {/* Parse Errors */}
                  {parseErrors.length > 0 && (
                    <div className="p-3 bg-red-950/40 border border-red-500/20 text-red-300 rounded-lg">
                      <div className="font-bold text-red-400 mb-1">Syntax Error:</div>
                      <ul className="list-disc pl-4 space-y-1">
                        {parseErrors.map((err, idx) => <li key={idx}>{err}</li>)}
                      </ul>
                    </div>
                  )}

                  {/* Runtime Error */}
                  {runtimeError && (
                    <div className="p-3 bg-red-950/40 border border-red-500/20 text-red-300 rounded-lg">
                      <div className="font-bold text-red-400 mb-1">Execution Crash:</div>
                      <div>{runtimeError}</div>
                    </div>
                  )}

                  {/* Output prints */}
                  <div className="space-y-1">
                    <div className="text-[10px] text-white/20 uppercase tracking-widest border-b border-white/5 pb-1 mb-2 font-sans font-bold">Standard Output</div>
                    {logs.length === 0 && !runtimeError && parseErrors.length === 0 ? (
                      <div className="text-white/30 italic">No output. Try using print("value") in your code!</div>
                    ) : (
                      logs.map((log, idx) => (
                        <div key={idx} className="flex gap-2 text-violet-200">
                          <span className="text-violet-500/40 select-none">&gt;</span>
                          <span>{log}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* AST TAB */}
              {activeTab === 'ast' && (
                <div>
                  <div className="text-[10px] text-white/20 uppercase tracking-widest border-b border-white/5 pb-1 mb-2 font-sans font-bold">Abstract Syntax Tree</div>
                  {ast ? (
                    <RenderAST node={ast} />
                  ) : (
                    <div className="text-white/30 italic">Syntax error or empty program.</div>
                  )}
                </div>
              )}

              {/* SCOPE (VARIABLES) TAB */}
              {activeTab === 'scope' && (
                <div className="space-y-2">
                  <div className="text-[10px] text-white/20 uppercase tracking-widest border-b border-white/5 pb-1 mb-2 font-sans font-bold">Local Variable Memory Store</div>
                  {Object.keys(currentScope).length === 0 ? (
                    <div className="text-white/30 italic">No active variables. (Run or animate step to inspect environment).</div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2 border border-white/5 rounded-lg overflow-hidden bg-black/40 max-w-md">
                      <div className="bg-white/5 px-3 py-1.5 font-sans font-bold text-white/50 text-[10px] border-b border-white/5">Identifier</div>
                      <div className="bg-white/5 px-3 py-1.5 font-sans font-bold text-white/50 text-[10px] border-b border-white/5">Current Value</div>
                      
                      {Object.entries(currentScope).map(([key, val]) => (
                        <>
                          <div key={`${key}-name`} className="px-3 py-1 text-violet-400 font-bold border-r border-white/5">{key}</div>
                          <div key={`${key}-value`} className="px-3 py-1 text-emerald-400 font-semibold">{JSON.stringify(val)}</div>
                        </>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* LEXER TOKENS TAB */}
              {activeTab === 'tokens' && (
                <div>
                  <div className="text-[10px] text-white/20 uppercase tracking-widest border-b border-white/5 pb-1 mb-2 font-sans font-bold">Lexical Scanner Tokens</div>
                  <div className="flex flex-wrap gap-1.5 max-h-60 overflow-y-auto">
                    {tokens.map((token, idx) => (
                      <span 
                        key={idx} 
                        className={`px-1.5 py-0.5 rounded text-[10px] border ${
                          token.type === 'ERROR' 
                            ? 'bg-red-950/40 border-red-500/30 text-red-300' 
                            : token.type === 'EOF'
                            ? 'bg-white/5 border-white/10 text-white/30'
                            : ['LET', 'IF', 'ELSE', 'REPEAT', 'WHILE'].includes(token.type)
                            ? 'bg-violet-950/50 border-violet-500/30 text-violet-300 font-bold'
                            : 'bg-white/5 border-white/5 text-white/60'
                        }`}
                        title={`Line ${token.line}, Col ${token.column}`}
                      >
                        {token.type}
                        {token.value ? `(${token.value})` : ''}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            </div>
          </div>

        </div>
      </div>
    </main>
  );
}
