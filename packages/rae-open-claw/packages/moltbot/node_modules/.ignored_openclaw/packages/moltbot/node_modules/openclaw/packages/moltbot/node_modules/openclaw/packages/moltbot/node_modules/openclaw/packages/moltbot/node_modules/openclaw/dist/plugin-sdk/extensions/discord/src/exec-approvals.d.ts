import type { ReplyPayload } from "../../../src/auto-reply/types.js";
import type { OpenClawConfig } from "../../../src/config/config.js";
export declare function isDiscordExecApprovalClientEnabled(params: {
    cfg: OpenClawConfig;
    accountId?: string | null;
}): boolean;
export declare function shouldSuppressLocalDiscordExecApprovalPrompt(params: {
    cfg: OpenClawConfig;
    accountId?: string | null;
    payload: ReplyPayload;
}): boolean;
