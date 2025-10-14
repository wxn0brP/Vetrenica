const transcriptsContainer = document.querySelector("#transcripts");
import type GlovesLinkClient from "@wxn0brp/gloves-link-client";
// @ts-ignore
import { GLC } from "/gloves-link/client.js";
import { TranscriptRes } from "../shared/types";

const socket: GlovesLinkClient = new GLC();

socket.on("connect", () => {
    console.log("Connected to server");
});

socket.on("data", (data) => {
    console.log(data);
    displayTranscript(data);
});

function displayTranscript(data: TranscriptRes) {
    const transcriptDiv = document.createElement("div");
    transcriptDiv.className = "transcript";

    const headerDiv = document.createElement("div");
    headerDiv.className = "transcript-header";
    headerDiv.innerHTML = `
        <h3>📁 ${data.filename}</h3>
        <p>🧾 Status: ${data.status}</p>
    `;

    transcriptDiv.appendChild(headerDiv);

    data.segments.forEach((segment, index) => {
        const segmentDiv = document.createElement("div");
        segmentDiv.className = "segment";
        segmentDiv.innerHTML = `
            <p class="time">[${index + 1}] ${formatTime(segment.start)} -> ${formatTime(segment.end)}</p>
            <p>${segment.text.trim()}</p>
        `;
        transcriptDiv.appendChild(segmentDiv);
    });

    transcriptsContainer.insertBefore(transcriptDiv, transcriptsContainer.firstChild);
    transcriptsContainer.scrollTop = 0;
}

function formatTime(sec: number): string {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 1000);
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}.${String(ms).padStart(3, "0")}`;
}