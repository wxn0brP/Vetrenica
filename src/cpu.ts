import { unlinkSync } from "fs";
import { prettyPrintTranscript } from "./log";
import { TranscriptRes } from "./shared/types";
import { identifySpeaker, nearby } from "./speaker";
import { wws } from "./vars";
import { spawn } from "bun";

async function getTranscribe(id: string): Promise<TranscriptRes> {
    const data = await fetch("http://localhost:55523/?id=" + id);
    return data.json();
}

export async function processNew(id: string) {
    const data = await getTranscribe(id);
    prettyPrintTranscript(data);
    unlinkSync("/tmp/vetrenica/segments/" + id + ".wav");
    wws.of("/").emit("data", data);

    const airCrafts = await nearby();
    const speaker = await identifySpeaker(data.segments.map(s => s.text).join(" "), airCrafts);
    console.log("Speaker: ", speaker);
    spawn(["xdg-open", `https://www.flightradar24.com/${speaker}`]).unref();
}
