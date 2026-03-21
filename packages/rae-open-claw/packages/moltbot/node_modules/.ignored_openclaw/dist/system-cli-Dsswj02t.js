import "./paths-tuenh9TL.js";
import { A as theme, p as defaultRuntime, v as danger } from "./subsystem-G54saDcg.js";
import "./utils-B8zCe27d.js";
import "./reply-cpXZjA1O.js";
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
import { t as formatDocsLink } from "./links-BpKafJs4.js";
import "./cli-utils-BSURvrmb.js";
import { n as callGatewayFromCli, t as addGatewayClientOptions } from "./gateway-rpc-Ck7nI1T1.js";
//#region src/cli/system-cli.ts
const normalizeWakeMode = (raw) => {
	const mode = typeof raw === "string" ? raw.trim() : "";
	if (!mode) return "next-heartbeat";
	if (mode === "now" || mode === "next-heartbeat") return mode;
	throw new Error("--mode must be now or next-heartbeat");
};
async function runSystemGatewayCommand(opts, action, successText) {
	try {
		const result = await action();
		if (opts.json || successText === void 0) defaultRuntime.log(JSON.stringify(result, null, 2));
		else defaultRuntime.log(successText);
	} catch (err) {
		defaultRuntime.error(danger(String(err)));
		defaultRuntime.exit(1);
	}
}
function registerSystemCli(program) {
	const system = program.command("system").description("System tools (events, heartbeat, presence)").addHelpText("after", () => `\n${theme.muted("Docs:")} ${formatDocsLink("/cli/system", "docs.openclaw.ai/cli/system")}\n`);
	addGatewayClientOptions(system.command("event").description("Enqueue a system event and optionally trigger a heartbeat").requiredOption("--text <text>", "System event text").option("--mode <mode>", "Wake mode (now|next-heartbeat)", "next-heartbeat").option("--json", "Output JSON", false)).action(async (opts) => {
		await runSystemGatewayCommand(opts, async () => {
			const text = typeof opts.text === "string" ? opts.text.trim() : "";
			if (!text) throw new Error("--text is required");
			return await callGatewayFromCli("wake", opts, {
				mode: normalizeWakeMode(opts.mode),
				text
			}, { expectFinal: false });
		}, "ok");
	});
	const heartbeat = system.command("heartbeat").description("Heartbeat controls");
	addGatewayClientOptions(heartbeat.command("last").description("Show the last heartbeat event").option("--json", "Output JSON", false)).action(async (opts) => {
		await runSystemGatewayCommand(opts, async () => {
			return await callGatewayFromCli("last-heartbeat", opts, void 0, { expectFinal: false });
		});
	});
	addGatewayClientOptions(heartbeat.command("enable").description("Enable heartbeats").option("--json", "Output JSON", false)).action(async (opts) => {
		await runSystemGatewayCommand(opts, async () => {
			return await callGatewayFromCli("set-heartbeats", opts, { enabled: true }, { expectFinal: false });
		});
	});
	addGatewayClientOptions(heartbeat.command("disable").description("Disable heartbeats").option("--json", "Output JSON", false)).action(async (opts) => {
		await runSystemGatewayCommand(opts, async () => {
			return await callGatewayFromCli("set-heartbeats", opts, { enabled: false }, { expectFinal: false });
		});
	});
	addGatewayClientOptions(system.command("presence").description("List system presence entries").option("--json", "Output JSON", false)).action(async (opts) => {
		await runSystemGatewayCommand(opts, async () => {
			return await callGatewayFromCli("system-presence", opts, void 0, { expectFinal: false });
		});
	});
}
//#endregion
export { registerSystemCli };
