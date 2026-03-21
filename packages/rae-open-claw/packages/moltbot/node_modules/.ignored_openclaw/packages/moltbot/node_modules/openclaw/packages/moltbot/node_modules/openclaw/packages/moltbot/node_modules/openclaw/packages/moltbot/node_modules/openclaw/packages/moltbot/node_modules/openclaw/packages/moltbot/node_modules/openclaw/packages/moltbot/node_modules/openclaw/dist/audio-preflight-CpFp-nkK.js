import { S as logVerbose, T as shouldLogVerbose } from "./subsystem-BKSEV_2a.js";
import "./paths-dQ_clcF4.js";
import "./boolean-BHdNsbzF.js";
import { Hf as normalizeMediaAttachments, Qf as isAudioAttachment, Uf as resolveMediaAttachmentLocalRoots, zf as runAudioTranscription } from "./send-C3_deGKY.js";
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
