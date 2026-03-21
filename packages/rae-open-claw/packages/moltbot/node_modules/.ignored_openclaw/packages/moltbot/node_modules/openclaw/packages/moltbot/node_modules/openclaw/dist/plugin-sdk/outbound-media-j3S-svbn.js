import { fi as loadWebMedia } from "./thread-bindings-DxarhdX6.js";
//#region src/plugin-sdk/outbound-media.ts
async function loadOutboundMediaFromUrl(mediaUrl, options = {}) {
	return await loadWebMedia(mediaUrl, {
		maxBytes: options.maxBytes,
		localRoots: options.mediaLocalRoots
	});
}
//#endregion
export { loadOutboundMediaFromUrl as t };
