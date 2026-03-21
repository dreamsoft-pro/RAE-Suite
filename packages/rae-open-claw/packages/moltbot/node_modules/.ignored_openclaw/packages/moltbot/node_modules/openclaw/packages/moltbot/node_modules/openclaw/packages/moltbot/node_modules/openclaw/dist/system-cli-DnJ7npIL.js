import { A as theme, p as defaultRuntime, v as danger } from "./subsystem-BKSEV_2a.js";
import "./paths-dQ_clcF4.js";
import "./boolean-BHdNsbzF.js";
import "./send-C3_deGKY.js";
import "./utils-DBcXcVLM.js";
import "./env-overrides-DWTUPhKx.js";
import "./version-D0tcvzW0.js";
import "./agent-scope-CwU5BIqj.js";
import "./boundary-file-read-Bb0WDUIN.js";
import "./logger-6-BbUobc.js";
import "./exec-CLorXZJE.js";
import "./github-copilot-token-DQd7axD5.js";
import "./query-expansion-Cd6sO7e-.js";
import "./plugins-9Dsb9585.js";
import "./redact-Dwh0T4LH.js";
import "./registry-Cmzp1GgU.js";
import "./frontmatter-0S6BwMCg.js";
import "./path-alias-guards-D0OaD7WI.js";
import "./skills-Dm6Oukfq.js";
import "./fetch-BiG0XwdQ.js";
import "./errors-DpLnShUX.js";
import "./cmd-argv-DyLQYBHg.js";
import "./restart-stale-pids-DVmesqGw.js";
import "./delivery-queue-BC7FiiKY.js";
import "./paths-CtLQlqaT.js";
import "./session-cost-usage-CSeJhdaB.js";
import "./search-manager-rcsEvvDP.js";
import "./prompt-style-DF1oEAAo.js";
import { t as formatDocsLink } from "./links-Mq4qvFsN.js";
import "./cli-utils-CCDylRkX.js";
import { n as callGatewayFromCli, t as addGatewayClientOptions } from "./gateway-rpc-CjPawmO_.js";
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
