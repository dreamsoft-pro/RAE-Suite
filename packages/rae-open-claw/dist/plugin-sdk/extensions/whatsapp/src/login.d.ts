import { type RuntimeEnv } from "../../../src/runtime.js";
import { waitForWaConnection } from "./session.js";
export declare function loginWeb(verbose: boolean, waitForConnection?: typeof waitForWaConnection, runtime?: RuntimeEnv, accountId?: string): Promise<void>;
