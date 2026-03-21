import type { OpenClawConfig } from "../../../src/config/config.js";
export declare function resolveDiscordDraftStreamingChunking(cfg: OpenClawConfig | undefined, accountId?: string | null): {
    minChars: number;
    maxChars: number;
    breakPreference: "paragraph" | "newline" | "sentence";
};
