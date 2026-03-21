import type { BaseProbeResult } from "../../../src/channels/plugins/types.js";
export type SignalProbe = BaseProbeResult & {
    status?: number | null;
    elapsedMs: number;
    version?: string | null;
};
export declare function probeSignal(baseUrl: string, timeoutMs: number): Promise<SignalProbe>;
