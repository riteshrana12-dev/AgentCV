import { server } from "./websocket/server";

const PORT = Number(process.env.PORT) || 3001;

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Server is running on port ${PORT}`);
});
