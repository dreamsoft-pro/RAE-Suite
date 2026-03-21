import "./paths-tuenh9TL.js";
import "./subsystem-G54saDcg.js";
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
import "./links-BpKafJs4.js";
import "./cli-utils-BSURvrmb.js";
import "./runtime-guard-C4h47dl7.js";
import "./note-DOFTT6QH.js";
import "./daemon-install-plan.shared-_2PUY3Nl.js";
import { n as buildGatewayInstallPlan, r as gatewayInstallErrorHint, t as resolveGatewayInstallToken } from "./gateway-install-token-BXZUC2nq.js";
import { r as isGatewayDaemonRuntime } from "./daemon-runtime-CYx-YMxc.js";
import "./runtime-parse-l56zRsXX.js";
import "./launchd-BLFV2ME0.js";
import { n as resolveGatewayService } from "./service-RXVSlLiU.js";
import { i as isSystemdUserServiceAvailable } from "./systemd-D47rkLi7.js";
import { n as ensureSystemdUserLingerNonInteractive } from "./systemd-linger-DwmFZpci.js";
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
