import { V as resolvePluginProviders } from "./send-C3_deGKY.js";
import { d as fetchWithTimeout } from "./fetch-BiG0XwdQ.js";
import { u as ensureModelAllowlistEntry } from "./auth-choice.apply-helpers-Dxie5QeC.js";
import { Gt as ZAI_CODING_CN_BASE_URL, Kt as ZAI_CODING_GLOBAL_BASE_URL, Wt as ZAI_CN_BASE_URL, f as applyAgentDefaultPrimaryModel, qt as ZAI_GLOBAL_BASE_URL } from "./provider-auth-helpers-Wuo5EfrP.js";
import { r as resolveProviderPluginChoice } from "./provider-wizard-CoOQ_6t0.js";
//#region src/commands/google-gemini-model-default.ts
const GOOGLE_GEMINI_DEFAULT_MODEL = "google/gemini-3.1-pro-preview";
function applyGoogleGeminiModelDefault(cfg) {
	return applyAgentDefaultPrimaryModel({
		cfg,
		model: GOOGLE_GEMINI_DEFAULT_MODEL
	});
}
//#endregion
//#region src/commands/zai-endpoint-detect.ts
async function probeZaiChatCompletions(params) {
	try {
		const res = await fetchWithTimeout(`${params.baseUrl}/chat/completions`, {
			method: "POST",
			headers: {
				authorization: `Bearer ${params.apiKey}`,
				"content-type": "application/json"
			},
			body: JSON.stringify({
				model: params.modelId,
				stream: false,
				max_tokens: 1,
				messages: [{
					role: "user",
					content: "ping"
				}]
			})
		}, params.timeoutMs, params.fetchFn);
		if (res.ok) return { ok: true };
		let errorCode;
		let errorMessage;
		try {
			const json = await res.json();
			const code = json?.error?.code;
			const msg = json?.error?.message ?? json?.msg ?? json?.message;
			if (typeof code === "string") errorCode = code;
			else if (typeof code === "number") errorCode = String(code);
			if (typeof msg === "string") errorMessage = msg;
		} catch {}
		return {
			ok: false,
			status: res.status,
			errorCode,
			errorMessage
		};
	} catch {
		return { ok: false };
	}
}
async function detectZaiEndpoint(params) {
	if (process.env.VITEST && !params.fetchFn) return null;
	const timeoutMs = params.timeoutMs ?? 5e3;
	const probeCandidates = (() => {
		const general = [{
			endpoint: "global",
			baseUrl: ZAI_GLOBAL_BASE_URL,
			modelId: "glm-5",
			note: "Verified GLM-5 on global endpoint."
		}, {
			endpoint: "cn",
			baseUrl: ZAI_CN_BASE_URL,
			modelId: "glm-5",
			note: "Verified GLM-5 on cn endpoint."
		}];
		const codingGlm5 = [{
			endpoint: "coding-global",
			baseUrl: ZAI_CODING_GLOBAL_BASE_URL,
			modelId: "glm-5",
			note: "Verified GLM-5 on coding-global endpoint."
		}, {
			endpoint: "coding-cn",
			baseUrl: ZAI_CODING_CN_BASE_URL,
			modelId: "glm-5",
			note: "Verified GLM-5 on coding-cn endpoint."
		}];
		const codingFallback = [{
			endpoint: "coding-global",
			baseUrl: ZAI_CODING_GLOBAL_BASE_URL,
			modelId: "glm-4.7",
			note: "Coding Plan endpoint verified, but this key/plan does not expose GLM-5 there. Defaulting to GLM-4.7."
		}, {
			endpoint: "coding-cn",
			baseUrl: ZAI_CODING_CN_BASE_URL,
			modelId: "glm-4.7",
			note: "Coding Plan CN endpoint verified, but this key/plan does not expose GLM-5 there. Defaulting to GLM-4.7."
		}];
		switch (params.endpoint) {
			case "global": return general.filter((candidate) => candidate.endpoint === "global");
			case "cn": return general.filter((candidate) => candidate.endpoint === "cn");
			case "coding-global": return [...codingGlm5.filter((candidate) => candidate.endpoint === "coding-global"), ...codingFallback.filter((candidate) => candidate.endpoint === "coding-global")];
			case "coding-cn": return [...codingGlm5.filter((candidate) => candidate.endpoint === "coding-cn"), ...codingFallback.filter((candidate) => candidate.endpoint === "coding-cn")];
			default: return [
				...general,
				...codingGlm5,
				...codingFallback
			];
		}
	})();
	for (const candidate of probeCandidates) if ((await probeZaiChatCompletions({
		baseUrl: candidate.baseUrl,
		apiKey: params.apiKey,
		modelId: candidate.modelId,
		timeoutMs,
		fetchFn: params.fetchFn
	})).ok) return candidate;
	return null;
}
//#endregion
//#region src/commands/openai-model-default.ts
const OPENAI_DEFAULT_MODEL = "openai/gpt-5.1-codex";
function applyOpenAIProviderConfig(cfg) {
	const next = ensureModelAllowlistEntry({
		cfg,
		modelRef: OPENAI_DEFAULT_MODEL
	});
	const models = { ...next.agents?.defaults?.models };
	models[OPENAI_DEFAULT_MODEL] = {
		...models[OPENAI_DEFAULT_MODEL],
		alias: models["openai/gpt-5.1-codex"]?.alias ?? "GPT"
	};
	return {
		...next,
		agents: {
			...next.agents,
			defaults: {
				...next.agents?.defaults,
				models
			}
		}
	};
}
function applyOpenAIConfig(cfg) {
	const next = applyOpenAIProviderConfig(cfg);
	return {
		...next,
		agents: {
			...next.agents,
			defaults: {
				...next.agents?.defaults,
				model: next.agents?.defaults?.model && typeof next.agents.defaults.model === "object" ? {
					...next.agents.defaults.model,
					primary: OPENAI_DEFAULT_MODEL
				} : { primary: OPENAI_DEFAULT_MODEL }
			}
		}
	};
}
//#endregion
//#region src/commands/auth-choice.preferred-provider.ts
const PREFERRED_PROVIDER_BY_AUTH_CHOICE = {
	oauth: "anthropic",
	"setup-token": "anthropic",
	"claude-cli": "anthropic",
	token: "anthropic",
	apiKey: "anthropic",
	"openai-codex": "openai-codex",
	"codex-cli": "openai-codex",
	chutes: "chutes",
	"openai-api-key": "openai",
	"openrouter-api-key": "openrouter",
	"kilocode-api-key": "kilocode",
	"ai-gateway-api-key": "vercel-ai-gateway",
	"cloudflare-ai-gateway-api-key": "cloudflare-ai-gateway",
	"moonshot-api-key": "moonshot",
	"moonshot-api-key-cn": "moonshot",
	"kimi-code-api-key": "kimi-coding",
	"gemini-api-key": "google",
	"google-gemini-cli": "google-gemini-cli",
	"mistral-api-key": "mistral",
	ollama: "ollama",
	sglang: "sglang",
	"zai-api-key": "zai",
	"zai-coding-global": "zai",
	"zai-coding-cn": "zai",
	"zai-global": "zai",
	"zai-cn": "zai",
	"xiaomi-api-key": "xiaomi",
	"synthetic-api-key": "synthetic",
	"venice-api-key": "venice",
	"together-api-key": "together",
	"huggingface-api-key": "huggingface",
	"github-copilot": "github-copilot",
	"copilot-proxy": "copilot-proxy",
	"minimax-global-oauth": "minimax-portal",
	"minimax-global-api": "minimax",
	"minimax-cn-oauth": "minimax-portal",
	"minimax-cn-api": "minimax",
	"opencode-zen": "opencode",
	"opencode-go": "opencode-go",
	"xai-api-key": "xai",
	"litellm-api-key": "litellm",
	"qwen-portal": "qwen-portal",
	"volcengine-api-key": "volcengine",
	"byteplus-api-key": "byteplus",
	"qianfan-api-key": "qianfan",
	"custom-api-key": "custom",
	vllm: "vllm"
};
function resolvePreferredProviderForAuthChoice(params) {
	const preferred = PREFERRED_PROVIDER_BY_AUTH_CHOICE[params.choice];
	if (preferred) return preferred;
	return resolveProviderPluginChoice({
		providers: resolvePluginProviders({
			config: params.config,
			workspaceDir: params.workspaceDir,
			env: params.env
		}),
		choice: params.choice
	})?.provider.id;
}
//#endregion
export { detectZaiEndpoint as a, applyOpenAIProviderConfig as i, OPENAI_DEFAULT_MODEL as n, GOOGLE_GEMINI_DEFAULT_MODEL as o, applyOpenAIConfig as r, applyGoogleGeminiModelDefault as s, resolvePreferredProviderForAuthChoice as t };
