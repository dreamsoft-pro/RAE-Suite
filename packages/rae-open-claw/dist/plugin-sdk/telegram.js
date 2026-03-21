import { g as normalizeAccountId, h as DEFAULT_ACCOUNT_ID } from "./session-key-CbP51u9x.js";
import { _ as formatPairingApproveHint } from "./channel-config-helpers-CX9AfjCJ.js";
import { $a as resolveTelegramGroupToolPolicy, Ea as listTelegramDirectoryPeersFromConfig, Mn as parseTelegramThreadId, Mt as projectCredentialSnapshotFields, Nt as resolveConfiguredFromCredentialStatuses, Qa as resolveTelegramGroupRequireMention, Ta as listTelegramDirectoryGroupsFromConfig, bs as getChatChannelMeta, do as resolveDefaultTelegramAccountId, fo as resolveTelegramAccount, jn as parseTelegramReplyToMessageId, lo as inspectTelegramAccount, m as TelegramConfigSchema, uo as listTelegramAccountIds } from "./thread-bindings-DxarhdX6.js";
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
import { B as clearAccountEntryFields, H as setAccountEnabledInConfigSection, V as deleteAccountFromConfigSection } from "./zod-schema.core-GWl_s9xp.js";
import "./redact-CqHkGWow.js";
import "./http-registry-CR-l0QpT.js";
import "./pairing-token-BwgaSu88.js";
import "./ssrf-Dlo7BZU6.js";
import "./fetch-guard-DEyOIg88.js";
import { i as resolveDefaultGroupPolicy, r as resolveAllowlistProviderRuntimeGroupPolicy } from "./runtime-group-policy-CDs_9_tb.js";
import "./registry-N-tffRct.js";
import "./http-body-CLS7yD5S.js";
import { t as emptyPluginConfigSchema } from "./config-schema-D85tZOYm.js";
import { o as buildTokenChannelStatusSummary } from "./status-helpers-BZuLH1ue.js";
import "./provider-env-vars-BJJqyIIb.js";
import "./helpers-DAMRJRRS.js";
import { r as migrateBaseNameToDefaultAccount, t as applyAccountNameToChannelSection } from "./setup-helpers-B1M39J3a.js";
import { i as buildChannelConfigSchema } from "./config-schema-BPehl1ON.js";
import { t as PAIRING_APPROVED_MESSAGE } from "./pairing-message-D2kONGcQ.js";
import "./shared-B4PQjsPw.js";
import { i as telegramOnboardingAdapter, n as looksLikeTelegramTargetId, r as normalizeTelegramMessagingTarget, t as collectTelegramStatusIssues } from "./telegram-B4ZoFrqL.js";
//#region src/channels/plugins/outbound/direct-text-media.ts
function resolvePayloadMediaUrls(payload) {
	return payload.mediaUrls?.length ? payload.mediaUrls : payload.mediaUrl ? [payload.mediaUrl] : [];
}
async function sendPayloadMediaSequence(params) {
	let lastResult;
	for (let i = 0; i < params.mediaUrls.length; i += 1) {
		const mediaUrl = params.mediaUrls[i];
		if (!mediaUrl) continue;
		lastResult = await params.send({
			text: i === 0 ? params.text : "",
			mediaUrl,
			index: i,
			isFirst: i === 0
		});
	}
	return lastResult;
}
//#endregion
//#region extensions/telegram/src/outbound-adapter.ts
async function sendTelegramPayloadMessages(params) {
	const telegramData = params.payload.channelData?.telegram;
	const quoteText = typeof telegramData?.quoteText === "string" ? telegramData.quoteText : void 0;
	const text = params.payload.text ?? "";
	const mediaUrls = resolvePayloadMediaUrls(params.payload);
	const payloadOpts = {
		...params.baseOpts,
		quoteText
	};
	if (mediaUrls.length === 0) return await params.send(params.to, text, {
		...payloadOpts,
		buttons: telegramData?.buttons
	});
	return await sendPayloadMediaSequence({
		text,
		mediaUrls,
		send: async ({ text, mediaUrl, isFirst }) => await params.send(params.to, text, {
			...payloadOpts,
			mediaUrl,
			...isFirst ? { buttons: telegramData?.buttons } : {}
		})
	}) ?? {
		messageId: "unknown",
		chatId: params.to
	};
}
//#endregion
export { DEFAULT_ACCOUNT_ID, PAIRING_APPROVED_MESSAGE, TelegramConfigSchema, applyAccountNameToChannelSection, buildChannelConfigSchema, buildTokenChannelStatusSummary, clearAccountEntryFields, collectTelegramStatusIssues, deleteAccountFromConfigSection, emptyPluginConfigSchema, formatPairingApproveHint, getChatChannelMeta, inspectTelegramAccount, listTelegramAccountIds, listTelegramDirectoryGroupsFromConfig, listTelegramDirectoryPeersFromConfig, looksLikeTelegramTargetId, migrateBaseNameToDefaultAccount, normalizeAccountId, normalizeTelegramMessagingTarget, parseTelegramReplyToMessageId, parseTelegramThreadId, projectCredentialSnapshotFields, resolveAllowlistProviderRuntimeGroupPolicy, resolveConfiguredFromCredentialStatuses, resolveDefaultGroupPolicy, resolveDefaultTelegramAccountId, resolveTelegramAccount, resolveTelegramGroupRequireMention, resolveTelegramGroupToolPolicy, sendTelegramPayloadMessages, setAccountEnabledInConfigSection, telegramOnboardingAdapter };
