import type { EventEmitter } from "node:events";
import type { RuntimeEnv } from "../../../src/runtime.js";
type GatewayEmitter = Pick<EventEmitter, "on" | "removeListener">;
export declare function attachDiscordGatewayLogging(params: {
    emitter?: GatewayEmitter;
    runtime: RuntimeEnv;
}): () => void;
export {};
