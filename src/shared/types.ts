export interface Transcript {
    start: number;
    end: number;
    text: string;
}

export interface TranscriptRes {
    filename: string;
    segments: Transcript[];
    status: string;
}
