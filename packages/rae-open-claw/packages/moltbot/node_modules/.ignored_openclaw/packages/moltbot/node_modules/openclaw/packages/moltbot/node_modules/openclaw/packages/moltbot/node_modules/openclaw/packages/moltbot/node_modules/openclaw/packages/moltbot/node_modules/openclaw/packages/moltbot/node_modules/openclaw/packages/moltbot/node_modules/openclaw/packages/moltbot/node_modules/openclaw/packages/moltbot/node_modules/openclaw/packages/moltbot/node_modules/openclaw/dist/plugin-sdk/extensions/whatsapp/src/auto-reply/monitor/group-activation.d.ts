import type { loadConfig } from "../../../../../src/config/config.js";
export declare function resolveGroupPolicyFor(cfg: ReturnType<typeof loadConfig>, conversationId: string): import("../../../../../src/config/group-policy.js").ChannelGroupPolicy;
export declare function resolveGroupRequireMentionFor(cfg: ReturnType<typeof loadConfig>, conversationId: string): boolean;
export declare function resolveGroupActivationFor(params: {
    cfg: ReturnType<typeof loadConfig>;
    agentId: string;
    sessionKey: string;
    conversationId: string;
}): import("../../../../../src/auto-reply/group-activation.js").GroupActivationMode;
