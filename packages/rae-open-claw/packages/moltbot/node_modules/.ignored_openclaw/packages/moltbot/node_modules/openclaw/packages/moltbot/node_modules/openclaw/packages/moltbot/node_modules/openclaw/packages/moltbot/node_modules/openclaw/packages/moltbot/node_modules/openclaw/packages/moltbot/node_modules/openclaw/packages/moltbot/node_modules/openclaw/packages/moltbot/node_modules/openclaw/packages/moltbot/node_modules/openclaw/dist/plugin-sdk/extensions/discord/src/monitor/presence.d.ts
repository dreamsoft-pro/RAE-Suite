import type { UpdatePresenceData } from "@buape/carbon/gateway";
import type { DiscordAccountConfig } from "../../../../src/config/config.js";
type DiscordPresenceConfig = Pick<DiscordAccountConfig, "activity" | "status" | "activityType" | "activityUrl">;
export declare function resolveDiscordPresenceUpdate(config: DiscordPresenceConfig): UpdatePresenceData | null;
export {};
