import { A as theme } from "./subsystem-BKSEV_2a.js";
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
import "./device-bootstrap-8StqluiZ.js";
import { registerQrCli } from "./qr-cli-DjWtpydV.js";
//#region src/cli/clawbot-cli.ts
function registerClawbotCli(program) {
	registerQrCli(program.command("clawbot").description("Legacy clawbot command aliases").addHelpText("after", () => `\n${theme.muted("Docs:")} ${formatDocsLink("/cli/clawbot", "docs.openclaw.ai/cli/clawbot")}\n`));
}
//#endregion
export { registerClawbotCli };
