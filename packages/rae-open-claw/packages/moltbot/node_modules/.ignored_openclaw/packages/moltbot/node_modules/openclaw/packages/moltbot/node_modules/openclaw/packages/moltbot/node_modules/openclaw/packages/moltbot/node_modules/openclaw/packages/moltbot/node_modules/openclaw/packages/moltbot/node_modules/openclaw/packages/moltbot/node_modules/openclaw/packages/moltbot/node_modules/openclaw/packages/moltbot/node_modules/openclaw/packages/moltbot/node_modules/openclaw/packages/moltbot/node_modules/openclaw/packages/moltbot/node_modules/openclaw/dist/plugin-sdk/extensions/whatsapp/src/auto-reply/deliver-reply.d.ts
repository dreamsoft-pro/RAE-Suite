import { type ChunkMode } from "../../../../src/auto-reply/chunk.js";
import type { ReplyPayload } from "../../../../src/auto-reply/types.js";
import type { MarkdownTableMode } from "../../../../src/config/types.base.js";
import type { WebInboundMsg } from "./types.js";
export declare function deliverWebReply(params: {
    replyResult: ReplyPayload;
    msg: WebInboundMsg;
    mediaLocalRoots?: readonly string[];
    maxMediaBytes: number;
    textLimit: number;
    chunkMode?: ChunkMode;
    replyLogger: {
        info: (obj: unknown, msg: string) => void;
        warn: (obj: unknown, msg: string) => void;
    };
    connectionId?: string;
    skipLog?: boolean;
    tableMode?: MarkdownTableMode;
}): Promise<void>;
