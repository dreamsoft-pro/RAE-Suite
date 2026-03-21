import "./subsystem-BKSEV_2a.js";
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
import "./links-Mq4qvFsN.js";
import "./cli-utils-CCDylRkX.js";
import "./note-D8VBKvW3.js";
import "./daemon-install-plan.shared-CYiptEdb.js";
import "./runtime-guard-Bk0rI8d9.js";
import { n as buildGatewayInstallPlan, r as gatewayInstallErrorHint, t as resolveGatewayInstallToken } from "./gateway-install-token-CRCTbKpq.js";
import { r as isGatewayDaemonRuntime } from "./daemon-runtime-CjlHpTU-.js";
import "./runtime-parse-DwIldjg_.js";
import "./launchd-DaQfJlhP.js";
import { n as resolveGatewayService } from "./service-CXKirQDx.js";
import { i as isSystemdUserServiceAvailable } from "./systemd-D38NY5Ac.js";
import { n as ensureSystemdUserLingerNonInteractive } from "./systemd-linger-CVXfcOJY.js";
//#region src/commands/onboard-non-interactive/local/daemon-install.ts
async function installGatewayDaemonNonInteractive(params) {
	const { opts, runtime, port } = params;
	if (!opts.installDaemon) return { installed: false };
	const daemonRuntimeRaw = opts.daemonRuntime ?? "node";
	const systemdAvailable = process.platform === "linux" ? await isSystemdUserServiceAvailable() : true;
	if (process.platform === "linux" && !systemdAvailable) {
		runtime.log("Systemd user services are unavailable; skipping service install. Use a direct shell run (`openclaw gateway run`) or rerun without --install-daemon on this session.");
		return {
			installed: false,
			skippedReason: "systemd-user-unavailable"
		};
	}
	if (!isGatewayDaemonRuntime(daemonRuntimeRaw)) {
		runtime.error("Invalid --daemon-runtime (use node or bun)");
		runtime.exit(1);
		return { installed: false };
	}
	const service = resolveGatewayService();
	const tokenResolution = await resolveGatewayInstallToken({
		config: params.nextConfig,
		env: process.env
	});
	for (const warning of tokenResolution.warnings) runtime.log(warning);
	if (tokenResolution.unavailableReason) {
		runtime.error([
			"Gateway install blocked:",
			tokenResolution.unavailableReason,
			"Fix gateway auth config/token input and rerun onboarding."
		].join(" "));
		runtime.exit(1);
		return { installed: false };
	}
	const { programArguments, workingDirectory, environment } = await buildGatewayInstallPlan({
		env: process.env,
		port,
		runtime: daemonRuntimeRaw,
		warn: (message) => runtime.log(message),
		config: params.nextConfig
	});
	try {
		await service.install({
			env: process.env,
			stdout: process.stdout,
			programArguments,
			workingDirectory,
			environment
		});
	} catch (err) {
		runtime.error(`Gateway service install failed: ${String(err)}`);
		runtime.log(gatewayInstallErrorHint());
		return { installed: false };
	}
	await ensureSystemdUserLingerNonInteractive({ runtime });
	return { installed: true };
}
//#endregion
export { installGatewayDaemonNonInteractive };
