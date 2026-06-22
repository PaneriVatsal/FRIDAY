'use client';

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Terminal, Settings, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

export default function FridayUI() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [history, setHistory] = useState<any[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = true;

        recognitionRef.current.onresult = (event: any) => {
          const current = event.resultIndex;
          const transcriptValue = event.results[current][0].transcript;
          setTranscript(transcriptValue);

          if (event.results[current].isFinal) {
            processQuery(transcriptValue);
          }
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setTranscript('');
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const processQuery = async (query: string) => {
    setIsProcessing(true);
    try {
      const res = await fetch('/api/friday', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, history }),
      });
      const data = await res.json();
      setResponse(data.text);
      setHistory(data.history || []);
      
      if (data.audio) {
        // Convert base64 to blob for better browser compatibility
        const base64Data = data.audio.split(',')[1];
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        
        const audio = new Audio(url);
        audio.play()
          .then(() => {
            // Clean up the URL after playing starts
            setTimeout(() => URL.revokeObjectURL(url), 10000);
          })
          .catch(e => console.error('Audio playback error:', e));
      } else {
        speak(data.text);
      }
    } catch (error) {
      console.error('Error processing query:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const speak = (text: string) => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      
      if (voices.length > 0) {
        // Find a suitable female/system voice
        const preferredVoice = voices.find(v => 
          v.name.includes('Female') || 
          v.name.includes('Google') || 
          v.name.includes('Natural')
        );
        utterance.voice = preferredVoice || voices[0];
      }
      
      utterance.pitch = 1.1;
      utterance.rate = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-between p-8 bg-[#0a0014] text-white">
      {/* Header */}
      <div className="w-full flex justify-between items-center max-w-6xl">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-violet-500 rounded-full animate-pulse" />
          <span className="text-sm font-mono tracking-widest text-violet-400 uppercase">System: Online</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tighter text-white/90">FRIDAY</h1>
        <div className="flex gap-4 items-center">
          <Link href="/playground" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/30 text-xs text-violet-300 transition-colors font-semibold">
            <Terminal className="w-3.5 h-3.5" /> AuraScript Playground
          </Link>
          <Settings className="w-5 h-5 text-white/40 cursor-pointer hover:text-violet-400" />
        </div>
      </div>

      {/* Center Visualizer */}
      <div className="relative flex flex-col items-center gap-12">
        <div className="arc-reactor group cursor-pointer" onClick={toggleListening}>
          <div className="core-inner">
            <div className={`core-pulse ${isListening ? 'opacity-100' : 'opacity-30'}`} />
            <AnimatePresence>
              {isListening ? (
                <motion.div 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="wave-container"
                >
                  {[...Array(5)].map((_, i) => (
                    <div 
                      key={i} 
                      className="wave-bar" 
                      style={{ animationDelay: `${i * 0.1}s`, width: '4px' }} 
                    />
                  ))}
                </motion.div>
              ) : (
                <div className="text-violet-400/50 group-hover:text-violet-400 transition-colors">
                  <Mic className="w-12 h-12" />
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
        
        <div className="h-8 text-center">
          <p className="text-lg text-violet-300/80 italic font-light">
            {isListening ? transcript || "listening..." : transcript || "Click to speak"}
          </p>
        </div>
      </div>

      {/* Footer / Console */}
      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card flex flex-col gap-4">
          <div className="flex items-center gap-2 text-violet-400">
            <MessageSquare className="w-4 h-4" />
            <span className="text-xs uppercase font-bold">Responses</span>
          </div>
          <div className="h-32 overflow-y-auto text-sm text-white/70 leading-relaxed font-light">
            {isProcessing ? "Processing intelligence..." : response || "I'm ready for your command."}
          </div>
        </div>

        <div className="glass-card flex flex-col gap-4">
          <div className="flex items-center gap-2 text-violet-400">
            <Terminal className="w-4 h-4" />
            <span className="text-xs uppercase font-bold">Execution Logs</span>
          </div>
          <div className="h-32 overflow-y-auto font-mono text-[10px] text-white/40 space-y-1">
            {(history || []).slice(-4).map((msg: any, i: number) => (
              <div key={i} className="border-l border-violet-500/20 pl-2">
                [{msg.role?.toUpperCase()}] {typeof msg.parts?.[0]?.text === 'string' ? msg.parts[0].text.slice(0, 50) + '...' : 'Tool called'}
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
