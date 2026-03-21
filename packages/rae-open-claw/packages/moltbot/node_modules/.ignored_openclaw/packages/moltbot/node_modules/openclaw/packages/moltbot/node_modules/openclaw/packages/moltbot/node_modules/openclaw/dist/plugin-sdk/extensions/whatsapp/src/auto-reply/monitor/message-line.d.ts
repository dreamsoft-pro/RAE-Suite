import { type EnvelopeFormatOptions } from "../../../../../src/auto-reply/envelope.js";
import type { loadConfig } from "../../../../../src/config/config.js";
import type { WebInboundMsg } from "../types.js";
export declare function formatReplyContext(msg: WebInboundMsg): string | null;
export declare function buildInboundLine(params: {
    cfg: ReturnType<typeof loadConfig>;
    msg: WebInboundMsg;
    agentId: string;
    previousTimestamp?: number;
    envelope?: EnvelopeFormatOptions;
}): string;
