import FalconFrame from "@wxn0brp/falcon-frame";
import { GlovesLinkServer } from "@wxn0brp/gloves-link-server";
import { processNew } from "./cpu";
import { TranscriptRes } from "./shared/types";

const app = new FalconFrame();

app.static("public");
app.static("dist");
app.static("src");

app.get("/new", (req, res) => {
    const id = req.query.id;
    res.end(id ? "ok" : "error");
    processNew(id);
});

const server = app.listen(55524, true);

const wws = new GlovesLinkServer({});
wws.falconFrame(app);
wws.attachToHttpServer(server);

wws.of("/").onConnect(socket => {
    console.log("Client connected");
});

export function sendToClients(data: TranscriptRes) {
    wws.of("/").emit("data", data);
}
