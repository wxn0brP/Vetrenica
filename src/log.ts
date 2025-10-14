import { TranscriptRes } from "./shared/types";

export function prettyPrintTranscript(res: TranscriptRes): void {
    const line = '─'.repeat(60);
    console.log(`\n${line}`);
    console.log(`📁  ${res.filename}`);
    console.log(`🧾  status: ${res.status}`);
    console.log(line);

    res.segments.forEach((seg, idx) => {
        const start = formatTime(seg.start);
        const end = formatTime(seg.end);
        console.log(`\n[${idx + 1}] ${start} → ${end}`);
        console.log(`    ${seg.text.trim()}`);
    });

    console.log(`${line}\n`);
}

function formatTime(sec: number): string {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 1000);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
}