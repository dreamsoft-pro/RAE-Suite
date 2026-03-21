import type { DiscordGuildEntry } from "../../../../src/config/types.discord.js";
import type { RuntimeEnv } from "../../../../src/runtime.js";
type GuildEntries = Record<string, DiscordGuildEntry>;
export declare function resolveDiscordAllowlistConfig(params: {
    token: string;
    guildEntries: unknown;
    allowFrom: unknown;
    fetcher: typeof fetch;
    runtime: RuntimeEnv;
}): Promise<{
    guildEntries: GuildEntries | undefined;
    allowFrom: string[] | undefined;
}>;
export {};
