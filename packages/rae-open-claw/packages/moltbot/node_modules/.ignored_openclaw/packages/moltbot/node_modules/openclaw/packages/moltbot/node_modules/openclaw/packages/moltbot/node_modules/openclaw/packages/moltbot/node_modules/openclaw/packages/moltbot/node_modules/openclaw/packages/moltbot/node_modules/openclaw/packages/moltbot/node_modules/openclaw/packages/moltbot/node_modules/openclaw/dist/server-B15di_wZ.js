import "./paths-tuenh9TL.js";
import { t as createSubsystemLogger } from "./subsystem-G54saDcg.js";
import "./utils-B8zCe27d.js";
import { $m as createBrowserRouteContext, Ch as ensureBrowserControlAuth, Fm as installBrowserCommonMiddleware, Im as registerBrowserRoutes, Pm as installBrowserAuthMiddleware, Qm as stopBrowserRuntime, Zm as createBrowserRuntimeState, d_ as loadConfig, rh as resolveBrowserConfig, wh as resolveBrowserControlAuth } from "./reply-cpXZjA1O.js";
import "./agent-scope-DmTcOjk4.js";
import "./openclaw-root-B5jXk2td.js";
import "./logger-BohkHL0S.js";
import "./exec-CNtAq7Md.js";
import "./github-copilot-token-Ff890Vmh.js";
import "./boolean-B938tROv.js";
import "./env-CQxWwTMn.js";
import "./env-overrides-BYyMsIvB.js";
import "./registry-aHEgjCIQ.js";
import "./skills-BtMFdOkk.js";
import "./frontmatter-BngyYhS0.js";
import "./plugins-om7vnHk0.js";
import "./query-expansion-BNb6Vys6.js";
import "./redact-owRpqMhM.js";
import "./path-alias-guards-BEqdGdn9.js";
import "./fetch-CGW2R_wh.js";
import "./errors-DNKaAVHN.js";
import "./cmd-argv-BdNFwuhe.js";
import "./restart-stale-pids-ZfbSMILU.js";
import "./delivery-queue-B7zSt4zY.js";
import "./paths-CfmKJcO5.js";
import "./session-cost-usage-C2jrTKxW.js";
import "./prompt-style-DlcWUCNR.js";
import "./links-BpKafJs4.js";
import "./cli-utils-BSURvrmb.js";
import express from "express";
//#region src/browser/server.ts
let state = null;
const logServer = createSubsystemLogger("browser").child("server");
async function startBrowserControlServerFromConfig() {
	if (state) return state;
	const cfg = loadConfig();
	const resolved = resolveBrowserConfig(cfg.browser, cfg);
	if (!resolved.enabled) return null;
	let browserAuth = resolveBrowserControlAuth(cfg);
	let browserAuthBootstrapFailed = false;
	try {
		const ensured = await ensureBrowserControlAuth({ cfg });
		browserAuth = ensured.auth;
		if (ensured.generatedToken) logServer.info("No browser auth configured; generated gateway.auth.token automatically.");
	} catch (err) {
		logServer.warn(`failed to auto-configure browser auth: ${String(err)}`);
		browserAuthBootstrapFailed = true;
	}
	if (browserAuthBootstrapFailed && !browserAuth.token && !browserAuth.password) {
		logServer.error("browser control startup aborted: authentication bootstrap failed and no fallback auth is configured.");
		return null;
	}
	const app = express();
	installBrowserCommonMiddleware(app);
	installBrowserAuthMiddleware(app, browserAuth);
	registerBrowserRoutes(app, createBrowserRouteContext({
		getState: () => state,
		refreshConfigFromDisk: true
	}));
	const port = resolved.controlPort;
	const server = await new Promise((resolve, reject) => {
		const s = app.listen(port, "127.0.0.1", () => resolve(s));
		s.once("error", reject);
	}).catch((err) => {
		logServer.error(`openclaw browser server failed to bind 127.0.0.1:${port}: ${String(err)}`);
		return null;
	});
	if (!server) return null;
	state = await createBrowserRuntimeState({
		server,
		port,
		resolved,
		onWarn: (message) => logServer.warn(message)
	});
	const authMode = browserAuth.token ? "token" : browserAuth.password ? "password" : "off";
	logServer.info(`Browser control listening on http://127.0.0.1:${port}/ (auth=${authMode})`);
	return state;
}
async function stopBrowserControlServer() {
	await stopBrowserRuntime({
		current: state,
		getState: () => state,
		clearState: () => {
			state = null;
		},
		closeServer: true,
		onWarn: (message) => logServer.warn(message)
	});
}
//#endregion
export { startBrowserControlServerFromConfig, stopBrowserControlServer };
