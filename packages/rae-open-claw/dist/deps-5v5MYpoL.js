//#region src/cli/outbound-send-mapping.ts
const LEGACY_SOURCE_TO_CHANNEL = {
	sendMessageWhatsApp: "whatsapp",
	sendMessageTelegram: "telegram",
	sendMessageDiscord: "discord",
	sendMessageSlack: "slack",
	sendMessageSignal: "signal",
	sendMessageIMessage: "imessage"
};
const CHANNEL_TO_LEGACY_DEP_KEY = {
	whatsapp: "sendWhatsApp",
	telegram: "sendTelegram",
	discord: "sendDiscord",
	slack: "sendSlack",
	signal: "sendSignal",
	imessage: "sendIMessage"
};
/**
* Pass CLI send sources through as-is — both CliOutboundSendSource and
* OutboundSendDeps are now channel-ID-keyed records.
*/
function createOutboundSendDepsFromCliSource(deps) {
	const outbound = { ...deps };
	for (const [legacySourceKey, channelId] of Object.entries(LEGACY_SOURCE_TO_CHANNEL)) {
		const sourceValue = deps[legacySourceKey];
		if (sourceValue !== void 0 && outbound[channelId] === void 0) outbound[channelId] = sourceValue;
	}
	for (const [channelId, legacyDepKey] of Object.entries(CHANNEL_TO_LEGACY_DEP_KEY)) {
		const sourceValue = outbound[channelId];
		if (sourceValue !== void 0 && outbound[legacyDepKey] === void 0) outbound[legacyDepKey] = sourceValue;
	}
	return outbound;
}
//#endregion
//#region src/cli/deps.ts
const senderCache = /* @__PURE__ */ new Map();
/**
* Create a lazy-loading send function proxy for a channel.
* The channel's module is loaded on first call and cached for reuse.
*/
function createLazySender(channelId, loader, exportName) {
	return async (...args) => {
		let cached = senderCache.get(channelId);
		if (!cached) {
			cached = loader();
			senderCache.set(channelId, cached);
		}
		const fn = (await cached)[exportName];
		return await fn(...args);
	};
}
function createDefaultDeps() {
	return {
		whatsapp: createLazySender("whatsapp", () => import("./web-BCGH1b-T.js"), "sendMessageWhatsApp"),
		telegram: createLazySender("telegram", () => import("./reply-cpXZjA1O.js").then((n) => n.st), "sendMessageTelegram"),
		discord: createLazySender("discord", () => import("./reply-cpXZjA1O.js").then((n) => n.fd), "sendMessageDiscord"),
		slack: createLazySender("slack", () => import("./reply-cpXZjA1O.js").then((n) => n.bt), "sendMessageSlack"),
		signal: createLazySender("signal", () => import("./reply-cpXZjA1O.js").then((n) => n.oa), "sendMessageSignal"),
		imessage: createLazySender("imessage", () => import("./reply-cpXZjA1O.js").then((n) => n.xt), "sendMessageIMessage")
	};
}
function createOutboundSendDeps(deps) {
	return createOutboundSendDepsFromCliSource(deps);
}
//#endregion
export { createOutboundSendDeps as n, createOutboundSendDepsFromCliSource as r, createDefaultDeps as t };
