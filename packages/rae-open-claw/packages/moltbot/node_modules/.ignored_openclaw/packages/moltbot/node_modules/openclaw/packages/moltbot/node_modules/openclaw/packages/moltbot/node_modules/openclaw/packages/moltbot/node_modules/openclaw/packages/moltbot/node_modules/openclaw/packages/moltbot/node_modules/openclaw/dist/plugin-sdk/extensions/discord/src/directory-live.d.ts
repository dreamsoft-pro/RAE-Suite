import type { DirectoryConfigParams } from "../../../src/channels/plugins/directory-config.js";
import type { ChannelDirectoryEntry } from "../../../src/channels/plugins/types.js";
export declare function listDiscordDirectoryGroupsLive(params: DirectoryConfigParams): Promise<ChannelDirectoryEntry[]>;
export declare function listDiscordDirectoryPeersLive(params: DirectoryConfigParams): Promise<ChannelDirectoryEntry[]>;
