import { b as resolveWhatsAppAccount } from "./channel-config-helpers-CX9AfjCJ.js";
import { Ra as resolveWhatsAppOutboundTarget, ar as createActionGate, cr as readReactionParams, ir as ToolAuthorizationError, lr as readStringParam, or as jsonResult } from "./thread-bindings-DxarhdX6.js";
import "./paths-WR8OhEmw.js";
import "./github-copilot-token-BGYH4ltJ.js";
import "./logger-D-go2oXy.js";
import "./tmp-openclaw-dir-DRPiOszV.js";
import "./subsystem-DOh66yR6.js";
import "./utils-BhiRkVxe.js";
import "./fetch-Cqwcg-Kq.js";
import "./exec-88qB5pUO.js";
import "./thinking-B2k7q5lY.js";
import "./query-expansion-ChYs46vb.js";
import "./logger-Jt8cCPPV.js";
import "./zod-schema.core-GWl_s9xp.js";
import "./redact-CqHkGWow.js";
import "./http-registry-CR-l0QpT.js";
import "./pairing-token-BwgaSu88.js";
import "./ssrf-Dlo7BZU6.js";
import "./fetch-guard-DEyOIg88.js";
import "./registry-N-tffRct.js";
import "./http-body-CLS7yD5S.js";
import { r as sendReactionWhatsApp } from "./send-Cv6ymWPw.js";
//#region src/agents/tools/whatsapp-target-auth.ts
function resolveAuthorizedWhatsAppOutboundTarget(params) {
	const account = resolveWhatsAppAccount({
		cfg: params.cfg,
		accountId: params.accountId
	});
	const resolution = resolveWhatsAppOutboundTarget({
		to: params.chatJid,
		allowFrom: account.allowFrom ?? [],
		mode: "implicit"
	});
	if (!resolution.ok) throw new ToolAuthorizationError(`WhatsApp ${params.actionLabel} blocked: chatJid "${params.chatJid}" is not in the configured allowFrom list for account "${account.accountId}".`);
	return {
		to: resolution.to,
		accountId: account.accountId
	};
}
//#endregion
//#region src/agents/tools/whatsapp-actions.ts
async function handleWhatsAppAction(params, cfg) {
	const action = readStringParam(params, "action", { required: true });
	const isActionEnabled = createActionGate(cfg.channels?.whatsapp?.actions);
	if (action === "react") {
		if (!isActionEnabled("reactions")) throw new Error("WhatsApp reactions are disabled.");
		const chatJid = readStringParam(params, "chatJid", { required: true });
		const messageId = readStringParam(params, "messageId", { required: true });
		const { emoji, remove, isEmpty } = readReactionParams(params, { removeErrorMessage: "Emoji is required to remove a WhatsApp reaction." });
		const participant = readStringParam(params, "participant");
		const accountId = readStringParam(params, "accountId");
		const fromMeRaw = params.fromMe;
		const fromMe = typeof fromMeRaw === "boolean" ? fromMeRaw : void 0;
		const resolved = resolveAuthorizedWhatsAppOutboundTarget({
			cfg,
			chatJid,
			accountId,
			actionLabel: "reaction"
		});
		const resolvedEmoji = remove ? "" : emoji;
		await sendReactionWhatsApp(resolved.to, messageId, resolvedEmoji, {
			verbose: false,
			fromMe,
			participant: participant ?? void 0,
			accountId: resolved.accountId
		});
		if (!remove && !isEmpty) return jsonResult({
			ok: true,
			added: emoji
		});
		return jsonResult({
			ok: true,
			removed: true
		});
	}
	throw new Error(`Unsupported WhatsApp action: ${action}`);
}
//#endregion
export { handleWhatsAppAction };
