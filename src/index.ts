import FalconFrame from "@wxn0brp/falcon-frame";
import { processNew } from "./cpu";
import { wws } from "./vars";

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

wws.falconFrame(app);
wws.attachToHttpServer(server);

wws.of("/").onConnect(socket => {
    console.log("Client connected");
});
