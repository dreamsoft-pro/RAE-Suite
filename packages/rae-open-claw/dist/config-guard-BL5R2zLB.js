import "./paths-tuenh9TL.js";
import { A as theme, O as colorize, X as shouldMigrateStateFromPath, k as isRich } from "./subsystem-G54saDcg.js";
import { S as shortenHomePath } from "./utils-B8zCe27d.js";
import { m_ as readConfigFileSnapshot } from "./reply-cpXZjA1O.js";
import "./agent-scope-DmTcOjk4.js";
import "./openclaw-root-B5jXk2td.js";
import "./logger-BohkHL0S.js";
import "./exec-CNtAq7Md.js";
import "./github-copilot-token-Ff890Vmh.js";
import { t as formatCliCommand } from "./command-format-p_4ya3m0.js";
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
import "./note-DOFTT6QH.js";
import { n as formatConfigIssueLines } from "./issue-format-DVRglcqF.js";
import { t as loadAndMaybeMigrateDoctorConfig } from "./doctor-config-flow-BaQ1VbS2.js";
//#region src/cli/program/config-guard.ts
const ALLOWED_INVALID_COMMANDS = new Set([
	"doctor",
	"logs",
	"health",
	"help",
	"status"
]);
const ALLOWED_INVALID_GATEWAY_SUBCOMMANDS = new Set([
	"status",
	"probe",
	"health",
	"discover",
	"call",
	"install",
	"uninstall",
	"start",
	"stop",
	"restart"
]);
let didRunDoctorConfigFlow = false;
let configSnapshotPromise = null;
function resetConfigGuardStateForTests() {
	didRunDoctorConfigFlow = false;
	configSnapshotPromise = null;
}
async function getConfigSnapshot() {
	if (process.env.VITEST === "true") return readConfigFileSnapshot();
	configSnapshotPromise ??= readConfigFileSnapshot();
	return configSnapshotPromise;
}
async function ensureConfigReady(params) {
	const commandPath = params.commandPath ?? [];
	if (!didRunDoctorConfigFlow && shouldMigrateStateFromPath(commandPath)) {
		didRunDoctorConfigFlow = true;
		const runDoctorConfigFlow = async () => loadAndMaybeMigrateDoctorConfig({
			options: { nonInteractive: true },
			confirm: async () => false
		});
		if (!params.suppressDoctorStdout) await runDoctorConfigFlow();
		else {
			const originalStdoutWrite = process.stdout.write.bind(process.stdout);
			const originalSuppressNotes = process.env.OPENCLAW_SUPPRESS_NOTES;
			process.stdout.write = (() => true);
			process.env.OPENCLAW_SUPPRESS_NOTES = "1";
			try {
				await runDoctorConfigFlow();
			} finally {
				process.stdout.write = originalStdoutWrite;
				if (originalSuppressNotes === void 0) delete process.env.OPENCLAW_SUPPRESS_NOTES;
				else process.env.OPENCLAW_SUPPRESS_NOTES = originalSuppressNotes;
			}
		}
	}
	const snapshot = await getConfigSnapshot();
	const commandName = commandPath[0];
	const subcommandName = commandPath[1];
	const allowInvalid = commandName ? ALLOWED_INVALID_COMMANDS.has(commandName) || commandName === "gateway" && subcommandName && ALLOWED_INVALID_GATEWAY_SUBCOMMANDS.has(subcommandName) : false;
	const issues = snapshot.exists && !snapshot.valid ? formatConfigIssueLines(snapshot.issues, "-", { normalizeRoot: true }) : [];
	const legacyIssues = snapshot.legacyIssues.length > 0 ? formatConfigIssueLines(snapshot.legacyIssues, "-") : [];
	if (!(snapshot.exists && !snapshot.valid)) return;
	const rich = isRich();
	const muted = (value) => colorize(rich, theme.muted, value);
	const error = (value) => colorize(rich, theme.error, value);
	const heading = (value) => colorize(rich, theme.heading, value);
	const commandText = (value) => colorize(rich, theme.command, value);
	params.runtime.error(heading("Config invalid"));
	params.runtime.error(`${muted("File:")} ${muted(shortenHomePath(snapshot.path))}`);
	if (issues.length > 0) {
		params.runtime.error(muted("Problem:"));
		params.runtime.error(issues.map((issue) => `  ${error(issue)}`).join("\n"));
	}
	if (legacyIssues.length > 0) {
		params.runtime.error(muted("Legacy config keys detected:"));
		params.runtime.error(legacyIssues.map((issue) => `  ${error(issue)}`).join("\n"));
	}
	params.runtime.error("");
	params.runtime.error(`${muted("Run:")} ${commandText(formatCliCommand("openclaw doctor --fix"))}`);
	if (!allowInvalid) params.runtime.exit(1);
}
const __test__ = { resetConfigGuardStateForTests };
//#endregion
export { __test__, ensureConfigReady };
