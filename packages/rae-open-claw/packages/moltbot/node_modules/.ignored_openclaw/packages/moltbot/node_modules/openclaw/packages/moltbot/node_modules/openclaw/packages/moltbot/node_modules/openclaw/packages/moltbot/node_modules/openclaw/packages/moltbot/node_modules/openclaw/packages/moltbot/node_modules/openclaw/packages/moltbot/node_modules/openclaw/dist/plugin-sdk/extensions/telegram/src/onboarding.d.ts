import type { ChannelOnboardingAdapter } from "../../../src/channels/plugins/onboarding-types.js";
export declare function normalizeTelegramAllowFromInput(raw: string): string;
export declare function parseTelegramAllowFromId(raw: string): string | null;
export declare const telegramOnboardingAdapter: ChannelOnboardingAdapter;
