import FalconFrame from "@wxn0brp/falcon-frame";
import { wws } from "./vars";
import { identifySpeaker, nearby } from "./speaker";
import { elapsed } from "./log";

const PORT = 55524;
const MAX_TEXT_LENGTH = 4000;

const app = new FalconFrame();

app.static("public");
app.static("dist");
app.static("src");

async function processText(text: string): Promise<void> {
	const startedAt = performance.now();
	try {
		const nearbyStartedAt = performance.now();
		const airCrafts = await nearby();
		console.log(
			`[process] nearby aircraft count=${airCrafts.length} elapsed=${elapsed(nearbyStartedAt)}`,
		);

		const identifyStartedAt = performance.now();
		const speaker = await identifySpeaker(text, airCrafts);
		console.log(
			`[process] speaker=${speaker} identify_elapsed=${elapsed(identifyStartedAt)}`,
		);

		console.log(
			`[process] emitting websocket data text_chars=${text.length} speaker=${speaker}`,
		);
		wws.of("/").emit("data", {
			segments: [
				{
					text,
				},
			],
			speaker,
		});
	} catch (error) {
		console.error("[process] processing failed", error);
	} finally {
		console.log(`[process] done elapsed=${elapsed(startedAt)}`);
	}
}

app.all("/process", async (req, res) => {
	const text = req.body.text ?? req.query.text;

	if (!text?.trim()) {
		res.status(400).end("error: missing text");
		return;
	}
	if (text.length > MAX_TEXT_LENGTH) {
		res.status(400).end(`error: text too long (max ${MAX_TEXT_LENGTH})`);
		return;
	}

	res.end("ok");
	processText(text.trim());
});

const server = app.listen(PORT, true);
console.log(`[http] server listening on port ${PORT}`);

wws.falconFrame(app);
wws.attachToHttpServer(server);
console.log("[ws] websocket server attached");

wws.of("/").onConnect(() => {
	console.log("[ws] client connected");
});
