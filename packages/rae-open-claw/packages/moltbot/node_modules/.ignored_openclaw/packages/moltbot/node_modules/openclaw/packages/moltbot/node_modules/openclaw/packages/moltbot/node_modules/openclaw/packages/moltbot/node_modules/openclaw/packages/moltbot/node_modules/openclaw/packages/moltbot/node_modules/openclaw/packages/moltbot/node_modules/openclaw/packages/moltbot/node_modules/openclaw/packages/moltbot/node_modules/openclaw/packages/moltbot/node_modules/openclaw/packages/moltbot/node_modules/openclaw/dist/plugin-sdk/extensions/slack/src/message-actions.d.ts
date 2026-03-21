import type { ChannelMessageActionName, ChannelToolSend } from "../../../src/channels/plugins/types.js";
import type { OpenClawConfig } from "../../../src/config/config.js";
export declare function listSlackMessageActions(cfg: OpenClawConfig): ChannelMessageActionName[];
export declare function extractSlackToolSend(args: Record<string, unknown>): ChannelToolSend | null;
