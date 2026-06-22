export async function generateVoice(text: string) {
  const url = process.env.VOICEBOX_URL || 'http://127.0.0.1:17493';
  const voiceId = process.env.DEFAULT_VOICE_ID || 'da552f29-53ac-4fe6-9539-901c6a69cfbb';

  try {
    // 1. Start generation
    const response = await fetch(`${url}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        profile_id: voiceId,
        engine: 'kokoro'
      })
    });

    if (!response.ok) {
      throw new Error(`Voicebox generation failed: ${response.statusText}`);
    }

    const { id } = await response.json();

    // 2. Poll for completion
    let status = 'generating';
    let attempts = 0;
    const maxAttempts = 120; // 60 seconds max to account for system load

    while (status === 'generating' && attempts < maxAttempts) {
      await new Promise(r => setTimeout(r, 500));
      const histRes = await fetch(`${url}/history`);
      const history = await histRes.json();
      const item = history.items?.find((h: any) => h.id === id);
      if (item) {
        status = item.status;
      }
      attempts++;
    }

    if (status !== 'completed') {
      throw new Error(`Voice generation timed out or failed: ${status}`);
    }

    // 3. Fetch the actual audio data
    const audioRes = await fetch(`${url}/audio/${id}`);
    if (!audioRes.ok) {
      throw new Error(`Failed to fetch audio file: ${audioRes.statusText}`);
    }

    const arrayBuffer = await audioRes.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const base64 = buffer.toString('base64');
    return `data:audio/wav;base64,${base64}`;
  } catch (error) {
    console.error('Failed to generate voice:', error);
    return null;
  }
}
