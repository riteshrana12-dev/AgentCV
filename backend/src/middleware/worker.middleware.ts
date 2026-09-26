import { Request, Response, NextFunction } from "express";

export const wokerMiddlewareSecret = (
  req: Request,
  res: Response,
  next: NextFunction,
) => {
  try {
    const secret = req.headers["x-worker-secret"];

    if (secret != process.env.WORKER_SECRET) {
      return res.status(401).json({
        success: false,
        message: "Unauthorized",
      });
    }
    return next();
  } catch (error: any) {
    return res.status(500).json({
      message: error.message,
    });
  }
};
