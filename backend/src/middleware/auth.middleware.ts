import jwt from "jsonwebtoken";
import { Request, Response, NextFunction } from "express";
import { DecodedToken } from "../types/index";

export const authMiddleware = (
  req: Request,
  res: Response,
  next: NextFunction,
) => {
  try {
    const token = req.cookies?.token;
    if (!token) {
      return res
        .status(401)
        .json({ message: "Unauthorized: No token provided" });
    }
    // Verify and decode
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as DecodedToken;

    // Attach userId to request
    req.userId = decoded.userid;
    return next();
  } catch (err: any) {
    return res
      .status(401)
      .json({ message: "Unauthorized: Invalid token", error: err.message });
  }
};
