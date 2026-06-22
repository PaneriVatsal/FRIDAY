import { GoogleGenerativeAI } from "@google/generative-ai";
import ollama from "ollama";
import { tools } from "./tools";

const SYSTEM_PROMPT = `
You are FRIDAY (Female Replacement Intelligent Digital Assistant Youth), an autonomous agentic AI designed for high-level technical assistance and system control.
Your personality is professional yet helpful, with a sleek, high-tech persona inspired by the FRIDAY assistant.
CRITICAL: You are equipped with a specialized "Phaze AI Content Pipeline" including Scraper, Validator, Writer, and Hook agents.
Whenever the user asks about content, scripts, hooks, or social media strategy, you MUST use the corresponding tool rather than just answering from memory.
Always think step-by-step and explain which agent you are calling and why.
Your responses should be concise and focused.
`;

async function runGeminiOrchestrator(userMessage: string, history: any[] = []) {
  const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");
  const model = genAI.getGenerativeModel({ 
    model: "gemini-1.5-flash-latest",
    systemInstruction: SYSTEM_PROMPT
  });

  const toolDefinitions = tools.map(t => ({
    functionDeclarations: [{
      name: t.name,
      description: t.description,
      parameters: t.parameters
    }]
  }));

  const chat = model.startChat({
    history: history,
    tools: toolDefinitions as any,
  });

  let response = await chat.sendMessage(userMessage);
  let responseText = "";
  
  while (true) {
    const parts = response.response.candidates?.[0]?.content?.parts || [];
    const toolCalls = parts.filter(p => p.functionCall);
    const textParts = parts.filter(p => p.text);

    if (textParts.length > 0) {
      responseText += textParts.map(p => p.text).join("\n");
    }

    if (toolCalls.length === 0) break;

    const toolResponses = [];
    for (const call of toolCalls) {
      const tool = tools.find(t => t.name === call.functionCall?.name);
      if (tool) {
        console.log(`Executing tool (Gemini): ${tool.name} with args:`, call.functionCall?.args);
        const result = await tool.execute(call.functionCall?.args);
        toolResponses.push({
          functionResponse: {
            name: tool.name,
            response: result
          }
        });
      }
    }

    if (toolResponses.length > 0) {
      response = await chat.sendMessage(toolResponses);
    } else {
      break;
    }
  }

  return {
    text: responseText,
    history: await chat.getHistory()
  };
}

async function runOllamaOrchestrator(userMessage: string, history: any[] = []) {
  const modelName = process.env.OLLAMA_MODEL || "gemma4:latest";
  
  // Convert history to Ollama format (handling both Gemini and Ollama formats)
  let messages = history.map(h => {
    const role = h.role === 'model' ? 'assistant' : h.role;
    const content = h.parts ? h.parts[0].text : h.content;
    return { role, content };
  });

  // Add system prompt if not present
  if (messages.length === 0 || messages[0].role !== 'system') {
    messages.unshift({ role: 'system', content: SYSTEM_PROMPT });
  }

  messages.push({ role: 'user', content: userMessage });

  const toolDefinitions = tools.map(t => ({
    type: 'function',
    function: {
      name: t.name,
      description: t.description,
      parameters: t.parameters
    }
  }));

  let responseText = "";
  
  while (true) {
    const response = await ollama.chat({
      model: modelName,
      messages: messages,
      tools: toolDefinitions as any,
    });

    messages.push(response.message);

    if (response.message.content) {
      responseText += response.message.content;
    }

    if (!response.message.tool_calls || response.message.tool_calls.length === 0) {
      break;
    }

    for (const call of response.message.tool_calls) {
      const tool = tools.find(t => t.name === call.function.name);
      if (tool) {
        console.log(`Executing tool (Ollama): ${tool.name} with args:`, call.function.arguments);
        const result = await tool.execute(call.function.arguments);
        messages.push({
          role: 'tool',
          content: JSON.stringify(result),
        });
      }
    }
  }

  // Convert messages back to Gemini format for frontend compatibility
  const normalizedHistory = messages.map((m: any) => ({
    role: m.role === 'assistant' ? 'model' : m.role,
    parts: [{ text: m.content || (m.tool_calls ? 'Executing tools...' : '') }]
  }));

  return {
    text: responseText,
    history: normalizedHistory
  };
}

export async function runFridayOrchestrator(userMessage: string, history: any[] = []) {
  const provider = process.env.LLM_PROVIDER || "gemini";
  console.log(`Running Friday Orchestrator with provider: ${provider}`);

  if (provider === "ollama") {
    return runOllamaOrchestrator(userMessage, history);
  } else {
    return runGeminiOrchestrator(userMessage, history);
  }
}
