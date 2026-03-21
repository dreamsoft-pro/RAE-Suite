import type { AgentToolResult } from "@mariozechner/pi-agent-core";
import type { TelegramInlineButtons } from "../../../extensions/telegram/src/button-types.js";
import type { OpenClawConfig } from "../../config/config.js";
export declare function readTelegramButtons(params: Record<string, unknown>): TelegramInlineButtons | undefined;
export declare function handleTelegramAction(params: Record<string, unknown>, cfg: OpenClawConfig, options?: {
    mediaLocalRoots?: readonly string[];
}): Promise<AgentToolResult<unknown>>;
