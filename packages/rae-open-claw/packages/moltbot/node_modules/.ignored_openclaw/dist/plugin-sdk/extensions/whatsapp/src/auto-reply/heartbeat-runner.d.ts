import { getReplyFromConfig } from "../../../../src/auto-reply/reply.js";
import { loadConfig } from "../../../../src/config/config.js";
import { sendMessageWhatsApp } from "../send.js";
export declare function runWebHeartbeatOnce(opts: {
    cfg?: ReturnType<typeof loadConfig>;
    to: string;
    verbose?: boolean;
    replyResolver?: typeof getReplyFromConfig;
    sender?: typeof sendMessageWhatsApp;
    sessionId?: string;
    overrideBody?: string;
    dryRun?: boolean;
}): Promise<void>;
export declare function resolveHeartbeatRecipients(cfg: ReturnType<typeof loadConfig>, opts?: {
    to?: string;
    all?: boolean;
}): {
    recipients: string[];
    source: string;
};
