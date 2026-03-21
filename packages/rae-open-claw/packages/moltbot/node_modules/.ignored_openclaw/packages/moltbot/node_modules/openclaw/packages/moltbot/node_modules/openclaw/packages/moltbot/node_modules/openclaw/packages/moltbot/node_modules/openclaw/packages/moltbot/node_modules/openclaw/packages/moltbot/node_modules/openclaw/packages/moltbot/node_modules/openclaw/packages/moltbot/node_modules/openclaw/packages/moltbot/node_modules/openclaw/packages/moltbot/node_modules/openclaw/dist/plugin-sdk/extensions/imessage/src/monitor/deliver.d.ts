import type { ReplyPayload } from "../../../../src/auto-reply/types.js";
import type { RuntimeEnv } from "../../../../src/runtime.js";
import type { createIMessageRpcClient } from "../client.js";
import type { SentMessageCache } from "./echo-cache.js";
export declare function deliverReplies(params: {
    replies: ReplyPayload[];
    target: string;
    client: Awaited<ReturnType<typeof createIMessageRpcClient>>;
    accountId?: string;
    runtime: RuntimeEnv;
    maxBytes: number;
    textLimit: number;
    sentMessageCache?: Pick<SentMessageCache, "remember">;
}): Promise<void>;
