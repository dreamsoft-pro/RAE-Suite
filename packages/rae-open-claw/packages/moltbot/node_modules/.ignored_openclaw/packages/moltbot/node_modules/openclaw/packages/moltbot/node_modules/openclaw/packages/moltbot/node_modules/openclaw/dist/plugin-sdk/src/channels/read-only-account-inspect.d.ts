import { type InspectedDiscordAccount } from "../../extensions/discord/src/account-inspect.js";
import { type InspectedSlackAccount } from "../../extensions/slack/src/account-inspect.js";
import { type InspectedTelegramAccount } from "../../extensions/telegram/src/account-inspect.js";
import type { OpenClawConfig } from "../config/config.js";
import type { ChannelId } from "./plugins/types.js";
export type ReadOnlyInspectedAccount = InspectedDiscordAccount | InspectedSlackAccount | InspectedTelegramAccount;
export declare function inspectReadOnlyChannelAccount(params: {
    channelId: ChannelId;
    cfg: OpenClawConfig;
    accountId?: string | null;
}): ReadOnlyInspectedAccount | null;
