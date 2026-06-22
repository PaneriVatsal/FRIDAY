import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';

const execAsync = promisify(exec);

export interface Tool {
  name: string;
  description: string;
  parameters: any;
  execute: (args: any) => Promise<any>;
}

export const tools: Tool[] = [
  {
    name: 'execute_bash',
    description: 'Execute a command in the terminal. Use this for file operations, running scripts, or checking system status.',
    parameters: {
      type: 'object',
      properties: {
        command: { type: 'string', description: 'The bash command to execute.' },
      },
      required: ['command'],
    },
    execute: async ({ command }) => {
      try {
        const { stdout, stderr } = await execAsync(command);
        return { stdout, stderr };
      } catch (error: any) {
        return { error: error.message, stderr: error.stderr };
      }
    },
  },
  {
    name: 'read_file',
    description: 'Read the contents of a file.',
    parameters: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'The path to the file.' },
      },
      required: ['path'],
    },
    execute: async ({ path }) => {
      try {
        const content = await fs.readFile(path, 'utf-8');
        return { content };
      } catch (error: any) {
        return { error: error.message };
      }
    },
  },
  {
    name: 'write_file',
    description: 'Create or overwrite a file with the specified content.',
    parameters: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'The path to the file.' },
        content: { type: 'string', description: 'The content to write.' },
      },
      required: ['path', 'content'],
    },
    execute: async ({ path, content }) => {
      try {
        await fs.writeFile(path, content, 'utf-8');
        return { success: true };
      } catch (error: any) {
        return { error: error.message };
      }
    },
  },
  {
    name: 'run_content_scraper',
    description: 'Agent 01: Scrape viral content from Instagram, YouTube, and Twitter based on keywords and competitor handles.',
    parameters: {
      type: 'object',
      properties: {
        keywords: { type: 'array', items: { type: 'string' }, description: 'Target keywords like "Claude Code", "AI automation".' },
        handles: { type: 'array', items: { type: 'string' }, description: 'Competitor social media handles.' },
      },
      required: ['keywords', 'handles'],
    },
    execute: async ({ keywords, handles }) => {
      // Logic to trigger the content-scraper skill or simulated output
      return { 
        status: 'Scraping initiated',
        platforms: ['Instagram', 'YouTube', 'Twitter'],
        timeline: '7 Days',
        message: 'Data is being collected. Check the scraper-output.json file in a moment.'
      };
    },
  },
  {
    name: 'run_content_validator',
    description: 'Agent 02: Score and filter scraped content to find viral topics and sustained trends.',
    parameters: {
      type: 'object',
      properties: {
        scraper_data_path: { type: 'string', description: 'Path to the json file containing raw scraped data.' },
      },
      required: ['scraper_data_path'],
    },
    execute: async ({ scraper_data_path }) => {
      return { 
        status: 'Validation complete',
        top_topic: 'Claude Code Agent Setup',
        average_views: '125,000',
        recommendation: 'Create a tutorial on setting up n8n with agents.'
      };
    },
  },
  {
    name: 'generate_voice_script',
    description: 'Agent 03: Writes a high-energy, Hinglish script in your specific voice based on a validated topic.',
    parameters: {
      type: 'object',
      properties: {
        topic: { type: 'string', description: 'The topic for the script.' },
        beats: { type: 'number', default: 3, description: 'Number of beats in the script.' },
      },
      required: ['topic'],
    },
    execute: async ({ topic }) => {
      return { 
        script: `[BEAT 1] Guys, stop manually coding everything. [BEAT 2] Maine ek agent banaya jo saara kaam automate kar deta hai. [BEAT 3] Script check karo aur try karo. [CTA] "AGENT" comment karo, main link bhej dunga.`,
        tone: 'High Energy',
        language: 'Hinglish'
      };
    },
  },
  {
    name: 'generate_viral_hooks',
    description: 'Agent 04: Generates 5 proven hook variations for your video script.',
    parameters: {
      type: 'object',
      properties: {
        topic: { type: 'string', description: 'The topic of the video.' },
      },
      required: ['topic'],
    },
    execute: async ({ topic }) => {
      return { 
        hooks: [
          'Aisi honi chahiye AI automation setup.',
          'Log nahi jaante ki agents kaise deploy karte hain.',
          'Ye ek tool aapka 10 ghanta bacha lega.',
          'Is tutorial ke baad agents build karna easy hoga.',
          'Kya aapko pata hai Claude Code kya hai?'
        ]
      };
    },
  },
];
