import { type Bot } from "grammy";
import { type ChunkMode } from "../../../../src/auto-reply/chunk.js";
import type { ReplyPayload } from "../../../../src/auto-reply/types.js";
import type { ReplyToMode } from "../../../../src/config/config.js";
import type { MarkdownTableMode } from "../../../../src/config/types.base.js";
import type { RuntimeEnv } from "../../../../src/runtime.js";
import { type TelegramThreadSpec } from "./helpers.js";
export declare function deliverReplies(params: {
    replies: ReplyPayload[];
    chatId: string;
    accountId?: string;
    sessionKeyForInternalHooks?: string;
    mirrorIsGroup?: boolean;
    mirrorGroupId?: string;
    token: string;
    runtime: RuntimeEnv;
    bot: Bot;
    mediaLocalRoots?: readonly string[];
    replyToMode: ReplyToMode;
    textLimit: number;
    thread?: TelegramThreadSpec | null;
    tableMode?: MarkdownTableMode;
    chunkMode?: ChunkMode;
    /** Callback invoked before sending a voice message to switch typing indicator. */
    onVoiceRecording?: () => Promise<void> | void;
    /** Controls whether link previews are shown. Default: true (previews enabled). */
    linkPreview?: boolean;
    /** Optional quote text for Telegram reply_parameters. */
    replyQuoteText?: string;
}): Promise<{
    delivered: boolean;
}>;
