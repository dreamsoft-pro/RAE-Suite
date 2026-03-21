import type { OpenClawConfig } from "../../../src/config/config.js";
import type { TelegramInlineButtonsScope } from "../../../src/config/types.telegram.js";
export declare function resolveTelegramInlineButtonsScope(params: {
    cfg: OpenClawConfig;
    accountId?: string | null;
}): TelegramInlineButtonsScope;
export declare function isTelegramInlineButtonsEnabled(params: {
    cfg: OpenClawConfig;
    accountId?: string | null;
}): boolean;
export { resolveTelegramTargetChatType } from "./targets.js";
