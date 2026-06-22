import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const { query, history } = await request.json();

    if (!query) {
      return NextResponse.json({ error: 'No query provided' }, { status: 400 });
    }

    const OLLAMA_URL = 'http://172.17.208.1:11434/v1/chat/completions';
    const VOICEBOX_URL = process.env.VOICEBOX_URL || 'http://127.0.0.1:17493';

    // 1. Call Ollama (The Brain)
    const ollamaRes = await fetch(OLLAMA_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'qwen2.5-coder:latest',
        messages: [
          { 
            role: 'system', 
            content: `You are Friday, Tony Stark's AI. Be calm, analytical, and proactive.
            PATHS: Use /mnt/c/Users/LP082W/ for Windows files.
            
            Always respond in JSON:
            {
              "reply": "Your response text here",
              "action": "shell command to run (optional)"
            }`
          },
          ...history.map((h: any) => ({ role: h.role, content: h.parts[0].text })),
          { role: 'user', content: query }
        ],
        response_format: { type: 'json_object' }
      }),
    });

    const data = await ollamaRes.json();
    const aiData = JSON.parse(data.choices[0].message.content);

    // 2. Execution (The Hands)
    if (aiData.action) {
      try {
        await execAsync(aiData.action);
      } catch (err) {
        console.error('Action failed:', err);
      }
    }

    // 3. TTS (The Voice) - Calling local Voicebox
    let audioData = null;
    try {
      const ttsRes = await fetch(`${VOICEBOX_URL}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: aiData.reply, voice_id: process.env.DEFAULT_VOICE_ID }),
      });
      if (ttsRes.ok) {
        const audioBlob = await ttsRes.blob();
        const buffer = await audioBlob.arrayBuffer();
        audioData = `data:audio/wav;base64,${Buffer.from(buffer).toString('base64')}`;
      }
    } catch (e) {
      console.warn('Voicebox not reachable, falling back to browser TTS');
    }

    return NextResponse.json({ 
      text: aiData.reply,
      history: [...history, { role: 'user', parts: [{ text: query }] }, { role: 'model', parts: [{ text: aiData.reply }] }],
      audio: audioData
    });

  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
