import type { loadConfig } from "../../../../src/config/config.js";
export declare function getSessionSnapshot(cfg: ReturnType<typeof loadConfig>, from: string, _isHeartbeat?: boolean, ctx?: {
    sessionKey?: string | null;
    isGroup?: boolean;
    messageThreadId?: string | number | null;
    threadLabel?: string | null;
    threadStarterBody?: string | null;
    parentSessionKey?: string | null;
}): {
    key: string;
    entry: import("../../../../src/config/sessions.js").SessionEntry;
    fresh: boolean;
    resetPolicy: import("../../../../src/config/sessions.js").SessionResetPolicy;
    resetType: import("../../../../src/config/sessions.js").SessionResetType;
    dailyResetAt: number | undefined;
    idleExpiresAt: number | undefined;
};
