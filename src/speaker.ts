import { Aircraft } from "./shared/types";

export async function nearby(): Promise<Aircraft[]> {
    const allData = await fetch("https://opensky-network.org/api/states/all?lamin=51.50&lomin=20.00&lamax=52.80&lomax=22.05").then(res => res.json());
    return allData.states.map((state: string[]) => {
        return {
            callSign: state[1].trim(),
            country: state[2],
        }
    }).filter((a: Aircraft) => a.callSign.length);
}

export async function identifySpeaker(
    transcription: string,
    airCrafts: Aircraft[]
): Promise<string> {
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

    const res = await fetch(`http://${process.env.OLLAMA_HOST || "localhost"}:11434/api/generate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            model: "qwen2.5:0.5b",
            prompt,
            stream: false
        })
    });

    if (!res.ok) {
        throw new Error(`Ollama error: ${res.status}`);
    }

    const data = await res.json();

    return data.response.trim();
}
