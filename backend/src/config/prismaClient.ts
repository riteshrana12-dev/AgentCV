import { PrismaClient } from "@prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const client = new PrismaClient({
  adapter: new PrismaPg({
    connectionString: process.env["DATABASE_URL"] as string,
  }),
});

export default client;
