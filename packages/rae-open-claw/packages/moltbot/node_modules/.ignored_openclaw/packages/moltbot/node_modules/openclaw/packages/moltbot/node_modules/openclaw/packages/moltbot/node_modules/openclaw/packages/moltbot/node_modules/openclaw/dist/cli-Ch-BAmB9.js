import "./paths-tuenh9TL.js";
import { t as createSubsystemLogger } from "./subsystem-G54saDcg.js";
import "./utils-B8zCe27d.js";
import { V as loadOpenClawPlugins, d_ as loadConfig } from "./reply-cpXZjA1O.js";
import { d as resolveAgentWorkspaceDir, f as resolveDefaultAgentId } from "./agent-scope-DmTcOjk4.js";
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
//#region src/plugins/cli.ts
const log = createSubsystemLogger("plugins");
function registerPluginCliCommands(program, cfg, env) {
	const config = cfg ?? loadConfig();
	const workspaceDir = resolveAgentWorkspaceDir(config, resolveDefaultAgentId(config));
	const logger = {
		info: (msg) => log.info(msg),
		warn: (msg) => log.warn(msg),
		error: (msg) => log.error(msg),
		debug: (msg) => log.debug(msg)
	};
	const registry = loadOpenClawPlugins({
		config,
		workspaceDir,
		env,
		logger
	});
	const existingCommands = new Set(program.commands.map((cmd) => cmd.name()));
	for (const entry of registry.cliRegistrars) {
		if (entry.commands.length > 0) {
			const overlaps = entry.commands.filter((command) => existingCommands.has(command));
			if (overlaps.length > 0) {
				log.debug(`plugin CLI register skipped (${entry.pluginId}): command already registered (${overlaps.join(", ")})`);
				continue;
			}
		}
		try {
			const result = entry.register({
				program,
				config,
				workspaceDir,
				logger
			});
			if (result && typeof result.then === "function") result.catch((err) => {
				log.warn(`plugin CLI register failed (${entry.pluginId}): ${String(err)}`);
			});
			for (const command of entry.commands) existingCommands.add(command);
		} catch (err) {
			log.warn(`plugin CLI register failed (${entry.pluginId}): ${String(err)}`);
		}
	}
}
//#endregion
export { registerPluginCliCommands };
