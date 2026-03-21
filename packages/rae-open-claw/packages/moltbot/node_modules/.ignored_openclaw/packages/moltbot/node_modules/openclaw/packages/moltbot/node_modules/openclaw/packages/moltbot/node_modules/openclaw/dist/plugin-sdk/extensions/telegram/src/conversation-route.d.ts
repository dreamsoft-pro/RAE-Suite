import { resolveConfiguredAcpRoute } from "../../../src/acp/persistent-bindings.route.js";
import type { OpenClawConfig } from "../../../src/config/config.js";
import { resolveAgentRoute } from "../../../src/routing/resolve-route.js";
export declare function resolveTelegramConversationRoute(params: {
    cfg: OpenClawConfig;
    accountId: string;
    chatId: number | string;
    isGroup: boolean;
    resolvedThreadId?: number;
    replyThreadId?: number;
    senderId?: string | number | null;
    topicAgentId?: string | null;
}): {
    route: ReturnType<typeof resolveAgentRoute>;
    configuredBinding: ReturnType<typeof resolveConfiguredAcpRoute>["configuredBinding"];
    configuredBindingSessionKey: string;
};
