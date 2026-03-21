import "./channel-config-helpers-CX9AfjCJ.js";
import { Ei as resolveMediaAttachmentLocalRoots, Mi as isAudioAttachment, Si as runAudioTranscription, Ti as normalizeMediaAttachments } from "./thread-bindings-DxarhdX6.js";
import "./paths-WR8OhEmw.js";
import "./github-copilot-token-BGYH4ltJ.js";
import "./logger-D-go2oXy.js";
import "./tmp-openclaw-dir-DRPiOszV.js";
import { d as logVerbose, m as shouldLogVerbose } from "./subsystem-DOh66yR6.js";
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
//#region src/media-understanding/audio-preflight.ts
/**
* Transcribes the first audio attachment BEFORE mention checking.
* This allows voice notes to be processed in group chats with requireMention: true.
* Returns the transcript or undefined if transcription fails or no audio is found.
*/
async function transcribeFirstAudio(params) {
	const { ctx, cfg } = params;
	const audioConfig = cfg.tools?.media?.audio;
	if (!audioConfig || audioConfig.enabled === false) return;
	const attachments = normalizeMediaAttachments(ctx);
	if (!attachments || attachments.length === 0) return;
	const firstAudio = attachments.find((att) => att && isAudioAttachment(att) && !att.alreadyTranscribed);
	if (!firstAudio) return;
	if (shouldLogVerbose()) logVerbose(`audio-preflight: transcribing attachment ${firstAudio.index} for mention check`);
	try {
		const { transcript } = await runAudioTranscription({
			ctx,
			cfg,
			attachments,
			agentDir: params.agentDir,
			providers: params.providers,
			activeModel: params.activeModel,
			localPathRoots: resolveMediaAttachmentLocalRoots({
				cfg,
				ctx
			})
		});
		if (!transcript) return;
		firstAudio.alreadyTranscribed = true;
		if (shouldLogVerbose()) logVerbose(`audio-preflight: transcribed ${transcript.length} chars from attachment ${firstAudio.index}`);
		return transcript;
	} catch (err) {
		if (shouldLogVerbose()) logVerbose(`audio-preflight: transcription failed: ${String(err)}`);
		return;
	}
}
//#endregion
export { transcribeFirstAudio };
