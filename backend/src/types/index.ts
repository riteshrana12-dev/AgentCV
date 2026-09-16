import { JwtPayload } from "jsonwebtoken";

export interface DecodedToken extends JwtPayload {
  userId: string;
  email: string;
}
