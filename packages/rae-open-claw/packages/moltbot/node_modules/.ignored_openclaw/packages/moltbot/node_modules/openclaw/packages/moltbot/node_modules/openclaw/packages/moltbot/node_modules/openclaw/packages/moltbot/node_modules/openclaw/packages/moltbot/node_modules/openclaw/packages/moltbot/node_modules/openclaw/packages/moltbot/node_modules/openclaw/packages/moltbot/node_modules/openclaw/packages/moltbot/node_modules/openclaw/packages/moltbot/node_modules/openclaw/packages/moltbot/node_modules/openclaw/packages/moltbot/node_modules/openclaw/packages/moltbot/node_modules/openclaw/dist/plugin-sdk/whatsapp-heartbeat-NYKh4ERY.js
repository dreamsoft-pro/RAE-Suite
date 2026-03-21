import { h as DEFAULT_ACCOUNT_ID } from "./session-key-CbP51u9x.js";
import { Fr as readChannelAllowFromStoreSync, qi as loadSessionStore, xs as normalizeChatChannelId } from "./thread-bindings-DxarhdX6.js";
import { d as normalizeE164 } from "./utils-BhiRkVxe.js";
import { R as resolveStorePath } from "./query-expansion-ChYs46vb.js";
//#region src/channels/plugins/whatsapp-heartbeat.ts
function getSessionRecipients(cfg) {
	if ((cfg.session?.scope ?? "per-sender") === "global") return [];
	const store = loadSessionStore(resolveStorePath(cfg.session?.store));
	const isGroupKey = (key) => key.includes(":group:") || key.includes(":channel:") || key.includes("@g.us");
	const isCronKey = (key) => key.startsWith("cron:");
	const recipients = Object.entries(store).filter(([key]) => key !== "global" && key !== "unknown").filter(([key]) => !isGroupKey(key) && !isCronKey(key)).map(([_, entry]) => ({
		to: normalizeChatChannelId(entry?.lastChannel) === "whatsapp" && entry?.lastTo ? normalizeE164(entry.lastTo) : "",
		updatedAt: entry?.updatedAt ?? 0
	})).filter(({ to }) => to.length > 1).toSorted((a, b) => b.updatedAt - a.updatedAt);
	const seen = /* @__PURE__ */ new Set();
	return recipients.filter((r) => {
		if (seen.has(r.to)) return false;
		seen.add(r.to);
		return true;
	});
}
function resolveWhatsAppHeartbeatRecipients(cfg, opts = {}) {
	if (opts.to) return {
		recipients: [normalizeE164(opts.to)],
		source: "flag"
	};
	const sessionRecipients = getSessionRecipients(cfg);
	const configuredAllowFrom = Array.isArray(cfg.channels?.whatsapp?.allowFrom) && cfg.channels.whatsapp.allowFrom.length > 0 ? cfg.channels.whatsapp.allowFrom.filter((v) => v !== "*").map(normalizeE164) : [];
	const storeAllowFrom = readChannelAllowFromStoreSync("whatsapp", process.env, DEFAULT_ACCOUNT_ID).map(normalizeE164);
	const unique = (list) => [...new Set(list.filter(Boolean))];
	const allowFrom = unique([...configuredAllowFrom, ...storeAllowFrom]);
	if (opts.all) return {
		recipients: unique([...sessionRecipients.map((s) => s.to), ...allowFrom]),
		source: "all"
	};
	if (allowFrom.length > 0) {
		const allowSet = new Set(allowFrom);
		const authorizedSessionRecipients = sessionRecipients.map((entry) => entry.to).filter((recipient) => allowSet.has(recipient));
		if (authorizedSessionRecipients.length === 1) return {
			recipients: [authorizedSessionRecipients[0]],
			source: "session-single"
		};
		if (authorizedSessionRecipients.length > 1) return {
			recipients: authorizedSessionRecipients,
			source: "session-ambiguous"
		};
		return {
			recipients: allowFrom,
			source: "allowFrom"
		};
	}
	if (sessionRecipients.length === 1) return {
		recipients: [sessionRecipients[0].to],
		source: "session-single"
	};
	if (sessionRecipients.length > 1) return {
		recipients: sessionRecipients.map((s) => s.to),
		source: "session-ambiguous"
	};
	return {
		recipients: allowFrom,
		source: "allowFrom"
	};
}
//#endregion
export { resolveWhatsAppHeartbeatRecipients as t };
