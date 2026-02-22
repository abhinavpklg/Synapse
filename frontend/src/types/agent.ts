/**
 * Agent node type definitions.
 *
 * These types define the shape of agent nodes on the canvas,
 * including their configuration (prompt, provider, model) and
 * the pre-built agent type presets.
 */

/** Pre-built agent types with sensible defaults. */
export type AgentType =
  | "researcher"
  | "writer"
  | "critic"
  | "editor"
  | "coder"
  | "summarizer"
  | "custom";

/** Supported LLM providers. */
export type ProviderType =
  | "openai"
  | "anthropic"
  | "gemini"
  | "groq"
  | "deepseek"
  | "openrouter"
  | "custom";

/** Configuration data stored inside each agent node. */
export interface AgentNodeData {
  label: string;
  agentType: AgentType;
  systemPrompt: string;
  provider: ProviderType;
  model: string;
  temperature: number;
  maxTokens: number;
  mcpServers: string[];
  inputMapping: Record<string, string>;
}

/** Default system prompts for each agent type. */
export const AGENT_TYPE_DEFAULTS: Record<
  AgentType,
  { label: string; emoji: string; systemPrompt: string; description: string }
> = {
  researcher: {
    label: "Researcher",
    emoji: "🔍",
    systemPrompt:
      "You are a thorough researcher. Gather comprehensive information on the given topic. Cite sources when possible. Focus on accuracy and depth.",
    description: "Gathers and synthesizes information on a topic",
  },
  writer: {
    label: "Writer",
    emoji: "✍️",
    systemPrompt:
      "You are a skilled writer. Using the provided research and context, create well-structured, engaging content. Focus on clarity, flow, and readability.",
    description: "Drafts content from research and context",
  },
  critic: {
    label: "Critic",
    emoji: "🧐",
    systemPrompt:
      "You are a constructive critic. Review the provided content for accuracy, logical gaps, tone issues, and areas for improvement. Be specific and actionable in your feedback.",
    description: "Reviews content for quality and accuracy",
  },
  editor: {
    label: "Editor",
    emoji: "📝",
    systemPrompt:
      "You are a meticulous editor. Incorporate the provided feedback to improve the content. Fix grammar, improve clarity, strengthen arguments, and polish the final output.",
    description: "Polishes content based on feedback",
  },
  coder: {
    label: "Coder",
    emoji: "💻",
    systemPrompt:
      "You are an expert programmer. Write clean, well-documented code based on the requirements. Follow best practices, include error handling, and add comments explaining complex logic.",
    description: "Writes and reviews code",
  },
  summarizer: {
    label: "Summarizer",
    emoji: "📋",
    systemPrompt:
      "You are a concise summarizer. Distill the provided content into key points and a clear summary. Preserve the most important information while reducing length.",
    description: "Condenses content into key points",
  },
  custom: {
    label: "Custom Agent",
    emoji: "⚙️",
    systemPrompt: "",
    description: "A blank agent — configure your own prompt",
  },
};

/** Available models per provider. */
export const PROVIDER_MODELS: Record<ProviderType, { name: string; models: string[] }> = {
  openai: {
    name: "OpenAI",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini"],
  },
  anthropic: {
    name: "Anthropic",
    models: ["claude-sonnet-4-20250514", "claude-opus-4-5-20250929", "claude-haiku-4-5-20251001"],
  },
  gemini: {
    name: "Google Gemini",
    models: ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.5-flash"],
  },
  groq: {
    name: "Groq",
    models: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
  },
  deepseek: {
    name: "DeepSeek",
    models: ["deepseek-chat", "deepseek-reasoner"],
  },
  openrouter: {
    name: "OpenRouter",
    models: [],
  },
  custom: {
    name: "Custom",
    models: [],
  },
};