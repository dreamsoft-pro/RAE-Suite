import type { DirectoryConfigParams } from "../../../src/channels/plugins/directory-config.js";
import type { ChannelDirectoryEntry } from "../../../src/channels/plugins/types.js";
export declare function listSlackDirectoryPeersLive(params: DirectoryConfigParams): Promise<ChannelDirectoryEntry[]>;
export declare function listSlackDirectoryGroupsLive(params: DirectoryConfigParams): Promise<ChannelDirectoryEntry[]>;
