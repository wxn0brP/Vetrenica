import { Aircraft } from "./shared/types";
import { elapsed } from "./log";

export async function nearby(): Promise<Aircraft[]> {
	const startedAt = performance.now();
	const url =
		"https://opensky-network.org/api/states/all?lamin=51.50&lomin=20.00&lamax=52.80&lomax=22.05";
	console.log(`[speaker:nearby] fetching aircraft url=${url}`);
	const response = await fetch(url);
	console.log(
		`[speaker:nearby] opensky responded status=${response.status} elapsed=${elapsed(startedAt)}`,
	);
	if (!response.ok) {
		throw new Error(`OpenSky error: ${response.status}`);
	}

	const allData = await response.json();
	const rawStates = Array.isArray(allData.states) ? allData.states : [];
	console.log(`[speaker:nearby] raw states count=${rawStates.length}`);

	const aircraft = rawStates
		.map((state: string[]) => {
			return {
				callSign: state[1]?.trim() ?? "",
				country: state[2],
			};
		})
		.filter((a: Aircraft) => a.callSign.length);
	console.log(
		`[speaker:nearby] filtered aircraft count=${aircraft.length} sample=${aircraft
			.slice(0, 5)
			.map(a => a.callSign)
			.join(",")}`,
	);
	return aircraft;
}

export async function identifySpeaker(
	transcription: string,
	airCrafts: Aircraft[],
): Promise<string> {
	const startedAt = performance.now();
	const ollamaHost = process.env.OLLAMA_HOST || "localhost";
	console.log(
		`[speaker:identify] start transcription_chars=${transcription.length} aircraft_count=${airCrafts.length} ollama=${ollamaHost}`,
	);
	const prompt = `
You are an aviation radio communication analyzer.

Your task:
Based on the transcription and the list of aircraft, determine which aircraft is speaking.

Rules:
- Match call signs mentioned in the transcription
- Consider phonetic alphabet (e.g. "Lufthansa one two three")
- If multiple match, choose the most likely one
- If none match, return "unknown"

Return ONLY the call sign.

Transcription:
"${transcription}"

Aircraft list:
${airCrafts
	.map(a => `- call sign: ${a.callSign}, country: ${a.country}`)
	.join("\n")}
`;

	console.log(`[speaker:identify] prompt chars=${prompt.length}`);
	const requestStartedAt = performance.now();
	const res = await fetch(`http://${ollamaHost}:11434/api/generate`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			model: "qwen2.5:0.5b",
			prompt,
			stream: false,
		}),
	});
	console.log(
		`[speaker:identify] ollama responded status=${res.status} elapsed=${elapsed(requestStartedAt)}`,
	);

	if (!res.ok) {
		throw new Error(`Ollama error: ${res.status}`);
	}

	const data = await res.json();
	const speaker = data.response.trim();
	console.log(
		`[speaker:identify] result speaker=${speaker} response_chars=${data.response.length} total_elapsed=${elapsed(startedAt)}`,
	);

	return speaker;
}
