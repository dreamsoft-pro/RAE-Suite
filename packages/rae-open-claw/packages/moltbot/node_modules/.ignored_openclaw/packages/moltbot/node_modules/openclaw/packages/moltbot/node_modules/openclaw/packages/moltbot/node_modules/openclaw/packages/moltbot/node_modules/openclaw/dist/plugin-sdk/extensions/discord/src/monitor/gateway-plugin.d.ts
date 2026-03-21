import { GatewayPlugin } from "@buape/carbon/gateway";
import type { DiscordAccountConfig } from "../../../../src/config/types.js";
import type { RuntimeEnv } from "../../../../src/runtime.js";
export declare function resolveDiscordGatewayIntents(intentsConfig?: import("../../../../src/config/types.discord.js").DiscordIntentsConfig): number;
export declare function createDiscordGatewayPlugin(params: {
    discordConfig: DiscordAccountConfig;
    runtime: RuntimeEnv;
}): GatewayPlugin;
