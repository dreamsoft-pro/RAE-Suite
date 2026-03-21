import type { ChannelThreadingContext, ChannelThreadingToolContext } from "../../../src/channels/plugins/types.js";
import type { OpenClawConfig } from "../../../src/config/config.js";
export declare function buildSlackThreadingToolContext(params: {
    cfg: OpenClawConfig;
    accountId?: string | null;
    context: ChannelThreadingContext;
    hasRepliedRef?: {
        value: boolean;
    };
}): ChannelThreadingToolContext;
