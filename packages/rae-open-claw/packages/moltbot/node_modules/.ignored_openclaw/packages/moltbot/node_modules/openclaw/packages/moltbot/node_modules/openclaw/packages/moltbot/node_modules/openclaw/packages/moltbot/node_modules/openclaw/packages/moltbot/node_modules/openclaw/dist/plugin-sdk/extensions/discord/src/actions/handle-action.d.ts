import type { AgentToolResult } from "@mariozechner/pi-agent-core";
import type { ChannelMessageActionContext } from "../../../../src/channels/plugins/types.js";
export declare function handleDiscordMessageAction(ctx: Pick<ChannelMessageActionContext, "action" | "params" | "cfg" | "accountId" | "requesterSenderId" | "toolContext" | "mediaLocalRoots">): Promise<AgentToolResult<unknown>>;
