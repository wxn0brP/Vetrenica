import { unlinkSync } from "fs";
import { prettyPrintTranscript } from "./log";
import { sendToClients } from ".";
import { TranscriptRes } from "./shared/types";

async function getTranscribe(id: string): Promise<TranscriptRes> {
    const data = await fetch("http://localhost:55523/?id=" + id);
    return data.json();
}

export async function processNew(id: string) {
    const data = await getTranscribe(id);
    prettyPrintTranscript(data);
    unlinkSync("segments/" + id + ".wav");
    sendToClients(data);
}